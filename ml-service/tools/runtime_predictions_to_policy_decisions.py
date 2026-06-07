#!/usr/bin/env python3
"""
Convert final Top-20 runtime predictions to policy decision format.

Purpose:
- Transform FastAPI prediction CSV into a controller-like policy_decisions.csv.
- Standardize fields for later controller/mitigation comparison.
- Produce summary JSON and Markdown report.

Input:
- final_top20_runtime_predictions.csv

Output:
- final_top20_policy_decisions.csv
- final_top20_policy_decisions_summary.json
- final_top20_policy_decisions_report.md

Usage:
python ml-service/tools/runtime_predictions_to_policy_decisions.py \
  --predictions experiments/results/final_top20_runtime_pipeline/<RUN>/final_top20_runtime_predictions.csv
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


def normalize_action(action, prediction):
    action = str(action or "").strip().upper()
    prediction = str(prediction or "").strip().upper()

    if action in {"ALLOW", "DROP", "RATE_LIMIT", "QUARANTINE", "MONITOR"}:
        return action

    if prediction == "ATTACK":
        return "DROP"

    return "ALLOW"


def severity_from_probability(prob):
    try:
        p = float(prob)
    except Exception:
        return "unknown"

    if p >= 0.95:
        return "critical"
    if p >= 0.80:
        return "high"
    if p >= 0.60:
        return "medium"
    if p >= 0.40:
        return "low"
    return "benign_like"


def build_policy_decisions(df: pd.DataFrame, model_name: str, decision_source: str):
    rows = []

    now = datetime.utcnow().isoformat()

    for _, r in df.iterrows():
        prediction = str(r.get("prediction", "")).upper()
        recommended_action = normalize_action(r.get("recommended_action", ""), prediction)
        attack_probability = float(r.get("attack_probability", 0.0))

        row = {
            "timestamp": now,
            "row_index": int(r.get("row_index", -1)),
            "src_ip": r.get("source_ip", ""),
            "dst_ip": r.get("destination_ip", ""),
            "src_port": int(r.get("source_port", 0)) if pd.notna(r.get("source_port", 0)) else 0,
            "dst_port": int(r.get("destination_port", 0)) if pd.notna(r.get("destination_port", 0)) else 0,
            "ip_proto": r.get("protocol", ""),
            "prediction": prediction,
            "prediction_value": int(r.get("prediction_value", 0)),
            "attack_probability": attack_probability,
            "recommended_action": recommended_action,
            "policy_final_action": recommended_action,
            "severity": severity_from_probability(attack_probability),
            "decision_source": decision_source,
            "model_name": model_name,
            "feature_count": int(r.get("feature_count", 0)),
            "missing_features": r.get("missing_features", "[]"),
            "extra_features": r.get("extra_features", "[]"),
            "inference_latency_ms": float(r.get("inference_latency_ms", 0.0)),
            "status_code": int(r.get("status_code", 0)),
            "note": r.get("note", ""),
        }

        rows.append(row)

    return pd.DataFrame(rows)


def summarize(policy_df: pd.DataFrame):
    summary = {
        "rows": int(len(policy_df)),
        "prediction_counts": {},
        "policy_action_counts": {},
        "severity_counts": {},
        "mean_attack_probability": None,
        "max_attack_probability": None,
        "min_attack_probability": None,
        "mean_inference_latency_ms": None,
        "drop_candidates": 0,
        "allow_candidates": 0,
        "rate_limit_candidates": 0,
        "quarantine_candidates": 0,
    }

    if len(policy_df) == 0:
        return summary

    summary["prediction_counts"] = {
        str(k): int(v)
        for k, v in policy_df["prediction"].value_counts(dropna=False).to_dict().items()
    }

    summary["policy_action_counts"] = {
        str(k): int(v)
        for k, v in policy_df["policy_final_action"].value_counts(dropna=False).to_dict().items()
    }

    summary["severity_counts"] = {
        str(k): int(v)
        for k, v in policy_df["severity"].value_counts(dropna=False).to_dict().items()
    }

    summary["mean_attack_probability"] = float(policy_df["attack_probability"].mean())
    summary["max_attack_probability"] = float(policy_df["attack_probability"].max())
    summary["min_attack_probability"] = float(policy_df["attack_probability"].min())

    summary["mean_inference_latency_ms"] = float(policy_df["inference_latency_ms"].mean())

    summary["drop_candidates"] = int((policy_df["policy_final_action"] == "DROP").sum())
    summary["allow_candidates"] = int((policy_df["policy_final_action"] == "ALLOW").sum())
    summary["rate_limit_candidates"] = int((policy_df["policy_final_action"] == "RATE_LIMIT").sum())
    summary["quarantine_candidates"] = int((policy_df["policy_final_action"] == "QUARANTINE").sum())

    return summary


def write_markdown_report(path: Path, prediction_csv: Path, policy_csv: Path, summary: dict, policy_df: pd.DataFrame):
    lines = []

    lines.append("# Final Top-20 Runtime Policy Decision Report")
    lines.append("")
    lines.append(f"- Generated at UTC: `{datetime.utcnow().isoformat()}`")
    lines.append(f"- Prediction CSV: `{prediction_csv}`")
    lines.append(f"- Policy decision CSV: `{policy_csv}`")
    lines.append("")

    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Rows: `{summary['rows']}`")
    lines.append(f"- Prediction counts: `{summary['prediction_counts']}`")
    lines.append(f"- Policy action counts: `{summary['policy_action_counts']}`")
    lines.append(f"- Severity counts: `{summary['severity_counts']}`")
    lines.append(f"- Mean attack probability: `{summary['mean_attack_probability']}`")
    lines.append(f"- Mean inference latency ms: `{summary['mean_inference_latency_ms']}`")
    lines.append("")

    lines.append("## Flow-Level Decisions")
    lines.append("")
    lines.append("| Row | Source | Destination | Src Port | Dst Port | Prediction | Probability | Action | Severity |")
    lines.append("|---:|---|---|---:|---:|---|---:|---|---|")

    for _, r in policy_df.iterrows():
        lines.append(
            f"| {r['row_index']} "
            f"| {r['src_ip']} "
            f"| {r['dst_ip']} "
            f"| {r['src_port']} "
            f"| {r['dst_port']} "
            f"| {r['prediction']} "
            f"| {r['attack_probability']} "
            f"| {r['policy_final_action']} "
            f"| {r['severity']} |"
        )

    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append(
        "The runtime ML prediction output was converted into a controller-like policy "
        "decision format. This enables later comparison with Ryu controller policy logs "
        "and mitigation logs."
    )
    lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", required=True)
    parser.add_argument("--output", default=None)
    parser.add_argument("--model-name", default="final_xgboost_top20")
    parser.add_argument("--decision-source", default="runtime_final_top20_ml_pipeline")
    args = parser.parse_args()

    pred_path = Path(args.predictions)
    if not pred_path.exists():
        raise FileNotFoundError(f"Prediction CSV not found: {pred_path}")

    if args.output:
        policy_csv = Path(args.output)
    else:
        policy_csv = pred_path.with_name("final_top20_policy_decisions.csv")

    summary_json = policy_csv.with_name("final_top20_policy_decisions_summary.json")
    report_md = policy_csv.with_name("final_top20_policy_decisions_report.md")

    df = pd.read_csv(pred_path)
    policy_df = build_policy_decisions(
        df,
        model_name=args.model_name,
        decision_source=args.decision_source,
    )

    policy_csv.parent.mkdir(parents=True, exist_ok=True)
    policy_df.to_csv(policy_csv, index=False)

    summary = summarize(policy_df)
    write_json(summary_json, summary)
    write_markdown_report(report_md, pred_path, policy_csv, summary, policy_df)

    print("[INFO] Runtime predictions converted to policy decisions.")
    print(f"[INFO] Input predictions : {pred_path}")
    print(f"[INFO] Policy CSV        : {policy_csv}")
    print(f"[INFO] Summary JSON      : {summary_json}")
    print(f"[INFO] Report MD         : {report_md}")
    print()
    print(policy_df.to_string(index=False))


if __name__ == "__main__":
    main()
