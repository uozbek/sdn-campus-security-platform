#!/usr/bin/env python3
"""
Extract final XGBoost Top-20 runtime features from a PCAP file.

Purpose:
- Generate the exact 20 features expected by final_xgboost_top20.
- Use active feature_order.json to enforce output column order.
- Produce flow-level CSV compatible with /predict-cicddos and active model.

Notes:
- This is a project-specific CICFlowMeter-style lightweight extractor.
- Source IP / Destination IP are kept only as metadata, not model features.
- Inbound is approximated using a configurable subnet rule.
- Active period features are approximated using an idle gap threshold.

Usage:
python ml-service/tools/pcap_to_final_top20_features.py \
  --pcap experiments/pcaps/h12_to_h14_udp_s6eth2.pcap \
  --output experiments/flow_features/final_top20_flows.csv \
  --feature-order ml-service/models/active/feature_order.json \
  --inbound-subnet 10.10.60.0/24
"""

import argparse
import ipaddress
import json
import math
from collections import defaultdict
from pathlib import Path

import pandas as pd
from scapy.all import rdpcap, IP, TCP, UDP


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def safe_var(values):
    if len(values) <= 1:
        return 0.0
    s = pd.Series(values, dtype="float64")
    return float(s.var())


def safe_rate(count, duration_sec):
    if duration_sec <= 0:
        return 0.0
    return float(count) / float(duration_sec)


def ip_in_subnet(ip_value: str, subnet: str) -> bool:
    try:
        return ipaddress.ip_address(ip_value) in ipaddress.ip_network(subnet, strict=False)
    except Exception:
        return False


def packet_header_len_bytes(pkt):
    """
    Approximate IP + TCP/UDP header length.
    CICFlowMeter-style header lengths are not always identical across tools,
    but this gives a consistent runtime approximation.
    """
    if not pkt.haslayer(IP):
        return 0

    ip_layer = pkt[IP]
    ip_header_len = int(ip_layer.ihl or 5) * 4

    if pkt.haslayer(TCP):
        tcp_layer = pkt[TCP]
        tcp_header_len = int(tcp_layer.dataofs or 5) * 4
        return ip_header_len + tcp_header_len

    if pkt.haslayer(UDP):
        return ip_header_len + 8

    return ip_header_len


def packet_payload_len(pkt):
    if not pkt.haslayer(IP):
        return 0

    ip_len = int(pkt[IP].len or 0)
    header_len = packet_header_len_bytes(pkt)
    return max(0, ip_len - header_len)


def packet_total_len(pkt):
    if pkt.haslayer(IP):
        return int(pkt[IP].len or len(pkt))
    return int(len(pkt))


def tcp_flag_set(pkt, flag_char: str) -> int:
    if not pkt.haslayer(TCP):
        return 0
    flags = str(pkt[TCP].flags)
    return 1 if flag_char in flags else 0


def flow_key(pkt):
    """
    Bidirectional flow key.
    Canonicalizes endpoints so both directions map to the same flow.
    Also stores direction later using first packet.
    """
    ip = pkt[IP]
    proto = int(ip.proto)

    if pkt.haslayer(TCP):
        sport = int(pkt[TCP].sport)
        dport = int(pkt[TCP].dport)
    elif pkt.haslayer(UDP):
        sport = int(pkt[UDP].sport)
        dport = int(pkt[UDP].dport)
    else:
        sport = 0
        dport = 0

    a = (ip.src, sport)
    b = (ip.dst, dport)

    if a <= b:
        return (ip.src, sport, ip.dst, dport, proto)
    return (ip.dst, dport, ip.src, sport, proto)


def update_flow(flow, pkt):
    ts = float(pkt.time)
    ip = pkt[IP]

    if flow["first_ts"] is None:
        flow["first_ts"] = ts
        flow["last_ts"] = ts

        flow["src_ip"] = ip.src
        flow["dst_ip"] = ip.dst

        if pkt.haslayer(TCP):
            flow["src_port"] = int(pkt[TCP].sport)
            flow["dst_port"] = int(pkt[TCP].dport)
            flow["protocol"] = 6
            flow["init_win_bytes_forward"] = int(pkt[TCP].window)
        elif pkt.haslayer(UDP):
            flow["src_port"] = int(pkt[UDP].sport)
            flow["dst_port"] = int(pkt[UDP].dport)
            flow["protocol"] = 17
            flow["init_win_bytes_forward"] = 0
        else:
            flow["src_port"] = 0
            flow["dst_port"] = 0
            flow["protocol"] = int(ip.proto)
            flow["init_win_bytes_forward"] = 0

    flow["last_ts"] = max(flow["last_ts"], ts)
    flow["timestamps"].append(ts)

    total_len = packet_total_len(pkt)
    payload_len = packet_payload_len(pkt)

    flow["packet_lengths"].append(total_len)

    is_forward = (
        ip.src == flow["src_ip"]
        and ip.dst == flow["dst_ip"]
    )

    if is_forward:
        flow["fwd_count"] += 1
        flow["fwd_lengths"].append(total_len)
        flow["fwd_payload_lengths"].append(payload_len)

        if pkt.haslayer(TCP):
            if tcp_flag_set(pkt, "P"):
                flow["fwd_psh_flags"] += 1
            if flow["init_win_bytes_forward"] == 0:
                flow["init_win_bytes_forward"] = int(pkt[TCP].window)
    else:
        flow["bwd_count"] += 1
        flow["bwd_lengths"].append(total_len)
        flow["bwd_header_length"] += packet_header_len_bytes(pkt)

    if pkt.haslayer(TCP):
        if tcp_flag_set(pkt, "U"):
            flow["urg_flag_count"] += 1
        if tcp_flag_set(pkt, "C"):
            flow["cwe_flag_count"] += 1


def compute_active_periods(timestamps, idle_gap_sec):
    """
    CICFlowMeter Active_* approximates active periods separated by idle periods.
    Here an active period continues while consecutive packets are within idle_gap_sec.
    """
    if not timestamps:
        return [0.0]

    ts = sorted(timestamps)

    periods = []
    start = ts[0]
    prev = ts[0]

    for t in ts[1:]:
        if (t - prev) > idle_gap_sec:
            periods.append(prev - start)
            start = t
        prev = t

    periods.append(prev - start)

    return periods or [0.0]


def flow_to_row(flow, inbound_subnet, idle_gap_sec):
    duration_sec = 0.0
    if flow["first_ts"] is not None and flow["last_ts"] is not None:
        duration_sec = max(0.0, flow["last_ts"] - flow["first_ts"])

    packet_lengths = flow["packet_lengths"] or [0]
    bwd_lengths = flow["bwd_lengths"] or []
    active_periods = compute_active_periods(flow["timestamps"], idle_gap_sec=idle_gap_sec)

    src_ip = flow["src_ip"] or ""
    dst_ip = flow["dst_ip"] or ""

    # Project-specific approximation:
    # Inbound = 1 if either endpoint belongs to the configured monitored subnet.
    inbound = 1 if (
        ip_in_subnet(src_ip, inbound_subnet)
        or ip_in_subnet(dst_ip, inbound_subnet)
    ) else 0

    row = {
        # metadata
        "Source_IP": src_ip,
        "Destination_IP": dst_ip,

        # final top-20 model features
        "Inbound": inbound,
        "URG_Flag_Count": int(flow["urg_flag_count"]),
        "Source_Port": int(flow["src_port"] or 0),
        "Destination_Port": int(flow["dst_port"] or 0),
        "Bwd_Packets_s": safe_rate(flow["bwd_count"], duration_sec),
        "Fwd_Packets_s": safe_rate(flow["fwd_count"], duration_sec),
        "Bwd_Packet_Length_Min": float(min(bwd_lengths)) if bwd_lengths else 0.0,
        "Active_Mean": float(sum(active_periods) / len(active_periods)) if active_periods else 0.0,
        "Min_Packet_Length": float(min(packet_lengths)),
        "Active_Min": float(min(active_periods)) if active_periods else 0.0,
        "Bwd_Header_Length": float(flow["bwd_header_length"]),
        "Flow_Bytes_s": safe_rate(sum(packet_lengths), duration_sec),
        "Bwd_Packet_Length_Max": float(max(bwd_lengths)) if bwd_lengths else 0.0,
        "min_seg_size_forward": float(min(flow["fwd_payload_lengths"])) if flow["fwd_payload_lengths"] else 0.0,
        "Fwd_PSH_Flags": int(flow["fwd_psh_flags"]),
        "CWE_Flag_Count": int(flow["cwe_flag_count"]),
        "Active_Max": float(max(active_periods)) if active_periods else 0.0,
        "Init_Win_bytes_forward": int(flow["init_win_bytes_forward"]),
        "Packet_Length_Variance": safe_var(packet_lengths),
        "act_data_pkt_fwd": int(sum(1 for x in flow["fwd_payload_lengths"] if x > 0)),
    }

    return row


def new_flow():
    return {
        "first_ts": None,
        "last_ts": None,
        "src_ip": None,
        "dst_ip": None,
        "src_port": None,
        "dst_port": None,
        "protocol": None,
        "timestamps": [],
        "packet_lengths": [],
        "fwd_lengths": [],
        "bwd_lengths": [],
        "fwd_payload_lengths": [],
        "fwd_count": 0,
        "bwd_count": 0,
        "bwd_header_length": 0,
        "fwd_psh_flags": 0,
        "urg_flag_count": 0,
        "cwe_flag_count": 0,
        "init_win_bytes_forward": 0,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pcap", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--feature-order", default="ml-service/models/active/feature_order.json")
    parser.add_argument("--inbound-subnet", default="10.10.60.0/24")
    parser.add_argument("--idle-gap-sec", type=float, default=1.0)
    args = parser.parse_args()

    pcap_path = Path(args.pcap)
    output_path = Path(args.output)
    feature_order_path = Path(args.feature_order)

    feature_order = load_json(feature_order_path)

    print(f"[INFO] Reading pcap: {pcap_path}")
    packets = rdpcap(str(pcap_path))

    flows = defaultdict(new_flow)

    ip_count = 0
    tcp_count = 0
    udp_count = 0

    for pkt in packets:
        if not pkt.haslayer(IP):
            continue

        ip_count += 1

        if pkt.haslayer(TCP):
            tcp_count += 1
        elif pkt.haslayer(UDP):
            udp_count += 1
        else:
            continue

        key = flow_key(pkt)
        update_flow(flows[key], pkt)

    rows = []

    for _, flow in flows.items():
        rows.append(
            flow_to_row(
                flow,
                inbound_subnet=args.inbound_subnet,
                idle_gap_sec=args.idle_gap_sec,
            )
        )

    df = pd.DataFrame(rows)

    # Ensure active model features exist and order them after metadata.
    for feature in feature_order:
        if feature not in df.columns:
            df[feature] = 0.0

    output_cols = ["Source_IP", "Destination_IP"] + feature_order
    df = df[output_cols]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)

    print("[INFO] Extraction completed.")
    print(f"[INFO] IP packets : {ip_count}")
    print(f"[INFO] TCP packets: {tcp_count}")
    print(f"[INFO] UDP packets: {udp_count}")
    print(f"[INFO] Flow rows  : {len(df)}")
    print(f"[INFO] Output     : {output_path}")
    print()
    print(df.head().to_string(index=False))


if __name__ == "__main__":
    main()
