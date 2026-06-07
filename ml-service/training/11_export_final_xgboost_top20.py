#!/usr/bin/env python3
"""
Export final XGBoost Top-20 selected-feature model.

Purpose:
- Copy the trained xgboost_normal_top_20 model to a final model directory.
- Copy/write the Top-20 feature_order.json.
- Save final model metadata.
- Save selected metrics.

Input model:
ml-service/models/xgboost_topk_ablation_models/normal/xgboost_top_20.pkl

Input feature set:
ml-service/experiments/xgboost_feature_reduction_ablation/xgboost_topk_ablation_feature_sets.json

Input metrics:
ml-service/experiments/xgboost_feature_reduction_ablation/xgboost_topk_ablation_metrics.csv

Output:
ml-service/models/final_xgboost_top20/
"""

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path

import pandas as pd


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model",
        default="ml-service/models/xgboost_topk_ablation_models/normal/xgboost_top_20.pkl",
    )
    parser.add_argument(
        "--feature-sets",
        default="ml-service/experiments/xgboost_feature_reduction_ablation/xgboost_topk_ablation_feature_sets.json",
    )
    parser.add_argument(
        "--metrics",
        default="ml-service/experiments/xgboost_feature_reduction_ablation/xgboost_topk_ablation_metrics.csv",
    )
    parser.add_argument(
        "--feature-key",
        default="normal_top_20",
    )
    parser.add_argument(
        "--output-dir",
        default="ml-service/models/final_xgboost_top20",
    )
    args = parser.parse_args()

    model_path = Path(args.model)
    feature_sets_path = Path(args.feature_sets)
    metrics_path = Path(args.metrics)
    output_dir = Path(args.output_dir)

    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")

    if not feature_sets_path.exists():
        raise FileNotFoundError(f"Feature sets JSON not found: {feature_sets_path}")

    if not metrics_path.exists():
        raise FileNotFoundError(f"Metrics CSV not found: {metrics_path}")

    output_dir.mkdir(parents=True, exist_ok=True)

    feature_sets = load_json(feature_sets_path)

    if args.feature_key not in feature_sets:
        raise KeyError(
            f"Feature key not found: {args.feature_key}. "
            f"Available keys: {list(feature_sets.keys())}"
        )

    feature_order = feature_sets[args.feature_key]

    metrics_df = pd.read_csv(metrics_path)

    row = metrics_df[
        (metrics_df["scenario"] == "normal")
        & (metrics_df["feature_count"] == 20)
    ]

    if row.empty:
        raise ValueError("Metrics row for scenario=normal and feature_count=20 not found.")

    metrics = row.iloc[0].to_dict()

    final_model_path = output_dir / "best_model.pkl"
    shutil.copy2(model_path, final_model_path)

    write_json(output_dir / "feature_order.json", feature_order)
    write_json(output_dir / "label_mapping.json", {"BENIGN": 0, "ATTACK": 1})

    training_metrics = {
        k: (None if pd.isna(v) else v)
        for k, v in metrics.items()
    }
    write_json(output_dir / "training_metrics.json", training_metrics)

    metadata = {
        "model_name": "final_xgboost_top20",
        "algorithm": "XGBoost",
        "task": "binary_ddos_detection",
        "dataset_family": "CIC-DDoS2019",
        "train_source": "CSV-01-12",
        "holdout_source": "CSV-03-11",
        "portmap_portscan_excluded": True,
        "source_ip_destination_ip_excluded": True,
        "constant_features_removed": True,
        "feature_selection_method": "xgboost_gain_topk",
        "feature_selection_scenario": "normal",
        "feature_count": len(feature_order),
        "model_file": "best_model.pkl",
        "feature_order_file": "feature_order.json",
        "label_mapping_file": "label_mapping.json",
        "training_metrics_file": "training_metrics.json",
        "threshold": 0.5,
        "input_schema": "cicddos2019_xgboost_top20_selected_features",
        "endpoint": "/predict-cicddos",
        "status": "candidate_final",
        "created_at_utc": datetime.utcnow().isoformat(),
        "holdout_metrics": {
            "accuracy": float(metrics["accuracy"]),
            "precision": float(metrics["precision"]),
            "recall": float(metrics["recall"]),
            "f1_score": float(metrics["f1_score"]),
            "auc": float(metrics["auc"]),
            "fpr": float(metrics["fpr"]),
            "fnr": float(metrics["fnr"]),
            "far": float(metrics["far"]),
            "fp": int(metrics["fp"]),
            "fn": int(metrics["fn"]),
            "tn": int(metrics["tn"]),
            "tp": int(metrics["tp"]),
        },
        "notes": (
            "Final selected-feature XGBoost Top-20 model. "
            "Source IP and Destination IP were excluded. "
            "Constant features were removed. "
            "Inbound is retained; ablation experiments showed that removing Inbound "
            "significantly increased false positives. "
            "This model reduced the feature count from 69 to 20 while preserving "
            "near-full XGBoost holdout performance."
        ),
    }

    write_json(output_dir / "model_metadata.json", metadata)

    print("[INFO] Final XGBoost Top-20 model exported.")
    print(f"[INFO] Output dir: {output_dir}")
    print(f"[INFO] Model: {final_model_path}")
    print(f"[INFO] Feature count: {len(feature_order)}")
    print("[INFO] Feature order:")
    for i, feature in enumerate(feature_order, start=1):
        print(f"{i:02d}. {feature}")

    print("[INFO] Holdout metrics:")
    for key in ["accuracy", "precision", "recall", "f1_score", "auc", "fpr", "fnr", "fp", "fn"]:
        print(f" - {key}: {metrics[key]}")


if __name__ == "__main__":
    main()
