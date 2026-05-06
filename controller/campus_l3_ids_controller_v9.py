import csv
import os
import json
import time
import http.client
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
# Path, logging, monitoring and ML API configuration
# -------------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, "logs")

FLOW_STATS_FILE = os.path.join(LOG_DIR, "flow_stats.csv")
PREDICTIONS_FILE = os.path.join(LOG_DIR, "predictions.csv")
POLICY_DECISIONS_FILE = os.path.join(LOG_DIR, "policy_decisions.csv")
MITIGATION_LOG_FILE = os.path.join(LOG_DIR, "mitigation_log.csv")
RATE_LIMIT_LOG_FILE = os.path.join(LOG_DIR, "rate_limit_log.csv")
QUARANTINE_LOG_FILE = os.path.join(LOG_DIR, "quarantine_log.csv")

STATS_INTERVAL = 5

ML_API_HOST = "127.0.0.1"
ML_API_PORT = 8000
ML_API_PATH = "/predict"
ML_API_TIMEOUT = 1.5


# -------------------------------------------------------------------
# Policy Engine configuration
# -------------------------------------------------------------------

POLICY_MONITOR_THRESHOLD = 0.70
POLICY_RATE_LIMIT_THRESHOLD = 0.85
POLICY_DROP_THRESHOLD = 0.95
POLICY_QUARANTINE_THRESHOLD = 0.97

REPEATED_ATTACK_THRESHOLD = 3


# -------------------------------------------------------------------
# Mitigation configuration
# -------------------------------------------------------------------

MITIGATION_ENABLED = True

MITIGATION_DROP_PRIORITY = 300
MITIGATION_DROP_IDLE_TIMEOUT = 60
MITIGATION_DROP_HARD_TIMEOUT = 120

MITIGATION_ACTIONS = {
    "drop",
}

# -------------------------------------------------------------------
# Rate-limit configuration
# -------------------------------------------------------------------

RATE_LIMIT_ENABLED = True

RATE_LIMIT_PRIORITY = 250
RATE_LIMIT_IDLE_TIMEOUT = 60
RATE_LIMIT_HARD_TIMEOUT = 120

# OpenFlow meter rate uses kbps when OFPMF_KBPS is selected.
# 2000 kbps = 2 Mbps.
RATE_LIMIT_KBPS = 2000

RATE_LIMIT_BURST_SIZE_KB = 256

RATE_LIMIT_ACTIONS = {
    "rate_limit",
}


# -------------------------------------------------------------------
# Quarantine forwarding configuration
# -------------------------------------------------------------------

QUARANTINE_ENABLED = True

QUARANTINE_IP = "10.10.99.16"
QUARANTINE_MAC = "00:00:00:00:99:16"

QUARANTINE_PRIORITY = 350
QUARANTINE_IDLE_TIMEOUT = 120
QUARANTINE_HARD_TIMEOUT = 300

QUARANTINE_ACTIONS = {
    "quarantine_candidate",
}


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
# Campus host inventory
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


EDGE_SWITCHES = {4, 5, 6, 7}


# -------------------------------------------------------------------
# Static host-facing ports
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


class CampusL3IdsControllerV9(app_manager.RyuApp):
    """
    Campus L3 IDS Controller V9.

    New in V9:
    - Policy Engine is preserved from V6.
    - OpenFlow drop mitigation is added for drop/quarantine_candidate decisions.
    - Mitigation events are logged to mitigation_log.csv.
    - Drop rules are temporary and protocol-aware.

    This version applies OpenFlow drop mitigation, OpenFlow meter-based rate-limit mitigation,
    and quarantine forwarding for repeated high-confidence attack sources.
    """

    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(CampusL3IdsControllerV9, self).__init__(*args, **kwargs)

        self.datapaths = {}

        # Previous flow counters for delta-based rate calculation.
        # key:
        #   (datapath_id, ipv4_src, ipv4_dst, ip_proto)
        # value:
        #   {
        #       "timestamp_monotonic": float,
        #       "packet_count": float,
        #       "byte_count": float
        #   }
        self.previous_flow_counters = {}

        # Tracks repeated attack-like decisions per source IP.
        # key: ipv4_src
        # value: repeated suspicious/drop count
        self.source_risk_counters = {}
        self.active_mitigations = {}

        # Tracks active rate-limit rules to avoid reinstalling them repeatedly.
        # key:
        #   (src_ip, dst_ip, ip_proto)
        # value:
        #   timestamp_iso
        self.active_rate_limits = {}

        # Tracks active quarantine rules to avoid reinstalling them repeatedly.
        # key:
        #   (src_ip, ip_proto)
        # value:
        #   timestamp_iso
        self.active_quarantines = {}

        # OpenFlow meter IDs are local to each datapath.
        self.next_meter_id = 1
        self.installed_meters = set()

        os.makedirs(LOG_DIR, exist_ok=True)

        self._init_flow_stats_file()
        self._init_predictions_file()
        self._init_policy_decisions_file()
        self._init_mitigation_log_file()
        self._init_rate_limit_log_file()
        self._init_quarantine_log_file()

        self.monitor_thread = hub.spawn(self._monitor)

        self.logger.info("Campus L3 IDS Controller V9 started")

    # ----------------------------------------------------------------
    # Initial OpenFlow setup
    # ----------------------------------------------------------------

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        self.datapaths[datapath.id] = datapath

        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto

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
    # CSV initialization
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
                "cumulative_packet_rate",
                "cumulative_byte_rate",
                "delta_time_sec",
                "delta_packet_count",
                "delta_byte_count",
                "packet_rate",
                "byte_rate",
                "is_source_edge"
            ])

    def _init_predictions_file(self):
        with open(PREDICTIONS_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "timestamp",
                "datapath_id",
                "ipv4_src",
                "ipv4_dst",
                "ip_proto",
                "duration_sec",
                "packet_count",
                "byte_count",
                "packet_rate",
                "byte_rate",
                "prediction",
                "confidence",
                "recommended_action",
                "model_id",
                "model_name",
                "inference_latency_ms",
                "controller_ml_roundtrip_ms",
                "api_status"
            ])

    def _init_policy_decisions_file(self):
        with open(POLICY_DECISIONS_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "timestamp",
                "datapath_id",
                "ipv4_src",
                "ipv4_dst",
                "ip_proto",
                "packet_rate",
                "byte_rate",
                "ml_prediction",
                "ml_confidence",
                "ml_recommended_action",
                "policy_final_action",
                "policy_reason",
                "source_risk_count"
            ])

    def _init_mitigation_log_file(self):
        with open(MITIGATION_LOG_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "timestamp",
                "src_ip",
                "dst_ip",
                "ip_proto",
                "policy_final_action",
                "mitigation_action",
                "datapath_id",
                "priority",
                "idle_timeout",
                "hard_timeout",
                "status",
                "reason"
            ])

    def _init_rate_limit_log_file(self):
        with open(RATE_LIMIT_LOG_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "timestamp",
                "src_ip",
                "dst_ip",
                "ip_proto",
                "policy_final_action",
                "mitigation_action",
                "datapath_id",
                "meter_id",
                "rate_limit_kbps",
                "burst_size_kb",
                "priority",
                "idle_timeout",
                "hard_timeout",
                "status",
                "reason"
            ])

    def _init_quarantine_log_file(self):
        with open(QUARANTINE_LOG_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "timestamp",
                "src_ip",
                "original_dst_ip",
                "quarantine_ip",
                "ip_proto",
                "policy_final_action",
                "mitigation_action",
                "datapath_id",
                "priority",
                "idle_timeout",
                "hard_timeout",
                "status",
                "reason"
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

    # ----------------------------------------------------------------
    # ML API integration
    # ----------------------------------------------------------------

    def ask_ml_api(self, features):
        """
        Send flow features to the ML inference API using stdlib http.client.

        Fail-open behavior:
        If the ML API is unreachable or returns an error, the controller
        logs the issue but recommends 'allow'.
        """

        start_time = datetime.utcnow()

        try:
            payload = json.dumps(features)

            conn = http.client.HTTPConnection(
                ML_API_HOST,
                ML_API_PORT,
                timeout=ML_API_TIMEOUT
            )

            headers = {
                "Content-Type": "application/json"
            }

            conn.request(
                "POST",
                ML_API_PATH,
                body=payload,
                headers=headers
            )

            response = conn.getresponse()
            response_body = response.read().decode("utf-8")

            end_time = datetime.utcnow()
            roundtrip_ms = (end_time - start_time).total_seconds() * 1000

            if response.status == 200:
                result = json.loads(response_body)
                result["controller_ml_roundtrip_ms"] = roundtrip_ms
                result["api_status"] = "ok"
                conn.close()
                return result

            conn.close()

            return {
                "prediction": "api_error",
                "confidence": 0.0,
                "recommended_action": "allow",
                "model_id": "",
                "model_name": "",
                "inference_latency_ms": 0.0,
                "controller_ml_roundtrip_ms": roundtrip_ms,
                "api_status": f"http_{response.status}"
            }

        except Exception as exc:
            end_time = datetime.utcnow()
            roundtrip_ms = (end_time - start_time).total_seconds() * 1000

            self.logger.warning("ML API request failed: %s", str(exc))

            return {
                "prediction": "api_unreachable",
                "confidence": 0.0,
                "recommended_action": "allow",
                "model_id": "",
                "model_name": "",
                "inference_latency_ms": 0.0,
                "controller_ml_roundtrip_ms": roundtrip_ms,
                "api_status": "unreachable"
            }

    def append_prediction_log(self, timestamp, features, ml_result):
        with open(PREDICTIONS_FILE, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                timestamp,
                features.get("datapath_id", ""),
                features.get("ipv4_src", ""),
                features.get("ipv4_dst", ""),
                features.get("ip_proto", ""),
                features.get("duration_sec", ""),
                features.get("packet_count", ""),
                features.get("byte_count", ""),
                features.get("packet_rate", ""),
                features.get("byte_rate", ""),
                ml_result.get("prediction", ""),
                ml_result.get("confidence", ""),
                ml_result.get("recommended_action", ""),
                ml_result.get("model_id", ""),
                ml_result.get("model_name", ""),
                ml_result.get("inference_latency_ms", ""),
                ml_result.get("controller_ml_roundtrip_ms", ""),
                ml_result.get("api_status", "")
            ])

    # ----------------------------------------------------------------
    # Policy Engine
    # ----------------------------------------------------------------

    def evaluate_policy(self, features, ml_result):
        """
        Convert ML output into a policy decision.

        This function does not install OpenFlow mitigation rules yet.
        It only produces a final action for logging and future mitigation.

        Final actions:
        - allow
        - monitor
        - rate_limit
        - drop
        - quarantine_candidate
        """

        src_ip = features.get("ipv4_src", "")
        dst_ip = features.get("ipv4_dst", "")
        ip_proto = features.get("ip_proto", None)

        confidence = float(ml_result.get("confidence", 0.0) or 0.0)
        ml_action = ml_result.get("recommended_action", "allow")
        prediction = ml_result.get("prediction", "unknown")

        # Track risk per flow instead of only per source IP.
        # This prevents benign TCP control traffic or zero-rate flow stats
        # from immediately reducing the risk score of an active UDP attack flow.
        risk_key = (
            src_ip,
            dst_ip,
            int(ip_proto) if ip_proto is not None else 0
        )

        current_risk_count = self.source_risk_counters.get(risk_key, 0)

        final_action = "allow"
        reason = "confidence_below_monitor_threshold"

        if confidence < POLICY_MONITOR_THRESHOLD:
            final_action = "allow"
            reason = "confidence_below_monitor_threshold"

            # Do not aggressively reduce the risk counter on zero-rate benign
            # observations, because flow stats continue to appear after traffic stops.
            # A future version can decay this counter with timestamps.
            self.source_risk_counters[risk_key] = current_risk_count

        elif POLICY_MONITOR_THRESHOLD <= confidence < POLICY_RATE_LIMIT_THRESHOLD:
            final_action = "monitor"
            reason = "confidence_between_monitor_and_rate_limit"

        elif POLICY_RATE_LIMIT_THRESHOLD <= confidence < POLICY_DROP_THRESHOLD:
            final_action = "rate_limit"
            reason = "confidence_between_rate_limit_and_drop"

            self.source_risk_counters[risk_key] = current_risk_count + 1

        elif confidence >= POLICY_DROP_THRESHOLD:
            final_action = "drop"
            reason = "confidence_above_drop_threshold"

            self.source_risk_counters[risk_key] = current_risk_count + 1

        updated_risk_count = self.source_risk_counters.get(risk_key, 0)

        if (
            confidence >= POLICY_DROP_THRESHOLD
            and updated_risk_count >= REPEATED_ATTACK_THRESHOLD
        ):
            final_action = "quarantine_candidate"
            reason = "repeated_high_confidence_attack"

        if ml_result.get("api_status") != "ok":
            final_action = "allow"
            reason = "ml_api_not_ok_fail_open"

        return {
            "final_action": final_action,
            "reason": reason,
            "source_risk_count": self.source_risk_counters.get(risk_key, 0),
            "ml_prediction": prediction,
            "ml_recommended_action": ml_action,
            "ml_confidence": confidence
        }
		
    def append_policy_decision_log(self, timestamp, features, ml_result, policy_result):
        with open(POLICY_DECISIONS_FILE, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                timestamp,
                features.get("datapath_id", ""),
                features.get("ipv4_src", ""),
                features.get("ipv4_dst", ""),
                features.get("ip_proto", ""),
                features.get("packet_rate", ""),
                features.get("byte_rate", ""),
                ml_result.get("prediction", ""),
                ml_result.get("confidence", ""),
                ml_result.get("recommended_action", ""),
                policy_result.get("final_action", ""),
                policy_result.get("reason", ""),
                policy_result.get("source_risk_count", "")
            ])

    # ----------------------------------------------------------------
    # Mitigation
    # ----------------------------------------------------------------

    def append_mitigation_log(
        self,
        timestamp,
        src_ip,
        dst_ip,
        ip_proto,
        policy_final_action,
        mitigation_action,
        datapath_id,
        status,
        reason
    ):
        with open(MITIGATION_LOG_FILE, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                timestamp,
                src_ip,
                dst_ip,
                ip_proto,
                policy_final_action,
                mitigation_action,
                datapath_id,
                MITIGATION_DROP_PRIORITY,
                MITIGATION_DROP_IDLE_TIMEOUT,
                MITIGATION_DROP_HARD_TIMEOUT,
                status,
                reason
            ])

    def should_apply_mitigation(self, policy_result):
        if not MITIGATION_ENABLED:
            return False

        final_action = policy_result.get("final_action", "allow")
        return final_action in MITIGATION_ACTIONS

    def mitigation_key(self, features):
        return (
            features.get("ipv4_src", ""),
            features.get("ipv4_dst", ""),
            int(features.get("ip_proto") or 0)
        )

    def install_drop_rules_for_flow(self, features, policy_result):
        src_ip = features.get("ipv4_src", "")
        dst_ip = features.get("ipv4_dst", "")
        ip_proto = features.get("ip_proto", None)
        final_action = policy_result.get("final_action", "")

        if not src_ip or not dst_ip:
            return

        key = self.mitigation_key(features)

        if key in self.active_mitigations:
            return

        self.active_mitigations[key] = datetime.utcnow().isoformat()

        for datapath_id, datapath in list(self.datapaths.items()):
            parser = datapath.ofproto_parser

            if ip_proto is None:
                match = parser.OFPMatch(
                    eth_type=ether_types.ETH_TYPE_IP,
                    ipv4_src=src_ip,
                    ipv4_dst=dst_ip
                )
            else:
                match = parser.OFPMatch(
                    eth_type=ether_types.ETH_TYPE_IP,
                    ipv4_src=src_ip,
                    ipv4_dst=dst_ip,
                    ip_proto=int(ip_proto)
                )

            actions = []

            self.add_flow(
                datapath=datapath,
                priority=MITIGATION_DROP_PRIORITY,
                match=match,
                actions=actions,
                idle_timeout=MITIGATION_DROP_IDLE_TIMEOUT,
                hard_timeout=MITIGATION_DROP_HARD_TIMEOUT
            )

            self.append_mitigation_log(
                timestamp=datetime.utcnow().isoformat(),
                src_ip=src_ip,
                dst_ip=dst_ip,
                ip_proto=ip_proto if ip_proto is not None else "",
                policy_final_action=final_action,
                mitigation_action="drop",
                datapath_id=datapath_id,
                status="installed",
                reason=policy_result.get("reason", "")
            )

        self.logger.warning(
            "Mitigation installed: DROP src=%s dst=%s proto=%s final_action=%s reason=%s",
            src_ip,
            dst_ip,
            ip_proto,
            final_action,
            policy_result.get("reason", "")
        )


    def append_rate_limit_log(
        self,
        timestamp,
        src_ip,
        dst_ip,
        ip_proto,
        policy_final_action,
        mitigation_action,
        datapath_id,
        meter_id,
        status,
        reason
    ):
        with open(RATE_LIMIT_LOG_FILE, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                timestamp,
                src_ip,
                dst_ip,
                ip_proto,
                policy_final_action,
                mitigation_action,
                datapath_id,
                meter_id,
                RATE_LIMIT_KBPS,
                RATE_LIMIT_BURST_SIZE_KB,
                RATE_LIMIT_PRIORITY,
                RATE_LIMIT_IDLE_TIMEOUT,
                RATE_LIMIT_HARD_TIMEOUT,
                status,
                reason
            ])

    def should_apply_rate_limit(self, policy_result):
        if not RATE_LIMIT_ENABLED:
            return False

        final_action = policy_result.get("final_action", "allow")
        return final_action in RATE_LIMIT_ACTIONS

    def rate_limit_key(self, features):
        return (
            features.get("ipv4_src", ""),
            features.get("ipv4_dst", ""),
            int(features.get("ip_proto") or 0)
        )

    def allocate_meter_id(self, datapath_id):
        """
        Allocate a small integer meter ID.

        Meter IDs are datapath-local in OpenFlow, but we still track
        (datapath_id, meter_id) to avoid duplicates.
        """

        while (datapath_id, self.next_meter_id) in self.installed_meters:
            self.next_meter_id += 1

        meter_id = self.next_meter_id
        self.installed_meters.add((datapath_id, meter_id))
        self.next_meter_id += 1

        return meter_id

    def install_meter(self, datapath, meter_id):
        """
        Install an OpenFlow 1.3 meter on the datapath.

        The meter uses KBPS mode and a DROP band.
        Traffic above RATE_LIMIT_KBPS is dropped by the meter.
        """

        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto

        bands = [
            parser.OFPMeterBandDrop(
                rate=RATE_LIMIT_KBPS,
                burst_size=RATE_LIMIT_BURST_SIZE_KB
            )
        ]

        req = parser.OFPMeterMod(
            datapath=datapath,
            command=ofproto.OFPMC_ADD,
            flags=ofproto.OFPMF_KBPS,
            meter_id=meter_id,
            bands=bands
        )

        datapath.send_msg(req)

    def add_metered_flow(
        self,
        datapath,
        priority,
        match,
        meter_id,
        actions,
        idle_timeout=60,
        hard_timeout=0
    ):
        """
        Add a flow with a meter instruction followed by normal forwarding actions.
        """

        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto

        instructions = [
            parser.OFPInstructionMeter(meter_id, ofproto.OFPIT_METER),
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

    def install_rate_limit_for_flow(self, features, policy_result):
        """
        Install a rate-limit rule on the source edge switch.

        V8 strategy:
        - Apply rate-limit only at the source edge switch.
        - Match IPv4 src/dst/proto.
        - Attach an OpenFlow meter.
        - Preserve normal L3 forwarding actions after metering.
        """

        src_ip = features.get("ipv4_src", "")
        dst_ip = features.get("ipv4_dst", "")
        ip_proto = features.get("ip_proto", None)
        final_action = policy_result.get("final_action", "")

        if not src_ip or not dst_ip:
            return

        if src_ip not in HOSTS:
            return

        key = self.rate_limit_key(features)

        if key in self.active_rate_limits:
            return

        source_edge_dpid = HOSTS[src_ip]["edge_switch"]
        datapath = self.datapaths.get(source_edge_dpid)

        if datapath is None:
            self.append_rate_limit_log(
                timestamp=datetime.utcnow().isoformat(),
                src_ip=src_ip,
                dst_ip=dst_ip,
                ip_proto=ip_proto if ip_proto is not None else "",
                policy_final_action=final_action,
                mitigation_action="rate_limit",
                datapath_id=source_edge_dpid,
                meter_id="",
                status="failed",
                reason="source_edge_datapath_not_registered"
            )
            return

        out_port = self.get_output_port(
            current_dpid=source_edge_dpid,
            dst_ip=dst_ip
        )

        if out_port is None:
            self.append_rate_limit_log(
                timestamp=datetime.utcnow().isoformat(),
                src_ip=src_ip,
                dst_ip=dst_ip,
                ip_proto=ip_proto if ip_proto is not None else "",
                policy_final_action=final_action,
                mitigation_action="rate_limit",
                datapath_id=source_edge_dpid,
                meter_id="",
                status="failed",
                reason="no_output_port_for_source_edge"
            )
            return

        parser = datapath.ofproto_parser

        if ip_proto is None:
            match = parser.OFPMatch(
                eth_type=ether_types.ETH_TYPE_IP,
                ipv4_src=src_ip,
                ipv4_dst=dst_ip
            )
        else:
            match = parser.OFPMatch(
                eth_type=ether_types.ETH_TYPE_IP,
                ipv4_src=src_ip,
                ipv4_dst=dst_ip,
                ip_proto=int(ip_proto)
            )

        dst_mac = HOSTS[dst_ip]["mac"]

        actions = [
            parser.OFPActionSetField(eth_src=VIRTUAL_GATEWAY_MAC),
            parser.OFPActionSetField(eth_dst=dst_mac),
            parser.OFPActionOutput(out_port)
        ]

        meter_id = self.allocate_meter_id(source_edge_dpid)
        self.install_meter(datapath, meter_id)

        self.add_metered_flow(
            datapath=datapath,
            priority=RATE_LIMIT_PRIORITY,
            match=match,
            meter_id=meter_id,
            actions=actions,
            idle_timeout=RATE_LIMIT_IDLE_TIMEOUT,
            hard_timeout=RATE_LIMIT_HARD_TIMEOUT
        )

        self.active_rate_limits[key] = datetime.utcnow().isoformat()

        self.append_rate_limit_log(
            timestamp=datetime.utcnow().isoformat(),
            src_ip=src_ip,
            dst_ip=dst_ip,
            ip_proto=ip_proto if ip_proto is not None else "",
            policy_final_action=final_action,
            mitigation_action="rate_limit",
            datapath_id=source_edge_dpid,
            meter_id=meter_id,
            status="installed",
            reason=policy_result.get("reason", "")
        )

        self.logger.warning(
            "Rate-limit installed: src=%s dst=%s proto=%s dpid=%s meter_id=%s rate=%s kbps",
            src_ip,
            dst_ip,
            ip_proto,
            source_edge_dpid,
            meter_id,
            RATE_LIMIT_KBPS
        )



    # ----------------------------------------------------------------
    # Quarantine forwarding
    # ----------------------------------------------------------------

    def append_quarantine_log(
        self,
        timestamp,
        src_ip,
        original_dst_ip,
        ip_proto,
        policy_final_action,
        mitigation_action,
        datapath_id,
        status,
        reason
    ):
        with open(QUARANTINE_LOG_FILE, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                timestamp,
                src_ip,
                original_dst_ip,
                QUARANTINE_IP,
                ip_proto,
                policy_final_action,
                mitigation_action,
                datapath_id,
                QUARANTINE_PRIORITY,
                QUARANTINE_IDLE_TIMEOUT,
                QUARANTINE_HARD_TIMEOUT,
                status,
                reason
            ])

    def should_apply_quarantine(self, policy_result):
        if not QUARANTINE_ENABLED:
            return False

        final_action = policy_result.get("final_action", "allow")
        return final_action in QUARANTINE_ACTIONS

    def quarantine_key(self, features):
        return (
            features.get("ipv4_src", ""),
            int(features.get("ip_proto") or 0)
        )

    def install_quarantine_forwarding_for_source(self, features, policy_result):
        """
        Install quarantine/sinkhole forwarding rules.

        V9 strategy:
        - Triggered by quarantine_candidate.
        - Match source IP and protocol.
        - Rewrite IPv4 destination to QUARANTINE_IP.
        - Rewrite Ethernet destination to QUARANTINE_MAC.
        - Forward traffic toward h16 using the static topology path.
        - Install on all datapaths to make forwarding consistent across the campus topology.
        """

        src_ip = features.get("ipv4_src", "")
        original_dst_ip = features.get("ipv4_dst", "")
        ip_proto = features.get("ip_proto", None)
        final_action = policy_result.get("final_action", "")

        if not src_ip:
            return

        key = self.quarantine_key(features)

        if key in self.active_quarantines:
            return

        self.active_quarantines[key] = datetime.utcnow().isoformat()

        for datapath_id, datapath in list(self.datapaths.items()):
            out_port = self.get_output_port(
                current_dpid=datapath_id,
                dst_ip=QUARANTINE_IP
            )

            if out_port is None:
                self.append_quarantine_log(
                    timestamp=datetime.utcnow().isoformat(),
                    src_ip=src_ip,
                    original_dst_ip=original_dst_ip,
                    ip_proto=ip_proto if ip_proto is not None else "",
                    policy_final_action=final_action,
                    mitigation_action="quarantine_forward",
                    datapath_id=datapath_id,
                    status="failed",
                    reason="no_output_port_to_quarantine"
                )
                continue

            parser = datapath.ofproto_parser

            if ip_proto is None:
                match = parser.OFPMatch(
                    eth_type=ether_types.ETH_TYPE_IP,
                    ipv4_src=src_ip
                )
            else:
                match = parser.OFPMatch(
                    eth_type=ether_types.ETH_TYPE_IP,
                    ipv4_src=src_ip,
                    ip_proto=int(ip_proto)
                )

            actions = [
                parser.OFPActionSetField(eth_src=VIRTUAL_GATEWAY_MAC),
                parser.OFPActionSetField(eth_dst=QUARANTINE_MAC),
                parser.OFPActionSetField(ipv4_dst=QUARANTINE_IP),
                parser.OFPActionOutput(out_port)
            ]

            self.add_flow(
                datapath=datapath,
                priority=QUARANTINE_PRIORITY,
                match=match,
                actions=actions,
                idle_timeout=QUARANTINE_IDLE_TIMEOUT,
                hard_timeout=QUARANTINE_HARD_TIMEOUT
            )

            self.append_quarantine_log(
                timestamp=datetime.utcnow().isoformat(),
                src_ip=src_ip,
                original_dst_ip=original_dst_ip,
                ip_proto=ip_proto if ip_proto is not None else "",
                policy_final_action=final_action,
                mitigation_action="quarantine_forward",
                datapath_id=datapath_id,
                status="installed",
                reason=policy_result.get("reason", "")
            )

        self.logger.warning(
            "Quarantine forwarding installed: src=%s original_dst=%s proto=%s quarantine_ip=%s final_action=%s reason=%s",
            src_ip,
            original_dst_ip,
            ip_proto,
            QUARANTINE_IP,
            final_action,
            policy_result.get("reason", "")
        )


    # ----------------------------------------------------------------
    # Delta-based flow statistics
    # ----------------------------------------------------------------

    def calculate_delta_rates(
        self,
        datapath_id,
        ipv4_src,
        ipv4_dst,
        ip_proto,
        packet_count,
        byte_count
    ):
        now = time.monotonic()
        key = (
            int(datapath_id),
            ipv4_src,
            ipv4_dst,
            int(ip_proto) if ip_proto != "" else 0
        )

        previous = self.previous_flow_counters.get(key)

        if previous is None:
            self.previous_flow_counters[key] = {
                "timestamp_monotonic": now,
                "packet_count": packet_count,
                "byte_count": byte_count
            }

            return {
                "delta_time_sec": 0.0,
                "delta_packet_count": 0.0,
                "delta_byte_count": 0.0,
                "packet_rate": 0.0,
                "byte_rate": 0.0
            }

        delta_time = max(now - previous["timestamp_monotonic"], 0.000001)
        delta_packets = max(packet_count - previous["packet_count"], 0.0)
        delta_bytes = max(byte_count - previous["byte_count"], 0.0)

        packet_rate = delta_packets / delta_time
        byte_rate = delta_bytes / delta_time

        self.previous_flow_counters[key] = {
            "timestamp_monotonic": now,
            "packet_count": packet_count,
            "byte_count": byte_count
        }

        return {
            "delta_time_sec": delta_time,
            "delta_packet_count": delta_packets,
            "delta_byte_count": delta_bytes,
            "packet_rate": packet_rate,
            "byte_rate": byte_rate
        }

    def is_source_edge_switch(self, datapath_id, ipv4_src):
        if ipv4_src not in HOSTS:
            return False

        return int(datapath_id) == int(HOSTS[ipv4_src]["edge_switch"])

    # ----------------------------------------------------------------
    # Flow statistics reply handling
    # ----------------------------------------------------------------

    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def flow_stats_reply_handler(self, ev):
        timestamp = datetime.utcnow().isoformat()
        datapath_id = ev.msg.datapath.id

        with open(FLOW_STATS_FILE, "a", newline="") as f:
            writer = csv.writer(f)

            for stat in ev.msg.body:
                if stat.priority == 0:
                    continue

                match = stat.match

                ipv4_src = match.get("ipv4_src", "")
                ipv4_dst = match.get("ipv4_dst", "")
                ip_proto = match.get("ip_proto", "")

                if not ipv4_src or not ipv4_dst:
                    continue

                duration = max(float(stat.duration_sec), 1.0)
                packet_count = float(stat.packet_count)
                byte_count = float(stat.byte_count)

                cumulative_packet_rate = packet_count / duration
                cumulative_byte_rate = byte_count / duration

                delta = self.calculate_delta_rates(
                    datapath_id=datapath_id,
                    ipv4_src=ipv4_src,
                    ipv4_dst=ipv4_dst,
                    ip_proto=ip_proto,
                    packet_count=packet_count,
                    byte_count=byte_count
                )

                is_source_edge = self.is_source_edge_switch(
                    datapath_id=datapath_id,
                    ipv4_src=ipv4_src
                )

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
                    cumulative_packet_rate,
                    cumulative_byte_rate,
                    delta["delta_time_sec"],
                    int(delta["delta_packet_count"]),
                    int(delta["delta_byte_count"]),
                    delta["packet_rate"],
                    delta["byte_rate"],
                    int(is_source_edge)
                ])

                # Only source edge switch sends prediction request to ML API.
                if not is_source_edge:
                    continue

                features = {
                    "datapath_id": int(datapath_id),
                    "ipv4_src": ipv4_src,
                    "ipv4_dst": ipv4_dst,
                    "ip_proto": int(ip_proto) if ip_proto != "" else None,
                    "duration_sec": float(stat.duration_sec),
                    "packet_count": float(packet_count),
                    "byte_count": float(byte_count),
                    "packet_rate": float(delta["packet_rate"]),
                    "byte_rate": float(delta["byte_rate"])
                }

                ml_result = self.ask_ml_api(features)
                self.append_prediction_log(timestamp, features, ml_result)

                policy_result = self.evaluate_policy(features, ml_result)
                self.append_policy_decision_log(
                    timestamp=timestamp,
                    features=features,
                    ml_result=ml_result,
                    policy_result=policy_result
                )

                if self.should_apply_rate_limit(policy_result):
                    self.install_rate_limit_for_flow(features, policy_result)

                if self.should_apply_quarantine(policy_result):
                    self.install_quarantine_forwarding_for_source(features, policy_result)

                if self.should_apply_mitigation(policy_result):
                    self.install_drop_rules_for_flow(features, policy_result)

                self.logger.info(
                    "Policy decision: dpid=%s src=%s dst=%s proto=%s "
                    "pps=%.2f bps=%.2f ml_prediction=%s ml_action=%s "
                    "confidence=%s final_action=%s reason=%s risk_count=%s api=%s",
                    datapath_id,
                    ipv4_src,
                    ipv4_dst,
                    ip_proto,
                    delta["packet_rate"],
                    delta["byte_rate"],
                    ml_result.get("prediction", ""),
                    ml_result.get("recommended_action", ""),
                    ml_result.get("confidence", ""),
                    policy_result.get("final_action", ""),
                    policy_result.get("reason", ""),
                    policy_result.get("source_risk_count", ""),
                    ml_result.get("api_status", "")
                )

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
        ip_proto = ip_pkt.proto

        if dst_ip in GATEWAY_IPS:
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
            ipv4_dst=dst_ip,
            ip_proto=ip_proto
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
            "IPv4 routed: dpid=%s src=%s dst=%s proto=%s out_port=%s dst_mac=%s",
            dpid,
            src_ip,
            dst_ip,
            ip_proto,
            out_port,
            dst_mac
        )

    def get_output_port(self, current_dpid, dst_ip):
        dst_edge = HOSTS[dst_ip]["edge_switch"]

        if current_dpid == dst_edge:
            return HOST_PORTS[dst_edge].get(dst_ip)

        if current_dpid in UPLINK_PORT:
            return UPLINK_PORT[current_dpid]

        if current_dpid in [2, 3]:
            current_dist = current_dpid
            dst_dist = EDGE_TO_DIST[dst_edge]

            if current_dist == dst_dist:
                return DIST_TO_ACCESS_PORT[current_dist][dst_edge]

            return DIST_TO_CORE_PORT[current_dist]

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
