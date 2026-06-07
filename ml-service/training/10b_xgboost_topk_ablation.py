#!/usr/bin/env python3
"""
XGBoost Top-K ablation experiments.

Scenarios:
1. normal
   Use all model-ready features.

2. without_inbound
   Exclude Inbound before ranking and Top-K selection.

3. without_inbound_ports
   Exclude Inbound, Source_Port and Destination_Port before ranking and Top-K selection.

Purpose:
- Check whether model performance depends heavily on dataset/topology-sensitive features.
- Evaluate if a more generalizable feature subset can preserve performance.

Usage:
python ml-service/training/10b_xgboost_topk_ablation.py
"""

import argparse
import json
import time
from pathlib import Path
from typing import Dict, List

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


def load_dataset(path: Path, features: List[str]):
    print(f"[INFO] Loading dataset: {path}")
    usecols = features + ["label"]

    df = pd.read_csv(path, usecols=usecols, low_memory=False)

    X = df[features].copy()
    y = df["label"].astype(int).copy()

    X = X.apply(pd.to_numeric, errors="coerce")
    X = X.replace([np.inf, -np.inf], np.nan).fillna(0.0)

    print(f"[INFO] X={X.shape}, y={y.shape}")
    return X, y


def compute_metrics(y_true, y_pred, y_prob):
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


def evaluate_model(model, X, y, threshold: float):
    start = time.perf_counter()
    y_prob = model.predict_proba(X)[:, 1]
    inference_sec = time.perf_counter() - start

    y_pred = (y_prob >= threshold).astype(int)

    metrics = compute_metrics(y, y_pred, y_prob)
    metrics["inference_total_sec"] = float(inference_sec)
    metrics["inference_latency_ms_per_sample"] = float((inference_sec / len(y)) * 1000.0)

    return metrics


def feature_importance_from_model(model, features: List[str]) -> pd.DataFrame:
    booster = model.get_booster()

    gain = booster.get_score(importance_type="gain")
    weight = booster.get_score(importance_type="weight")
    cover = booster.get_score(importance_type="cover")

    rows = []
    for f in features:
        rows.append({
            "feature": f,
            "gain": float(gain.get(f, 0.0)),
            "weight": float(weight.get(f, 0.0)),
            "cover": float(cover.get(f, 0.0)),
        })

    df = pd.DataFrame(rows)
    df = df.sort_values(["gain", "weight", "cover"], ascending=False).reset_index(drop=True)
    df["rank_gain"] = np.arange(1, len(df) + 1)

    return df


def scenario_features(all_features: List[str], scenario: str) -> List[str]:
    excluded = set()

    if scenario == "normal":
        excluded = set()

    elif scenario == "without_inbound":
        excluded = {"Inbound"}

    elif scenario == "without_inbound_ports":
        excluded = {
            "Inbound",
            "Source_Port",
            "Destination_Port",
        }

    else:
        raise ValueError(f"Unknown scenario: {scenario}")

    return [f for f in all_features if f not in excluded]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", default="ml-service/datasets/processed/cicddos2019_train_01_12_model_ready.csv")
    parser.add_argument("--holdout", default="ml-service/datasets/processed/cicddos2019_holdout_03_11_model_ready.csv")
    parser.add_argument("--feature-order", default="ml-service/datasets/metadata/model_ready_large/feature_order_all_features.json")
    parser.add_argument("--output-dir", default="ml-service/experiments/xgboost_feature_reduction_ablation")
    parser.add_argument("--model-dir", default="ml-service/models/xgboost_topk_ablation_models")
    parser.add_argument("--scenarios", default="normal,without_inbound,without_inbound_ports")
    parser.add_argument("--topk", default="10,15,20,25,30,40,50,69")
    parser.add_argument("--threshold", type=float, default=0.5)
    parser.add_argument("--random-state", type=int, default=42)
    parser.add_argument("--n-jobs", type=int, default=-1)
    args = parser.parse_args()

    train_path = Path(args.train)
    holdout_path = Path(args.holdout)
    feature_order_path = Path(args.feature_order)

    output_dir = Path(args.output_dir)
    model_dir = Path(args.model_dir)

    output_dir.mkdir(parents=True, exist_ok=True)
    model_dir.mkdir(parents=True, exist_ok=True)

    all_features = load_json(feature_order_path)

    scenarios = [x.strip() for x in args.scenarios.split(",") if x.strip()]
    topk_values = sorted(set(int(x.strip()) for x in args.topk.split(",") if x.strip()))

    all_rows = []
    all_feature_sets: Dict[str, List[str]] = {}

    for scenario in scenarios:
        print("\n" + "#" * 100)
        print(f"[INFO] Scenario: {scenario}")

        features_for_scenario = scenario_features(all_features, scenario)

        print(f"[INFO] Feature count after scenario exclusion: {len(features_for_scenario)}")
        removed = sorted(set(all_features) - set(features_for_scenario))
        print(f"[INFO] Removed features: {removed}")

        # Train a scenario full model first to get feature ranking without excluded features.
        X_train_full, y_train = load_dataset(train_path, features_for_scenario)
        X_holdout_full, y_holdout = load_dataset(holdout_path, features_for_scenario)

        ranking_model = get_xgboost_model(args.random_state, args.n_jobs)

        print(f"[INFO] Training ranking model for scenario={scenario}")
        start = time.perf_counter()
        ranking_model.fit(X_train_full, y_train)
        ranking_train_sec = time.perf_counter() - start

        importance_df = feature_importance_from_model(ranking_model, features_for_scenario)

        importance_path = output_dir / f"{scenario}_xgboost_feature_importance.csv"
        importance_df.to_csv(importance_path, index=False)

        print(f"[INFO] Importance written: {importance_path}")
        print("[INFO] Top 20 features:")
        print(importance_df.head(20).to_string(index=False))

        for k in topk_values:
            if k > len(features_for_scenario):
                continue

            print("\n" + "=" * 90)
            print(f"[INFO] Scenario={scenario}, Top-{k}")

            selected = importance_df.head(k)["feature"].tolist()
            key = f"{scenario}_top_{k}"
            all_feature_sets[key] = selected

            X_train = X_train_full[selected]
            X_holdout = X_holdout_full[selected]

            model = get_xgboost_model(args.random_state, args.n_jobs)

            start = time.perf_counter()
            model.fit(X_train, y_train)
            train_sec = time.perf_counter() - start

            metrics = evaluate_model(model, X_holdout, y_holdout, args.threshold)

            metrics.update({
                "scenario": scenario,
                "model": f"xgboost_{scenario}_top_{k}",
                "top_k": k,
                "feature_count": k,
                "removed_features": ",".join(removed),
                "threshold": args.threshold,
                "train_rows": int(len(y_train)),
                "holdout_rows": int(len(y_holdout)),
                "training_time_sec": float(train_sec),
                "ranking_model_training_time_sec": float(ranking_train_sec),
            })

            all_rows.append(metrics)

            scenario_model_dir = model_dir / scenario
            scenario_model_dir.mkdir(parents=True, exist_ok=True)

            joblib.dump(model, scenario_model_dir / f"xgboost_top_{k}.pkl")
            write_json(scenario_model_dir / f"xgboost_top_{k}_feature_order.json", selected)

            print(
                f"[RESULT] {scenario} Top-{k} | "
                f"F1={metrics['f1_score']:.6f} "
                f"Recall={metrics['recall']:.6f} "
                f"FNR={metrics['fnr']:.6f} "
                f"FPR={metrics['fpr']:.6f} "
                f"FP={metrics['fp']} "
                f"FN={metrics['fn']} "
                f"TrainSec={train_sec:.2f}"
            )

        # Free memory between scenarios.
        del X_train_full
        del X_holdout_full

    results_df = pd.DataFrame(all_rows)
    results_df = results_df.sort_values(
        ["fnr", "fn", "fpr", "feature_count"],
        ascending=[True, True, True, True],
    )

    metrics_csv = output_dir / "xgboost_topk_ablation_metrics.csv"
    metrics_json = output_dir / "xgboost_topk_ablation_metrics.json"
    feature_sets_json = output_dir / "xgboost_topk_ablation_feature_sets.json"

    results_df.to_csv(metrics_csv, index=False)
    write_json(metrics_json, results_df.to_dict(orient="records"))
    write_json(feature_sets_json, all_feature_sets)

    print("\n" + "#" * 100)
    print("[INFO] Ablation experiments completed.")
    print(f"[INFO] Metrics CSV: {metrics_csv}")
    print(f"[INFO] Feature sets JSON: {feature_sets_json}")

    cols = [
        "scenario",
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

    print(results_df[cols].to_string(index=False))


if __name__ == "__main__":
    main()
