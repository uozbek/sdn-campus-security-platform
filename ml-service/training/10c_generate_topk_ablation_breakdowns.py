#!/usr/bin/env python3
"""
Generate attack-type error breakdowns for XGBoost Top-K ablation models.

This script loads trained Top-K ablation models and evaluates them on the
full holdout dataset with attack_type metadata.

Outputs:
- one breakdown CSV per scenario/top-k model

Usage:
python ml-service/training/10c_generate_topk_ablation_breakdowns.py \
  --scenarios normal,without_inbound,without_inbound_ports \
  --topk 10,15,20,25,30,40,50,69
"""

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_breakdown_csv(path: Path, breakdown: pd.DataFrame):
    path.parent.mkdir(parents=True, exist_ok=True)
    breakdown.to_csv(path, index=False)


def attack_type_error_breakdown(meta: pd.DataFrame, y_true, y_prob, threshold: float = 0.5):
    y_pred = (y_prob >= threshold).astype(int)

    df = meta.copy()
    df["y_true"] = np.asarray(y_true)
    df["y_pred"] = y_pred

    rows = []

    for attack_type, g in df.groupby("attack_type"):
        total = len(g)

        fn = int(((g["y_true"] == 1) & (g["y_pred"] == 0)).sum())
        fp = int(((g["y_true"] == 0) & (g["y_pred"] == 1)).sum())
        tp = int(((g["y_true"] == 1) & (g["y_pred"] == 1)).sum())
        tn = int(((g["y_true"] == 0) & (g["y_pred"] == 0)).sum())

        rows.append({
            "attack_type": attack_type,
            "rows": int(total),
            "tn": tn,
            "fp": fp,
            "fn": fn,
            "tp": tp,
            "fn_ratio_within_type": fn / total if total > 0 else 0.0,
            "fp_ratio_within_type": fp / total if total > 0 else 0.0,
        })

    return pd.DataFrame(rows).sort_values(["fn", "fp"], ascending=False)


def evaluate_model(model_path: Path, feature_order_path: Path, holdout_csv: Path, threshold: float):
    model = joblib.load(model_path)
    feature_order = load_json(feature_order_path)

    usecols = feature_order + ["label", "attack_type"]
    df = pd.read_csv(holdout_csv, usecols=usecols, low_memory=False)

    X = df[feature_order].copy()
    y = df["label"].astype(int).copy()
    meta = df[["attack_type", "label"]].copy()

    X = X.apply(pd.to_numeric, errors="coerce")
    X = X.replace([np.inf, -np.inf], np.nan).fillna(0.0)

    y_prob = model.predict_proba(X)[:, 1]

    return attack_type_error_breakdown(meta, y, y_prob, threshold=threshold)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--holdout",
        default="ml-service/datasets/processed/cicddos2019_holdout_03_11_model_ready.csv",
    )
    parser.add_argument(
        "--model-base-dir",
        default="ml-service/models/xgboost_topk_ablation_models",
    )
    parser.add_argument(
        "--output-dir",
        default="ml-service/experiments/xgboost_feature_reduction_ablation/breakdowns",
    )
    parser.add_argument(
        "--scenarios",
        default="normal,without_inbound,without_inbound_ports",
    )
    parser.add_argument(
        "--topk",
        default="10,15,20,25,30,40,50,69",
    )
    parser.add_argument("--threshold", type=float, default=0.5)
    args = parser.parse_args()

    holdout_csv = Path(args.holdout)
    model_base_dir = Path(args.model_base_dir)
    output_dir = Path(args.output_dir)

    scenarios = [x.strip() for x in args.scenarios.split(",") if x.strip()]
    topk_values = [int(x.strip()) for x in args.topk.split(",") if x.strip()]

    for scenario in scenarios:
        for k in topk_values:
            model_path = model_base_dir / scenario / f"xgboost_top_{k}.pkl"
            feature_order_path = model_base_dir / scenario / f"xgboost_top_{k}_feature_order.json"

            if not model_path.exists() or not feature_order_path.exists():
                print(f"[WARN] Skipping missing model/features: scenario={scenario}, top_k={k}")
                continue

            print(f"[INFO] Evaluating breakdown: scenario={scenario}, top_k={k}")

            breakdown = evaluate_model(
                model_path=model_path,
                feature_order_path=feature_order_path,
                holdout_csv=holdout_csv,
                threshold=args.threshold,
            )

            out = output_dir / f"{scenario}_top_{k}_holdout_attack_type_error_breakdown.csv"
            write_breakdown_csv(out, breakdown)

            print(f"[INFO] Written: {out}")
            print(breakdown.to_string(index=False))


if __name__ == "__main__":
    main()
