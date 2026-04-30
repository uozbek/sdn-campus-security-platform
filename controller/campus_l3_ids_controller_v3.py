import csv
import os
from datetime import datetime

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import (
    CONFIG_DISPATCHER,
    MAIN_DISPATCHER,
    DEAD_DISPATCHER,
    set_ev_cls,
)
from ryu.ofproto import ofproto_v1_3

from ryu.lib import hub
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
from ryu.lib.packet import arp
from ryu.lib.packet import ipv4


# -------------------------------------------------------------------
# Path and logging configuration
# -------------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, "logs")
FLOW_STATS_FILE = os.path.join(LOG_DIR, "flow_stats.csv")
STATS_INTERVAL = 5


# -------------------------------------------------------------------
# Virtual gateway configuration
# -------------------------------------------------------------------

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


# -------------------------------------------------------------------
# Static host mapping based on campus_topology_v1.py
# -------------------------------------------------------------------

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


# -------------------------------------------------------------------
# Static host-facing ports
# -------------------------------------------------------------------
#
# These values are based on the Mininet net output:
#
# h1  h1-eth0:s4-eth2
# h2  h2-eth0:s4-eth3
# h3  h3-eth0:s4-eth4
# h4  h4-eth0:s4-eth5
#
# h5  h5-eth0:s5-eth2
# h6  h6-eth0:s5-eth3
# h7  h7-eth0:s5-eth4
# h8  h8-eth0:s5-eth5
# h9  h9-eth0:s5-eth6
# h10 h10-eth0:s5-eth7
# h11 h11-eth0:s5-eth8
#
# h12 h12-eth0:s6-eth2
# h13 h13-eth0:s6-eth3
# h14 h14-eth0:s6-eth4
#
# h15 h15-eth0:s7-eth2
# h16 h16-eth0:s7-eth3
# -------------------------------------------------------------------

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


# -------------------------------------------------------------------
# Static switch-to-switch port mapping
# -------------------------------------------------------------------
#
# Based on Mininet net output:
#
# s1-eth1 <-> s2-eth1
# s1-eth2 <-> s3-eth1
#
# s2-eth1 <-> s1-eth1
# s2-eth2 <-> s4-eth1
# s2-eth3 <-> s5-eth1
#
# s3-eth1 <-> s1-eth2
# s3-eth2 <-> s6-eth1
# s3-eth3 <-> s7-eth1
#
# s4-eth1 <-> s2-eth2
# s5-eth1 <-> s2-eth3
# s6-eth1 <-> s3-eth2
# s7-eth1 <-> s3-eth3
# -------------------------------------------------------------------

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


class CampusL3IdsControllerV3(app_manager.RyuApp):
    """
    Campus L3 IDS Controller V3.

    This controller provides the routing foundation for the SDN-based
    IDS/IPS prototype.

    Features:
    - OpenFlow 1.3
    - Virtual gateway ARP replies
    - Static-path L3 forwarding
    - Ethernet source/destination rewrite for routed IPv4 traffic
    - Flow rule installation for IPv4 source/destination pairs
    - Periodic OpenFlow flow statistics collection
    - CSV logging for IDS/ML feature extraction

    This version does not yet call the ML inference API.
    That will be added in the next phase.
    """

    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(CampusL3IdsControllerV3, self).__init__(*args, **kwargs)

        self.datapaths = {}

        os.makedirs(LOG_DIR, exist_ok=True)
        self._init_flow_stats_file()

        self.monitor_thread = hub.spawn(self._monitor)

        self.logger.info("Campus L3 IDS Controller V3 started")

    # ----------------------------------------------------------------
    # Initial OpenFlow setup
    # ----------------------------------------------------------------

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        self.datapaths[datapath.id] = datapath

        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto

        # Table-miss rule:
        # Any unmatched packet is sent to the controller.
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

    def add_flow(
        self,
        datapath,
        priority,
        match,
        actions,
        idle_timeout=60,
        hard_timeout=0
    ):
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

    # ----------------------------------------------------------------
    # CSV logging
    # ----------------------------------------------------------------

    def _init_flow_stats_file(self):
        with open(FLOW_STATS_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "timestamp",
                "datapath_id",
                "priority",
                "ipv4_src",
                "ipv4_dst",
                "ip_proto",
                "duration_sec",
                "packet_count",
                "byte_count",
                "packet_rate",
                "byte_rate"
            ])

    # ----------------------------------------------------------------
    # Datapath registration and monitoring
    # ----------------------------------------------------------------

    @set_ev_cls(ofp_event.EventOFPStateChange, [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def state_change_handler(self, ev):
        datapath = ev.datapath

        if ev.state == MAIN_DISPATCHER:
            if datapath.id not in self.datapaths:
                self.logger.info("Register datapath: %s", datapath.id)
                self.datapaths[datapath.id] = datapath

        elif ev.state == DEAD_DISPATCHER:
            if datapath.id in self.datapaths:
                self.logger.info("Unregister datapath: %s", datapath.id)
                del self.datapaths[datapath.id]

    def _monitor(self):
        while True:
            for datapath in list(self.datapaths.values()):
                self._request_flow_stats(datapath)

            hub.sleep(STATS_INTERVAL)

    def _request_flow_stats(self, datapath):
        parser = datapath.ofproto_parser
        req = parser.OFPFlowStatsRequest(datapath)
        datapath.send_msg(req)

    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def flow_stats_reply_handler(self, ev):
        timestamp = datetime.utcnow().isoformat()
        datapath_id = ev.msg.datapath.id

        with open(FLOW_STATS_FILE, "a", newline="") as f:
            writer = csv.writer(f)

            for stat in ev.msg.body:
                # Skip table-miss rule.
                if stat.priority == 0:
                    continue

                match = stat.match

                ipv4_src = match.get("ipv4_src", "")
                ipv4_dst = match.get("ipv4_dst", "")
                ip_proto = match.get("ip_proto", "")

                # Only log IPv4 source/destination flows.
                if not ipv4_src or not ipv4_dst:
                    continue

                duration = max(float(stat.duration_sec), 1.0)
                packet_count = float(stat.packet_count)
                byte_count = float(stat.byte_count)

                packet_rate = packet_count / duration
                byte_rate = byte_count / duration

                writer.writerow([
                    timestamp,
                    datapath_id,
                    stat.priority,
                    ipv4_src,
                    ipv4_dst,
                    ip_proto,
                    stat.duration_sec,
                    int(packet_count),
                    int(byte_count),
                    packet_rate,
                    byte_rate
                ])

    # ----------------------------------------------------------------
    # Packet-In handling
    # ----------------------------------------------------------------

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
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

    # ----------------------------------------------------------------
    # ARP handling
    # ----------------------------------------------------------------

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

        actions = [
            parser.OFPActionOutput(ofproto.OFPP_FLOOD)
        ]

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

        actions = [
            parser.OFPActionOutput(out_port)
        ]

        out = parser.OFPPacketOut(
            datapath=datapath,
            buffer_id=ofproto.OFP_NO_BUFFER,
            in_port=ofproto.OFPP_CONTROLLER,
            actions=actions,
            data=p.data
        )

        datapath.send_msg(out)

    def rebuild_arp_packet(self, arp_pkt):
        """
        Rebuild an ARP packet as an Ethernet broadcast frame.
        This is used for same-subnet ARP flooding.
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

    # ----------------------------------------------------------------
    # IPv4 routing
    # ----------------------------------------------------------------

    def handle_ipv4(self, datapath, in_port, ip_pkt, msg):
        dpid = datapath.id
        src_ip = ip_pkt.src
        dst_ip = ip_pkt.dst

        if dst_ip in GATEWAY_IPS:
            # In this version, the controller replies to ARP for gateway IPs,
            # but it does not generate ICMP Echo Reply for gateway ping.
            return

        if src_ip not in HOSTS:
            self.logger.warning("Unknown source IP: %s", src_ip)
            return

        if dst_ip not in HOSTS:
            self.logger.warning("Unknown destination IP: %s", dst_ip)
            return

        out_port = self.get_output_port(
            current_dpid=dpid,
            dst_ip=dst_ip
        )

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

        self.send_packet_out(
            datapath=datapath,
            msg=msg,
            in_port=in_port,
            actions=actions
        )

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

        # If the current switch is the destination edge switch,
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

        # If current switch is the core switch.
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
