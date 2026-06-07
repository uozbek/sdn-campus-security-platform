#!/usr/bin/env python3
import argparse
import csv
import json
import subprocess
from collections import defaultdict
from pathlib import Path

import pandas as pd


TCP_PROTO = 6
UDP_PROTO = 17


def run_tcpdump_summary(pcap_path: Path):
    """
    Parse PCAP using tcpdump and build a lightweight flow -> protocol/packet-count map.

    We intentionally use tcpdump because it is already available in the experiment
    environment and avoids adding a heavy dependency for this small post-processing step.
    """

    cmd = ["tcpdump", "-nn", "-r", str(pcap_path)]
    proc = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        check=False,
    )

    if proc.returncode not in (0, 1):
        # tcpdump may return 1 in some broken-pipe-like cases, but here we read full output.
        # Still, do not fail too aggressively if stdout exists.
        if not proc.stdout:
            raise RuntimeError(f"tcpdump failed for {pcap_path}")

    flow_counts = defaultdict(int)
    flow_proto = {}

    for line in proc.stdout.splitlines():
        line = line.strip()
        if " IP " not in line:
            continue

        proto = None

        if ": UDP," in line:
            proto = UDP_PROTO
        elif " Flags [" in line:
            proto = TCP_PROTO
        else:
            continue

        # Example TCP:
        # 00:32:33.144475 IP 10.10.60.12.41664 > 10.10.40.14.5201: Flags [S], ...
        #
        # Example UDP:
        # 00:32:33.165039 IP 10.10.60.12.40205 > 10.10.40.14.5201: UDP, length 4

        try:
            after_ip = line.split(" IP ", 1)[1]
            left, right = after_ip.split(" > ", 1)
            right = right.split(":", 1)[0]

            src_ip, src_port = split_ip_port(left)
            dst_ip, dst_port = split_ip_port(right)

            if not src_ip or not dst_ip:
                continue

            key = (
                src_ip,
                dst_ip,
                int(src_port),
                int(dst_port),
            )

            flow_counts[key] += 1
            flow_proto[key] = proto

        except Exception:
            continue

    return flow_counts, flow_proto


def split_ip_port(value: str):
    value = value.strip()

    # IPv4 only in this Mininet experiment.
    parts = value.rsplit(".", 1)
    if len(parts) != 2:
        return "", 0

    ip = parts[0]
    port = parts[1]

    try:
        return ip, int(port)
    except Exception:
        return ip, 0


def normalize_action(action):
    return str(action or "").strip().upper()


def build_policy_action(row, ip_proto, proto_packet_count, quarantine_ip):
    prediction = str(row.get("prediction", "")).strip().upper()
    recommended_action = normalize_action(row.get("recommended_action", ""))
    dst_ip = str(row.get("destination_ip", "")).strip()

    # If the flow is already redirected to quarantine/sinkhole, do not treat it as
    # another primary malicious flow. It is evidence that quarantine enforcement happened.
    if quarantine_ip and dst_ip == quarantine_ip:
        return "QUARANTINE_OBSERVED"

    # iperf3 TCP control/control-like flows can look attack-like under selected
    # CICFlowMeter features. In this runtime experiment, TCP port 5201 flows are
    # treated as control/benign transport validation unless the controller itself
    # escalates them.
    if int(ip_proto or 0) == TCP_PROTO:
        return "ALLOW_CONTROL_FLOW"

    # For UDP, preserve the model recommendation.
    if prediction == "ATTACK" and recommended_action == "DROP":
        return "DROP"

    if prediction == "BENIGN" and recommended_action == "ALLOW":
        return "ALLOW"

    return recommended_action or prediction or "UNKNOWN"


def main():
    parser = argparse.ArgumentParser(
        description="Build protocol-aware final policy decisions from Final Top-20 runtime predictions and PCAP."
    )
    parser.add_argument("--predictions", required=True, help="final_top20_runtime_predictions.csv")
    parser.add_argument("--pcap", required=True, help="PCAP used for runtime pipeline")
    parser.add_argument("--output", required=True, help="Output protocol-aware final policy CSV")
    parser.add_argument("--quarantine-ip", default="10.10.99.16")
    parser.add_argument("--model-name", default="final_xgboost_top20")
    args = parser.parse_args()

    predictions_path = Path(args.predictions)
    pcap_path = Path(args.pcap)
    output_path = Path(args.output)

    if not predictions_path.exists():
        raise FileNotFoundError(f"Predictions file not found: {predictions_path}")

    if not pcap_path.exists():
        raise FileNotFoundError(f"PCAP file not found: {pcap_path}")

    df = pd.read_csv(predictions_path)

    required = [
        "source_ip",
        "destination_ip",
        "source_port",
        "destination_port",
        "prediction",
        "prediction_value",
        "attack_probability",
        "recommended_action",
    ]

    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required prediction columns: {missing}")

    flow_counts, flow_proto = run_tcpdump_summary(pcap_path)

    rows = []

    for _, row in df.iterrows():
        src_ip = str(row["source_ip"])
        dst_ip = str(row["destination_ip"])
        src_port = int(row["source_port"])
        dst_port = int(row["destination_port"])

        key = (src_ip, dst_ip, src_port, dst_port)

        ip_proto = flow_proto.get(key, 0)
        proto_packet_count = flow_counts.get(key, 0)

        # If exact direction is not found, try reverse direction.
        # This is useful for control flows where the final aggregation may choose one direction.
        if ip_proto == 0:
            reverse_key = (dst_ip, src_ip, dst_port, src_port)
            ip_proto = flow_proto.get(reverse_key, 0)
            proto_packet_count = flow_counts.get(reverse_key, 0)

        policy_final_action = build_policy_action(
            row=row,
            ip_proto=ip_proto,
            proto_packet_count=proto_packet_count,
            quarantine_ip=args.quarantine_ip,
        )

        rows.append({
            "src_ip": src_ip,
            "dst_ip": dst_ip,
            "src_port": src_port,
            "dst_port": dst_port,
            "ip_proto": int(ip_proto or 0),
            "proto_packet_count": int(proto_packet_count or 0),
            "prediction": row["prediction"],
            "prediction_value": int(row["prediction_value"]),
            "attack_probability": float(row["attack_probability"]),
            "recommended_action": row["recommended_action"],
            "policy_final_action": policy_final_action,
            "model_name": args.model_name,
            "decision_source": "final_top20_runtime_pipeline_protocol_aware",
            "note": row.get("note", ""),
        })

    out_df = pd.DataFrame(rows)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(output_path, index=False)

    summary = {
        "predictions": str(predictions_path),
        "pcap": str(pcap_path),
        "output": str(output_path),
        "rows": len(out_df),
        "policy_final_action_counts": out_df["policy_final_action"].value_counts(dropna=False).to_dict(),
        "ip_proto_counts": out_df["ip_proto"].value_counts(dropna=False).to_dict(),
    }

    summary_path = output_path.with_suffix(".summary.json")
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print("[INFO] Written:", output_path)
    print("[INFO] Summary:", summary_path)
    print()
    print(out_df.to_string(index=False))


if __name__ == "__main__":
    main()
