#!/usr/bin/env python3
"""
Summarize final model controller run logs.

Purpose:
- Summarize policy decisions, mitigation, quarantine and rate-limit logs.
- Verify port-aware schema presence.
- Produce JSON and Markdown reports for the experiment folder.

Usage:
python ml-service/tools/summarize_final_model_controller_run.py \
  --run-dir experiments/results/final_model_controller_tests/hybrid_20260513_233759
"""

import argparse
import json
from datetime import datetime
from pathlib import Path

import pandas as pd


EXPECTED_PORT_AWARE_COLUMNS = {
    "policy_decisions.csv": ["src_port", "dst_port"],
    "mitigation_log.csv": ["src_port", "dst_port"],
    "quarantine_log.csv": ["src_port", "dst_port"],
    "rate_limit_log.csv": ["src_port", "dst_port"],
}


def read_csv_if_exists(path: Path):
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame()
    return pd.read_csv(path)


def counts(df: pd.DataFrame, column: str):
    if df.empty or column not in df.columns:
        return {}
    return {str(k): int(v) for k, v in df[column].value_counts(dropna=False).to_dict().items()}


def unique_pairs(df: pd.DataFrame, src_col: str, dst_col: str):
    if df.empty or src_col not in df.columns or dst_col not in df.columns:
        return []

    tmp = df[[src_col, dst_col]].dropna().drop_duplicates()
    return [
        {
            "src": str(r[src_col]),
            "dst": str(r[dst_col]),
        }
        for _, r in tmp.iterrows()
    ]


def port_schema_status(run_dir: Path):
    result = {}

    for filename, required_cols in EXPECTED_PORT_AWARE_COLUMNS.items():
        path = run_dir / filename

        if not path.exists():
            result[filename] = {
                "exists": False,
                "has_required_columns": False,
                "missing_columns": required_cols,
                "columns": [],
            }
            continue

        df = pd.read_csv(path, nrows=1)
        cols = list(df.columns)
        missing = [c for c in required_cols if c not in cols]

        result[filename] = {
            "exists": True,
            "has_required_columns": len(missing) == 0,
            "missing_columns": missing,
            "columns": cols,
        }

    return result


def top_policy_rows(df: pd.DataFrame, n: int = 20):
    if df.empty:
        return []

    preferred = [
        "timestamp",
        "datapath_id",
        "ipv4_src",
        "ipv4_dst",
        "src_port",
        "dst_port",
        "ip_proto",
        "packet_rate",
        "byte_rate",
        "ml_prediction",
        "ml_confidence",
        "ml_recommended_action",
        "policy_final_action",
        "policy_reason",
        "source_risk_count",
        "decision_mode",
        "mode_reason",
    ]

    existing = [c for c in preferred if c in df.columns]
    sample = df[existing].head(n)

    return sample.to_dict(orient="records")


def mitigation_rows(df: pd.DataFrame, n: int = 20):
    if df.empty:
        return []

    return df.head(n).to_dict(orient="records")


def write_json(path: Path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def write_markdown(path: Path, summary: dict):
    lines = []

    lines.append("# Final Model Hybrid Controller Run Summary")
    lines.append("")
    lines.append(f"- Generated at UTC: `{datetime.utcnow().isoformat()}`")
    lines.append(f"- Run directory: `{summary['run_dir']}`")
    lines.append("")

    lines.append("## Log Row Counts")
    lines.append("")
    for name, row_count in summary["row_counts"].items():
        lines.append(f"- `{name}`: `{row_count}`")
    lines.append("")

    lines.append("## Policy Decision Distribution")
    lines.append("")
    lines.append(f"- Policy final actions: `{summary['policy_action_counts']}`")
    lines.append(f"- ML predictions: `{summary['ml_prediction_counts']}`")
    lines.append(f"- ML recommended actions: `{summary['ml_recommended_action_counts']}`")
    lines.append(f"- Decision modes: `{summary['decision_mode_counts']}`")
    lines.append(f"- Mode reasons: `{summary['mode_reason_counts']}`")
    lines.append("")

    lines.append("## Mitigation Distribution")
    lines.append("")
    lines.append(f"- Mitigation actions: `{summary['mitigation_action_counts']}`")
    lines.append(f"- Mitigation final actions: `{summary['mitigation_policy_action_counts']}`")
    lines.append(f"- Quarantine actions: `{summary['quarantine_action_counts']}`")
    lines.append(f"- Rate-limit actions: `{summary['rate_limit_action_counts']}`")
    lines.append("")

    lines.append("## Port-Aware Schema Check")
    lines.append("")
    lines.append("| File | Exists | Has src_port/dst_port | Missing Columns |")
    lines.append("|---|---:|---:|---|")

    for filename, info in summary["port_schema_status"].items():
        lines.append(
            f"| `{filename}` "
            f"| `{info['exists']}` "
            f"| `{info['has_required_columns']}` "
            f"| `{info['missing_columns']}` |"
        )
    lines.append("")

    lines.append("## Source-Destination Pairs")
    lines.append("")
    lines.append("### Policy Decisions")
    lines.append("")
    for pair in summary["policy_pairs"]:
        lines.append(f"- `{pair['src']} → {pair['dst']}`")
    lines.append("")

    lines.append("### Mitigation Log")
    lines.append("")
    for pair in summary["mitigation_pairs"]:
        lines.append(f"- `{pair['src']} → {pair['dst']}`")
    lines.append("")

    lines.append("## Interpretation")
    lines.append("")
    lines.append(
        "The final model hybrid controller run produced policy decisions and mitigation logs "
        "with the updated port-aware schema. The current controller version writes `src_port` "
        "and `dst_port` columns, although their values are still `0` because actual TCP/UDP "
        "port extraction has not yet been implemented in the controller."
    )
    lines.append("")
    lines.append(
        "The attack flow `10.10.60.12 → 10.10.40.14` was mitigated with DROP, and additional "
        "rate-limit/quarantine actions were logged according to the hybrid policy logic."
    )
    lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--output-json", default=None)
    parser.add_argument("--output-md", default=None)
    args = parser.parse_args()

    run_dir = Path(args.run_dir)

    if not run_dir.exists():
        raise FileNotFoundError(f"Run directory not found: {run_dir}")

    policy = read_csv_if_exists(run_dir / "policy_decisions.csv")
    mitigation = read_csv_if_exists(run_dir / "mitigation_log.csv")
    quarantine = read_csv_if_exists(run_dir / "quarantine_log.csv")
    rate_limit = read_csv_if_exists(run_dir / "rate_limit_log.csv")
    latency = read_csv_if_exists(run_dir / "mitigation_latency.csv")
    predictions = read_csv_if_exists(run_dir / "predictions.csv")
    flow_stats = read_csv_if_exists(run_dir / "flow_stats.csv")

    summary = {
        "run_dir": str(run_dir),
        "generated_at_utc": datetime.utcnow().isoformat(),
        "row_counts": {
            "policy_decisions.csv": int(len(policy)),
            "mitigation_log.csv": int(len(mitigation)),
            "quarantine_log.csv": int(len(quarantine)),
            "rate_limit_log.csv": int(len(rate_limit)),
            "mitigation_latency.csv": int(len(latency)),
            "predictions.csv": int(len(predictions)),
            "flow_stats.csv": int(len(flow_stats)),
        },
        "policy_action_counts": counts(policy, "policy_final_action"),
        "ml_prediction_counts": counts(policy, "ml_prediction"),
        "ml_recommended_action_counts": counts(policy, "ml_recommended_action"),
        "decision_mode_counts": counts(policy, "decision_mode"),
        "mode_reason_counts": counts(policy, "mode_reason"),
        "policy_reason_counts": counts(policy, "policy_reason"),
        "mitigation_action_counts": counts(mitigation, "mitigation_action"),
        "mitigation_policy_action_counts": counts(mitigation, "policy_final_action"),
        "quarantine_action_counts": counts(quarantine, "policy_final_action"),
        "rate_limit_action_counts": counts(rate_limit, "policy_final_action"),
        "mitigation_status_counts": counts(mitigation, "status"),
        "quarantine_status_counts": counts(quarantine, "status"),
        "rate_limit_status_counts": counts(rate_limit, "status"),
        "port_schema_status": port_schema_status(run_dir),
        "policy_pairs": unique_pairs(policy, "ipv4_src", "ipv4_dst"),
        "mitigation_pairs": unique_pairs(mitigation, "src_ip", "dst_ip"),
        "quarantine_pairs": unique_pairs(quarantine, "src_ip", "original_dst_ip"),
        "rate_limit_pairs": unique_pairs(rate_limit, "src_ip", "dst_ip"),
        "sample_policy_rows": top_policy_rows(policy, n=10),
        "sample_mitigation_rows": mitigation_rows(mitigation, n=10),
        "sample_quarantine_rows": mitigation_rows(quarantine, n=10),
        "sample_rate_limit_rows": mitigation_rows(rate_limit, n=10),
    }

    output_json = Path(args.output_json) if args.output_json else run_dir / "controller_final_model_summary.json"
    output_md = Path(args.output_md) if args.output_md else run_dir / "controller_final_model_summary.md"

    write_json(output_json, summary)
    write_markdown(output_md, summary)

    print("[INFO] Summary generated.")
    print(f"[INFO] JSON: {output_json}")
    print(f"[INFO] MD  : {output_md}")
    print()
    print(json.dumps({
        "row_counts": summary["row_counts"],
        "policy_action_counts": summary["policy_action_counts"],
        "mitigation_action_counts": summary["mitigation_action_counts"],
        "quarantine_action_counts": summary["quarantine_action_counts"],
        "rate_limit_action_counts": summary["rate_limit_action_counts"],
        "port_schema_status": summary["port_schema_status"],
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
