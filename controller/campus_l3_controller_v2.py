from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_3

from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
from ryu.lib.packet import arp
from ryu.lib.packet import ipv4


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


# Static IP to MAC mapping based on campus_topology_v1.py
HOSTS = {
    "10.10.10.1":  {"mac": "00:00:00:00:10:01", "edge_switch": 4},
    "10.10.10.2":  {"mac": "00:00:00:00:10:02", "edge_switch": 4},
    "10.10.10.3":  {"mac": "00:00:00:00:10:03", "edge_switch": 4},
    "10.10.10.4":  {"mac": "00:00:00:00:10:04", "edge_switch": 4},

    "10.10.20.5":  {"mac": "00:00:00:00:20:05", "edge_switch": 5},
    "10.10.20.6":  {"mac": "00:00:00:00:20:06", "edge_switch": 5},
    "10.10.20.7":  {"mac": "00:00:00:00:20:07", "edge_switch": 5},

    "10.10.30.8":  {"mac": "00:00:00:00:30:08", "edge_switch": 5},
    "10.10.30.9":  {"mac": "00:00:00:00:30:09", "edge_switch": 5},

    "10.10.50.10": {"mac": "00:00:00:00:50:10", "edge_switch": 5},
    "10.10.50.11": {"mac": "00:00:00:00:50:11", "edge_switch": 5},

    "10.10.60.12": {"mac": "00:00:00:00:60:12", "edge_switch": 6},
    "10.10.60.13": {"mac": "00:00:00:00:60:13", "edge_switch": 6},

    "10.10.40.14": {"mac": "00:00:00:00:40:14", "edge_switch": 6},

    "10.10.70.15": {"mac": "00:00:00:00:70:15", "edge_switch": 7},
    "10.10.99.16": {"mac": "00:00:00:00:99:16", "edge_switch": 7},
}


# Host-facing ports based on addLink order in campus_topology_v1.py.
# Important:
# On each access switch, host links were added after inter-switch links.
# Mininet generally assigns ports in link creation order.
HOST_PORTS = {
    4: {
        "10.10.10.1": 2,
        "10.10.10.2": 3,
        "10.10.10.3": 4,
        "10.10.10.4": 5,
    },
    5: {
        "10.10.20.5": 2,
        "10.10.20.6": 3,
        "10.10.20.7": 4,
        "10.10.30.8": 5,
        "10.10.30.9": 6,
        "10.10.50.10": 7,
        "10.10.50.11": 8,
    },
    6: {
        "10.10.60.12": 2,
        "10.10.60.13": 3,
        "10.10.40.14": 4,
    },
    7: {
        "10.10.70.15": 2,
        "10.10.99.16": 3,
    },
}


# Static switch-to-switch output ports.
# These values come from link creation order:
# s1-s2, s1-s3, s2-s4, s2-s5, s3-s6, s3-s7
#
# Expected ports:
# s1: port1 -> s2, port2 -> s3
# s2: port1 -> s1, port2 -> s4, port3 -> s5
# s3: port1 -> s1, port2 -> s6, port3 -> s7
# s4: port1 -> s2
# s5: port1 -> s2
# s6: port1 -> s3
# s7: port1 -> s3
UPLINK_PORT = {
    4: 1,
    5: 1,
    6: 1,
    7: 1,
}

DIST_TO_ACCESS_PORT = {
    2: {
        4: 2,
        5: 3,
    },
    3: {
        6: 2,
        7: 3,
    },
}

CORE_TO_DIST_PORT = {
    1: {
        2: 1,
        3: 2,
    }
}

DIST_TO_CORE_PORT = {
    2: 1,
    3: 1,
}


EDGE_TO_DIST = {
    4: 2,
    5: 2,
    6: 3,
    7: 3,
}


class CampusL3ControllerV2(app_manager.RyuApp):
    """
    Static-path L3-aware campus controller.

    This controller is intentionally deterministic for the first professional prototype.

    Features:
    - OpenFlow 1.3
    - Gateway ARP replies
    - Static host mapping
    - Static inter-switch forwarding
    - Ethernet rewrite for routed IPv4 traffic
    - Flow installation for IPv4 src/dst pairs
    """

    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(CampusL3ControllerV2, self).__init__(*args, **kwargs)
        self.datapaths = {}
        self.logger.info("Campus L3 Controller V2 started")

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        self.datapaths[datapath.id] = datapath

        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto

        # Table-miss: send unknown packets to controller
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
            actions=actions,
            idle_timeout=0
        )

        self.logger.info("Switch connected: dpid=%s", datapath.id)

    def add_flow(self, datapath, priority, match, actions, idle_timeout=60, hard_timeout=0):
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto

        instructions = [
            parser.OFPInstructionActions(
                ofproto.OFPIT_APPLY_ACTIONS,
                actions
            )
        ]

        mod = parser.OFPFlowMod(
            datapath=datapath,
            priority=priority,
            match=match,
            instructions=instructions,
            idle_timeout=idle_timeout,
            hard_timeout=hard_timeout
        )

        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        dpid = datapath.id
        in_port = msg.match["in_port"]

        pkt = packet.Packet(msg.data)
        eth_pkt = pkt.get_protocol(ethernet.ethernet)

        if eth_pkt is None:
            return

        if eth_pkt.ethertype == ether_types.ETH_TYPE_LLDP:
            return

        arp_pkt = pkt.get_protocol(arp.arp)
        if arp_pkt:
            self.handle_arp(datapath, in_port, arp_pkt)
            return

        ip_pkt = pkt.get_protocol(ipv4.ipv4)
        if ip_pkt:
            self.handle_ipv4(datapath, in_port, ip_pkt, msg)
            return

    def handle_arp(self, datapath, in_port, arp_pkt):
        src_ip = arp_pkt.src_ip
        dst_ip = arp_pkt.dst_ip

        if arp_pkt.opcode == arp.ARP_REQUEST and dst_ip in GATEWAY_IPS:
            self.logger.info(
                "ARP gateway request: src_ip=%s dst_gateway=%s dpid=%s in_port=%s",
                src_ip,
                dst_ip,
                datapath.id,
                in_port
            )

            self.send_arp_reply(
                datapath=datapath,
                out_port=in_port,
                target_mac=arp_pkt.src_mac,
                target_ip=src_ip,
                gateway_ip=dst_ip
            )
            return

        # For same-subnet ARP, flood.
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto

        actions = [parser.OFPActionOutput(ofproto.OFPP_FLOOD)]

        out = parser.OFPPacketOut(
            datapath=datapath,
            buffer_id=ofproto.OFP_NO_BUFFER,
            in_port=in_port,
            actions=actions,
            data=self.rebuild_arp_packet(arp_pkt)
        )

        datapath.send_msg(out)

    def send_arp_reply(self, datapath, out_port, target_mac, target_ip, gateway_ip):
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto

        eth_reply = ethernet.ethernet(
            dst=target_mac,
            src=VIRTUAL_GATEWAY_MAC,
            ethertype=ether_types.ETH_TYPE_ARP
        )

        arp_reply = arp.arp(
            opcode=arp.ARP_REPLY,
            src_mac=VIRTUAL_GATEWAY_MAC,
            src_ip=gateway_ip,
            dst_mac=target_mac,
            dst_ip=target_ip
        )

        p = packet.Packet()
        p.add_protocol(eth_reply)
        p.add_protocol(arp_reply)
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

    def handle_ipv4(self, datapath, in_port, ip_pkt, msg):
        dpid = datapath.id
        src_ip = ip_pkt.src
        dst_ip = ip_pkt.dst

        if dst_ip in GATEWAY_IPS:
            # We do not answer ICMP to gateway in this version.
            return

        if src_ip not in HOSTS:
            self.logger.warning("Unknown source IP: %s", src_ip)
            return

        if dst_ip not in HOSTS:
            self.logger.warning("Unknown destination IP: %s", dst_ip)
            return

        out_port = self.get_output_port(current_dpid=dpid, dst_ip=dst_ip)

        if out_port is None:
            self.logger.warning(
                "No output port found: dpid=%s src_ip=%s dst_ip=%s",
                dpid,
                src_ip,
                dst_ip
            )
            return

        dst_mac = HOSTS[dst_ip]["mac"]

        parser = datapath.ofproto_parser

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
            priority=100,
            match=match,
            actions=actions,
            idle_timeout=60
        )

        self.send_packet_out(datapath, msg, in_port, actions)

        self.logger.info(
            "IPv4 routed: dpid=%s src=%s dst=%s out_port=%s dst_mac=%s",
            dpid,
            src_ip,
            dst_ip,
            out_port,
            dst_mac
        )

    def get_output_port(self, current_dpid, dst_ip):
        dst_edge = HOSTS[dst_ip]["edge_switch"]

        # If we are already on the destination edge switch,
        # output to the host-facing port.
        if current_dpid == dst_edge:
            return HOST_PORTS[dst_edge].get(dst_ip)

        # If current switch is an access switch,
        # send traffic upward to its distribution switch.
        if current_dpid in UPLINK_PORT:
            return UPLINK_PORT[current_dpid]

        # If current switch is a distribution switch.
        if current_dpid in [2, 3]:
            current_dist = current_dpid
            dst_dist = EDGE_TO_DIST[dst_edge]

            if current_dist == dst_dist:
                return DIST_TO_ACCESS_PORT[current_dist][dst_edge]

            return DIST_TO_CORE_PORT[current_dist]

        # If current switch is core.
        if current_dpid == 1:
            dst_dist = EDGE_TO_DIST[dst_edge]
            return CORE_TO_DIST_PORT[1][dst_dist]

        return None

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

    def rebuild_arp_packet(self, arp_pkt):
        """
        For same-subnet ARP flooding.
        This function builds a broadcast Ethernet frame for the ARP payload.
        """
        eth_broadcast = ethernet.ethernet(
            dst="ff:ff:ff:ff:ff:ff",
            src=arp_pkt.src_mac,
            ethertype=ether_types.ETH_TYPE_ARP
        )

        p = packet.Packet()
        p.add_protocol(eth_broadcast)
        p.add_protocol(arp_pkt)
        p.serialize()

        return p.data
