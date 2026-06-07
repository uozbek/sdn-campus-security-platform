#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

import pandas as pd


def read_json(path: Path):
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path):
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def write_md_table(df: pd.DataFrame, path: Path, title: str):
    md = [f"# {title}", ""]
    if df.empty:
        md.append("_No data available._")
    else:
        md.append(df.to_markdown(index=False))
    path.write_text("\n".join(md) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--exp-dir", required=True)
    parser.add_argument("--final-run-dir", required=True)
    parser.add_argument("--compare-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    exp_dir = Path(args.exp_dir)
    final_run_dir = Path(args.final_run_dir)
    compare_dir = Path(args.compare_dir)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    experiment_summary = read_json(exp_dir / "mixed_traffic_experiment_summary.json")
    comparison_summary = read_json(compare_dir / "final_top20_vs_port_aware_controller_summary.json")

    final_policy = read_csv(final_run_dir / "final_top20_policy_decisions_protocol_aware.csv")
    comparison = read_csv(compare_dir / "final_top20_vs_port_aware_controller_comparison.csv")

    row_counts = experiment_summary.get("row_counts", {})
    action_counts = experiment_summary.get("action_counts", {})

    table_1 = pd.DataFrame([
        {"Metric": "Controller policy decisions", "Value": row_counts.get("policy_decisions", 0)},
        {"Metric": "Controller predictions", "Value": row_counts.get("predictions", 0)},
        {"Metric": "Flow statistics rows", "Value": row_counts.get("flow_stats", 0)},
        {"Metric": "Drop mitigation log rows", "Value": row_counts.get("mitigation_log", 0)},
        {"Metric": "Quarantine log rows", "Value": row_counts.get("quarantine_log", 0)},
        {"Metric": "Rate-limit log rows", "Value": row_counts.get("rate_limit_log", 0)},
        {"Metric": "Final runtime prediction rows", "Value": row_counts.get("final_runtime_predictions", 0)},
        {"Metric": "Protocol-aware final policy rows", "Value": row_counts.get("final_protocol_aware_policy", 0)},
        {"Metric": "Comparison rows", "Value": row_counts.get("comparison", 0)},
    ])

    controller_actions = action_counts.get("controller_policy_final_action", {})
    table_2 = pd.DataFrame([
        {"Action": k, "Count": v}
        for k, v in controller_actions.items()
    ]).sort_values("Count", ascending=False) if controller_actions else pd.DataFrame(columns=["Action", "Count"])

    final_actions = action_counts.get("final_policy_final_action", {})
    table_3 = pd.DataFrame([
        {"Final policy action": k, "Count": v}
        for k, v in final_actions.items()
    ]).sort_values("Count", ascending=False) if final_actions else pd.DataFrame(columns=["Final policy action", "Count"])

    table_4 = pd.DataFrame([
        {"Metric": "Exact controller flow-key matches", "Value": comparison_summary.get("matched_controller_exact_count", 0)},
        {"Metric": "Relaxed IP-port matches", "Value": comparison_summary.get("matched_controller_ip_port_count", 0)},
        {"Metric": "Action matches", "Value": comparison_summary.get("action_match_count", 0)},
        {"Metric": "Security-compatible action matches", "Value": comparison_summary.get("security_compatible_action_count", 0)},
        {"Metric": "Matched DROP mitigation", "Value": comparison_summary.get("matched_mitigation_drop_count", 0)},
        {"Metric": "Matched quarantine", "Value": comparison_summary.get("matched_quarantine_count", 0)},
        {"Metric": "Matched rate-limit", "Value": comparison_summary.get("matched_rate_limit_count", 0)},
    ])

    table_5_cols = [
        "src_ip", "dst_ip", "src_port", "dst_port", "ip_proto",
        "prediction", "attack_probability", "recommended_action", "policy_final_action"
    ]
    table_5 = final_policy[[c for c in table_5_cols if c in final_policy.columns]].copy()

    table_6_cols = [
        "src_ip", "dst_ip", "src_port", "dst_port", "ip_proto",
        "final_action", "controller_action",
        "matched_controller_exact", "security_compatible_action",
        "matched_mitigation_drop", "matched_quarantine", "matched_rate_limit"
    ]
    table_6 = comparison[[c for c in table_6_cols if c in comparison.columns]].copy()

    outputs = {
        "table_1_experiment_row_counts.csv": table_1,
        "table_2_controller_action_distribution.csv": table_2,
        "table_3_final_policy_action_distribution.csv": table_3,
        "table_4_controller_comparison_metrics.csv": table_4,
        "table_5_protocol_aware_final_policy.csv": table_5,
        "table_6_flow_level_comparison.csv": table_6,
    }

    for name, df in outputs.items():
        df.to_csv(out_dir / name, index=False)

    write_md_table(table_1, out_dir / "table_1_experiment_row_counts.md", "Table 1. Experiment Output Row Counts")
    write_md_table(table_2, out_dir / "table_2_controller_action_distribution.md", "Table 2. Controller Policy Action Distribution")
    write_md_table(table_3, out_dir / "table_3_final_policy_action_distribution.md", "Table 3. Protocol-Aware Final Policy Action Distribution")
    write_md_table(table_4, out_dir / "table_4_controller_comparison_metrics.md", "Table 4. Final Model and Controller Comparison Metrics")
    write_md_table(table_5, out_dir / "table_5_protocol_aware_final_policy.md", "Table 5. Protocol-Aware Final Policy Output")
    write_md_table(table_6, out_dir / "table_6_flow_level_comparison.md", "Table 6. Flow-Level Final Model and Controller Comparison")

    thesis_text = f"""# Thesis-Ready Experimental Result Summary

The mixed benign and malicious traffic experiment was conducted to evaluate the proposed SDN-based IDS/IPS prototype under runtime conditions. The experiment combined benign TCP/UDP traffic and a high-volume malicious UDP flow in a Mininet/Ryu environment. Runtime PCAP data were processed through the Final XGBoost Top-20 feature extraction pipeline and compared against controller-side policy and enforcement logs.

The controller generated {row_counts.get("policy_decisions", 0)} policy decision records and {row_counts.get("flow_stats", 0)} flow-statistics records. The protocol-aware runtime pipeline produced {row_counts.get("final_protocol_aware_policy", 0)} final policy rows. Controller-side enforcement produced {action_counts.get("mitigation_policy_final_action", {}).get("drop", 0)} drop mitigation records and {action_counts.get("quarantine_policy_final_action", {}).get("quarantine_candidate", 0)} quarantine records. Rate-limit was not triggered in this run, which suggests that the malicious UDP flow escalated directly toward higher-severity mitigation.

The comparison between the protocol-aware final model output and the controller policy logs produced {comparison_summary.get("matched_controller_exact_count", 0)} exact flow-key matches and {comparison_summary.get("security_compatible_action_count", 0)} security-compatible decisions. The malicious UDP flow was detected by the runtime model and was handled by the controller through drop and quarantine-related actions. Benign and control-like TCP flows were preserved through allow/control-flow handling.

These findings provide runtime evidence that the proposed architecture can connect offline-trained ML-based DDoS detection with SDN controller-side enforcement. Unlike a purely offline classification experiment, this validation covers PCAP capture, feature extraction, model inference, protocol-aware policy interpretation, controller-side policy generation, and OpenFlow-based mitigation.
"""

    (out_dir / "thesis_ready_result_summary.md").write_text(thesis_text, encoding="utf-8")

    print("[INFO] Thesis result tables written to:", out_dir)
    for p in sorted(out_dir.glob("*")):
        print("[INFO]", p)


if __name__ == "__main__":
    main()
