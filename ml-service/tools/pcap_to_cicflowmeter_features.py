#!/usr/bin/env python3
"""
Custom CICFlowMeter-compatible selected feature extractor.

Purpose:
- Read a PCAP file.
- Build bidirectional flows.
- Compute CICFlowMeter-style flow features.
- Optionally select model-required features from feature_order.json.
- Generate a feature semantics report.

This is not a full CICFlowMeter replacement.
It is a lightweight, extensible extractor designed for selected-feature
runtime ML integration.

Initial supported active model features:
- Destination_Port
- Protocol
- Total_Fwd_Packets
- Total_Length_of_Fwd_Packets
- Bwd_IAT_Mean
- Bwd_Packets_s
- Packet_Length_Variance
- SYN_Flag_Count
- URG_Flag_Count
- CWE_Flag_Count
- Init_Win_bytes_forward
- Active_Min
- Inbound

Usage examples:

Full supported feature output:
python ml-service/tools/pcap_to_cicflowmeter_features.py \
  --pcap experiments/pcaps/h12_to_h14_udp_s6eth2.pcap \
  --output experiments/flow_features/runtime_cicflowmeter_features.csv

Selected model feature output:
python ml-service/tools/pcap_to_cicflowmeter_features.py \
  --pcap experiments/pcaps/h12_to_h14_udp_s6eth2.pcap \
  --output experiments/flow_features/runtime_selected_features.csv \
  --feature-order ml-service/models/active/feature_order.json \
  --semantics-output experiments/flow_features/runtime_feature_semantics_report.json
"""

import argparse
import json
import math
import statistics
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd
from scapy.all import IP, TCP, UDP, rdpcap


# ---------------------------------------------------------------------
# Feature registry
# ---------------------------------------------------------------------

FEATURE_SEMANTICS = {
    "Source_IP": {
        "status": "metadata",
        "description": "Forward direction source IP, defined by the first packet of the bidirectional flow.",
    },
    "Destination_IP": {
        "status": "metadata",
        "description": "Forward direction destination IP, defined by the first packet of the bidirectional flow.",
    },
    "Source_Port": {
        "status": "metadata",
        "description": "Forward direction source TCP/UDP port.",
    },
    "Destination_Port": {
        "status": "computed",
        "description": "Forward direction destination TCP/UDP port.",
    },
    "Protocol": {
        "status": "computed",
        "description": "IP protocol number. TCP=6, UDP=17.",
    },
    "Flow_Duration": {
        "status": "computed",
        "description": "Flow duration in seconds between first and last packet.",
    },
    "Total_Fwd_Packets": {
        "status": "computed",
        "description": "Number of packets in the forward direction.",
    },
    "Total_Backward_Packets": {
        "status": "computed",
        "description": "Number of packets in the backward direction.",
    },
    "Total_Length_of_Fwd_Packets": {
        "status": "computed",
        "description": "Sum of packet lengths in the forward direction.",
    },
    "Total_Length_of_Bwd_Packets": {
        "status": "computed",
        "description": "Sum of packet lengths in the backward direction.",
    },
    "Flow_Bytes_s": {
        "status": "computed",
        "description": "Total bytes divided by flow duration.",
    },
    "Flow_Packets_s": {
        "status": "computed",
        "description": "Total packet count divided by flow duration.",
    },
    "Bwd_IAT_Mean": {
        "status": "computed",
        "description": "Mean inter-arrival time between backward packets.",
    },
    "Bwd_Packets_s": {
        "status": "computed",
        "description": "Backward packet count divided by flow duration.",
    },
    "Packet_Length_Mean": {
        "status": "computed",
        "description": "Mean packet length over all packets in the bidirectional flow.",
    },
    "Packet_Length_Std": {
        "status": "computed",
        "description": "Sample standard deviation of packet lengths.",
    },
    "Packet_Length_Variance": {
        "status": "computed",
        "description": "Sample variance of packet lengths.",
    },
    "SYN_Flag_Count": {
        "status": "computed",
        "description": "Count of TCP packets with SYN flag.",
    },
    "URG_Flag_Count": {
        "status": "computed",
        "description": "Count of TCP packets with URG flag.",
    },
    "CWE_Flag_Count": {
        "status": "computed_approximation",
        "description": "Approximated as count of TCP CWR flag. CICFlowMeter naming may differ.",
    },
    "ACK_Flag_Count": {
        "status": "computed",
        "description": "Count of TCP packets with ACK flag.",
    },
    "PSH_Flag_Count": {
        "status": "computed",
        "description": "Count of TCP packets with PSH flag.",
    },
    "RST_Flag_Count": {
        "status": "computed",
        "description": "Count of TCP packets with RST flag.",
    },
    "FIN_Flag_Count": {
        "status": "computed",
        "description": "Count of TCP packets with FIN flag.",
    },
    "Init_Win_bytes_forward": {
        "status": "computed",
        "description": "TCP window size of the first forward TCP packet. UDP flows receive 0.",
    },
    "Init_Win_bytes_backward": {
        "status": "computed",
        "description": "TCP window size of the first backward TCP packet. UDP flows receive 0.",
    },
    "Active_Min": {
        "status": "computed_approximation",
        "description": "Minimum active period duration using configurable idle gap threshold.",
    },
    "Active_Mean": {
        "status": "computed_approximation",
        "description": "Mean active period duration using configurable idle gap threshold.",
    },
    "Active_Max": {
        "status": "computed_approximation",
        "description": "Maximum active period duration using configurable idle gap threshold.",
    },
    "Active_Std": {
        "status": "computed_approximation",
        "description": "Standard deviation of active period durations.",
    },
    "Idle_Min": {
        "status": "computed_approximation",
        "description": "Minimum idle period using configurable idle gap threshold.",
    },
    "Idle_Mean": {
        "status": "computed_approximation",
        "description": "Mean idle period using configurable idle gap threshold.",
    },
    "Idle_Max": {
        "status": "computed_approximation",
        "description": "Maximum idle period using configurable idle gap threshold.",
    },
    "Idle_Std": {
        "status": "computed_approximation",
        "description": "Standard deviation of idle periods.",
    },
    "Inbound": {
        "status": "dataset_specific_rule",
        "description": "Project-specific approximation. Currently set to 1 if either endpoint is in 10.10.60.0/24.",
    },
}


# ---------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------

def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        value = float(value)
        if math.isnan(value) or math.isinf(value):
            return default
        return value
    except Exception:
        return default


def mean(values: List[float]) -> float:
    if not values:
        return 0.0
    return float(sum(values) / len(values))


def sample_std(values: List[float]) -> float:
    if len(values) < 2:
        return 0.0
    return float(statistics.stdev(values))


def sample_var(values: List[float]) -> float:
    if len(values) < 2:
        return 0.0
    return float(statistics.variance(values))


def canonical_flow_key(src_ip: str, dst_ip: str, src_port: int, dst_port: int, proto: int) -> Tuple:
    """
    Direction-independent 5-tuple key.
    """
    a = (str(src_ip), int(src_port))
    b = (str(dst_ip), int(dst_port))

    if a <= b:
        return (a[0], b[0], a[1], b[1], int(proto))
    return (b[0], a[0], b[1], a[1], int(proto))


def get_ports(pkt) -> Tuple[int, int]:
    if pkt.haslayer(TCP):
        return int(pkt[TCP].sport), int(pkt[TCP].dport)
    if pkt.haslayer(UDP):
        return int(pkt[UDP].sport), int(pkt[UDP].dport)
    return 0, 0


def has_tcp_flag(pkt, flag_char: str) -> int:
    if not pkt.haslayer(TCP):
        return 0

    flags = str(pkt[TCP].flags)
    return 1 if flag_char in flags else 0


def get_tcp_window(pkt) -> int:
    if pkt.haslayer(TCP):
        return int(pkt[TCP].window)
    return 0


def compute_iats(times: List[float]) -> List[float]:
    if len(times) < 2:
        return []

    ts = sorted(float(t) for t in times)
    return [ts[i] - ts[i - 1] for i in range(1, len(ts))]


def compute_active_idle_stats(all_times: List[float], idle_gap_threshold: float = 1.0) -> Dict[str, float]:
    """
    Approximate CICFlowMeter active/idle behavior.

    If inter-packet gap > idle_gap_threshold, the flow is considered idle
    and a new active period starts.
    """
    if len(all_times) < 2:
        return {
            "Active_Min": 0.0,
            "Active_Mean": 0.0,
            "Active_Max": 0.0,
            "Active_Std": 0.0,
            "Idle_Min": 0.0,
            "Idle_Mean": 0.0,
            "Idle_Max": 0.0,
            "Idle_Std": 0.0,
        }

    ts = sorted(float(t) for t in all_times)

    active_durations = []
    idle_durations = []

    start = ts[0]
    prev = ts[0]

    for t in ts[1:]:
        gap = t - prev

        if gap > idle_gap_threshold:
            active_duration = prev - start
            if active_duration > 0:
                active_durations.append(active_duration)

            idle_durations.append(gap)
            start = t

        prev = t

    final_active = prev - start
    if final_active > 0:
        active_durations.append(final_active)

    return {
        "Active_Min": min(active_durations) if active_durations else 0.0,
        "Active_Mean": mean(active_durations),
        "Active_Max": max(active_durations) if active_durations else 0.0,
        "Active_Std": sample_std(active_durations),
        "Idle_Min": min(idle_durations) if idle_durations else 0.0,
        "Idle_Mean": mean(idle_durations),
        "Idle_Max": max(idle_durations) if idle_durations else 0.0,
        "Idle_Std": sample_std(idle_durations),
    }


def infer_inbound(src_ip: str, dst_ip: str) -> int:
    """
    Project-specific Inbound approximation.

    This must be revisited for full CIC-DDoS2019 retraining.
    """
    src_ip = str(src_ip)
    dst_ip = str(dst_ip)

    if src_ip.startswith("10.10.60.") or dst_ip.startswith("10.10.60."):
        return 1

    return 0


# ---------------------------------------------------------------------
# Flow extraction
# ---------------------------------------------------------------------

def empty_flow(first_pkt, src_ip: str, dst_ip: str, src_port: int, dst_port: int, proto: int) -> Dict[str, Any]:
    return {
        "first_src_ip": src_ip,
        "first_dst_ip": dst_ip,
        "first_src_port": src_port,
        "first_dst_port": dst_port,
        "proto": proto,

        "fwd_lengths": [],
        "bwd_lengths": [],
        "all_lengths": [],

        "fwd_times": [],
        "bwd_times": [],
        "all_times": [],

        "syn_count": 0,
        "urg_count": 0,
        "cwe_count": 0,
        "ack_count": 0,
        "psh_count": 0,
        "rst_count": 0,
        "fin_count": 0,

        "init_win_fwd": 0,
        "init_win_bwd": 0,
    }


def add_packet_to_flow(flow: Dict[str, Any], pkt) -> None:
    ip = pkt[IP]
    src_ip = str(ip.src)
    dst_ip = str(ip.dst)
    src_port, dst_port = get_ports(pkt)

    pkt_time = float(pkt.time)
    pkt_len = int(len(pkt))

    is_forward = (
        src_ip == flow["first_src_ip"]
        and dst_ip == flow["first_dst_ip"]
        and src_port == flow["first_src_port"]
        and dst_port == flow["first_dst_port"]
    )

    flow["all_lengths"].append(pkt_len)
    flow["all_times"].append(pkt_time)

    if is_forward:
        flow["fwd_lengths"].append(pkt_len)
        flow["fwd_times"].append(pkt_time)

        if flow["init_win_fwd"] == 0 and pkt.haslayer(TCP):
            flow["init_win_fwd"] = get_tcp_window(pkt)
    else:
        flow["bwd_lengths"].append(pkt_len)
        flow["bwd_times"].append(pkt_time)

        if flow["init_win_bwd"] == 0 and pkt.haslayer(TCP):
            flow["init_win_bwd"] = get_tcp_window(pkt)

    flow["syn_count"] += has_tcp_flag(pkt, "S")
    flow["urg_count"] += has_tcp_flag(pkt, "U")
    flow["cwe_count"] += has_tcp_flag(pkt, "C")
    flow["ack_count"] += has_tcp_flag(pkt, "A")
    flow["psh_count"] += has_tcp_flag(pkt, "P")
    flow["rst_count"] += has_tcp_flag(pkt, "R")
    flow["fin_count"] += has_tcp_flag(pkt, "F")


def build_flows_from_pcap(pcap_path: Path) -> Dict[Tuple, Dict[str, Any]]:
    packets = rdpcap(str(pcap_path))

    print(f"[INFO] Total packets read: {len(packets)}")

    flows: Dict[Tuple, Dict[str, Any]] = {}

    for pkt in packets:
        if not pkt.haslayer(IP):
            continue

        if not (pkt.haslayer(TCP) or pkt.haslayer(UDP)):
            continue

        ip = pkt[IP]
        proto = int(ip.proto)

        src_ip = str(ip.src)
        dst_ip = str(ip.dst)
        src_port, dst_port = get_ports(pkt)

        key = canonical_flow_key(src_ip, dst_ip, src_port, dst_port, proto)

        if key not in flows:
            flows[key] = empty_flow(pkt, src_ip, dst_ip, src_port, dst_port, proto)

        add_packet_to_flow(flows[key], pkt)

    return flows


def flow_to_features(flow: Dict[str, Any], idle_gap_threshold: float = 1.0) -> Dict[str, Any]:
    all_times = flow["all_times"]
    all_lengths = [float(x) for x in flow["all_lengths"]]
    fwd_lengths = [float(x) for x in flow["fwd_lengths"]]
    bwd_lengths = [float(x) for x in flow["bwd_lengths"]]

    duration = 0.0
    if all_times:
        duration = max(max(all_times) - min(all_times), 1e-6)
    else:
        duration = 1e-6

    total_packets = len(all_lengths)
    total_bytes = float(sum(all_lengths))

    bwd_iats = compute_iats(flow["bwd_times"])
    active_idle = compute_active_idle_stats(all_times, idle_gap_threshold=idle_gap_threshold)

    row = {
        "Source_IP": flow["first_src_ip"],
        "Destination_IP": flow["first_dst_ip"],
        "Source_Port": int(flow["first_src_port"]),
        "Destination_Port": int(flow["first_dst_port"]),

        "Protocol": int(flow["proto"]),
        "Flow_Duration": duration,

        "Total_Fwd_Packets": int(len(fwd_lengths)),
        "Total_Backward_Packets": int(len(bwd_lengths)),
        "Total_Length_of_Fwd_Packets": float(sum(fwd_lengths)),
        "Total_Length_of_Bwd_Packets": float(sum(bwd_lengths)),

        "Flow_Bytes_s": total_bytes / duration,
        "Flow_Packets_s": total_packets / duration,

        "Bwd_IAT_Mean": mean(bwd_iats),
        "Bwd_Packets_s": len(bwd_lengths) / duration,

        "Packet_Length_Mean": mean(all_lengths),
        "Packet_Length_Std": sample_std(all_lengths),
        "Packet_Length_Variance": sample_var(all_lengths),

        "SYN_Flag_Count": int(flow["syn_count"]),
        "URG_Flag_Count": int(flow["urg_count"]),
        "CWE_Flag_Count": int(flow["cwe_count"]),
        "ACK_Flag_Count": int(flow["ack_count"]),
        "PSH_Flag_Count": int(flow["psh_count"]),
        "RST_Flag_Count": int(flow["rst_count"]),
        "FIN_Flag_Count": int(flow["fin_count"]),

        "Init_Win_bytes_forward": int(flow["init_win_fwd"]),
        "Init_Win_bytes_backward": int(flow["init_win_bwd"]),

        "Inbound": infer_inbound(flow["first_src_ip"], flow["first_dst_ip"]),
    }

    row.update(active_idle)

    return row


def load_feature_order(path: str) -> List[str]:
    with Path(path).open("r", encoding="utf-8") as f:
        return json.load(f)


def write_semantics_report(
    output_path: Path,
    all_columns: List[str],
    selected_columns: List[str],
    missing_columns: List[str],
) -> None:
    report = {
        "all_feature_count": len(all_columns),
        "selected_feature_count": len(selected_columns),
        "missing_feature_count": len(missing_columns),
        "all_columns": all_columns,
        "selected_columns": selected_columns,
        "missing_columns": missing_columns,
        "semantics": {
            col: FEATURE_SEMANTICS.get(
                col,
                {
                    "status": "unknown",
                    "description": "No semantic metadata registered for this feature.",
                },
            )
            for col in selected_columns
        },
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"[INFO] Semantics report written: {output_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pcap", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--feature-order", default=None)
    parser.add_argument("--semantics-output", default=None)
    parser.add_argument("--active-gap-threshold", type=float, default=1.0)
    args = parser.parse_args()

    pcap_path = Path(args.pcap)
    output_path = Path(args.output)

    print(f"[INFO] Reading PCAP: {pcap_path}")
    flows = build_flows_from_pcap(pcap_path)
    print(f"[INFO] Bidirectional flows built: {len(flows)}")

    rows = [
        flow_to_features(flow, idle_gap_threshold=args.active_gap_threshold)
        for flow in flows.values()
    ]

    df = pd.DataFrame(rows)

    if df.empty:
        raise RuntimeError("No TCP/UDP IP flows were extracted from the PCAP.")

    all_columns = list(df.columns)

    selected_columns = all_columns
    missing_columns: List[str] = []

    if args.feature_order:
        feature_order = load_feature_order(args.feature_order)
        missing_columns = [c for c in feature_order if c not in df.columns]

        if missing_columns:
            print("[WARN] Missing requested features:")
            for col in missing_columns:
                print(f" - {col}")

        # Keep metadata columns for traceability plus requested features.
        metadata_cols = [
            "Source_IP",
            "Destination_IP",
            "Source_Port",
        ]

        selected_columns = metadata_cols + [c for c in feature_order if c in df.columns]
        df = df[selected_columns]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)

    print(f"[INFO] Output written: {output_path}")
    print(f"[INFO] Shape: {df.shape}")
    print(df.head().to_string(index=False))

    if args.semantics_output:
        write_semantics_report(
            Path(args.semantics_output),
            all_columns=all_columns,
            selected_columns=selected_columns,
            missing_columns=missing_columns,
        )


if __name__ == "__main__":
    main()
