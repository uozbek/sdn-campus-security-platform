#!/usr/bin/env python3
"""
Aşama 14.4-G — Balanced Dataset Validation with LightGBM

Bu script üç veri dağılımını karşılaştırır:
- imbalanced pilot reduced dataset
- balanced 1:1 dataset
- moderate imbalance 1:5 dataset

Her biri üzerinde LightGBM eğitir ve aynı metrikleri üretir.
"""

import json
import time
import re
from pathlib import Path

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from lightgbm import LGBMClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATASETS = {
    "pilot_imbalanced": PROJECT_ROOT / "ml-service/datasets/processed/cicddos2019_syn_udp_udplag_reduced.csv",
    "balanced_1to1": PROJECT_ROOT / "ml-service/datasets/processed/cicddos2019_syn_udp_udplag_balanced_1to1.csv",
    "balanced_1to5": PROJECT_ROOT / "ml-service/datasets/processed/cicddos2019_syn_udp_udplag_balanced_1to5.csv",
}

OUTPUT_METRICS_DIR = PROJECT_ROOT / "ml-service/experiments/ml_metrics"
OUTPUT_FIGURES_DIR = PROJECT_ROOT / "ml-service/experiments/figures"

def sanitize_feature_name(name):
    """
    LightGBM özel JSON karakterleri içeren feature isimlerini kabul etmeyebilir.
    Örnek:
    'Flow Bytes/s'  -> 'Flow_Bytes_s'
    'Down/Up Ratio' -> 'Down_Up_Ratio'
    """

    name = str(name).strip()
    name = re.sub(r"[^A-Za-z0-9_]+", "_", name)
    name = re.sub(r"_+", "_", name)
    name = name.strip("_")

    if not name:
        name = "feature"

    return name


def sanitize_dataframe_columns(df):
    """
    DataFrame kolonlarını LightGBM uyumlu hale getirir.
    Aynı isme dönüşen kolonlar olursa sonuna sıra numarası ekler.
    """

    used = {}
    new_columns = []

    for col in df.columns:
        clean = sanitize_feature_name(col)

        if clean in used:
            used[clean] += 1
            clean_unique = f"{clean}_{used[clean]}"
        else:
            used[clean] = 0
            clean_unique = clean

        new_columns.append(clean_unique)

    df = df.copy()
    df.columns = new_columns

    return df

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


def build_model():
    return LGBMClassifier(
        boosting_type="gbdt",
        n_estimators=300,
        learning_rate=0.05,
        num_leaves=31,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
        verbose=-1,
    )


def train_dataset(name, path):
    if not path.exists():
        raise FileNotFoundError(f"Dataset bulunamadı: {path}")

    df = pd.read_csv(path, low_memory=False)
    df.columns = df.columns.str.strip()

    if "label" not in df.columns:
        raise ValueError(f"label kolonu bulunamadı: {path}")

    y = df["label"].astype(int)
    X = df.drop(columns=["label"])
    # LightGBM uyumluluğu için feature isimlerini güvenli hale getir
    X = sanitize_dataframe_columns(X)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.30,
        random_state=42,
        stratify=y,
    )

    model = build_model()

    start = time.perf_counter()
    model.fit(X_train, y_train)
    training_time = time.perf_counter() - start

    start = time.perf_counter()
    y_pred = model.predict(X_test)
    inference_total = time.perf_counter() - start

    if hasattr(model, "predict_proba"):
        y_score = model.predict_proba(X_test)[:, 1]
    else:
        y_score = y_pred

    try:
        auc = roc_auc_score(y_test, y_score)
    except Exception:
        auc = 0.0

    cm = calculate_fpr_far(y_test, y_pred)

    result = {
        "dataset": name,
        "dataset_path": str(path),
        "rows": int(df.shape[0]),
        "feature_count": int(X.shape[1]),
        "class_0_benign": int((y == 0).sum()),
        "class_1_attack": int((y == 1).sum()),
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision": float(precision_score(y_test, y_pred, zero_division=0)),
        "recall": float(recall_score(y_test, y_pred, zero_division=0)),
        "f1_score": float(f1_score(y_test, y_pred, zero_division=0)),
        "auc": float(auc),
        "fpr": cm["fpr"],
        "fnr": cm["fnr"],
        "far": cm["far"],
        "tn": cm["tn"],
        "fp": cm["fp"],
        "fn": cm["fn"],
        "tp": cm["tp"],
        "training_time_sec": float(training_time),
        "inference_latency_ms_per_sample": float((inference_total * 1000) / len(X_test)),
        "train_rows": int(X_train.shape[0]),
        "test_rows": int(X_test.shape[0]),
    }

    print(
        f"[RESULT] {name} | "
        f"rows={result['rows']} "
        f"features={result['feature_count']} "
        f"F1={result['f1_score']:.6f} "
        f"AUC={result['auc']:.6f} "
        f"FPR={result['fpr']:.6f} "
        f"FAR={result['far']:.6f}"
    )

    return result


def save_bar(df, metric, filename, title, ylabel, ascending=False):
    plot_df = df.sort_values(by=metric, ascending=ascending)

    plt.figure(figsize=(8, 5))
    plt.bar(plot_df["dataset"], plot_df[metric])
    plt.xlabel("Dataset")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.xticks(rotation=20, ha="right")
    plt.tight_layout()
    plt.savefig(OUTPUT_FIGURES_DIR / filename, dpi=300)
    plt.close()


def main():
    OUTPUT_METRICS_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    results = []

    for name, path in DATASETS.items():
        print("[INFO] Training:", name)
        results.append(train_dataset(name, path))

    df = pd.DataFrame(results)

    csv_path = OUTPUT_METRICS_DIR / "balanced_validation_lightgbm_metrics.csv"
    json_path = OUTPUT_METRICS_DIR / "balanced_validation_lightgbm_metrics.json"

    df.to_csv(csv_path, index=False)

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(
            {
                "description": "LightGBM validation on imbalanced, balanced 1:1 and moderate 1:5 CIC-DDoS2019 subsets.",
                "results": results,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    save_bar(
        df,
        "f1_score",
        "balanced_validation_f1_comparison.png",
        "Balanced Validation F1-Score Comparison",
        "F1-Score",
        ascending=False,
    )

    save_bar(
        df,
        "far",
        "balanced_validation_far_comparison.png",
        "Balanced Validation FAR Comparison",
        "FAR",
        ascending=True,
    )

    save_bar(
        df,
        "fpr",
        "balanced_validation_fpr_comparison.png",
        "Balanced Validation FPR Comparison",
        "FPR",
        ascending=True,
    )

    save_bar(
        df,
        "auc",
        "balanced_validation_auc_comparison.png",
        "Balanced Validation AUC Comparison",
        "AUC",
        ascending=False,
    )

    print("[INFO] Metrics CSV:", csv_path)
    print("[INFO] Metrics JSON:", json_path)


if __name__ == "__main__":
    main()
