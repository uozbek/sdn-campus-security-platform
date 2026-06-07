#!/usr/bin/env python3
"""
Aşama 14.4-E — Train Models on Metaheuristic Selected Feature Sets

Bu script HHO, PSO ve GWO ile seçilmiş feature setleri üzerinde LightGBM modeli eğitir
ve baseline_all_features sonucu ile karşılaştırma metrikleri üretir.

Çıktılar:
- selected_feature_model_metrics.csv
- selected_feature_model_metrics.json
- selected_feature_comparison_*.png
- best_selected_model.pkl
"""

import json
import time
from pathlib import Path

import joblib
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
)
from sklearn.model_selection import train_test_split
from lightgbm import LGBMClassifier


PROJECT_ROOT = Path(__file__).resolve().parents[2]

BASELINE_METRICS_PATH = (
    PROJECT_ROOT / "ml-service" / "experiments" / "ml_metrics" / "baseline_model_metrics.csv"
)

FEATURE_SELECTION_DIR = (
    PROJECT_ROOT / "ml-service" / "experiments" / "feature_selection"
)

OUTPUT_METRICS_DIR = (
    PROJECT_ROOT / "ml-service" / "experiments" / "ml_metrics"
)

OUTPUT_FIGURES_DIR = (
    PROJECT_ROOT / "ml-service" / "experiments" / "figures"
)

OUTPUT_MODEL_DIR = (
    PROJECT_ROOT / "ml-service" / "models" / "selected"
)

SELECTED_DATASETS = {
    "hho": FEATURE_SELECTION_DIR / "dataset_selected_hho.csv",
    "pso": FEATURE_SELECTION_DIR / "dataset_selected_pso.csv",
    "gwo": FEATURE_SELECTION_DIR / "dataset_selected_gwo.csv",
}


def calculate_fpr_far(y_true, y_pred):
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()

    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0
    far = (fpr + fnr) / 2.0

    return {
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp),
        "fpr": float(fpr),
        "fnr": float(fnr),
        "far": float(far),
    }


def build_lightgbm(random_state=42):
    return LGBMClassifier(
        boosting_type="gbdt",
        n_estimators=300,
        learning_rate=0.05,
        num_leaves=31,
        class_weight="balanced",
        random_state=random_state,
        n_jobs=-1,
        verbose=-1,
    )


def measure_latency(model, X_test, sample_size=5000, repeat=3):
    if len(X_test) > sample_size:
        X_sample = X_test.sample(n=sample_size, random_state=42)
    else:
        X_sample = X_test

    values = []

    for _ in range(repeat):
        start = time.perf_counter()
        _ = model.predict(X_sample)
        end = time.perf_counter()
        values.append(((end - start) * 1000) / len(X_sample))

    return sum(values) / len(values)


def train_one_dataset(method, dataset_path):
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset bulunamadı: {dataset_path}")

    df = pd.read_csv(dataset_path, low_memory=False)
    df.columns = df.columns.str.strip()

    if "label" not in df.columns:
        raise ValueError(f"label kolonu bulunamadı: {dataset_path}")

    y = df["label"].astype(int)
    X = df.drop(columns=["label"])

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.30,
        random_state=42,
        stratify=y,
    )

    model = build_lightgbm(random_state=42)

    start = time.perf_counter()
    model.fit(X_train, y_train)
    train_time = time.perf_counter() - start

    y_pred = model.predict(X_test)

    if hasattr(model, "predict_proba"):
        y_score = model.predict_proba(X_test)[:, 1]
    else:
        y_score = y_pred

    cm_stats = calculate_fpr_far(y_test, y_pred)

    try:
        auc = roc_auc_score(y_test, y_score)
    except Exception:
        auc = 0.0

    latency = measure_latency(model, X_test)

    result = {
        "method": method,
        "model": "lightgbm",
        "dataset_path": str(dataset_path),
        "feature_count": int(X.shape[1]),
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision": float(precision_score(y_test, y_pred, zero_division=0)),
        "recall": float(recall_score(y_test, y_pred, zero_division=0)),
        "f1_score": float(f1_score(y_test, y_pred, zero_division=0)),
        "auc": float(auc),
        "fpr": float(cm_stats["fpr"]),
        "fnr": float(cm_stats["fnr"]),
        "far": float(cm_stats["far"]),
        "tn": cm_stats["tn"],
        "fp": cm_stats["fp"],
        "fn": cm_stats["fn"],
        "tp": cm_stats["tp"],
        "training_time_sec": float(train_time),
        "inference_latency_ms_per_sample": float(latency),
        "train_rows": int(X_train.shape[0]),
        "test_rows": int(X_test.shape[0]),
    }

    return result, model, X.columns.tolist()


def load_baseline_lightgbm_result():
    if not BASELINE_METRICS_PATH.exists():
        return None

    df = pd.read_csv(BASELINE_METRICS_PATH)

    if "model" not in df.columns:
        return None

    lightgbm_rows = df[df["model"] == "lightgbm"]

    if lightgbm_rows.empty:
        return None

    row = lightgbm_rows.iloc[0]

    return {
        "method": "baseline_all_features",
        "model": "lightgbm",
        "dataset_path": "ml-service/datasets/processed/cicddos2019_syn_udp_udplag_reduced.csv",
        "feature_count": int(row["feature_count"]),
        "accuracy": float(row["accuracy"]),
        "precision": float(row["precision"]),
        "recall": float(row["recall"]),
        "f1_score": float(row["f1_score"]),
        "auc": float(row["auc"]),
        "fpr": float(row["fpr"]),
        "fnr": float(row["fnr"]),
        "far": float(row["far"]),
        "tn": int(row["tn"]),
        "fp": int(row["fp"]),
        "fn": int(row["fn"]),
        "tp": int(row["tp"]),
        "training_time_sec": float(row["training_time_sec"]),
        "inference_latency_ms_per_sample": float(row["inference_latency_ms_per_sample"]),
        "train_rows": int(row["train_rows"]),
        "test_rows": int(row["test_rows"]),
    }


def save_bar(df, metric, filename, title, ylabel, ascending=False):
    plot_df = df.sort_values(by=metric, ascending=ascending)

    plt.figure(figsize=(9, 5))
    plt.bar(plot_df["method"], plot_df[metric])
    plt.xlabel("Feature Selection Method")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.xticks(rotation=25, ha="right")
    plt.tight_layout()
    plt.savefig(OUTPUT_FIGURES_DIR / filename, dpi=300)
    plt.close()


def main():
    OUTPUT_METRICS_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_MODEL_DIR.mkdir(parents=True, exist_ok=True)

    results = []

    baseline = load_baseline_lightgbm_result()
    if baseline:
        results.append(baseline)

    best_model = None
    best_method = None
    best_feature_order = None
    best_score_tuple = None

    for method, dataset_path in SELECTED_DATASETS.items():
        print(f"[INFO] Training selected feature model: {method}")
        result, model, feature_order = train_one_dataset(method, dataset_path)

        print(
            f"[RESULT] {method} | "
            f"features={result['feature_count']} "
            f"F1={result['f1_score']:.6f} "
            f"AUC={result['auc']:.6f} "
            f"FAR={result['far']:.6f} "
            f"FPR={result['fpr']:.6f}"
        )

        results.append(result)

        # Seçim kriteri: yüksek F1, düşük FAR, yüksek AUC, az feature
        score_tuple = (
            result["f1_score"],
            -result["far"],
            result["auc"],
            -result["feature_count"],
        )

        if best_score_tuple is None or score_tuple > best_score_tuple:
            best_score_tuple = score_tuple
            best_model = model
            best_method = method
            best_feature_order = feature_order

    df = pd.DataFrame(results)
    df.sort_values(
        by=["f1_score", "far", "auc", "feature_count"],
        ascending=[False, True, False, True],
        inplace=True,
    )

    metrics_csv = OUTPUT_METRICS_DIR / "selected_feature_model_metrics.csv"
    metrics_json = OUTPUT_METRICS_DIR / "selected_feature_model_metrics.json"

    df.to_csv(metrics_csv, index=False)

    payload = {
        "description": "Comparison of baseline all-feature LightGBM and metaheuristic-selected feature LightGBM models.",
        "selection_methods": list(SELECTED_DATASETS.keys()),
        "best_selected_method": best_method,
        "results": results,
    }

    with metrics_json.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    save_bar(
        df,
        metric="feature_count",
        filename="selected_feature_count_comparison.png",
        title="Selected Feature Count Comparison",
        ylabel="Feature Count",
        ascending=True,
    )

    save_bar(
        df,
        metric="f1_score",
        filename="selected_feature_f1_comparison.png",
        title="Selected Feature Models F1-Score Comparison",
        ylabel="F1-Score",
        ascending=False,
    )

    save_bar(
        df,
        metric="far",
        filename="selected_feature_far_comparison.png",
        title="Selected Feature Models FAR Comparison",
        ylabel="FAR",
        ascending=True,
    )

    save_bar(
        df,
        metric="fpr",
        filename="selected_feature_fpr_comparison.png",
        title="Selected Feature Models FPR Comparison",
        ylabel="FPR",
        ascending=True,
    )

    save_bar(
        df,
        metric="inference_latency_ms_per_sample",
        filename="selected_feature_latency_comparison.png",
        title="Selected Feature Models Inference Latency Comparison",
        ylabel="ms/sample",
        ascending=True,
    )

    if best_model is not None:
        joblib.dump(best_model, OUTPUT_MODEL_DIR / "best_selected_model.pkl")

        with (OUTPUT_MODEL_DIR / "feature_order.json").open("w", encoding="utf-8") as f:
            json.dump(best_feature_order, f, indent=2, ensure_ascii=False)

        metadata = {
            "best_selected_method": best_method,
            "model": "lightgbm",
            "feature_count": len(best_feature_order),
            "metrics_csv": str(metrics_csv),
            "metrics_json": str(metrics_json),
            "selection_stage": "metaheuristic_feature_selection",
        }

        with (OUTPUT_MODEL_DIR / "model_metadata.json").open("w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

    print("[INFO] Metrics CSV:", metrics_csv)
    print("[INFO] Metrics JSON:", metrics_json)
    print("[INFO] Best selected method:", best_method)
    print("[INFO] Best selected model dir:", OUTPUT_MODEL_DIR)


if __name__ == "__main__":
    main()
