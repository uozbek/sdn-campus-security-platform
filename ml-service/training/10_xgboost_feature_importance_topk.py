#!/usr/bin/env python3
"""
XGBoost feature importance and Top-K feature subset experiments.

Purpose:
- Load the full XGBoost candidate model.
- Extract feature importance.
- Train XGBoost models using Top-K most important features.
- Evaluate each Top-K model on full holdout set.
- Identify the smallest feature subset that preserves near-full performance.

Inputs:
- Full model-ready train CSV
- Full model-ready holdout CSV
- Full feature order JSON
- Full candidate XGBoost model

Outputs:
- xgboost_feature_importance.csv
- xgboost_topk_metrics.csv
- xgboost_topk_metrics.json
- xgboost_topk_feature_sets.json
- trained Top-K models

Usage:
python ml-service/training/10_xgboost_feature_importance_topk.py
"""

import argparse
import json
import time
from pathlib import Path
from typing import Dict, List, Tuple

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


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_dataset(path: Path, feature_order: List[str]):
    print(f"[INFO] Loading dataset: {path}")
    df = pd.read_csv(path, low_memory=False)

    missing = [c for c in feature_order if c not in df.columns]
    if missing:
        raise ValueError(f"Missing features in {path}: {missing}")

    X = df[feature_order].copy()
    y = df["label"].astype(int).copy()

    X = X.apply(pd.to_numeric, errors="coerce")
    X = X.replace([np.inf, -np.inf], np.nan).fillna(0.0)

    print(f"[INFO] X={X.shape}, y={y.shape}")
    print("[INFO] Label distribution:")
    print(y.value_counts().to_string())

    return X, y


def compute_metrics(y_true, y_pred, y_prob) -> Dict:
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


def evaluate_model(model, X, y, threshold: float = 0.5) -> Dict:
    start = time.perf_counter()
    y_prob = model.predict_proba(X)[:, 1]
    infer_sec = time.perf_counter() - start

    y_pred = (y_prob >= threshold).astype(int)
    metrics = compute_metrics(y, y_pred, y_prob)

    metrics["inference_total_sec"] = float(infer_sec)
    metrics["inference_latency_ms_per_sample"] = float((infer_sec / len(y)) * 1000.0)

    return metrics


def get_xgboost_model(random_state: int, n_jobs: int):
    from xgboost import XGBClassifier

    return XGBClassifier(
        n_estimators=400,
        learning_rate=0.05,
        max_depth=8,
        subsample=0.9,
        colsample_bytree=0.9,
        objective="binary:logistic",
        eval_metric="logloss",
        tree_method="hist",
        random_state=random_state,
        n_jobs=n_jobs,
    )


def extract_feature_importance(model, feature_order: List[str]) -> pd.DataFrame:
    booster = model.get_booster()

    score_gain = booster.get_score(importance_type="gain")
    score_weight = booster.get_score(importance_type="weight")
    score_cover = booster.get_score(importance_type="cover")

    rows = []

    for feature in feature_order:
        rows.append({
            "feature": feature,
            "gain": float(score_gain.get(feature, 0.0)),
            "weight": float(score_weight.get(feature, 0.0)),
            "cover": float(score_cover.get(feature, 0.0)),
        })

    df = pd.DataFrame(rows)

    # Main ranking by gain.
    df = df.sort_values(["gain", "weight", "cover"], ascending=False).reset_index(drop=True)
    df["rank_gain"] = np.arange(1, len(df) + 1)

    return df


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", default="ml-service/datasets/processed/cicddos2019_train_01_12_model_ready.csv")
    parser.add_argument("--holdout", default="ml-service/datasets/processed/cicddos2019_holdout_03_11_model_ready.csv")
    parser.add_argument("--feature-order", default="ml-service/datasets/metadata/model_ready_large/feature_order_all_features.json")
    parser.add_argument("--full-model", default="ml-service/models/full_candidate_models/xgboost.pkl")
    parser.add_argument("--output-dir", default="ml-service/experiments/xgboost_feature_reduction")
    parser.add_argument("--model-dir", default="ml-service/models/xgboost_topk_models")
    parser.add_argument("--topk", default="10,15,20,25,30,40,50,69")
    parser.add_argument("--threshold", type=float, default=0.5)
    parser.add_argument("--random-state", type=int, default=42)
    parser.add_argument("--n-jobs", type=int, default=-1)
    args = parser.parse_args()

    train_path = Path(args.train)
    holdout_path = Path(args.holdout)
    feature_order_path = Path(args.feature_order)
    full_model_path = Path(args.full_model)

    output_dir = Path(args.output_dir)
    model_dir = Path(args.model_dir)

    output_dir.mkdir(parents=True, exist_ok=True)
    model_dir.mkdir(parents=True, exist_ok=True)

    feature_order = load_json(feature_order_path)

    print("[INFO] Loading full XGBoost model:", full_model_path)
    full_model = joblib.load(full_model_path)

    importance_df = extract_feature_importance(full_model, feature_order)

    importance_csv = output_dir / "xgboost_feature_importance.csv"
    importance_df.to_csv(importance_csv, index=False)
    print(f"[INFO] Feature importance written: {importance_csv}")

    print("[INFO] Top 20 features by gain:")
    print(importance_df.head(20).to_string(index=False))

    topk_values = [int(x.strip()) for x in args.topk.split(",") if x.strip()]
    topk_values = sorted(set(topk_values))

    print("[INFO] Loading train and holdout datasets...")
    X_train_all, y_train = load_dataset(train_path, feature_order)
    X_holdout_all, y_holdout = load_dataset(holdout_path, feature_order)

    rows = []
    feature_sets = {}

    for k in topk_values:
        print("\n" + "=" * 90)
        print(f"[INFO] Training Top-{k} XGBoost model")

        selected_features = importance_df.head(k)["feature"].tolist()
        feature_sets[f"top_{k}"] = selected_features

        X_train = X_train_all[selected_features]
        X_holdout = X_holdout_all[selected_features]

        model = get_xgboost_model(random_state=args.random_state, n_jobs=args.n_jobs)

        start = time.perf_counter()
        model.fit(X_train, y_train)
        training_time_sec = time.perf_counter() - start

        metrics = evaluate_model(model, X_holdout, y_holdout, threshold=args.threshold)

        metrics.update({
            "model": f"xgboost_top_{k}",
            "top_k": k,
            "feature_count": k,
            "threshold": args.threshold,
            "train_rows": int(len(y_train)),
            "holdout_rows": int(len(y_holdout)),
            "training_time_sec": float(training_time_sec),
        })

        rows.append(metrics)

        model_path = model_dir / f"xgboost_top_{k}.pkl"
        joblib.dump(model, model_path)

        write_json(model_dir / f"xgboost_top_{k}_feature_order.json", selected_features)

        print(
            f"[RESULT] Top-{k} | "
            f"F1={metrics['f1_score']:.6f} "
            f"Recall={metrics['recall']:.6f} "
            f"FNR={metrics['fnr']:.6f} "
            f"FPR={metrics['fpr']:.6f} "
            f"FP={metrics['fp']} "
            f"FN={metrics['fn']} "
            f"TrainSec={training_time_sec:.2f}"
        )

    metrics_df = pd.DataFrame(rows)
    metrics_df = metrics_df.sort_values(["fnr", "fn", "fpr", "feature_count"], ascending=[True, True, True, True])

    metrics_csv = output_dir / "xgboost_topk_metrics.csv"
    metrics_json = output_dir / "xgboost_topk_metrics.json"
    feature_sets_json = output_dir / "xgboost_topk_feature_sets.json"

    metrics_df.to_csv(metrics_csv, index=False)
    write_json(metrics_json, metrics_df.to_dict(orient="records"))
    write_json(feature_sets_json, feature_sets)

    print("\n" + "=" * 90)
    print("[INFO] Top-K experiment completed.")
    print(f"[INFO] Metrics CSV: {metrics_csv}")
    print(f"[INFO] Feature sets: {feature_sets_json}")

    cols = [
        "model",
        "feature_count",
        "accuracy",
        "precision",
        "recall",
        "f1_score",
        "auc",
        "fpr",
        "fnr",
        "fp",
        "fn",
        "training_time_sec",
        "inference_latency_ms_per_sample",
    ]

    print(metrics_df[cols].to_string(index=False))


if __name__ == "__main__":
    main()
