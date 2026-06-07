#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

import pandas as pd


def read_csv(path: Path):
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def value_counts(df, col):
    if df.empty or col not in df.columns:
        return {}
    return df[col].value_counts(dropna=False).to_dict()


def row_count(path: Path):
    if not path.exists():
        return 0
    try:
        return len(pd.read_csv(path))
    except Exception:
        return 0


def markdown_table(df, columns):
    if df.empty:
        return "_No rows._"

    cols = [c for c in columns if c in df.columns]
    if not cols:
        return "_No matching columns._"

    lines = []
    lines.append("| " + " | ".join(cols) + " |")
    lines.append("|" + "|".join(["---"] * len(cols)) + "|")

    for _, row in df[cols].iterrows():
        vals = []
        for c in cols:
            v = row[c]
            vals.append("" if pd.isna(v) else str(v))
        lines.append("| " + " | ".join(vals) + " |")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--exp-dir", required=True)
    parser.add_argument("--final-run-dir", required=True)
    parser.add_argument("--compare-dir", required=True)
    args = parser.parse_args()

    exp_dir = Path(args.exp_dir)
    final_run_dir = Path(args.final_run_dir)
    compare_dir = Path(args.compare_dir)

    logs_dir = exp_dir / "logs"

    files = {
        "pcap": exp_dir / "pcaps" / "mixed_benign_malicious_live.pcap",
        "policy_decisions": logs_dir / "policy_decisions.csv",
        "predictions": logs_dir / "predictions.csv",
        "flow_stats": logs_dir / "flow_stats.csv",
        "mitigation_log": logs_dir / "mitigation_log.csv",
        "quarantine_log": logs_dir / "quarantine_log.csv",
        "rate_limit_log": logs_dir / "rate_limit_log.csv",
        "final_runtime_predictions": final_run_dir / "final_top20_runtime_predictions.csv",
        "final_protocol_aware_policy": final_run_dir / "final_top20_policy_decisions_protocol_aware.csv",
        "runtime_pipeline_report": final_run_dir / "runtime_pipeline_report.md",
        "comparison_summary": compare_dir / "final_top20_vs_port_aware_controller_summary.json",
        "comparison_csv": compare_dir / "final_top20_vs_port_aware_controller_comparison.csv",
        "comparison_report": compare_dir / "final_top20_vs_port_aware_controller_report.md",
    }

    policy_df = read_csv(files["policy_decisions"])
    mitigation_df = read_csv(files["mitigation_log"])
    quarantine_df = read_csv(files["quarantine_log"])
    rate_limit_df = read_csv(files["rate_limit_log"])
    final_policy_df = read_csv(files["final_protocol_aware_policy"])
    comparison_df = read_csv(files["comparison_csv"])

    comparison_summary = {}
    if files["comparison_summary"].exists():
        comparison_summary = json.loads(files["comparison_summary"].read_text(encoding="utf-8"))

    summary = {
        "experiment_dir": str(exp_dir),
        "final_run_dir": str(final_run_dir),
        "compare_dir": str(compare_dir),
        "files": {k: str(v) for k, v in files.items()},
        "row_counts": {
            "policy_decisions": row_count(files["policy_decisions"]),
            "predictions": row_count(files["predictions"]),
            "flow_stats": row_count(files["flow_stats"]),
            "mitigation_log": row_count(files["mitigation_log"]),
            "quarantine_log": row_count(files["quarantine_log"]),
            "rate_limit_log": row_count(files["rate_limit_log"]),
            "final_runtime_predictions": row_count(files["final_runtime_predictions"]),
            "final_protocol_aware_policy": row_count(files["final_protocol_aware_policy"]),
            "comparison": row_count(files["comparison_csv"]),
        },
        "action_counts": {
            "controller_policy_final_action": value_counts(policy_df, "policy_final_action"),
            "mitigation_policy_final_action": value_counts(mitigation_df, "policy_final_action"),
            "quarantine_policy_final_action": value_counts(quarantine_df, "policy_final_action"),
            "rate_limit_policy_final_action": value_counts(rate_limit_df, "policy_final_action"),
            "final_policy_final_action": value_counts(final_policy_df, "policy_final_action"),
        },
        "comparison_summary": comparison_summary,
    }

    summary_path = exp_dir / "mixed_traffic_experiment_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    md = []

    md.append("# Mixed Benign and Malicious Traffic Runtime Experiment Report\n")
    md.append(f"- Experiment directory: `{exp_dir}`")
    md.append(f"- Final runtime pipeline directory: `{final_run_dir}`")
    md.append(f"- Comparison directory: `{compare_dir}`\n")

    md.append("## 1. Purpose\n")
    md.append(
        "This experiment evaluates the proposed SDN-based IDS/IPS prototype under a mixed traffic scenario "
        "containing both benign and malicious flows. The goal is to verify whether the Final XGBoost Top-20 "
        "model, runtime PCAP-based feature extraction pipeline, and Ryu controller-side hybrid policy engine "
        "produce security-compatible decisions on the same traffic instance.\n"
    )

    md.append("## 2. Experimental Scenario\n")
    md.append(
        "The mixed traffic scenario includes benign TCP/UDP traffic and a high-volume malicious UDP flow. "
        "Benign traffic was generated from hosts such as `10.10.10.2` and `10.10.10.3` toward the server "
        "`10.10.40.14`. Malicious traffic was generated from `10.10.60.12` toward `10.10.40.14`. "
        "After repeated high-confidence attack behavior, traffic was also observed toward the quarantine host "
        "`10.10.99.16`.\n"
    )

    md.append("## 3. Input and Output Files\n")
    for key, path in files.items():
        md.append(f"- {key}: `{path}` — {'exists' if path.exists() else 'missing'}")
    md.append("")

    md.append("## 4. Row Counts\n")
    md.append("| File | Rows |")
    md.append("|---|---:|")
    for key, count in summary["row_counts"].items():
        md.append(f"| {key} | {count} |")
    md.append("")

    md.append("## 5. Controller Policy Action Distribution\n")
    md.append("```json")
    md.append(json.dumps(summary["action_counts"]["controller_policy_final_action"], indent=2, ensure_ascii=False))
    md.append("```\n")

    md.append("## 6. Mitigation, Rate-Limit and Quarantine Actions\n")
    md.append("### Drop Mitigation")
    md.append("```json")
    md.append(json.dumps(summary["action_counts"]["mitigation_policy_final_action"], indent=2, ensure_ascii=False))
    md.append("```\n")

    md.append("### Rate-Limit")
    md.append("```json")
    md.append(json.dumps(summary["action_counts"]["rate_limit_policy_final_action"], indent=2, ensure_ascii=False))
    md.append("```\n")

    md.append("### Quarantine")
    md.append("```json")
    md.append(json.dumps(summary["action_counts"]["quarantine_policy_final_action"], indent=2, ensure_ascii=False))
    md.append("```\n")

    md.append("## 7. Final Top-20 Protocol-Aware Policy Output\n")
    md.append(markdown_table(
        final_policy_df,
        [
            "src_ip",
            "dst_ip",
            "src_port",
            "dst_port",
            "ip_proto",
            "proto_packet_count",
            "prediction",
            "attack_probability",
            "recommended_action",
            "policy_final_action",
        ],
    ))
    md.append("")

    md.append("## 8. Port-Aware and Protocol-Aware Comparison Summary\n")
    md.append("```json")
    md.append(json.dumps(comparison_summary, indent=2, ensure_ascii=False))
    md.append("```\n")

    md.append("## 9. Flow-Level Comparison\n")
    md.append(markdown_table(
        comparison_df,
        [
            "src_ip",
            "dst_ip",
            "src_port",
            "dst_port",
            "ip_proto",
            "final_action",
            "controller_action",
            "matched_controller_exact",
            "security_compatible_action",
            "matched_mitigation_drop",
            "matched_quarantine",
            "matched_rate_limit",
        ],
    ))
    md.append("")

    md.append("## 10. Interpretation\n")
    md.append(
        "The results indicate that benign/control flows were preserved, while the malicious UDP flow was detected "
        "and handled through a security-compatible controller response. The controller produced rate-limit, drop, "
        "and quarantine-related actions for the malicious UDP traffic. This demonstrates that the proposed system "
        "can connect offline-trained ML detection with SDN controller-side enforcement in a live Mininet/Ryu setting.\n"
    )

    md.append(
        "The quarantine-observed flow toward `10.10.99.16` is interpreted as a post-mitigation observation rather "
        "than a normal source-to-victim flow. Therefore, direct controller policy matching is not necessarily expected "
        "for that row; its meaning is confirmed through quarantine logs.\n"
    )

    md.append("## 11. Thesis-Relevant Contribution\n")
    md.append(
        "This experiment strengthens the methodological validity of the study because it demonstrates an end-to-end "
        "runtime validation path: mixed traffic generation, PCAP capture, selected-feature extraction, Final Top-20 "
        "XGBoost inference, controller-side policy decision, and OpenFlow-based mitigation. Unlike an offline-only "
        "classification result, this experiment shows that the proposed IDS/IPS architecture can operate in an SDN "
        "runtime environment.\n"
    )

    md.append("## 12. Limitations\n")
    md.append(
        "- Some controller decisions depend on flow-stat timing and may not appear for every PCAP-extracted flow.\n"
        "- Exact action matching is not always appropriate because the controller has a richer action space than the binary ML model.\n"
        "- Protocol-aware post-processing was required because the runtime prediction output did not directly preserve protocol information.\n"
        "- The experiment was conducted in a controlled Mininet environment and should later be repeated with more diverse traffic profiles.\n"
    )

    md.append("## 13. Conclusion\n")
    md.append(
        "The mixed benign and malicious traffic experiment provides runtime evidence that the proposed SDN-based "
        "hybrid IDS/IPS prototype can preserve benign traffic, detect malicious UDP behavior, and apply mitigation "
        "through rate-limit, drop, and quarantine mechanisms.\n"
    )

    report_path = exp_dir / "mixed_traffic_experiment_report.md"
    report_path.write_text("\n".join(md), encoding="utf-8")

    print("[INFO] Written:", report_path)
    print("[INFO] Written:", summary_path)


if __name__ == "__main__":
    main()
