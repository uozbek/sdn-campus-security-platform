#!/usr/bin/env python3
import argparse
import json
from datetime import datetime
from pathlib import Path

import pandas as pd


SUMMARY_NAME = "mixed_traffic_experiment_summary.json"


def safe_read_json(path):
    path = Path(path)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def flatten_summary(summary):
    comparison = summary.get("comparison_summary", {})
    row_counts = summary.get("row_counts", {})
    action_counts = summary.get("action_counts", {})

    controller_actions = action_counts.get("controller_policy_final_action", {})
    final_actions = action_counts.get("final_policy_final_action", {})
    mitigation_actions = action_counts.get("mitigation_policy_final_action", {})
    quarantine_actions = action_counts.get("quarantine_policy_final_action", {})
    rate_limit_actions = action_counts.get("rate_limit_policy_final_action", {})

    return {
        "experiment_dir": summary.get("experiment_dir", ""),

        "policy_decisions_rows": row_counts.get("policy_decisions", 0),
        "predictions_rows": row_counts.get("predictions", 0),
        "flow_stats_rows": row_counts.get("flow_stats", 0),
        "mitigation_log_rows": row_counts.get("mitigation_log", 0),
        "quarantine_log_rows": row_counts.get("quarantine_log", 0),
        "rate_limit_log_rows": row_counts.get("rate_limit_log", 0),
        "final_runtime_predictions_rows": row_counts.get("final_runtime_predictions", 0),
        "final_protocol_aware_policy_rows": row_counts.get("final_protocol_aware_policy", 0),
        "comparison_rows": row_counts.get("comparison", 0),

        "controller_allow": controller_actions.get("allow", 0),
        "controller_monitor": controller_actions.get("monitor", 0),
        "controller_rate_limit": controller_actions.get("rate_limit", 0),
        "controller_drop": controller_actions.get("drop", 0),
        "controller_quarantine_candidate": controller_actions.get("quarantine_candidate", 0),

        "final_allow": final_actions.get("ALLOW", 0),
        "final_allow_control_flow": final_actions.get("ALLOW_CONTROL_FLOW", 0),
        "final_drop": final_actions.get("DROP", 0),
        "final_quarantine_observed": final_actions.get("QUARANTINE_OBSERVED", 0),

        "mitigation_drop": mitigation_actions.get("drop", 0),
        "quarantine_candidate": quarantine_actions.get("quarantine_candidate", 0),
        "rate_limit": rate_limit_actions.get("rate_limit", 0),

        "matched_controller_exact_count": comparison.get("matched_controller_exact_count", 0),
        "matched_controller_ip_port_count": comparison.get("matched_controller_ip_port_count", 0),
        "action_match_count": comparison.get("action_match_count", 0),
        "security_compatible_action_count": comparison.get("security_compatible_action_count", 0),
        "matched_mitigation_drop_count": comparison.get("matched_mitigation_drop_count", 0),
        "matched_quarantine_count": comparison.get("matched_quarantine_count", 0),
        "matched_rate_limit_count": comparison.get("matched_rate_limit_count", 0),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Aggregate multiple mixed traffic experiment summaries."
    )
    parser.add_argument(
        "--root-dir",
        default="experiments/results/mixed_traffic_experiments",
        help="Root directory containing mixed traffic experiment folders.",
    )
    parser.add_argument(
        "--pattern",
        default="*mixed_benign_malicious_replay_v1",
        help="Experiment directory glob pattern.",
    )
    parser.add_argument(
        "--output-dir",
        default="experiments/results/mixed_traffic_experiments/aggregate_reports",
        help="Output directory for aggregate CSV/JSON/MD reports.",
    )
    parser.add_argument(
        "--min-runs",
        type=int,
        default=1,
        help="Minimum run count expected. Used only for reporting warning.",
    )
    args = parser.parse_args()

    root_dir = Path(args.root_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    run_dirs = sorted(root_dir.glob(args.pattern))

    rows = []
    skipped = []

    for run_dir in run_dirs:
        summary_path = run_dir / SUMMARY_NAME
        if not summary_path.exists():
            skipped.append(str(run_dir))
            continue

        summary = safe_read_json(summary_path)
        if not summary:
            skipped.append(str(run_dir))
            continue

        rows.append(flatten_summary(summary))

    if not rows:
        raise SystemExit("[ERROR] No valid mixed traffic experiment summaries found.")

    df = pd.DataFrame(rows)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    csv_path = output_dir / f"mixed_traffic_multi_run_summary_{timestamp}.csv"
    json_path = output_dir / f"mixed_traffic_multi_run_summary_{timestamp}.json"
    md_path = output_dir / f"mixed_traffic_multi_run_report_{timestamp}.md"

    df.to_csv(csv_path, index=False)

    numeric_cols = [
        c for c in df.columns
        if c != "experiment_dir" and pd.api.types.is_numeric_dtype(df[c])
    ]

    aggregate_stats = {}

    for col in numeric_cols:
        aggregate_stats[col] = {
            "mean": float(df[col].mean()),
            "std": float(df[col].std(ddof=0)),
            "min": float(df[col].min()),
            "max": float(df[col].max()),
            "sum": float(df[col].sum()),
        }

    payload = {
        "generated_at_utc": datetime.utcnow().isoformat(),
        "root_dir": str(root_dir),
        "pattern": args.pattern,
        "run_count": int(len(df)),
        "skipped_count": int(len(skipped)),
        "skipped_dirs": skipped,
        "csv": str(csv_path),
        "aggregate_stats": aggregate_stats,
        "runs": rows,
    }

    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    md = []
    md.append("# Mixed Traffic Multi-Run Aggregate Report")
    md.append("")
    md.append(f"- Generated at UTC: `{payload['generated_at_utc']}`")
    md.append(f"- Root directory: `{root_dir}`")
    md.append(f"- Pattern: `{args.pattern}`")
    md.append(f"- Valid run count: `{len(df)}`")
    md.append(f"- Skipped directories: `{len(skipped)}`")
    md.append("")

    if len(df) < args.min_runs:
        md.append("> WARNING: Valid run count is lower than the requested minimum run count.")
        md.append("")

    md.append("## 1. Per-Run Summary")
    md.append("")
    display_cols = [
        "experiment_dir",
        "policy_decisions_rows",
        "flow_stats_rows",
        "final_runtime_predictions_rows",
        "controller_allow",
        "controller_drop",
        "controller_rate_limit",
        "controller_quarantine_candidate",
        "mitigation_drop",
        "quarantine_candidate",
        "rate_limit",
        "matched_controller_exact_count",
        "security_compatible_action_count",
        "matched_mitigation_drop_count",
        "matched_quarantine_count",
        "matched_rate_limit_count",
    ]

    available_display_cols = [c for c in display_cols if c in df.columns]
    md.append(df[available_display_cols].to_markdown(index=False))
    md.append("")

    md.append("## 2. Aggregate Metrics")
    md.append("")
    selected_metrics = [
        "policy_decisions_rows",
        "flow_stats_rows",
        "final_runtime_predictions_rows",
        "controller_allow",
        "controller_drop",
        "controller_rate_limit",
        "controller_quarantine_candidate",
        "mitigation_drop",
        "quarantine_candidate",
        "rate_limit",
        "matched_controller_exact_count",
        "security_compatible_action_count",
        "matched_mitigation_drop_count",
        "matched_quarantine_count",
        "matched_rate_limit_count",
    ]

    md.append("| Metric | Mean | Std | Min | Max | Sum |")
    md.append("|---|---:|---:|---:|---:|---:|")
    for metric in selected_metrics:
        if metric not in aggregate_stats:
            continue
        s = aggregate_stats[metric]
        md.append(
            f"| {metric} | {s['mean']:.4f} | {s['std']:.4f} | "
            f"{s['min']:.4f} | {s['max']:.4f} | {s['sum']:.4f} |"
        )
    md.append("")

    md.append("## 3. Interpretation")
    md.append("")
    md.append(
        "This aggregate report summarizes repeated mixed benign/malicious traffic experiments. "
        "The key thesis-relevant indicators are the number of security-compatible final/controller decisions, "
        "and whether rate-limit, drop, and quarantine enforcement actions are repeatedly observed."
    )
    md.append("")

    md.append("## 4. Thesis-Relevant Use")
    md.append("")
    md.append(
        "The table can be used in the experimental results chapter to report repeated runtime validation outcomes. "
        "If multiple runs show consistent mitigation and quarantine behavior, the experiment becomes stronger than a single-run demonstration."
    )
    md.append("")

    md_path.write_text("\n".join(md), encoding="utf-8")

    print("[INFO] Valid runs:", len(df))
    print("[INFO] Skipped dirs:", len(skipped))
    print("[INFO] CSV :", csv_path)
    print("[INFO] JSON:", json_path)
    print("[INFO] MD  :", md_path)


if __name__ == "__main__":
    main()
