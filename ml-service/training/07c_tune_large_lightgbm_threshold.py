#!/usr/bin/env python3
"""
Threshold tuning for Large LightGBM baseline on CIC-DDoS2019 holdout set.

Purpose:
- Load trained Large LightGBM model.
- Predict probabilities on holdout CSV-03-11.
- Evaluate different decision thresholds.
- Focus on FN / FNR / Recall trade-off.

Usage:
python ml-service/training/07c_tune_large_lightgbm_threshold.py
"""

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


MODEL_PATH = Path("ml-service/models/large_baseline_lightgbm/best_model.pkl")
FEATURE_ORDER_PATH = Path("ml-service/models/large_baseline_lightgbm/feature_order.json")
HOLDOUT_CSV = Path("ml-service/datasets/processed/cicddos2019_holdout_03_11_model_ready.csv")

OUTPUT_CSV = Path("ml-service/experiments/ml_metrics/large_lightgbm_threshold_tuning.csv")
OUTPUT_JSON = Path("ml-service/experiments/ml_metrics/large_lightgbm_threshold_tuning.json")


THRESHOLDS = [
    0.50,
    0.45,
    0.40,
    0.35,
    0.30,
    0.25,
    0.20,
    0.15,
    0.10,
]


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def compute_metrics(y_true, y_prob, threshold):
    y_pred = (y_prob >= threshold).astype(int)

    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()

    accuracy = accuracy_score(y_true, y_pred)
    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)

    try:
        auc = roc_auc_score(y_true, y_prob)
    except Exception:
        auc = None

    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0
    far = (fp + fn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0.0

    return {
        "threshold": threshold,
        "accuracy": float(accuracy),
        "precision": float(precision),
        "recall": float(recall),
        "f1_score": float(f1),
        "auc": None if auc is None else float(auc),
        "fpr": float(fpr),
        "fnr": float(fnr),
        "far": float(far),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp),
    }


def main():
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    print("[INFO] Loading model:", MODEL_PATH)
    model = joblib.load(MODEL_PATH)

    feature_order = load_json(FEATURE_ORDER_PATH)

    print("[INFO] Loading holdout:", HOLDOUT_CSV)
    df = pd.read_csv(HOLDOUT_CSV, low_memory=False)

    X = df[feature_order].copy()
    y = df["label"].astype(int).copy()

    X = X.apply(pd.to_numeric, errors="coerce")
    X = X.replace([np.inf, -np.inf], np.nan).fillna(0.0)

    print("[INFO] Holdout shape:", X.shape)
    print("[INFO] Label distribution:")
    print(y.value_counts().to_string())

    print("[INFO] Predicting probabilities...")
    y_prob = model.predict_proba(X)[:, 1]

    rows = []
    for threshold in THRESHOLDS:
        m = compute_metrics(y, y_prob, threshold)
        rows.append(m)

        print(
            f"[TH={threshold:.2f}] "
            f"Recall={m['recall']:.6f} "
            f"F1={m['f1_score']:.6f} "
            f"FPR={m['fpr']:.6f} "
            f"FNR={m['fnr']:.6f} "
            f"FP={m['fp']} "
            f"FN={m['fn']}"
        )

    out = pd.DataFrame(rows)
    out.to_csv(OUTPUT_CSV, index=False)

    with OUTPUT_JSON.open("w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2, ensure_ascii=False)

    print("[INFO] Written:", OUTPUT_CSV)
    print("[INFO] Written:", OUTPUT_JSON)

    print()
    print("[INFO] Threshold tuning summary:")
    cols = [
        "threshold",
        "accuracy",
        "precision",
        "recall",
        "f1_score",
        "fpr",
        "fnr",
        "fp",
        "fn",
    ]
    print(out[cols].to_string(index=False))


if __name__ == "__main__":
    main()
