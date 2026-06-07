import ipaddress

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_3

from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
from ryu.lib.packet import arp
from ryu.lib.packet import ipv4
from ryu.lib.packet import icmp


VIRTUAL_GATEWAY_MAC = "00:00:00:00:fe:fe"

GATEWAY_IPS = {
    "10.10.10.254",
    "10.10.20.254",
    "10.10.30.254",
    "10.10.40.254",
    "10.10.50.254",
    "10.10.60.254",
    "10.10.70.254",
    "10.10.99.254",
}


class CampusL3ControllerV1(app_manager.RyuApp):
    """
    First professional L3-aware SDN controller.

    Features:
    - OpenFlow 1.3
    - Basic L2 learning
    - ARP reply for virtual gateway IP addresses
    - IPv4 inter-subnet forwarding by rewriting Ethernet headers
    - Initial flow installation for routed IPv4 traffic

    This is not yet the IDS/IPS controller.
    This is the routing foundation on which IDS/IPS will be added.
    """

    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(CampusL3ControllerV1, self).__init__(*args, **kwargs)

        self.mac_to_port = {}

        # Learned IP -> MAC mapping
        self.ip_to_mac = {}

        # Learned MAC -> datapath ID mapping
        self.mac_to_dpid = {}

        self.logger.info("Campus L3 Controller V1 started")

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto

        # Table-miss rule: send unknown packets to controller
        match = parser.OFPMatch()
        actions = [
            parser.OFPActionOutput(
                ofproto.OFPP_CONTROLLER,
                ofproto.OFPCML_NO_BUFFER
            )
        ]

        self.add_flow(
            datapath=datapath,
            priority=0,
            match=match,
            actions=actions
        )

        self.logger.info("Switch connected: dpid=%s", datapath.id)

    def add_flow(
        self,
        datapath,
        priority,
        match,
        actions,
        idle_timeout=30,
        hard_timeout=0
    ):
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto

        inst = [
            parser.OFPInstructionActions(
                ofproto.OFPIT_APPLY_ACTIONS,
                actions
            )
        ]

        mod = parser.OFPFlowMod(
            datapath=datapath,
            priority=priority,
            match=match,
            instructions=inst,
            idle_timeout=idle_timeout,
            hard_timeout=hard_timeout
        )

        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        dpid = datapath.id

        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto

        in_port = msg.match["in_port"]

        pkt = packet.Packet(msg.data)
        eth_pkt = pkt.get_protocol(ethernet.ethernet)

        if eth_pkt is None:
            return

        if eth_pkt.ethertype == ether_types.ETH_TYPE_LLDP:
            return

        src_mac = eth_pkt.src
        dst_mac = eth_pkt.dst

        self.mac_to_port.setdefault(dpid, {})
        self.mac_to_port[dpid][src_mac] = in_port
        self.mac_to_dpid[src_mac] = dpid

        arp_pkt = pkt.get_protocol(arp.arp)
        if arp_pkt:
            self.handle_arp(datapath, in_port, eth_pkt, arp_pkt)
            return

        ip_pkt = pkt.get_protocol(ipv4.ipv4)
        if ip_pkt:
            self.handle_ipv4(datapath, in_port, pkt, eth_pkt, ip_pkt, msg)
            return

        # Fallback L2 learning behavior
        if dst_mac in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst_mac]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]
        self.send_packet_out(datapath, msg, in_port, actions)

    def handle_arp(self, datapath, in_port, eth_pkt, arp_pkt):
        """
        Reply to ARP requests for virtual gateway IPs.
        Also learn host IP-MAC mappings.
        """
        src_ip = arp_pkt.src_ip
        src_mac = arp_pkt.src_mac
        dst_ip = arp_pkt.dst_ip

        if src_ip and src_mac:
            self.ip_to_mac[src_ip] = src_mac

        if arp_pkt.opcode == arp.ARP_REQUEST and dst_ip in GATEWAY_IPS:
            self.logger.info(
                "ARP request for gateway %s from %s/%s",
                dst_ip,
                src_ip,
                src_mac
            )

            self.send_arp_reply(
                datapath=datapath,
                out_port=in_port,
                target_mac=src_mac,
                target_ip=src_ip,
                gateway_ip=dst_ip
            )
            return

        # For non-gateway ARP, flood
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto
        actions = [parser.OFPActionOutput(ofproto.OFPP_FLOOD)]

        out = parser.OFPPacketOut(
            datapath=datapath,
            buffer_id=ofproto.OFP_NO_BUFFER,
            in_port=in_port,
            actions=actions,
            data=self.build_packet_data(eth_pkt, arp_pkt)
        )

        datapath.send_msg(out)

    def send_arp_reply(self, datapath, out_port, target_mac, target_ip, gateway_ip):
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto

        e = ethernet.ethernet(
            dst=target_mac,
            src=VIRTUAL_GATEWAY_MAC,
            ethertype=ether_types.ETH_TYPE_ARP
        )

        a = arp.arp(
            opcode=arp.ARP_REPLY,
            src_mac=VIRTUAL_GATEWAY_MAC,
            src_ip=gateway_ip,
            dst_mac=target_mac,
            dst_ip=target_ip
        )

        p = packet.Packet()
        p.add_protocol(e)
        p.add_protocol(a)
        p.serialize()

        actions = [parser.OFPActionOutput(out_port)]

        out = parser.OFPPacketOut(
            datapath=datapath,
            buffer_id=ofproto.OFP_NO_BUFFER,
            in_port=ofproto.OFPP_CONTROLLER,
            actions=actions,
            data=p.data
        )

        datapath.send_msg(out)

    def handle_ipv4(self, datapath, in_port, pkt, eth_pkt, ip_pkt, msg):
        """
        Basic routed forwarding.

        If destination IP is known, rewrite:
        - Ethernet source MAC to virtual gateway MAC
        - Ethernet destination MAC to destination host MAC

        Then forward using L2 learned output port if available.
        If output port is unknown, flood after rewrite.
        """
        dpid = datapath.id
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto

        src_ip = ip_pkt.src
        dst_ip = ip_pkt.dst
        src_mac = eth_pkt.src

        self.ip_to_mac[src_ip] = src_mac

        dst_mac = self.ip_to_mac.get(dst_ip)

        if not dst_mac:
            self.logger.info(
                "Unknown destination IP %s. Flooding packet for discovery.",
                dst_ip
            )
            actions = [parser.OFPActionOutput(ofproto.OFPP_FLOOD)]
            self.send_packet_out(datapath, msg, in_port, actions)
            return

        if dst_mac in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst_mac]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [
            parser.OFPActionSetField(eth_src=VIRTUAL_GATEWAY_MAC),
            parser.OFPActionSetField(eth_dst=dst_mac),
            parser.OFPActionOutput(out_port)
        ]

        match = parser.OFPMatch(
            eth_type=ether_types.ETH_TYPE_IP,
            ipv4_src=src_ip,
            ipv4_dst=dst_ip
        )

        self.add_flow(
            datapath=datapath,
            priority=20,
            match=match,
            actions=actions,
            idle_timeout=20
        )

        self.send_packet_out(datapath, msg, in_port, actions)

    def send_packet_out(self, datapath, msg, in_port, actions):
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto

        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(
            datapath=datapath,
            buffer_id=msg.buffer_id,
            in_port=in_port,
            actions=actions,
            data=data
        )

        datapath.send_msg(out)

    def build_packet_data(self, eth_pkt, payload_pkt):
        """
        Helper for packet serialization.
        Mainly used for ARP flood fallback.
        """
        p = packet.Packet()
        p.add_protocol(eth_pkt)
        p.add_protocol(payload_pkt)
        p.serialize()
        return p.data
