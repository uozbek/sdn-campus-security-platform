#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

import pandas as pd


def read_csv_safe(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def value_counts_safe(df: pd.DataFrame, column: str):
    if df.empty or column not in df.columns:
        return {}
    return df[column].value_counts(dropna=False).to_dict()


def main():
    parser = argparse.ArgumentParser(
        description="Generate a consolidated report for same-run final Top-20 controller comparison."
    )
    parser.add_argument("--exp-dir", required=True, help="Experiment directory")
    parser.add_argument("--output-report", default=None)
    parser.add_argument("--output-summary", default=None)
    args = parser.parse_args()

    exp_dir = Path(args.exp_dir)

    if not exp_dir.exists():
        raise FileNotFoundError(f"Experiment directory not found: {exp_dir}")

    policy_path = exp_dir / "policy_decisions.csv"
    mitigation_path = exp_dir / "mitigation_log.csv"
    quarantine_path = exp_dir / "quarantine_log.csv"
    rate_limit_path = exp_dir / "rate_limit_log.csv"
    flow_stats_path = exp_dir / "flow_stats.csv"
    predictions_path = exp_dir / "predictions.csv"

    comparison_dir = exp_dir / "port_aware_comparison_udp_aware_v2"
    comparison_summary_path = comparison_dir / "final_top20_vs_port_aware_controller_summary.json"
    comparison_csv_path = comparison_dir / "final_top20_vs_port_aware_controller_comparison.csv"
    comparison_report_path = comparison_dir / "final_top20_vs_port_aware_controller_report.md"

    policy_df = read_csv_safe(policy_path)
    mitigation_df = read_csv_safe(mitigation_path)
    quarantine_df = read_csv_safe(quarantine_path)
    rate_limit_df = read_csv_safe(rate_limit_path)
    flow_stats_df = read_csv_safe(flow_stats_path)
    predictions_df = read_csv_safe(predictions_path)
    comparison_df = read_csv_safe(comparison_csv_path)

    comparison_summary = {}
    if comparison_summary_path.exists():
        comparison_summary = json.loads(comparison_summary_path.read_text(encoding="utf-8"))

    summary = {
        "experiment_dir": str(exp_dir),
        "files": {
            "policy_decisions": str(policy_path),
            "mitigation_log": str(mitigation_path),
            "quarantine_log": str(quarantine_path),
            "rate_limit_log": str(rate_limit_path),
            "flow_stats": str(flow_stats_path),
            "predictions": str(predictions_path),
            "comparison_summary": str(comparison_summary_path),
            "comparison_csv": str(comparison_csv_path),
            "comparison_report": str(comparison_report_path),
        },
        "row_counts": {
            "policy_decisions": int(len(policy_df)),
            "mitigation_log": int(len(mitigation_df)),
            "quarantine_log": int(len(quarantine_df)),
            "rate_limit_log": int(len(rate_limit_df)),
            "flow_stats": int(len(flow_stats_df)),
            "predictions": int(len(predictions_df)),
            "comparison": int(len(comparison_df)),
        },
        "action_counts": {
            "policy_final_action": value_counts_safe(policy_df, "policy_final_action"),
            "mitigation_policy_final_action": value_counts_safe(mitigation_df, "policy_final_action"),
            "quarantine_policy_final_action": value_counts_safe(quarantine_df, "policy_final_action"),
            "rate_limit_policy_final_action": value_counts_safe(rate_limit_df, "policy_final_action"),
        },
        "comparison_summary": comparison_summary,
    }

    output_summary = Path(args.output_summary) if args.output_summary else exp_dir / "same_run_experiment_summary.json"
    output_report = Path(args.output_report) if args.output_report else exp_dir / "same_run_experiment_report.md"

    output_summary.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    md = []
    md.append("# Same-Run Final Top-20 Controller Experiment Report")
    md.append("")
    md.append(f"- Experiment directory: `{exp_dir}`")
    md.append("")
    md.append("## 1. Purpose")
    md.append("")
    md.append(
        "This experiment evaluates whether the external Final XGBoost Top-20 runtime "
        "pipeline and the Ryu controller-side IDS/IPS policy engine produce security-compatible "
        "decisions for the same Mininet traffic run."
    )
    md.append("")
    md.append("## 2. Input and Output Files")
    md.append("")
    for key, value in summary["files"].items():
        exists = Path(value).exists()
        md.append(f"- {key}: `{value}` — {'exists' if exists else 'missing'}")
    md.append("")
    md.append("## 3. Row Counts")
    md.append("")
    md.append("| File | Rows |")
    md.append("|---|---:|")
    for key, value in summary["row_counts"].items():
        md.append(f"| {key} | {value} |")
    md.append("")
    md.append("## 4. Controller Policy Action Distribution")
    md.append("")
    md.append("```json")
    md.append(json.dumps(summary["action_counts"]["policy_final_action"], indent=2, ensure_ascii=False))
    md.append("```")
    md.append("")
    md.append("## 5. Mitigation Action Distribution")
    md.append("")
    md.append("```json")
    md.append(json.dumps(summary["action_counts"]["mitigation_policy_final_action"], indent=2, ensure_ascii=False))
    md.append("```")
    md.append("")
    md.append("## 6. Quarantine Action Distribution")
    md.append("")
    md.append("```json")
    md.append(json.dumps(summary["action_counts"]["quarantine_policy_final_action"], indent=2, ensure_ascii=False))
    md.append("```")
    md.append("")
    md.append("## 7. Port-Aware Final Top-20 vs Controller Comparison")
    md.append("")

    if comparison_summary:
        md.append("```json")
        md.append(json.dumps(comparison_summary, indent=2, ensure_ascii=False))
        md.append("```")
    else:
        md.append("_Comparison summary not found._")

    md.append("")
    md.append("## 8. Flow-Level Comparison")
    md.append("")

    if not comparison_df.empty:
        columns = [
            "src_ip",
            "dst_ip",
            "src_port",
            "dst_port",
            "final_action",
            "controller_action",
            "security_compatible_action",
            "matched_mitigation_drop",
            "matched_quarantine",
            "matched_rate_limit",
        ]
        available = [c for c in columns if c in comparison_df.columns]
        table_df = comparison_df[available].copy()

        # Avoid optional pandas dependency: DataFrame.to_markdown() requires tabulate.
        # Generate a simple Markdown table manually.
        md.append("| " + " | ".join(table_df.columns) + " |")
        md.append("|" + "|".join(["---"] * len(table_df.columns)) + "|")

        for _, row in table_df.iterrows():
            values = [str(row.get(col, "")) for col in table_df.columns]
            md.append("| " + " | ".join(values) + " |")
    else:
        md.append("_No flow-level comparison rows._")

    md.append("")
    md.append("## 9. Interpretation")
    md.append("")
    md.append(
        "The key expected result is that the UDP data flow is classified as malicious by the "
        "final runtime pipeline and is also handled by the controller through DROP and/or "
        "quarantine escalation. TCP control traffic should be treated as control flow and allowed "
        "when UDP-aware policy is applied."
    )
    md.append("")
    md.append("A successful run is characterized by:")
    md.append("")
    md.append("- `matched_controller_ip_port_count` greater than zero")
    md.append("- `security_compatible_action_count` equal to the number of final policy rows")
    md.append("- at least one matched DROP or quarantine action for the UDP attack flow")
    md.append("")
    md.append("## 10. Thesis-Relevant Summary")
    md.append("")
    md.append(
        "This experiment provides runtime evidence that the proposed SDN-based hybrid IDS/IPS "
        "architecture can connect offline-trained ML models with controller-side enforcement. "
        "The same-run design strengthens the methodological validity because PCAP-based model "
        "outputs and controller-side policy decisions are evaluated on the same traffic instance."
    )

    output_report.write_text("\n".join(md), encoding="utf-8")

    print("[INFO] Written summary:", output_summary)
    print("[INFO] Written report :", output_report)
    print(json.dumps(summary["row_counts"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
