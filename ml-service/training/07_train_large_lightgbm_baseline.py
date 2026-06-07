#!/usr/bin/env python3
"""
Train Large CIC-DDoS2019 LightGBM Baseline Model.

Purpose:
- Train LightGBM on model-ready CSV-01-12 train dataset.
- Evaluate on internal validation split.
- Evaluate on CSV-03-11 holdout dataset.
- Save metrics, confusion matrices, model and metadata.

Inputs:
- cicddos2019_train_01_12_model_ready.csv
- cicddos2019_holdout_03_11_model_ready.csv
- feature_order_all_features.json

Outputs:
- ml-service/models/large_baseline_lightgbm/
- ml-service/experiments/ml_metrics/large_lightgbm_baseline_metrics.csv
- ml-service/experiments/ml_metrics/large_lightgbm_baseline_metrics.json
- ml-service/experiments/ml_metrics/large_lightgbm_confusion_matrices.json
"""

import argparse
import json
import time
from pathlib import Path
from typing import Dict, Tuple

import joblib
import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split


PROTECTED_COLS = ["raw_label", "attack_type", "label", "source_file", "split"]


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_dataset(path: Path, feature_order):
    print(f"[INFO] Loading dataset: {path}")
    df = pd.read_csv(path, low_memory=False)

    missing = [c for c in feature_order if c not in df.columns]
    if missing:
        raise ValueError(f"Missing features in {path}: {missing}")

    if "label" not in df.columns:
        raise ValueError(f"'label' column not found in {path}")

    X = df[feature_order].copy()
    y = df["label"].astype(int).copy()

    # Ensure numeric and safe values.
    X = X.apply(pd.to_numeric, errors="coerce")
    X = X.replace([np.inf, -np.inf], np.nan).fillna(0.0)

    print(f"[INFO] Shape X={X.shape}, y={y.shape}")
    print("[INFO] Label distribution:")
    print(y.value_counts().to_string())

    return X, y, df


def compute_metrics(y_true, y_pred, y_prob) -> Tuple[Dict, Dict]:
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

    # FAR here is interpreted as average of false alarm-related rates.
    # For binary IDS reporting, FPR is usually the main false alarm rate.
    far = (fp + fn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0.0

    metrics = {
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

    cm = {
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp),
        "matrix_labels": ["BENIGN", "ATTACK"],
        "matrix": [[int(tn), int(fp)], [int(fn), int(tp)]],
    }

    return metrics, cm


def evaluate_model(model, X, y, split_name: str) -> Tuple[Dict, Dict]:
    print(f"[INFO] Evaluating split: {split_name}")

    start = time.perf_counter()
    y_prob = model.predict_proba(X)[:, 1]
    y_pred = (y_prob >= 0.5).astype(int)
    elapsed = time.perf_counter() - start

    metrics, cm = compute_metrics(y, y_pred, y_prob)
    metrics["split"] = split_name
    metrics["rows"] = int(len(y))
    metrics["inference_total_sec"] = float(elapsed)
    metrics["inference_latency_ms_per_sample"] = float((elapsed / len(y)) * 1000.0)

    auc_text = f"{metrics['auc']:.6f}" if metrics["auc"] is not None else "NA"

    print(
        f"[RESULT] {split_name} | "
        f"F1={metrics['f1_score']:.6f} "
        f"AUC={auc_text} "
        f"FPR={metrics['fpr']:.6f} "
        f"FAR={metrics['far']:.6f}"
   )

    return metrics, cm


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--train",
        default="ml-service/datasets/processed/cicddos2019_train_01_12_model_ready.csv",
    )
    parser.add_argument(
        "--holdout",
        default="ml-service/datasets/processed/cicddos2019_holdout_03_11_model_ready.csv",
    )
    parser.add_argument(
        "--feature-order",
        default="ml-service/datasets/metadata/model_ready_large/feature_order_all_features.json",
    )
    parser.add_argument(
        "--model-dir",
        default="ml-service/models/large_baseline_lightgbm",
    )
    parser.add_argument(
        "--metrics-dir",
        default="ml-service/experiments/ml_metrics",
    )
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--random-state", type=int, default=42)
    parser.add_argument("--n-estimators", type=int, default=300)
    parser.add_argument("--learning-rate", type=float, default=0.05)
    parser.add_argument("--num-leaves", type=int, default=64)
    parser.add_argument("--n-jobs", type=int, default=-1)
    args = parser.parse_args()

    train_path = Path(args.train)
    holdout_path = Path(args.holdout)
    feature_order_path = Path(args.feature_order)
    model_dir = Path(args.model_dir)
    metrics_dir = Path(args.metrics_dir)

    model_dir.mkdir(parents=True, exist_ok=True)
    metrics_dir.mkdir(parents=True, exist_ok=True)

    feature_order = load_json(feature_order_path)

    X_all, y_all, train_df = load_dataset(train_path, feature_order)
    X_holdout, y_holdout, holdout_df = load_dataset(holdout_path, feature_order)

    print("[INFO] Splitting train into train/validation...")
    X_train, X_val, y_train, y_val = train_test_split(
        X_all,
        y_all,
        test_size=args.test_size,
        random_state=args.random_state,
        stratify=y_all,
    )

    print(f"[INFO] X_train={X_train.shape}, X_val={X_val.shape}")

    model = LGBMClassifier(
        objective="binary",
        n_estimators=args.n_estimators,
        learning_rate=args.learning_rate,
        num_leaves=args.num_leaves,
        random_state=args.random_state,
        n_jobs=args.n_jobs,
        class_weight="balanced",
        force_row_wise=True,
        verbosity=-1,
    )

    print("[INFO] Training LightGBM large baseline...")
    train_start = time.perf_counter()
    model.fit(X_train, y_train)
    training_time_sec = time.perf_counter() - train_start

    print(f"[INFO] Training completed in {training_time_sec:.2f} sec")

    val_metrics, val_cm = evaluate_model(model, X_val, y_val, "validation_01_12")
    holdout_metrics, holdout_cm = evaluate_model(model, X_holdout, y_holdout, "holdout_03_11")

    for m in [val_metrics, holdout_metrics]:
        m["model"] = "lightgbm"
        m["dataset_family"] = "CIC-DDoS2019"
        m["training_source"] = "CSV-01-12"
        m["holdout_source"] = "CSV-03-11"
        m["feature_count"] = len(feature_order)
        m["training_time_sec"] = float(training_time_sec)
        m["n_estimators"] = args.n_estimators
        m["learning_rate"] = args.learning_rate
        m["num_leaves"] = args.num_leaves
        m["class_weight"] = "balanced"

    metrics_df = pd.DataFrame([val_metrics, holdout_metrics])

    metrics_csv = metrics_dir / "large_lightgbm_baseline_metrics.csv"
    metrics_json = metrics_dir / "large_lightgbm_baseline_metrics.json"
    cm_json = metrics_dir / "large_lightgbm_confusion_matrices.json"

    metrics_df.to_csv(metrics_csv, index=False)
    write_json(metrics_json, metrics_df.to_dict(orient="records"))
    write_json(
        cm_json,
        {
            "validation_01_12": val_cm,
            "holdout_03_11": holdout_cm,
        },
    )

    model_path = model_dir / "best_model.pkl"
    joblib.dump(model, model_path)

    write_json(model_dir / "feature_order.json", feature_order)
    write_json(model_dir / "label_mapping.json", {"BENIGN": 0, "ATTACK": 1})

    metadata = {
        "model_name": "large_lightgbm_baseline",
        "base_model": "LightGBM",
        "task": "binary_ddos_detection",
        "dataset_family": "CIC-DDoS2019",
        "train_source": "CSV-01-12",
        "holdout_source": "CSV-03-11",
        "portmap_portscan_excluded": True,
        "feature_count": len(feature_order),
        "feature_order_file": "feature_order.json",
        "model_file": "best_model.pkl",
        "label_mapping_file": "label_mapping.json",
        "class_weight": "balanced",
        "n_estimators": args.n_estimators,
        "learning_rate": args.learning_rate,
        "num_leaves": args.num_leaves,
        "random_state": args.random_state,
        "notes": (
            "Large cross-day LightGBM baseline trained on CIC-DDoS2019 CSV-01-12 "
            "and evaluated on CSV-03-11 holdout. Constant features removed. "
            "Portmap/PortScan excluded from main DDoS pipeline."
        ),
    }

    write_json(model_dir / "model_metadata.json", metadata)

    print("[INFO] Outputs:")
    print(f" - Model: {model_path}")
    print(f" - Metrics CSV: {metrics_csv}")
    print(f" - Metrics JSON: {metrics_json}")
    print(f" - Confusion matrices: {cm_json}")
    print(f" - Metadata: {model_dir / 'model_metadata.json'}")

    print("[INFO] Metrics:")
    print(metrics_df.to_string(index=False))


if __name__ == "__main__":
    main()
