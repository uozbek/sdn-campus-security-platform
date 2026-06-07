#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from datetime import datetime

import pandas as pd

# Headless server için
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def read_csv_safe(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def save_bar_chart(series: pd.Series, title: str, xlabel: str, ylabel: str, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)

    if series is None or len(series) == 0:
        fig, ax = plt.subplots(figsize=(8, 4.5))
        ax.text(0.5, 0.5, "No data available", ha="center", va="center")
        ax.set_axis_off()
        fig.tight_layout()
        fig.savefig(output, dpi=200)
        plt.close(fig)
        return

    series = series.sort_values(ascending=False)

    fig, ax = plt.subplots(figsize=(9, 5))
    series.plot(kind="bar", ax=ax)

    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.tick_params(axis="x", rotation=30)

    for container in ax.containers:
        ax.bar_label(container, fmt="%.0f", padding=3)

    fig.tight_layout()
    fig.savefig(output, dpi=200)
    plt.close(fig)


def save_table_as_csv_and_md(df: pd.DataFrame, csv_path: Path, md_path: Path) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(csv_path, index=False)
    md_path.write_text(df.to_markdown(index=False), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate thesis-ready tables and figures from canonical SDN IDS/IPS runtime validation outputs."
    )
    parser.add_argument("--run-dir", required=True, help="Canonical run directory, e.g. run_05_port_aware_repeat_validation")
    parser.add_argument("--final-run-dir", required=True, help="Final runtime pipeline directory for the selected run")
    parser.add_argument("--compare-dir", required=True, help="Comparison directory for the selected run")
    parser.add_argument("--canonical-agg-csv", required=True, help="Canonical aggregate CSV summary")
    parser.add_argument("--output-dir", required=True, help="Output directory for thesis tables and figures")

    args = parser.parse_args()

    run_dir = Path(args.run_dir)
    final_run_dir = Path(args.final_run_dir)
    compare_dir = Path(args.compare_dir)
    canonical_agg_csv = Path(args.canonical_agg_csv)
    output_dir = Path(args.output_dir)

    tables_dir = output_dir / "tables"
    figures_dir = output_dir / "figures"
    manifest_path = output_dir / "thesis_artifacts_manifest.md"
    summary_path = output_dir / "thesis_artifacts_summary.json"

    output_dir.mkdir(parents=True, exist_ok=True)
    tables_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    policy_csv = run_dir / "logs" / "policy_decisions.csv"
    predictions_csv = final_run_dir / "final_top20_runtime_predictions.csv"
    final_policy_csv = final_run_dir / "final_top20_policy_decisions_protocol_aware.csv"
    mitigation_csv = run_dir / "logs" / "mitigation_log.csv"
    quarantine_csv = run_dir / "logs" / "quarantine_log.csv"
    rate_limit_csv = run_dir / "logs" / "rate_limit_log.csv"
    comparison_csv = compare_dir / "final_top20_vs_port_aware_controller_comparison.csv"

    policy_df = read_csv_safe(policy_csv)
    pred_df = read_csv_safe(predictions_csv)
    final_policy_df = read_csv_safe(final_policy_csv)
    mitigation_df = read_csv_safe(mitigation_csv)
    quarantine_df = read_csv_safe(quarantine_csv)
    rate_limit_df = read_csv_safe(rate_limit_csv)
    comparison_df = read_csv_safe(comparison_csv)
    canonical_df = read_csv_safe(canonical_agg_csv)

    generated = []

    # 1) Canonical aggregate thesis table
    canonical_cols = [
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
    canonical_table = canonical_df[[c for c in canonical_cols if c in canonical_df.columns]].copy()
    canonical_table_csv = tables_dir / "table_canonical_runtime_validation_summary.csv"
    canonical_table_md = tables_dir / "table_canonical_runtime_validation_summary.md"
    save_table_as_csv_and_md(canonical_table, canonical_table_csv, canonical_table_md)
    generated += [canonical_table_csv, canonical_table_md]

    # 2) run_05 controller action distribution table
    if not policy_df.empty and "policy_final_action" in policy_df.columns:
        controller_action_table = (
            policy_df["policy_final_action"]
            .value_counts(dropna=False)
            .rename_axis("policy_final_action")
            .reset_index(name="count")
        )
    else:
        controller_action_table = pd.DataFrame(columns=["policy_final_action", "count"])

    controller_action_csv = tables_dir / "table_controller_action_distribution.csv"
    controller_action_md = tables_dir / "table_controller_action_distribution.md"
    save_table_as_csv_and_md(controller_action_table, controller_action_csv, controller_action_md)
    generated += [controller_action_csv, controller_action_md]

    save_bar_chart(
        controller_action_table.set_index("policy_final_action")["count"] if not controller_action_table.empty else pd.Series(dtype=float),
        "Controller Policy Action Distribution",
        "Controller action",
        "Count",
        figures_dir / "fig_controller_action_distribution.png",
    )
    generated.append(figures_dir / "fig_controller_action_distribution.png")

    # 3) Final model prediction distribution
    if not pred_df.empty and "prediction" in pred_df.columns:
        prediction_table = (
            pred_df["prediction"]
            .value_counts(dropna=False)
            .rename_axis("prediction")
            .reset_index(name="count")
        )
    else:
        prediction_table = pd.DataFrame(columns=["prediction", "count"])

    prediction_csv = tables_dir / "table_final_top20_prediction_distribution.csv"
    prediction_md = tables_dir / "table_final_top20_prediction_distribution.md"
    save_table_as_csv_and_md(prediction_table, prediction_csv, prediction_md)
    generated += [prediction_csv, prediction_md]

    save_bar_chart(
        prediction_table.set_index("prediction")["count"] if not prediction_table.empty else pd.Series(dtype=float),
        "Final Top-20 Runtime Prediction Distribution",
        "Prediction",
        "Count",
        figures_dir / "fig_final_top20_prediction_distribution.png",
    )
    generated.append(figures_dir / "fig_final_top20_prediction_distribution.png")

    # 4) Final protocol-aware policy distribution
    if not final_policy_df.empty and "policy_final_action" in final_policy_df.columns:
        final_policy_action_table = (
            final_policy_df["policy_final_action"]
            .value_counts(dropna=False)
            .rename_axis("policy_final_action")
            .reset_index(name="count")
        )
    else:
        final_policy_action_table = pd.DataFrame(columns=["policy_final_action", "count"])

    final_policy_action_csv = tables_dir / "table_protocol_aware_final_policy_distribution.csv"
    final_policy_action_md = tables_dir / "table_protocol_aware_final_policy_distribution.md"
    save_table_as_csv_and_md(final_policy_action_table, final_policy_action_csv, final_policy_action_md)
    generated += [final_policy_action_csv, final_policy_action_md]

    save_bar_chart(
        final_policy_action_table.set_index("policy_final_action")["count"] if not final_policy_action_table.empty else pd.Series(dtype=float),
        "Protocol-Aware Final Policy Distribution",
        "Final policy action",
        "Count",
        figures_dir / "fig_protocol_aware_final_policy_distribution.png",
    )
    generated.append(figures_dir / "fig_protocol_aware_final_policy_distribution.png")

    # 5) Enforcement summary
    enforcement_rows = []

    if not mitigation_df.empty and "policy_final_action" in mitigation_df.columns:
        enforcement_rows.append({
            "enforcement_type": "drop_mitigation",
            "count": int((mitigation_df["policy_final_action"] == "drop").sum()),
        })
    else:
        enforcement_rows.append({"enforcement_type": "drop_mitigation", "count": 0})

    if not quarantine_df.empty and "policy_final_action" in quarantine_df.columns:
        enforcement_rows.append({
            "enforcement_type": "quarantine_candidate",
            "count": int((quarantine_df["policy_final_action"] == "quarantine_candidate").sum()),
        })
    else:
        enforcement_rows.append({"enforcement_type": "quarantine_candidate", "count": 0})

    if not rate_limit_df.empty and "policy_final_action" in rate_limit_df.columns:
        enforcement_rows.append({
            "enforcement_type": "rate_limit",
            "count": int((rate_limit_df["policy_final_action"] == "rate_limit").sum()),
        })
    else:
        enforcement_rows.append({"enforcement_type": "rate_limit", "count": 0})

    enforcement_table = pd.DataFrame(enforcement_rows)
    enforcement_csv = tables_dir / "table_enforcement_action_summary.csv"
    enforcement_md = tables_dir / "table_enforcement_action_summary.md"
    save_table_as_csv_and_md(enforcement_table, enforcement_csv, enforcement_md)
    generated += [enforcement_csv, enforcement_md]

    save_bar_chart(
        enforcement_table.set_index("enforcement_type")["count"],
        "SDN Controller Enforcement Action Summary",
        "Enforcement action",
        "Count",
        figures_dir / "fig_enforcement_action_summary.png",
    )
    generated.append(figures_dir / "fig_enforcement_action_summary.png")

    # 6) Flow-level comparison table, compact thesis version
    comparison_cols = [
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
    ]
    comparison_table = comparison_df[[c for c in comparison_cols if c in comparison_df.columns]].copy()
    comparison_table_csv = tables_dir / "table_flow_level_model_controller_comparison.csv"
    comparison_table_md = tables_dir / "table_flow_level_model_controller_comparison.md"
    save_table_as_csv_and_md(comparison_table, comparison_table_csv, comparison_table_md)
    generated += [comparison_table_csv, comparison_table_md]

    # 7) Attack probability table
    attack_prob_cols = [
        "src_ip",
        "dst_ip",
        "src_port",
        "dst_port",
        "ip_proto",
        "prediction",
        "attack_probability",
        "recommended_action",
        "policy_final_action",
    ]
    attack_prob_table = final_policy_df[[c for c in attack_prob_cols if c in final_policy_df.columns]].copy()
    attack_prob_csv = tables_dir / "table_protocol_aware_attack_probability_summary.csv"
    attack_prob_md = tables_dir / "table_protocol_aware_attack_probability_summary.md"
    save_table_as_csv_and_md(attack_prob_table, attack_prob_csv, attack_prob_md)
    generated += [attack_prob_csv, attack_prob_md]

    # 8) Manifest
    manifest = f"""# Thesis Artifacts Manifest

Generated at UTC: `{datetime.utcnow().isoformat()}`

## Input Directories

- Run directory: `{run_dir}`
- Final runtime pipeline directory: `{final_run_dir}`
- Comparison directory: `{compare_dir}`
- Canonical aggregate CSV: `{canonical_agg_csv}`

## Generated Tables

| Table | File | Suggested Caption |
|---|---|---|
| Canonical runtime validation summary | `tables/table_canonical_runtime_validation_summary.csv` | Canonical repeated runtime validation results |
| Controller action distribution | `tables/table_controller_action_distribution.csv` | Distribution of controller-side IDS/IPS policy actions |
| Final Top-20 prediction distribution | `tables/table_final_top20_prediction_distribution.csv` | Runtime prediction distribution of the Final XGBoost Top-20 model |
| Protocol-aware final policy distribution | `tables/table_protocol_aware_final_policy_distribution.csv` | Protocol-aware policy interpretation of runtime model outputs |
| Enforcement action summary | `tables/table_enforcement_action_summary.csv` | Summary of rate-limit, drop, and quarantine enforcement actions |
| Flow-level model-controller comparison | `tables/table_flow_level_model_controller_comparison.csv` | Port-aware and protocol-aware comparison of model and controller decisions |
| Attack probability summary | `tables/table_protocol_aware_attack_probability_summary.csv` | Flow-level attack probability and final policy action summary |

## Generated Figures

| Figure | File | Suggested Caption |
|---|---|---|
| Controller action distribution | `figures/fig_controller_action_distribution.png` | Controller-side policy action distribution in the port-aware canonical run |
| Final Top-20 prediction distribution | `figures/fig_final_top20_prediction_distribution.png` | Runtime BENIGN/ATTACK prediction distribution of the Final XGBoost Top-20 model |
| Protocol-aware final policy distribution | `figures/fig_protocol_aware_final_policy_distribution.png` | Protocol-aware final policy action distribution |
| Enforcement action summary | `figures/fig_enforcement_action_summary.png` | SDN controller enforcement actions observed during runtime validation |

## Recommended Use in Thesis

The main text should use the canonical aggregate table and the run_05 figures as the primary experimental evidence. The run_03 results may be used as supporting repeated validation. The diagnostic run_04 should be discussed only as an implementation limitation or intermediate debugging case.
"""
    manifest_path.write_text(manifest, encoding="utf-8")
    generated.append(manifest_path)

    summary = {
        "generated_at_utc": datetime.utcnow().isoformat(),
        "run_dir": str(run_dir),
        "final_run_dir": str(final_run_dir),
        "compare_dir": str(compare_dir),
        "canonical_agg_csv": str(canonical_agg_csv),
        "output_dir": str(output_dir),
        "generated_files": [str(p) for p in generated],
        "row_counts": {
            "policy_decisions": int(len(policy_df)),
            "final_runtime_predictions": int(len(pred_df)),
            "final_protocol_aware_policy": int(len(final_policy_df)),
            "mitigation_log": int(len(mitigation_df)),
            "quarantine_log": int(len(quarantine_df)),
            "rate_limit_log": int(len(rate_limit_df)),
            "comparison": int(len(comparison_df)),
            "canonical_aggregate": int(len(canonical_df)),
        },
    }
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    generated.append(summary_path)

    print("[INFO] Thesis artifacts generated.")
    print("[INFO] Output directory:", output_dir)
    print("[INFO] Manifest:", manifest_path)
    print("[INFO] Summary:", summary_path)
    print()
    for p in generated:
        print(p)


if __name__ == "__main__":
    main()
