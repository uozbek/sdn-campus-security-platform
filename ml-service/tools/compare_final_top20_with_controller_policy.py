#!/usr/bin/env python3
"""
Compare final Top-20 runtime ML policy decisions with controller policy/mitigation logs.

Purpose:
- Compare external final ML pipeline decisions with Ryu controller logs.
- Summarize action distributions.
- Match decisions by src/dst/port when possible.
- Produce CSV, JSON and Markdown report.

Usage:
python ml-service/tools/compare_final_top20_with_controller_policy.py \
  --final-policy experiments/results/final_top20_runtime_pipeline/<RUN>/final_top20_policy_decisions.csv \
  --controller-policy logs/policy_decisions.csv \
  --mitigation-log logs/mitigation_log.csv
"""

import argparse
import json
from datetime import datetime
from pathlib import Path

import pandas as pd


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def normalize_ip(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


def normalize_port(value):
    if pd.isna(value) or value == "":
        return 0
    try:
        return int(float(value))
    except Exception:
        return 0


def normalize_action(value):
    if pd.isna(value):
        return ""
    return str(value).strip().upper()


def load_csv_if_exists(path: Path, required=False):
    if not path:
        return pd.DataFrame()

    if not path.exists():
        if required:
            raise FileNotFoundError(f"Required CSV not found: {path}")
        print(f"[WARN] CSV not found, skipping: {path}")
        return pd.DataFrame()

    if path.stat().st_size == 0:
        print(f"[WARN] Empty CSV, skipping: {path}")
        return pd.DataFrame()

    return pd.read_csv(path)


def standardize_final_policy(df: pd.DataFrame):
    out = pd.DataFrame()

    out["src_ip"] = df.get("src_ip", "").apply(normalize_ip)
    out["dst_ip"] = df.get("dst_ip", "").apply(normalize_ip)
    out["src_port"] = df.get("src_port", 0).apply(normalize_port)
    out["dst_port"] = df.get("dst_port", 0).apply(normalize_port)

    out["prediction"] = df.get("prediction", "").astype(str).str.upper()
    out["attack_probability"] = pd.to_numeric(df.get("attack_probability", 0.0), errors="coerce").fillna(0.0)
    out["policy_final_action"] = df.get("policy_final_action", "").apply(normalize_action)
    out["recommended_action"] = df.get("recommended_action", "").apply(normalize_action)
    out["model_name"] = df.get("model_name", "final_xgboost_top20")
    out["decision_source"] = df.get("decision_source", "final_top20_runtime_pipeline")
    out["source"] = "final_top20_runtime_pipeline"

    out["flow_key"] = (
        out["src_ip"] + "|" +
        out["dst_ip"] + "|" +
        out["src_port"].astype(str) + "|" +
        out["dst_port"].astype(str)
    )

    return out


def find_col(df: pd.DataFrame, candidates):
    lower_map = {c.lower(): c for c in df.columns}
    for c in candidates:
        if c in df.columns:
            return c
        if c.lower() in lower_map:
            return lower_map[c.lower()]
    return None


def standardize_controller_policy(df: pd.DataFrame):
    if df.empty:
        return pd.DataFrame()

    src_col = find_col(df, ["src_ip", "source_ip", "ip_src", "nw_src"])
    dst_col = find_col(df, ["dst_ip", "destination_ip", "ip_dst", "nw_dst"])
    sport_col = find_col(df, ["src_port", "source_port", "tp_src"])
    dport_col = find_col(df, ["dst_port", "destination_port", "tp_dst"])
    action_col = find_col(df, ["policy_final_action", "final_action", "recommended_action", "action"])
    prob_col = find_col(df, ["attack_probability", "probability", "confidence", "ml_confidence"])
    pred_col = find_col(df, ["prediction", "ml_prediction", "label"])

    out = pd.DataFrame()

    out["src_ip"] = df[src_col].apply(normalize_ip) if src_col else ""
    out["dst_ip"] = df[dst_col].apply(normalize_ip) if dst_col else ""
    out["src_port"] = df[sport_col].apply(normalize_port) if sport_col else 0
    out["dst_port"] = df[dport_col].apply(normalize_port) if dport_col else 0

    out["prediction"] = df[pred_col].astype(str).str.upper() if pred_col else ""
    out["attack_probability"] = (
        pd.to_numeric(df[prob_col], errors="coerce").fillna(0.0) if prob_col else 0.0
    )
    out["policy_final_action"] = df[action_col].apply(normalize_action) if action_col else ""
    out["source"] = "controller_policy"

    out["flow_key"] = (
        out["src_ip"] + "|" +
        out["dst_ip"] + "|" +
        out["src_port"].astype(str) + "|" +
        out["dst_port"].astype(str)
    )

    return out


def standardize_mitigation_log(df: pd.DataFrame):
    if df.empty:
        return pd.DataFrame()

    src_col = find_col(df, ["src_ip", "source_ip", "ip_src", "nw_src"])
    dst_col = find_col(df, ["dst_ip", "destination_ip", "ip_dst", "nw_dst"])
    action_col = find_col(df, ["policy_final_action", "mitigation_action", "action", "installed_action"])

    out = pd.DataFrame()
    out["src_ip"] = df[src_col].apply(normalize_ip) if src_col else ""
    out["dst_ip"] = df[dst_col].apply(normalize_ip) if dst_col else ""
    out["policy_final_action"] = df[action_col].apply(normalize_action) if action_col else ""
    out["source"] = "controller_mitigation_log"

    out["flow_pair"] = out["src_ip"] + "|" + out["dst_ip"]

    return out


def value_counts_dict(series):
    if series is None or len(series) == 0:
        return {}
    return {str(k): int(v) for k, v in series.value_counts(dropna=False).to_dict().items()}


def build_comparison(final_df, controller_df):
    if controller_df.empty:
        return pd.DataFrame()

    merged = final_df.merge(
        controller_df,
        on="flow_key",
        how="left",
        suffixes=("_final", "_controller"),
    )

    merged["matched_controller_policy"] = merged["source_controller"].notna()
    merged["action_match"] = (
        merged["policy_final_action_final"] == merged["policy_final_action_controller"]
    )

    return merged


def write_markdown(path, summary, comparison_df):
    lines = []

    lines.append("# Final Top-20 vs Controller Policy Comparison")
    lines.append("")
    lines.append(f"- Generated at UTC: `{datetime.utcnow().isoformat()}`")
    lines.append("")

    lines.append("## Input Files")
    lines.append("")
    for k, v in summary["inputs"].items():
        lines.append(f"- {k}: `{v}`")
    lines.append("")

    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Final policy rows: `{summary['final_policy_rows']}`")
    lines.append(f"- Controller policy rows: `{summary['controller_policy_rows']}`")
    lines.append(f"- Mitigation log rows: `{summary['mitigation_log_rows']}`")
    lines.append(f"- Final action counts: `{summary['final_action_counts']}`")
    lines.append(f"- Controller action counts: `{summary['controller_action_counts']}`")
    lines.append(f"- Mitigation action counts: `{summary['mitigation_action_counts']}`")
    lines.append("")

    if not comparison_df.empty:
        lines.append("## Flow-Level Comparison")
        lines.append("")
        lines.append("| Flow Key | Final Action | Controller Action | Match | Final Probability |")
        lines.append("|---|---|---|---:|---:|")

        for _, r in comparison_df.iterrows():
            lines.append(
                f"| {r.get('flow_key', '')} "
                f"| {r.get('policy_final_action_final', '')} "
                f"| {r.get('policy_final_action_controller', '')} "
                f"| {r.get('action_match', False)} "
                f"| {r.get('attack_probability_final', '')} |"
            )
        lines.append("")
    else:
        lines.append("## Flow-Level Comparison")
        lines.append("")
        lines.append("No controller policy rows were available for exact flow-key comparison.")
        lines.append("")

    lines.append("## Interpretation")
    lines.append("")
    lines.append(
        "This report compares the external final Top-20 runtime ML pipeline decisions "
        "with controller-side policy and mitigation logs. Exact matching is based on "
        "src_ip, dst_ip, src_port and dst_port when those fields are available."
    )
    lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--final-policy", required=True)
    parser.add_argument("--controller-policy", default="logs/policy_decisions.csv")
    parser.add_argument("--mitigation-log", default="logs/mitigation_log.csv")
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args()

    final_policy_path = Path(args.final_policy)
    controller_policy_path = Path(args.controller_policy)
    mitigation_log_path = Path(args.mitigation_log)

    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = final_policy_path.parent

    output_dir.mkdir(parents=True, exist_ok=True)

    final_raw = load_csv_if_exists(final_policy_path, required=True)
    controller_raw = load_csv_if_exists(controller_policy_path, required=False)
    mitigation_raw = load_csv_if_exists(mitigation_log_path, required=False)

    final_df = standardize_final_policy(final_raw)
    controller_df = standardize_controller_policy(controller_raw)
    mitigation_df = standardize_mitigation_log(mitigation_raw)

    comparison_df = build_comparison(final_df, controller_df)

    comparison_csv = output_dir / "final_top20_vs_controller_policy_comparison.csv"
    summary_json = output_dir / "final_top20_vs_controller_policy_summary.json"
    report_md = output_dir / "final_top20_vs_controller_policy_report.md"

    comparison_df.to_csv(comparison_csv, index=False)

    summary = {
        "inputs": {
            "final_policy": str(final_policy_path),
            "controller_policy": str(controller_policy_path),
            "mitigation_log": str(mitigation_log_path),
        },
        "final_policy_rows": int(len(final_df)),
        "controller_policy_rows": int(len(controller_df)),
        "mitigation_log_rows": int(len(mitigation_df)),
        "final_action_counts": value_counts_dict(final_df.get("policy_final_action")),
        "controller_action_counts": value_counts_dict(controller_df.get("policy_final_action")) if not controller_df.empty else {},
        "mitigation_action_counts": value_counts_dict(mitigation_df.get("policy_final_action")) if not mitigation_df.empty else {},
        "exact_flow_matches": int(comparison_df["matched_controller_policy"].sum()) if not comparison_df.empty else 0,
        "exact_action_matches": int(comparison_df["action_match"].sum()) if not comparison_df.empty else 0,
    }

    write_json(summary_json, summary)
    write_markdown(report_md, summary, comparison_df)

    print("[INFO] Comparison completed.")
    print(f"[INFO] Comparison CSV: {comparison_csv}")
    print(f"[INFO] Summary JSON   : {summary_json}")
    print(f"[INFO] Report MD      : {report_md}")
    print()
    print(json.dumps(summary, indent=2, ensure_ascii=False))

    if not comparison_df.empty:
        print()
        print(comparison_df.to_string(index=False))


if __name__ == "__main__":
    main()
