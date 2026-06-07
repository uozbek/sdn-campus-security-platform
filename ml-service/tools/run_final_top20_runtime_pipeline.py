#!/usr/bin/env python3
"""
Run final Top-20 runtime ML pipeline.

Pipeline:
1. Extract final Top-20 CICFlowMeter-style features from PCAP.
2. Validate schema against active model feature_order.json.
3. Send extracted flows to active FastAPI /predict-cicddos endpoint.
4. Save predictions.
5. Write summary JSON and Markdown report.

Usage:
python ml-service/tools/run_final_top20_runtime_pipeline.py \
  --pcap experiments/pcaps/h12_to_h14_udp_s6eth2.pcap \
  --run-name h12_to_h14_udp_final_top20 \
  --inbound-subnet 10.10.60.0/24
"""

import argparse
import json
import subprocess
from datetime import datetime
from pathlib import Path

import pandas as pd


def run_cmd(cmd, cwd: Path):
    print()
    print("[CMD]", " ".join(str(x) for x in cmd))

    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    print(proc.stdout)

    if proc.returncode != 0:
        raise RuntimeError(
            f"Command failed with return code {proc.returncode}: {' '.join(str(x) for x in cmd)}"
        )

    return proc.stdout


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def write_markdown(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def summarize_predictions(pred_csv: Path):
    df = pd.read_csv(pred_csv)

    summary = {
        "rows": int(len(df)),
        "prediction_counts": {},
        "recommended_action_counts": {},
        "mean_attack_probability": None,
        "max_attack_probability": None,
        "min_attack_probability": None,
        "mean_inference_latency_ms": None,
        "flows": [],
    }

    if len(df) == 0:
        return summary

    if "prediction" in df.columns:
        summary["prediction_counts"] = {
            str(k): int(v) for k, v in df["prediction"].value_counts(dropna=False).to_dict().items()
        }

    if "recommended_action" in df.columns:
        summary["recommended_action_counts"] = {
            str(k): int(v) for k, v in df["recommended_action"].value_counts(dropna=False).to_dict().items()
        }

    if "attack_probability" in df.columns:
        summary["mean_attack_probability"] = float(df["attack_probability"].mean())
        summary["max_attack_probability"] = float(df["attack_probability"].max())
        summary["min_attack_probability"] = float(df["attack_probability"].min())

    if "inference_latency_ms" in df.columns:
        summary["mean_inference_latency_ms"] = float(df["inference_latency_ms"].mean())

    flow_cols = [
        "row_index",
        "source_ip",
        "destination_ip",
        "source_port",
        "destination_port",
        "protocol",
        "prediction",
        "prediction_value",
        "attack_probability",
        "recommended_action",
        "feature_count",
        "missing_features",
        "extra_features",
        "inference_latency_ms",
    ]

    existing = [c for c in flow_cols if c in df.columns]

    for _, r in df[existing].iterrows():
        item = {}
        for c in existing:
            val = r[c]
            if pd.isna(val):
                item[c] = None
            elif hasattr(val, "item"):
                item[c] = val.item()
            else:
                item[c] = val
        summary["flows"].append(item)

    return summary


def markdown_report(
    run_name,
    pcap_path,
    feature_csv,
    schema_report,
    prediction_csv,
    summary,
    active_model_info,
):
    lines = []

    lines.append(f"# Final Top-20 Runtime ML Pipeline Report — {run_name}")
    lines.append("")
    lines.append(f"- Generated at UTC: `{datetime.utcnow().isoformat()}`")
    lines.append(f"- PCAP: `{pcap_path}`")
    lines.append(f"- Feature CSV: `{feature_csv}`")
    lines.append(f"- Schema report: `{schema_report}`")
    lines.append(f"- Prediction CSV: `{prediction_csv}`")
    lines.append("")

    lines.append("## Active Model")
    lines.append("")
    lines.append(f"- Model status: `{active_model_info.get('model_status')}`")
    lines.append(f"- Model name: `{active_model_info.get('model_metadata', {}).get('model_name', active_model_info.get('model_name', 'unknown'))}`")
    lines.append(f"- Active model directory: `{active_model_info.get('active_model_dir', '')}`")
    lines.append(f"- Feature count: `{len(active_model_info.get('feature_order', []))}`")
    lines.append("")

    lines.append("## Prediction Summary")
    lines.append("")
    lines.append(f"- Flow rows: `{summary['rows']}`")
    lines.append(f"- Prediction counts: `{summary['prediction_counts']}`")
    lines.append(f"- Recommended action counts: `{summary['recommended_action_counts']}`")
    lines.append(f"- Mean attack probability: `{summary['mean_attack_probability']}`")
    lines.append(f"- Mean inference latency ms: `{summary['mean_inference_latency_ms']}`")
    lines.append("")

    lines.append("## Flow-Level Results")
    lines.append("")
    lines.append("| Row | Source | Destination | Src Port | Dst Port | Prediction | Probability | Action | Missing | Extra |")
    lines.append("|---:|---|---|---:|---:|---|---:|---|---|---|")

    for f in summary["flows"]:
        lines.append(
            f"| {f.get('row_index')} "
            f"| {f.get('source_ip')} "
            f"| {f.get('destination_ip')} "
            f"| {f.get('source_port')} "
            f"| {f.get('destination_port')} "
            f"| {f.get('prediction')} "
            f"| {f.get('attack_probability')} "
            f"| {f.get('recommended_action')} "
            f"| {f.get('missing_features')} "
            f"| {f.get('extra_features')} |"
        )

    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append(
        "The runtime pipeline extracted the final Top-20 selected features from the PCAP, "
        "validated the schema against the active model, and submitted the resulting flows "
        "to the active FastAPI prediction endpoint."
    )
    lines.append("")
    lines.append(
        "This confirms that the selected-feature XGBoost model can be used in the runtime "
        "traffic analysis pipeline, provided that the PCAP/collector stage is available."
    )
    lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pcap", required=True)
    parser.add_argument("--run-name", default=None)
    parser.add_argument("--inbound-subnet", default="10.10.60.0/24")
    parser.add_argument("--feature-order", default="ml-service/models/active/feature_order.json")
    parser.add_argument("--api-base", default="http://127.0.0.1:8000")
    parser.add_argument("--output-root", default="experiments/results/final_top20_runtime_pipeline")
    parser.add_argument("--idle-gap-sec", type=float, default=1.0)
    args = parser.parse_args()

    project_root = Path.cwd()

    pcap_path = Path(args.pcap)
    if not pcap_path.exists():
        raise FileNotFoundError(f"PCAP not found: {pcap_path}")

    run_name = args.run_name
    if not run_name:
        run_name = pcap_path.stem

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    run_dir = Path(args.output_root) / f"{timestamp}_{run_name}"
    run_dir.mkdir(parents=True, exist_ok=True)

    feature_csv = run_dir / "final_top20_flows.csv"
    prediction_csv = run_dir / "final_top20_runtime_predictions.csv"
    summary_json = run_dir / "runtime_pipeline_summary.json"
    summary_md = run_dir / "runtime_pipeline_report.md"

    schema_report = feature_csv.with_suffix(".schema_report.json")

    print("[INFO] Run directory:", run_dir)

    # 1. Extract final Top-20 features.
    run_cmd(
        [
            "python",
            "ml-service/tools/pcap_to_final_top20_features.py",
            "--pcap",
            str(pcap_path),
            "--output",
            str(feature_csv),
            "--feature-order",
            args.feature_order,
            "--inbound-subnet",
            args.inbound_subnet,
            "--idle-gap-sec",
            str(args.idle_gap_sec),
        ],
        cwd=project_root,
    )

    # 2. Validate schema.
    run_cmd(
        [
            "python",
            "ml-service/tools/compare_runtime_flow_schema.py",
            "--flow-csv",
            str(feature_csv),
            "--feature-order",
            args.feature_order,
        ],
        cwd=project_root,
    )

    # compare_runtime_flow_schema writes report next to flow CSV.
    # Depending on implementation, report is <stem>.schema_report.json.
    if not schema_report.exists():
        alternative = feature_csv.parent / f"{feature_csv.stem}.schema_report.json"
        if alternative.exists():
            schema_report = alternative

    # 3. Test runtime flows with active model.
    # Existing tool uses active API endpoint.
    run_cmd(
        [
            "python",
            "ml-service/tools/test_runtime_flows_with_active_model.py",
            "--flow-csv",
            str(feature_csv),
            "--feature-order",
            args.feature_order,
            "--output",
            str(prediction_csv),
        ],
        cwd=project_root,
    )

    # 4. Get active model-info if possible.
    active_model_info = {}
    try:
        import requests

        resp = requests.get(f"{args.api_base}/model-info", timeout=10)
        if resp.status_code == 200:
            active_model_info = resp.json()
        else:
            active_model_info = {"model_info_status_code": resp.status_code, "text": resp.text}
    except Exception as exc:
        active_model_info = {"error": str(exc)}

    # 5. Summarize predictions.
    pred_summary = summarize_predictions(prediction_csv)

    result = {
        "run_name": run_name,
        "timestamp_utc": datetime.utcnow().isoformat(),
        "pcap": str(pcap_path),
        "run_dir": str(run_dir),
        "feature_csv": str(feature_csv),
        "schema_report": str(schema_report),
        "prediction_csv": str(prediction_csv),
        "active_model_info": active_model_info,
        "prediction_summary": pred_summary,
    }

    write_json(summary_json, result)

    report_text = markdown_report(
        run_name=run_name,
        pcap_path=pcap_path,
        feature_csv=feature_csv,
        schema_report=schema_report,
        prediction_csv=prediction_csv,
        summary=pred_summary,
        active_model_info=active_model_info,
    )
    write_markdown(summary_md, report_text)

    print()
    print("[INFO] Runtime pipeline completed.")
    print(f"[INFO] Run dir       : {run_dir}")
    print(f"[INFO] Feature CSV   : {feature_csv}")
    print(f"[INFO] Prediction CSV: {prediction_csv}")
    print(f"[INFO] Summary JSON  : {summary_json}")
    print(f"[INFO] Summary MD    : {summary_md}")
    print()
    print("[INFO] Prediction summary:")
    print(json.dumps(pred_summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
