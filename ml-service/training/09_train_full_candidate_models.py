#!/usr/bin/env python3
"""
Train full candidate models on large CIC-DDoS2019 cross-day dataset.

Purpose:
- Train selected candidate models on full model-ready train set.
- Evaluate on full holdout set.
- Save metrics, confusion matrices, models, and attack-type error breakdowns.

Candidates:
- xgboost
- extra_trees
- lightgbm
- soft_voting_lgbm_xgb_et

Recommended first run:
python ml-service/training/09_train_full_candidate_models.py \
  --models xgboost

Then:
python ml-service/training/09_train_full_candidate_models.py \
  --models extra_trees

Then:
python ml-service/training/09_train_full_candidate_models.py \
  --models soft_voting_lgbm_xgb_et
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

from sklearn.ensemble import ExtraTreesClassifier
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

warnings.filterwarnings("ignore")


PROTECTED_COLS = ["raw_label", "attack_type", "label", "source_file", "split"]


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_dataset(path: Path, feature_order: List[str], include_meta: bool = False):
    print(f"[INFO] Loading dataset: {path}")
    df = pd.read_csv(path, low_memory=False)

    missing = [c for c in feature_order if c not in df.columns]
    if missing:
        raise ValueError(f"Missing features in {path}: {missing}")

    if "label" not in df.columns:
        raise ValueError(f"'label' column not found in {path}")

    X = df[feature_order].copy()
    y = df["label"].astype(int).copy()

    X = X.apply(pd.to_numeric, errors="coerce")
    X = X.replace([np.inf, -np.inf], np.nan).fillna(0.0)

    meta = None
    if include_meta:
        keep_meta = [c for c in ["attack_type", "label", "source_file", "split"] if c in df.columns]
        meta = df[keep_meta].copy()

    print(f"[INFO] Shape X={X.shape}, y={y.shape}")
    print("[INFO] Label distribution:")
    print(y.value_counts().to_string())

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


def predict_probability(model, X):
    if hasattr(model, "predict_proba"):
        return model.predict_proba(X)[:, 1]

    preds = model.predict(X)
    return np.asarray(preds, dtype=float)


def evaluate_model(model, X, y, threshold: float = 0.5):
    start = time.perf_counter()
    y_prob = predict_probability(model, X)
    infer_sec = time.perf_counter() - start

    y_pred = (y_prob >= threshold).astype(int)
    metrics, cm = compute_metrics(y, y_pred, y_prob)

    metrics["inference_total_sec"] = float(infer_sec)
    metrics["inference_latency_ms_per_sample"] = float((infer_sec / len(y)) * 1000.0)

    return metrics, cm, y_prob


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


def build_model(model_name: str, random_state: int, n_jobs: int):
    if model_name == "xgboost":
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

    if model_name == "extra_trees":
        return ExtraTreesClassifier(
            n_estimators=300,
            max_depth=None,
            min_samples_split=2,
            min_samples_leaf=1,
            class_weight="balanced",
            random_state=random_state,
            n_jobs=n_jobs,
        )

    if model_name == "lightgbm":
        from lightgbm import LGBMClassifier

        return LGBMClassifier(
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

    raise ValueError(f"Unsupported model_name: {model_name}")


def train_single_candidate(
    model_name: str,
    X_train,
    y_train,
    X_holdout,
    y_holdout,
    holdout_meta,
    feature_order,
    output_dir: Path,
    model_dir: Path,
    threshold: float,
    random_state: int,
    n_jobs: int,
):
    print("\n" + "=" * 90)
    print(f"[INFO] Training full candidate: {model_name}")

    model = build_model(model_name, random_state=random_state, n_jobs=n_jobs)

    start = time.perf_counter()
    model.fit(X_train, y_train)
    training_time_sec = time.perf_counter() - start

    print(f"[INFO] Training completed: {model_name}, sec={training_time_sec:.2f}")

    model_path = model_dir / f"{model_name}.pkl"
    joblib.dump(model, model_path)

    metrics, cm, y_prob = evaluate_model(model, X_holdout, y_holdout, threshold=threshold)

    metrics.update({
        "model": model_name,
        "threshold": threshold,
        "train_rows": int(len(y_train)),
        "holdout_rows": int(len(y_holdout)),
        "feature_count": len(feature_order),
        "training_time_sec": float(training_time_sec),
        "model_path": str(model_path),
    })

    breakdown = attack_type_error_breakdown(holdout_meta, y_holdout, y_prob, threshold=threshold)
    breakdown_path = output_dir / f"{model_name}_full_holdout_attack_type_error_breakdown.csv"
    breakdown.to_csv(breakdown_path, index=False)

    prob_path = output_dir / f"{model_name}_full_holdout_probabilities.npy"
    np.save(prob_path, y_prob)

    print(
        f"[RESULT] {model_name} | "
        f"F1={metrics['f1_score']:.6f} "
        f"Recall={metrics['recall']:.6f} "
        f"FNR={metrics['fnr']:.6f} "
        f"FPR={metrics['fpr']:.6f} "
        f"FP={metrics['fp']} "
        f"FN={metrics['fn']}"
    )

    return metrics, cm, y_prob


def evaluate_soft_voting(
    members: List[str],
    y_probs: Dict[str, np.ndarray],
    y_holdout,
    holdout_meta,
    feature_order,
    output_dir: Path,
    threshold: float,
):
    available = [m for m in members if m in y_probs]
    if len(available) < 2:
        print(f"[WARN] Not enough available members for ensemble: {members}")
        return None, None

    ensemble_name = "soft_voting_" + "_".join(available)

    print("\n" + "=" * 90)
    print(f"[INFO] Evaluating full ensemble: {ensemble_name}")

    probs = np.vstack([y_probs[m] for m in available])
    y_prob = probs.mean(axis=0)

    y_pred = (y_prob >= threshold).astype(int)
    metrics, cm = compute_metrics(y_holdout, y_pred, y_prob)

    metrics.update({
        "model": ensemble_name,
        "threshold": threshold,
        "train_rows": None,
        "holdout_rows": int(len(y_holdout)),
        "feature_count": len(feature_order),
        "training_time_sec": None,
        "inference_total_sec": None,
        "inference_latency_ms_per_sample": None,
        "model_path": "",
        "ensemble_members": ",".join(available),
    })

    breakdown = attack_type_error_breakdown(holdout_meta, y_holdout, y_prob, threshold=threshold)
    breakdown_path = output_dir / f"{ensemble_name}_full_holdout_attack_type_error_breakdown.csv"
    breakdown.to_csv(breakdown_path, index=False)

    prob_path = output_dir / f"{ensemble_name}_full_holdout_probabilities.npy"
    np.save(prob_path, y_prob)

    print(
        f"[RESULT] {ensemble_name} | "
        f"F1={metrics['f1_score']:.6f} "
        f"Recall={metrics['recall']:.6f} "
        f"FNR={metrics['fnr']:.6f} "
        f"FPR={metrics['fpr']:.6f} "
        f"FP={metrics['fp']} "
        f"FN={metrics['fn']}"
    )

    return metrics, cm


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", default="ml-service/datasets/processed/cicddos2019_train_01_12_model_ready.csv")
    parser.add_argument("--holdout", default="ml-service/datasets/processed/cicddos2019_holdout_03_11_model_ready.csv")
    parser.add_argument("--feature-order", default="ml-service/datasets/metadata/model_ready_large/feature_order_all_features.json")
    parser.add_argument("--models", default="xgboost")
    parser.add_argument("--output-dir", default="ml-service/experiments/full_candidate_models")
    parser.add_argument("--model-dir", default="ml-service/models/full_candidate_models")
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

    feature_order = load_json(feature_order_path)

    requested_models = [
        m.strip()
        for m in args.models.split(",")
        if m.strip()
    ]

    valid_single_models = {"xgboost", "extra_trees", "lightgbm"}
    wants_ensemble = "soft_voting_lgbm_xgb_et" in requested_models

    single_models = [m for m in requested_models if m in valid_single_models]

    if wants_ensemble:
        # Ensemble needs probabilities from all members.
        for required in ["lightgbm", "xgboost", "extra_trees"]:
            if required not in single_models:
                single_models.append(required)

    print("[INFO] Requested models:", requested_models)
    print("[INFO] Single models to train:", single_models)
    print("[INFO] Ensemble requested:", wants_ensemble)

    X_train, y_train, _ = load_dataset(train_path, feature_order, include_meta=False)
    X_holdout, y_holdout, holdout_meta = load_dataset(holdout_path, feature_order, include_meta=True)

    metrics_rows = []
    cm_results = {}
    y_probs: Dict[str, np.ndarray] = {}

    for model_name in single_models:
        metrics, cm, y_prob = train_single_candidate(
            model_name=model_name,
            X_train=X_train,
            y_train=y_train,
            X_holdout=X_holdout,
            y_holdout=y_holdout,
            holdout_meta=holdout_meta,
            feature_order=feature_order,
            output_dir=output_dir,
            model_dir=model_dir,
            threshold=args.threshold,
            random_state=args.random_state,
            n_jobs=args.n_jobs,
        )

        metrics_rows.append(metrics)
        cm_results[model_name] = cm
        y_probs[model_name] = y_prob

    if wants_ensemble:
        metrics, cm = evaluate_soft_voting(
            ["lightgbm", "xgboost", "extra_trees"],
            y_probs=y_probs,
            y_holdout=y_holdout,
            holdout_meta=holdout_meta,
            feature_order=feature_order,
            output_dir=output_dir,
            threshold=args.threshold,
        )

        if metrics is not None:
            metrics_rows.append(metrics)
            cm_results[metrics["model"]] = cm

    metrics_df = pd.DataFrame(metrics_rows)
    metrics_df = metrics_df.sort_values(
        ["fnr", "fn", "fpr", "f1_score"],
        ascending=[True, True, True, False],
    )

    metrics_csv = output_dir / "full_candidate_model_metrics.csv"
    metrics_json = output_dir / "full_candidate_model_metrics.json"
    cm_json = output_dir / "full_candidate_confusion_matrices.json"

    metrics_df.to_csv(metrics_csv, index=False)
    write_json(metrics_json, metrics_df.to_dict(orient="records"))
    write_json(cm_json, cm_results)

    write_json(
        output_dir / "full_candidate_model_config.json",
        {
            "train": str(train_path),
            "holdout": str(holdout_path),
            "feature_order": str(feature_order_path),
            "requested_models": requested_models,
            "single_models_trained": single_models,
            "threshold": args.threshold,
            "feature_count": len(feature_order),
        },
    )

    print("\n" + "=" * 90)
    print("[INFO] Full candidate training completed.")
    print(f"[INFO] Metrics CSV: {metrics_csv}")

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
