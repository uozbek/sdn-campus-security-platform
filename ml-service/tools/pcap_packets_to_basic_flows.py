#!/usr/bin/env python3

import argparse
from pathlib import Path

import pandas as pd


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--packets-csv", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    packets_path = Path(args.packets_csv)
    output_path = Path(args.output)

    df = pd.read_csv(packets_path)

    # Kolon adlarını sadeleştir
    df = df.rename(columns={
        "frame.time_epoch": "time",
        "ip.src": "src_ip",
        "ip.dst": "dst_ip",
        "ip.proto": "protocol",
        "tcp.srcport": "tcp_srcport",
        "tcp.dstport": "tcp_dstport",
        "udp.srcport": "udp_srcport",
        "udp.dstport": "udp_dstport",
        "frame.len": "frame_len",
        "tcp.flags.syn": "tcp_syn",
        "tcp.flags.urg": "tcp_urg",
    })

    # IP olmayan satırları at
    df = df.dropna(subset=["src_ip", "dst_ip", "protocol"], how="any")

    df["protocol"] = pd.to_numeric(df["protocol"], errors="coerce").fillna(0).astype(int)
    df["frame_len"] = pd.to_numeric(df["frame_len"], errors="coerce").fillna(0)
    df["time"] = pd.to_numeric(df["time"], errors="coerce")

    df["src_port"] = df["tcp_srcport"].fillna(df["udp_srcport"])
    df["dst_port"] = df["tcp_dstport"].fillna(df["udp_dstport"])

    df["src_port"] = pd.to_numeric(df["src_port"], errors="coerce").fillna(0).astype(int)
    df["dst_port"] = pd.to_numeric(df["dst_port"], errors="coerce").fillna(0).astype(int)

    # 5-tuple flow
    group_cols = ["src_ip", "dst_ip", "src_port", "dst_port", "protocol"]

    rows = []

    for key, g in df.groupby(group_cols):
        src_ip, dst_ip, src_port, dst_port, protocol = key

        start = g["time"].min()
        end = g["time"].max()
        duration = max(float(end - start), 1e-6)

        packet_count = len(g)
        byte_count = float(g["frame_len"].sum())

        rows.append({
            # CICFlowMeter-style bazı kolon adları
            "Source_IP": src_ip,
            "Destination_IP": dst_ip,
            "Source_Port": src_port,
            "Destination_Port": dst_port,
            "Protocol": protocol,
            "Flow_Duration": duration,
            "Total_Fwd_Packets": packet_count,
            "Total_Length_of_Fwd_Packets": byte_count,
            "Flow_Bytes_s": byte_count / duration,
            "Flow_Packets_s": packet_count / duration,
            "Packet_Length_Variance": float(g["frame_len"].var()) if packet_count > 1 else 0.0,
            "SYN_Flag_Count": int(pd.to_numeric(g.get("tcp_syn", 0), errors="coerce").fillna(0).sum()) if "tcp_syn" in g else 0,
            "URG_Flag_Count": int(pd.to_numeric(g.get("tcp_urg", 0), errors="coerce").fillna(0).sum()) if "tcp_urg" in g else 0,

            # Henüz basic extractor ile üretilemeyen alanlar için placeholder
            "Bwd_IAT_Mean": 0.0,
            "Bwd_Packets_s": 0.0,
            "CWE_Flag_Count": 0,
            "Init_Win_bytes_forward": 0,
            "Active_Min": 0.0,
            "Inbound": 1,
        })

    out = pd.DataFrame(rows)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(output_path, index=False)

    print("[INFO] Written:", output_path)
    print("[INFO] Shape:", out.shape)
    print(out.head().to_string(index=False))


if __name__ == "__main__":
    main()
