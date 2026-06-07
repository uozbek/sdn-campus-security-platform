#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

import pandas as pd


REQUIRED_ROOT_FILES = [
    "policy_decisions.csv",
    "predictions.csv",
    "mitigation_log.csv",
    "quarantine_log.csv",
    "rate_limit_log.csv",
    "flow_stats.csv",
    "same_run_experiment_report.md",
    "same_run_experiment_summary.json",
]

REQUIRED_COMPARISON_FILES = [
    "final_top20_vs_port_aware_controller_summary.json",
    "final_top20_vs_port_aware_controller_comparison.csv",
    "final_top20_vs_port_aware_controller_report.md",
]


def file_status(path: Path):
    return {
        "path": str(path),
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() else 0,
    }


def read_json_safe(path: Path):
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def read_csv_safe(path: Path):
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def main():
    parser = argparse.ArgumentParser(
        description="Validate same-run Final Top-20 controller experiment outputs."
    )
    parser.add_argument("--exp-dir", required=True, help="Experiment directory")
    parser.add_argument(
        "--comparison-dir-name",
        default="port_aware_comparison_udp_aware_v2",
        help="Comparison subdirectory name"
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output validation JSON path"
    )

    args = parser.parse_args()

    exp_dir = Path(args.exp_dir)
    comparison_dir = exp_dir / args.comparison_dir_name

    if not exp_dir.exists():
        raise FileNotFoundError(f"Experiment directory not found: {exp_dir}")

    root_file_checks = {
        name: file_status(exp_dir / name)
        for name in REQUIRED_ROOT_FILES
    }

    comparison_file_checks = {
        name: file_status(comparison_dir / name)
        for name in REQUIRED_COMPARISON_FILES
    }

    summary_path = exp_dir / "same_run_experiment_summary.json"
    comparison_summary_path = comparison_dir / "final_top20_vs_port_aware_controller_summary.json"
    comparison_csv_path = comparison_dir / "final_top20_vs_port_aware_controller_comparison.csv"

    experiment_summary = read_json_safe(summary_path)
    comparison_summary = read_json_safe(comparison_summary_path)
    comparison_df = read_csv_safe(comparison_csv_path)

    missing_root_files = [
        name for name, info in root_file_checks.items()
        if not info["exists"] or info["size_bytes"] == 0
    ]

    missing_comparison_files = [
        name for name, info in comparison_file_checks.items()
        if not info["exists"] or info["size_bytes"] == 0
    ]

    row_counts = experiment_summary.get("row_counts", {})
    comparison_metrics = comparison_summary

    final_policy_rows = comparison_metrics.get("row_counts", {}).get("final_policy", 0)
    comparison_rows = comparison_metrics.get("row_counts", {}).get("comparison", 0)
    matched_ip_port = comparison_metrics.get("matched_controller_ip_port_count", 0)
    security_compatible = comparison_metrics.get("security_compatible_action_count", 0)
    matched_drop = comparison_metrics.get("matched_mitigation_drop_count", 0)
    matched_quarantine = comparison_metrics.get("matched_quarantine_count", 0)

    pass_conditions = {
        "no_missing_root_files": len(missing_root_files) == 0,
        "no_missing_comparison_files": len(missing_comparison_files) == 0,
        "policy_rows_exist": int(row_counts.get("policy_decisions", 0)) > 0,
        "predictions_rows_exist": int(row_counts.get("predictions", 0)) > 0,
        "flow_stats_rows_exist": int(row_counts.get("flow_stats", 0)) > 0,
        "final_policy_rows_exist": int(final_policy_rows) > 0,
        "comparison_rows_exist": int(comparison_rows) > 0,
        "ip_port_matches_exist": int(matched_ip_port) > 0,
        "security_compatible_all_final_rows": (
            int(final_policy_rows) > 0
            and int(security_compatible) == int(final_policy_rows)
        ),
        "udp_attack_has_drop_or_quarantine": (
            int(matched_drop) > 0 or int(matched_quarantine) > 0
        ),
    }

    overall_pass = all(pass_conditions.values())

    validation = {
        "experiment_dir": str(exp_dir),
        "comparison_dir": str(comparison_dir),
        "status": "PASS" if overall_pass else "FAIL",
        "root_file_checks": root_file_checks,
        "comparison_file_checks": comparison_file_checks,
        "missing_root_files": missing_root_files,
        "missing_comparison_files": missing_comparison_files,
        "row_counts": row_counts,
        "comparison_metrics": {
            "final_policy_rows": final_policy_rows,
            "comparison_rows": comparison_rows,
            "matched_controller_ip_port_count": matched_ip_port,
            "security_compatible_action_count": security_compatible,
            "matched_mitigation_drop_count": matched_drop,
            "matched_quarantine_count": matched_quarantine,
        },
        "pass_conditions": pass_conditions,
    }

    output_path = Path(args.output) if args.output else exp_dir / "same_run_experiment_validation.json"
    output_path.write_text(
        json.dumps(validation, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print("=" * 80)
    print("Same-Run Experiment Validation")
    print("=" * 80)
    print("Experiment:", exp_dir)
    print("Status    :", validation["status"])
    print()
    print("Pass conditions:")
    for key, value in pass_conditions.items():
        print(f" - {key}: {value}")

    print()
    print("[INFO] Written:", output_path)

    if not overall_pass:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
