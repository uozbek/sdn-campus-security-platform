#!/usr/bin/env python3
"""
Large CIC-DDoS2019 Model Comparison.

Purpose:
- Compare multiple classifiers on a representative sample of the large cross-day dataset.
- Focus especially on holdout false negatives / FNR.
- Train on CSV-01-12 model-ready sample.
- Evaluate on CSV-03-11 model-ready sample.
- Optionally build a soft-voting ensemble from available probability models.

Why sample-based?
Full train set has ~3.35M rows. Tree ensembles such as RandomForest and ExtraTrees
can be expensive on the full dataset. This script first compares models on a
controlled sample. Best candidates can later be trained on the full dataset.

Usage:
python ml-service/training/08_train_large_model_comparison.py \
  --train ml-service/datasets/processed/cicddos2019_train_01_12_model_ready.csv \
  --holdout ml-service/datasets/processed/cicddos2019_holdout_03_11_model_ready.csv \
  --feature-order ml-service/datasets/metadata/model_ready_large/feature_order_all_features.json \
  --attack-max-rows 100000 \
  --benign-max-rows -1 \
  --chunksize 100000
"""

import argparse
import json
import time
import warnings
from pathlib import Path
from typing import Dict, List, Tuple

import joblib
import numpy as np
import pandas as pd

from sklearn.ensemble import ExtraTreesClassifier, RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


warnings.filterwarnings("ignore")

PROTECTED_COLS = ["raw_label", "attack_type", "label", "source_file", "split"]


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def normalize_limit(value: int):
    """
    -1 means no limit.
    """
    if value is None or int(value) < 0:
        return None
    return int(value)


def sample_by_attack_type(
    csv_path: Path,
    feature_order: List[str],
    attack_max_rows: int,
    benign_max_rows: int,
    chunksize: int,
    random_state: int,
) -> Tuple[pd.DataFrame, pd.Series, pd.DataFrame]:
    """
    Chunk-based sampling by attack_type.

    Keeps:
    - up to benign_max_rows benign rows, or all benign if -1
    - up to attack_max_rows per attack_type
    """
    attack_limit = normalize_limit(attack_max_rows)
    benign_limit = normalize_limit(benign_max_rows)

    required_cols = feature_order + ["label", "attack_type"]
    available_cols = list(pd.read_csv(csv_path, nrows=0).columns)

    missing = [c for c in required_cols if c not in available_cols]
    if missing:
        raise ValueError(f"Missing columns in {csv_path}: {missing}")

    counters: Dict[str, int] = {}
    sampled_parts = []

    print(f"[INFO] Sampling: {csv_path}")

    for chunk_idx, chunk in enumerate(
        pd.read_csv(csv_path, usecols=required_cols, chunksize=chunksize, low_memory=False)
    ):
        chunk_parts = []

        for attack_type, g in chunk.groupby("attack_type"):
            current = counters.get(attack_type, 0)

            if attack_type == "benign":
                limit = benign_limit
            else:
                limit = attack_limit

            if limit is not None:
                remaining = limit - current
                if remaining <= 0:
                    continue

                if len(g) > remaining:
                    g = g.sample(n=remaining, random_state=random_state + chunk_idx)

            counters[attack_type] = current + len(g)
            chunk_parts.append(g)

        if chunk_parts:
            sampled_parts.append(pd.concat(chunk_parts, axis=0, ignore_index=True))

        if chunk_idx % 10 == 0:
            print(f"[INFO] chunk={chunk_idx} counters={counters}")

        # Early stop if all known classes have hit limits.
        # We do not know all classes upfront reliably, so we keep reading.
        # Still safe due to chunking.

    if not sampled_parts:
        raise RuntimeError(f"No rows sampled from {csv_path}")

    df = pd.concat(sampled_parts, axis=0, ignore_index=True)
    df = df.sample(frac=1.0, random_state=random_state).reset_index(drop=True)

    X = df[feature_order].copy()
    y = df["label"].astype(int).copy()

    X = X.apply(pd.to_numeric, errors="coerce")
    X = X.replace([np.inf, -np.inf], np.nan).fillna(0.0)

    meta = df[["attack_type", "label"]].copy()

    print(f"[INFO] Sampled shape X={X.shape}, y={y.shape}")
    print("[INFO] Sampled label distribution:")
    print(y.value_counts().to_string())
    print("[INFO] Sampled attack distribution:")
    print(meta["attack_type"].value_counts().to_string())

    return X, y, meta


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


def evaluate_predictions(y_true, y_prob, threshold: float = 0.5):
    y_pred = (y_prob >= threshold).astype(int)
    return compute_metrics(y_true, y_pred, y_prob)


def get_models(random_state: int, n_jobs: int):
    models = {}

    try:
        from lightgbm import LGBMClassifier

        models["lightgbm"] = LGBMClassifier(
            objective="binary",
            n_estimators=300,
            learning_rate=0.05,
            num_leaves=64,
            random_state=random_state,
            n_jobs=n_jobs,
            class_weight="balanced",
            force_row_wise=True,
            verbosity=-1,
        )
    except Exception as exc:
        print(f"[WARN] LightGBM unavailable: {exc}")

    try:
        from xgboost import XGBClassifier

        models["xgboost"] = XGBClassifier(
            n_estimators=300,
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
    except Exception as exc:
        print(f"[WARN] XGBoost unavailable, skipping: {exc}")

    models["extra_trees"] = ExtraTreesClassifier(
        n_estimators=200,
        max_depth=None,
        min_samples_split=2,
        min_samples_leaf=1,
        class_weight="balanced",
        random_state=random_state,
        n_jobs=n_jobs,
    )

    models["random_forest"] = RandomForestClassifier(
        n_estimators=150,
        max_depth=32,
        min_samples_split=2,
        min_samples_leaf=1,
        class_weight="balanced_subsample",
        random_state=random_state,
        n_jobs=n_jobs,
    )

    models["hist_gradient_boosting"] = HistGradientBoostingClassifier(
        max_iter=200,
        learning_rate=0.05,
        max_leaf_nodes=64,
        l2_regularization=0.0,
        random_state=random_state,
    )

    models["logistic_regression"] = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            (
                "clf",
                LogisticRegression(
                    class_weight="balanced",
                    max_iter=1000,
                    solver="saga",
                    n_jobs=n_jobs,
                    random_state=random_state,
                ),
            ),
        ]
    )

    return models


def predict_probability(model, X):
    if hasattr(model, "predict_proba"):
        return model.predict_proba(X)[:, 1]

    if hasattr(model, "decision_function"):
        scores = model.decision_function(X)
        # Min-max fallback.
        scores = np.asarray(scores)
        return (scores - scores.min()) / (scores.max() - scores.min() + 1e-12)

    preds = model.predict(X)
    return np.asarray(preds, dtype=float)


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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", default="ml-service/datasets/processed/cicddos2019_train_01_12_model_ready.csv")
    parser.add_argument("--holdout", default="ml-service/datasets/processed/cicddos2019_holdout_03_11_model_ready.csv")
    parser.add_argument("--feature-order", default="ml-service/datasets/metadata/model_ready_large/feature_order_all_features.json")
    parser.add_argument("--output-dir", default="ml-service/experiments/model_comparison_large")
    parser.add_argument("--model-dir", default="ml-service/models/large_model_comparison")
    parser.add_argument("--attack-max-rows", type=int, default=100000)
    parser.add_argument("--benign-max-rows", type=int, default=-1)
    parser.add_argument("--chunksize", type=int, default=100000)
    parser.add_argument("--random-state", type=int, default=42)
    parser.add_argument("--n-jobs", type=int, default=-1)
    parser.add_argument("--threshold", type=float, default=0.5)
    args = parser.parse_args()

    train_path = Path(args.train)
    holdout_path = Path(args.holdout)
    feature_order_path = Path(args.feature_order)

    output_dir = Path(args.output_dir)
    model_dir = Path(args.model_dir)

    output_dir.mkdir(parents=True, exist_ok=True)
    model_dir.mkdir(parents=True, exist_ok=True)

    feature_order = load_json(feature_order_path)

    X_train, y_train, train_meta = sample_by_attack_type(
        train_path,
        feature_order,
        attack_max_rows=args.attack_max_rows,
        benign_max_rows=args.benign_max_rows,
        chunksize=args.chunksize,
        random_state=args.random_state,
    )

    X_holdout, y_holdout, holdout_meta = sample_by_attack_type(
        holdout_path,
        feature_order,
        attack_max_rows=args.attack_max_rows,
        benign_max_rows=args.benign_max_rows,
        chunksize=args.chunksize,
        random_state=args.random_state,
    )

    models = get_models(args.random_state, args.n_jobs)

    metrics_rows = []
    cm_results = {}
    probability_cache = {}

    for name, model in models.items():
        print("\n" + "=" * 80)
        print(f"[INFO] Training model: {name}")

        start = time.perf_counter()
        model.fit(X_train, y_train)
        train_sec = time.perf_counter() - start

        print(f"[INFO] Training completed: {name}, sec={train_sec:.2f}")

        model_path = model_dir / f"{name}.pkl"
        joblib.dump(model, model_path)

        print(f"[INFO] Evaluating model: {name}")

        start = time.perf_counter()
        y_prob = predict_probability(model, X_holdout)
        infer_sec = time.perf_counter() - start

        probability_cache[name] = y_prob

        metrics, cm = evaluate_predictions(y_holdout, y_prob, threshold=args.threshold)

        metrics.update({
            "model": name,
            "threshold": args.threshold,
            "train_rows": int(len(y_train)),
            "holdout_rows": int(len(y_holdout)),
            "feature_count": len(feature_order),
            "training_time_sec": float(train_sec),
            "inference_total_sec": float(infer_sec),
            "inference_latency_ms_per_sample": float((infer_sec / len(y_holdout)) * 1000.0),
            "model_path": str(model_path),
        })

        cm_results[name] = cm
        metrics_rows.append(metrics)

        breakdown = attack_type_error_breakdown(
            holdout_meta,
            y_holdout,
            y_prob,
            threshold=args.threshold,
        )

        breakdown_path = output_dir / f"{name}_holdout_attack_type_error_breakdown.csv"
        breakdown.to_csv(breakdown_path, index=False)

        print(
            f"[RESULT] {name} | "
            f"F1={metrics['f1_score']:.6f} "
            f"Recall={metrics['recall']:.6f} "
            f"FNR={metrics['fnr']:.6f} "
            f"FPR={metrics['fpr']:.6f} "
            f"FP={metrics['fp']} "
            f"FN={metrics['fn']}"
        )

    # Soft voting ensembles from available probability models.
    ensemble_candidates = [
        ["lightgbm", "xgboost", "extra_trees"],
        ["lightgbm", "extra_trees"],
        ["lightgbm", "xgboost"],
        ["extra_trees", "random_forest", "lightgbm"],
    ]

    for candidate in ensemble_candidates:
        available = [m for m in candidate if m in probability_cache]
        if len(available) < 2:
            continue

        ensemble_name = "soft_voting_" + "_".join(available)
        print("\n" + "=" * 80)
        print(f"[INFO] Evaluating ensemble: {ensemble_name}")

        # Simple equal-weight average.
        probs = np.vstack([probability_cache[m] for m in available])
        y_prob = probs.mean(axis=0)

        metrics, cm = evaluate_predictions(y_holdout, y_prob, threshold=args.threshold)

        metrics.update({
            "model": ensemble_name,
            "threshold": args.threshold,
            "train_rows": int(len(y_train)),
            "holdout_rows": int(len(y_holdout)),
            "feature_count": len(feature_order),
            "training_time_sec": None,
            "inference_total_sec": None,
            "inference_latency_ms_per_sample": None,
            "model_path": "",
            "ensemble_members": ",".join(available),
        })

        cm_results[ensemble_name] = cm
        metrics_rows.append(metrics)

        breakdown = attack_type_error_breakdown(
            holdout_meta,
            y_holdout,
            y_prob,
            threshold=args.threshold,
        )

        breakdown_path = output_dir / f"{ensemble_name}_holdout_attack_type_error_breakdown.csv"
        breakdown.to_csv(breakdown_path, index=False)

        print(
            f"[RESULT] {ensemble_name} | "
            f"F1={metrics['f1_score']:.6f} "
            f"Recall={metrics['recall']:.6f} "
            f"FNR={metrics['fnr']:.6f} "
            f"FPR={metrics['fpr']:.6f} "
            f"FP={metrics['fp']} "
            f"FN={metrics['fn']}"
        )

    metrics_df = pd.DataFrame(metrics_rows)
    metrics_df = metrics_df.sort_values(
        ["fnr", "fn", "fpr", "f1_score"],
        ascending=[True, True, True, False],
    )

    metrics_csv = output_dir / "large_model_comparison_metrics.csv"
    metrics_json = output_dir / "large_model_comparison_metrics.json"
    cm_json = output_dir / "large_model_comparison_confusion_matrices.json"

    metrics_df.to_csv(metrics_csv, index=False)
    write_json(metrics_json, metrics_df.to_dict(orient="records"))
    write_json(cm_json, cm_results)

    write_json(
        output_dir / "large_model_comparison_config.json",
        {
            "train": str(train_path),
            "holdout": str(holdout_path),
            "feature_order": str(feature_order_path),
            "attack_max_rows": args.attack_max_rows,
            "benign_max_rows": args.benign_max_rows,
            "chunksize": args.chunksize,
            "threshold": args.threshold,
            "feature_count": len(feature_order),
            "models": list(models.keys()),
        },
    )

    print("\n" + "=" * 80)
    print("[INFO] Model comparison completed.")
    print(f"[INFO] Metrics CSV: {metrics_csv}")
    print(f"[INFO] Confusion matrices: {cm_json}")

    cols = [
        "model",
        "holdout_rows",
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
