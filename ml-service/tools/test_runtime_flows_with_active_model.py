#!/usr/bin/env python3
"""
Test runtime-extracted flow CSV with active PSO-LightGBM model endpoint.

IMPORTANT:
This script is experimental. It uses basic runtime flow features generated
from PCAP. Some features may be placeholders and not semantically equivalent
to full CICFlowMeter features.

Usage:
python ml-service/tools/test_runtime_flows_with_active_model.py \
  --flow-csv experiments/flow_features/flows.csv \
  --feature-order ml-service/models/active/feature_order.json \
  --url http://127.0.0.1:8000/predict-cicddos \
  --output experiments/results/flow_extraction/runtime_flow_predictions.csv
"""

import argparse
import json
from pathlib import Path

import pandas as pd
import requests


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--flow-csv", required=True)
    parser.add_argument("--feature-order", default="ml-service/models/active/feature_order.json")
    parser.add_argument("--url", default="http://127.0.0.1:8000/predict-cicddos")
    parser.add_argument("--output", default="experiments/results/flow_extraction/runtime_flow_predictions.csv")
    args = parser.parse_args()

    flow_csv = Path(args.flow_csv)
    feature_order_path = Path(args.feature_order)
    output_path = Path(args.output)

    df = pd.read_csv(flow_csv)

    with feature_order_path.open("r", encoding="utf-8") as f:
        feature_order = json.load(f)

    missing = [c for c in feature_order if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required features: {missing}")

    rows = []

    for idx, row in df.iterrows():
        features = {}

        for col in feature_order:
            val = row[col]
            if pd.isna(val):
                val = 0.0
            features[col] = float(val)

        payload = {
            "features": features
        }

        try:
            resp = requests.post(args.url, json=payload, timeout=10)
            status_code = resp.status_code

            if status_code == 200:
                result = resp.json()
            else:
                result = {
                    "error": resp.text
                }

        except Exception as exc:
            status_code = -1
            result = {
                "error": str(exc)
            }

        rows.append({
            "row_index": idx,
            "source_ip": row.get("Source_IP", ""),
            "destination_ip": row.get("Destination_IP", ""),
            "source_port": row.get("Source_Port", ""),
            "destination_port": row.get("Destination_Port", ""),
            "protocol": row.get("Protocol", ""),
            "status_code": status_code,
            "prediction": result.get("prediction", ""),
            "prediction_value": result.get("prediction_value", ""),
            "attack_probability": result.get("attack_probability", result.get("confidence", "")),
            "recommended_action": result.get("recommended_action", ""),
            "feature_count": result.get("feature_count", len(feature_order)),
            "missing_features": json.dumps(result.get("missing_features", [])),
            "extra_features": json.dumps(result.get("extra_features", [])),
            "inference_latency_ms": result.get("inference_latency_ms", ""),
            "raw_response": json.dumps(result, ensure_ascii=False),
            "note": "experimental_cicflowmeter_compatible_selected_features",
        })

    out = pd.DataFrame(rows)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(output_path, index=False)

    print("[INFO] Written:", output_path)
    print("[INFO] Shape:", out.shape)
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
