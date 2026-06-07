#!/usr/bin/env python3
"""
Aşama 14.7-E — Runtime Metrics Summary and Figures

Bu script SDN IDS/IPS runtime loglarından özet CSV/JSON ve PNG grafikler üretir.

Girdi logları:
- logs/policy_decisions.csv
- logs/mitigation_latency.csv
- logs/mitigation_log.csv
- logs/quarantine_log.csv
- logs/flow_rule_timing.csv
- logs/controller_resource_usage_observe_only.csv

Çıktılar:
- reports/runtime/*.csv
- reports/runtime/runtime_summary.json
- reports/runtime/figures/*.png
"""

import json
from pathlib import Path

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


PROJECT_ROOT = Path(__file__).resolve().parents[1]

LOG_DIR = PROJECT_ROOT / "logs"
REPORT_DIR = PROJECT_ROOT / "reports" / "runtime"
FIGURE_DIR = REPORT_DIR / "figures"
TABLE_DIR = REPORT_DIR / "tables"

POLICY_LOG = LOG_DIR / "policy_decisions.csv"
MITIGATION_LATENCY_LOG = LOG_DIR / "mitigation_latency.csv"
MITIGATION_LOG = LOG_DIR / "mitigation_log.csv"
QUARANTINE_LOG = LOG_DIR / "quarantine_log.csv"
FLOW_RULE_TIMING_LOG = LOG_DIR / "flow_rule_timing.csv"
RESOURCE_LOG = LOG_DIR / "controller_resource_usage_observe_only.csv"


def ensure_dirs():
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)


def read_csv_if_exists(path: Path) -> pd.DataFrame:
    if not path.exists():
        print(f"[WARN] Missing file: {path}")
        return pd.DataFrame()

    try:
        df = pd.read_csv(path)
        print(f"[INFO] Loaded {path}: shape={df.shape}")
        return df
    except pd.errors.EmptyDataError:
        print(f"[WARN] Empty CSV: {path}")
        return pd.DataFrame()


def save_bar(series, output_path: Path, title: str, xlabel: str, ylabel: str):
    if series.empty:
        print(f"[WARN] Empty series, skipped figure: {output_path}")
        return

    plt.figure(figsize=(8, 5))
    series.plot(kind="bar")
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.xticks(rotation=25, ha="right")
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()

    print(f"[INFO] Figure written: {output_path}")


def save_line(df: pd.DataFrame, y_col: str, output_path: Path, title: str, ylabel: str):
    if df.empty or y_col not in df.columns:
        print(f"[WARN] Missing {y_col}, skipped figure: {output_path}")
        return

    plot_df = df.copy()

    if "timestamp" in plot_df.columns:
        plot_df["timestamp"] = pd.to_datetime(plot_df["timestamp"], errors="coerce")
        plot_df = plot_df.dropna(subset=["timestamp"])
        plot_df = plot_df.sort_values("timestamp")
        x = plot_df["timestamp"]
    else:
        x = range(len(plot_df))

    plt.figure(figsize=(10, 5))
    plt.plot(x, plot_df[y_col])
    plt.title(title)
    plt.xlabel("Time")
    plt.ylabel(ylabel)
    plt.xticks(rotation=25, ha="right")
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()

    print(f"[INFO] Figure written: {output_path}")


def summarize_policy(policy_df: pd.DataFrame) -> dict:
    if policy_df.empty:
        return {}

    summary = {
        "rows": int(len(policy_df)),
    }

    if "policy_final_action" in policy_df.columns:
        action_counts = (
            policy_df["policy_final_action"]
            .value_counts(dropna=False)
            .rename_axis("policy_final_action")
            .reset_index(name="count")
        )
        action_counts.to_csv(REPORT_DIR / "runtime_policy_action_distribution.csv", index=False)

        save_bar(
            policy_df["policy_final_action"].value_counts(dropna=False),
            FIGURE_DIR / "policy_action_distribution.png",
            "Policy Final Action Distribution",
            "Policy Action",
            "Count",
        )

        summary["policy_final_action_counts"] = {
            str(k): int(v)
            for k, v in policy_df["policy_final_action"].value_counts(dropna=False).to_dict().items()
        }

    if "ml_prediction" in policy_df.columns:
        summary["ml_prediction_counts"] = {
            str(k): int(v)
            for k, v in policy_df["ml_prediction"].value_counts(dropna=False).to_dict().items()
        }

    if "ip_proto" in policy_df.columns:
        summary["ip_proto_counts"] = {
            str(k): int(v)
            for k, v in policy_df["ip_proto"].value_counts(dropna=False).to_dict().items()
        }

    required_bad_cols = {"ml_prediction", "policy_final_action"}
    if required_bad_cols.issubset(policy_df.columns):
        bad = policy_df[
            (policy_df["ml_prediction"].astype(str).str.lower() == "benign")
            & (policy_df["policy_final_action"].isin(["drop", "rate_limit", "quarantine_candidate"]))
        ]

        bad.to_csv(REPORT_DIR / "runtime_benign_but_mitigated_rows.csv", index=False)
        summary["benign_but_mitigated_rows"] = int(len(bad))

    if {"packet_rate", "byte_rate"}.issubset(policy_df.columns):
        summary["packet_rate"] = {
            "mean": float(policy_df["packet_rate"].mean()),
            "max": float(policy_df["packet_rate"].max()),
            "min": float(policy_df["packet_rate"].min()),
        }
        summary["byte_rate"] = {
            "mean": float(policy_df["byte_rate"].mean()),
            "max": float(policy_df["byte_rate"].max()),
            "min": float(policy_df["byte_rate"].min()),
        }

    return summary


def summarize_mitigation_latency(df: pd.DataFrame) -> dict:
    if df.empty:
        return {}

    if "latency_ms" not in df.columns:
        return {"rows": int(len(df)), "error": "latency_ms column not found"}

    summary = {
        "rows": int(len(df)),
        "latency_ms": {
            "mean": float(df["latency_ms"].mean()),
            "min": float(df["latency_ms"].min()),
            "max": float(df["latency_ms"].max()),
            "std": float(df["latency_ms"].std()) if len(df) > 1 else 0.0,
        },
    }

    if "mitigation_action" in df.columns:
        grouped = (
            df.groupby("mitigation_action")["latency_ms"]
            .agg(["count", "mean", "min", "max", "std"])
            .reset_index()
        )
        grouped.to_csv(REPORT_DIR / "runtime_mitigation_latency_summary.csv", index=False)

        save_bar(
            df.groupby("mitigation_action")["latency_ms"].mean(),
            FIGURE_DIR / "mitigation_latency_by_action.png",
            "Mitigation Latency by Action",
            "Mitigation Action",
            "Mean Latency (ms)",
        )

        summary["by_mitigation_action"] = {
            row["mitigation_action"]: {
                "count": int(row["count"]),
                "mean": float(row["mean"]),
                "min": float(row["min"]),
                "max": float(row["max"]),
                "std": float(row["std"]) if pd.notna(row["std"]) else 0.0,
            }
            for _, row in grouped.iterrows()
        }

    return summary


def summarize_mitigation_logs(mitigation_df: pd.DataFrame, quarantine_df: pd.DataFrame) -> dict:
    summary = {}

    if not mitigation_df.empty:
        summary["mitigation_log_rows"] = int(len(mitigation_df))

        if "mitigation_action" in mitigation_df.columns:
            summary["mitigation_action_counts"] = {
                str(k): int(v)
                for k, v in mitigation_df["mitigation_action"].value_counts(dropna=False).to_dict().items()
            }

    if not quarantine_df.empty:
        summary["quarantine_log_rows"] = int(len(quarantine_df))

        if "mitigation_action" in quarantine_df.columns:
            summary["quarantine_action_counts"] = {
                str(k): int(v)
                for k, v in quarantine_df["mitigation_action"].value_counts(dropna=False).to_dict().items()
            }

    return summary


def summarize_flow_rule_timing(df: pd.DataFrame) -> dict:
    if df.empty:
        return {}

    if "duration_ms" not in df.columns:
        return {"rows": int(len(df)), "error": "duration_ms column not found"}

    summary = {
        "rows": int(len(df)),
        "duration_ms": {
            "mean": float(df["duration_ms"].mean()),
            "min": float(df["duration_ms"].min()),
            "max": float(df["duration_ms"].max()),
            "std": float(df["duration_ms"].std()) if len(df) > 1 else 0.0,
        },
    }

    if "rule_type" in df.columns:
        grouped = (
            df.groupby("rule_type")["duration_ms"]
            .agg(["count", "mean", "min", "max", "std"])
            .reset_index()
        )
        grouped.to_csv(REPORT_DIR / "runtime_flow_rule_timing_summary.csv", index=False)

        save_bar(
            df.groupby("rule_type")["duration_ms"].mean(),
            FIGURE_DIR / "flow_rule_timing_by_type.png",
            "Flow Rule Timing by Rule Type",
            "Rule Type",
            "Mean Duration (ms)",
        )

        summary["by_rule_type"] = {
            row["rule_type"]: {
                "count": int(row["count"]),
                "mean": float(row["mean"]),
                "min": float(row["min"]),
                "max": float(row["max"]),
                "std": float(row["std"]) if pd.notna(row["std"]) else 0.0,
            }
            for _, row in grouped.iterrows()
        }

    return summary


def summarize_resource_usage(df: pd.DataFrame) -> dict:
    if df.empty:
        return {}

    summary = {
        "rows": int(len(df)),
    }

    numeric_cols = [
        "cpu_percent",
        "memory_rss_mb",
        "memory_vms_mb",
        "num_threads",
    ]

    for col in numeric_cols:
        if col in df.columns:
            summary[col] = {
                "mean": float(df[col].mean()),
                "min": float(df[col].min()),
                "max": float(df[col].max()),
                "std": float(df[col].std()) if len(df) > 1 else 0.0,
            }

    if "cpu_percent" in df.columns:
        save_line(
            df,
            "cpu_percent",
            FIGURE_DIR / "controller_cpu_usage.png",
            "Controller CPU Usage Over Time",
            "CPU Percent",
        )

    if "memory_rss_mb" in df.columns:
        save_line(
            df,
            "memory_rss_mb",
            FIGURE_DIR / "controller_memory_usage.png",
            "Controller RSS Memory Usage Over Time",
            "Memory RSS (MB)",
        )

    resource_summary_df = pd.DataFrame([
        {
            "metric": metric,
            "mean": values.get("mean"),
            "min": values.get("min"),
            "max": values.get("max"),
            "std": values.get("std"),
        }
        for metric, values in summary.items()
        if isinstance(values, dict)
    ])

    if not resource_summary_df.empty:
        resource_summary_df.to_csv(REPORT_DIR / "runtime_controller_resource_summary.csv", index=False)

    return summary


def main():
    ensure_dirs()

    policy_df = read_csv_if_exists(POLICY_LOG)
    mitigation_latency_df = read_csv_if_exists(MITIGATION_LATENCY_LOG)
    mitigation_df = read_csv_if_exists(MITIGATION_LOG)
    quarantine_df = read_csv_if_exists(QUARANTINE_LOG)
    flow_rule_df = read_csv_if_exists(FLOW_RULE_TIMING_LOG)
    resource_df = read_csv_if_exists(RESOURCE_LOG)

    runtime_summary = {
        "policy": summarize_policy(policy_df),
        "mitigation_latency": summarize_mitigation_latency(mitigation_latency_df),
        "mitigation_logs": summarize_mitigation_logs(mitigation_df, quarantine_df),
        "flow_rule_timing": summarize_flow_rule_timing(flow_rule_df),
        "controller_resource_usage": summarize_resource_usage(resource_df),
    }

    summary_path = REPORT_DIR / "runtime_summary.json"
    with summary_path.open("w", encoding="utf-8") as f:
        json.dump(runtime_summary, f, indent=2, ensure_ascii=False)

    print(f"[INFO] Runtime summary written: {summary_path}")
    print(json.dumps(runtime_summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
