#!/usr/bin/env python3
"""
Aşama 14.4-G — Balanced Validation for PSO-Selected Features

Bu script, PSO ile seçilmiş 13 feature setini kullanarak üç veri dağılımında
LightGBM modeli eğitir:

- pilot_imbalanced
- balanced_1to1
- balanced_1to5

Önemli:
CIC-DDoS2019 / CICFlowMeter kolon adlarında boşluk, '/', ':' gibi karakterler
olduğu için LightGBM-safe feature name sanitization zorunludur.
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
    "pilot_imbalanced_pso": PROJECT_ROOT / "ml-service/datasets/processed/cicddos2019_syn_udp_udplag_reduced.csv",
    "balanced_1to1_pso": PROJECT_ROOT / "ml-service/datasets/processed/cicddos2019_syn_udp_udplag_balanced_1to1.csv",
    "balanced_1to5_pso": PROJECT_ROOT / "ml-service/datasets/processed/cicddos2019_syn_udp_udplag_balanced_1to5.csv",
}

PSO_FEATURES_PATH = (
    PROJECT_ROOT
    / "ml-service"
    / "experiments"
    / "feature_selection"
    / "selected_features_pso.json"
)

OUTPUT_METRICS_DIR = PROJECT_ROOT / "ml-service/experiments/ml_metrics"
OUTPUT_FIGURES_DIR = PROJECT_ROOT / "ml-service/experiments/figures"


def sanitize_feature_name(name):
    name = str(name).strip()
    name = re.sub(r"[^A-Za-z0-9_]+", "_", name)
    name = re.sub(r"_+", "_", name)
    name = name.strip("_")
    return name if name else "feature"


def sanitize_dataframe_columns(df):
    used = {}
    mapping = {}
    new_columns = []

    for col in df.columns:
        clean = sanitize_feature_name(col)

        if clean in used:
            used[clean] += 1
            clean_unique = f"{clean}_{used[clean]}"
        else:
            used[clean] = 0
            clean_unique = clean

        mapping[col] = clean_unique
        new_columns.append(clean_unique)

    df = df.copy()
    df.columns = new_columns

    return df, mapping


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


def load_pso_features():
    if not PSO_FEATURES_PATH.exists():
        raise FileNotFoundError(f"PSO selected feature file not found: {PSO_FEATURES_PATH}")

    with PSO_FEATURES_PATH.open("r", encoding="utf-8") as f:
        features = json.load(f)

    return features


def train_dataset(name, path, selected_features):
    if not path.exists():
        raise FileNotFoundError(f"Dataset bulunamadı: {path}")

    df = pd.read_csv(path, low_memory=False)
    df.columns = df.columns.str.strip()

    if "label" not in df.columns:
        raise ValueError(f"label kolonu bulunamadı: {path}")

    y = df["label"].astype(int)
    X_raw = df.drop(columns=["label"])

    # LightGBM-safe kolon isimleri
    X, feature_name_mapping = sanitize_dataframe_columns(X_raw)

    missing = [f for f in selected_features if f not in X.columns]
    if missing:
        raise ValueError(
            f"{name} datasetinde PSO feature'ları eksik: {missing}. "
            f"Mevcut ilk 20 kolon: {list(X.columns)[:20]}"
        )

    X = X[selected_features].copy()

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

    return {
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

    selected_features = load_pso_features()

    print("[INFO] PSO selected feature count:", len(selected_features))
    print("[INFO] PSO selected features:", selected_features)

    results = []

    for name, path in DATASETS.items():
        print("[INFO] Training:", name)
        result = train_dataset(name, path, selected_features)

        print(
            f"[RESULT] {name} | "
            f"rows={result['rows']} "
            f"features={result['feature_count']} "
            f"F1={result['f1_score']:.6f} "
            f"AUC={result['auc']:.6f} "
            f"FPR={result['fpr']:.6f} "
            f"FAR={result['far']:.6f}"
        )

        results.append(result)

    df = pd.DataFrame(results)

    csv_path = OUTPUT_METRICS_DIR / "balanced_validation_pso_lightgbm_metrics.csv"
    json_path = OUTPUT_METRICS_DIR / "balanced_validation_pso_lightgbm_metrics.json"

    df.to_csv(csv_path, index=False)

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(
            {
                "description": "LightGBM validation using PSO-selected features on imbalanced, balanced 1:1 and moderate 1:5 CIC-DDoS2019 subsets.",
                "selected_features": selected_features,
                "results": results,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    save_bar(
        df,
        "f1_score",
        "balanced_validation_pso_f1_comparison.png",
        "Balanced Validation PSO-Selected F1-Score Comparison",
        "F1-Score",
        ascending=False,
    )

    save_bar(
        df,
        "far",
        "balanced_validation_pso_far_comparison.png",
        "Balanced Validation PSO-Selected FAR Comparison",
        "FAR",
        ascending=True,
    )

    save_bar(
        df,
        "fpr",
        "balanced_validation_pso_fpr_comparison.png",
        "Balanced Validation PSO-Selected FPR Comparison",
        "FPR",
        ascending=True,
    )

    save_bar(
        df,
        "auc",
        "balanced_validation_pso_auc_comparison.png",
        "Balanced Validation PSO-Selected AUC Comparison",
        "AUC",
        ascending=False,
    )

    print("[INFO] Metrics CSV:", csv_path)
    print("[INFO] Metrics JSON:", json_path)


if __name__ == "__main__":
    main()
