#!/usr/bin/env python3
"""
Aşama 14.4-A — Baseline Model Training

Bu script, feature selection uygulanmadan önce reduced CIC-DDoS2019 dataset üzerinde
temel ML modellerini eğitir ve karşılaştırmalı metrikler üretir.

Üretilen metrikler:
- Accuracy
- Precision
- Recall
- F1-Score
- AUC
- FPR
- FAR
- Training time
- Inference latency

Örnek kullanım:

python ml-service/training/04_train_models.py \
  --input ml-service/datasets/processed/cicddos2019_syn_udp_udplag_reduced.csv \
  --metrics-output ml-service/experiments/ml_metrics/baseline_model_metrics.csv \
  --metrics-json ml-service/experiments/ml_metrics/baseline_model_metrics.json \
  --confusion-json ml-service/experiments/ml_metrics/baseline_confusion_matrices.json \
  --figures-dir ml-service/experiments/figures \
  --model-output-dir ml-service/models/baseline \
  --test-size 0.30 \
  --random-state 42
"""

import argparse
import json
import time
import re
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

import matplotlib.pyplot as plt

from sklearn.ensemble import (
    RandomForestClassifier,
    ExtraTreesClassifier,
    GradientBoostingClassifier,
)
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    roc_curve,
    confusion_matrix,
    classification_report,
)
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from lightgbm import LGBMClassifier
from xgboost import XGBClassifier

def sanitize_feature_name(name):
    """
    LightGBM özel JSON karakterlerini feature isimlerinde kabul etmeyebilir.
    Bu nedenle tüm feature isimlerini güvenli hale getiriyoruz.

    Örnek:
    'Flow Bytes/s'  -> 'Flow_Bytes_s'
    'Bwd Packets/s' -> 'Bwd_Packets_s'
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
    DataFrame kolonlarını güvenli hale getirir.
    Aynı isme dönüşen kolonlar olursa sonuna sıra numarası ekler.
    Mapping döndürür:
      original_name -> sanitized_name
    """

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
    """
    Binary classification için FPR ve FAR hesaplar.

    Bu projede:
    0 = BENIGN
    1 = ATTACK

    Confusion matrix:
              Pred 0   Pred 1
    True 0      TN       FP
    True 1      FN       TP

    FPR = FP / (FP + TN)
    FNR = FN / (FN + TP)
    FAR = (FPR + FNR) / 2
    """

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


def get_models(random_state):
    """
    Baseline model sözlüğü.

    Not:
    - LogisticRegression ve MLP için StandardScaler kullanacağız.
    - Tree tabanlı modeller için scaling şart değildir.
    """

    models = {
        "logistic_regression": Pipeline(
            steps=[
                ("scaler", StandardScaler()),
                (
                    "model",
                    LogisticRegression(
                        max_iter=1000,
                        class_weight="balanced",
                        n_jobs=-1,
                        random_state=random_state,
                    ),
                ),
            ]
        ),

        "random_forest": RandomForestClassifier(
            n_estimators=200,
            max_depth=None,
            class_weight="balanced",
            random_state=random_state,
            n_jobs=-1,
        ),

        "extra_trees": ExtraTreesClassifier(
            n_estimators=200,
            max_depth=None,
            class_weight="balanced",
            random_state=random_state,
            n_jobs=-1,
        ),

        "gradient_boosting": GradientBoostingClassifier(
            n_estimators=150,
            learning_rate=0.05,
            max_depth=3,
            random_state=random_state,
        ),

        "lightgbm": LGBMClassifier(
            boosting_type="gbdt",
            n_estimators=300,
            learning_rate=0.05,
            num_leaves=31,
            class_weight="balanced",
            random_state=random_state,
            n_jobs=-1,
        ),

        "xgboost": XGBClassifier(
            n_estimators=300,
            learning_rate=0.05,
            max_depth=6,
            subsample=0.9,
            colsample_bytree=0.9,
            objective="binary:logistic",
            eval_metric="logloss",
            random_state=random_state,
            n_jobs=-1,
        ),

        "mlp": Pipeline(
            steps=[
                ("scaler", StandardScaler()),
                (
                    "model",
                    MLPClassifier(
                        hidden_layer_sizes=(64, 32),
                        activation="relu",
                        solver="adam",
                        alpha=0.0001,
                        batch_size=256,
                        learning_rate_init=0.001,
                        max_iter=100,
                        random_state=random_state,
                        early_stopping=True,
                    ),
                ),
            ]
        ),
    }

    return models


def get_prediction_scores(model, X_test):
    """
    ROC/AUC için pozitif sınıf olasılığı döndürür.
    Model predict_proba desteklemiyorsa decision_function fallback denenir.
    """

    if hasattr(model, "predict_proba"):
        return model.predict_proba(X_test)[:, 1]

    if hasattr(model, "decision_function"):
        scores = model.decision_function(X_test)
        min_score = np.min(scores)
        max_score = np.max(scores)

        if max_score - min_score == 0:
            return np.zeros_like(scores, dtype=float)

        return (scores - min_score) / (max_score - min_score)

    # En son fallback: sınıf tahmini
    return model.predict(X_test)


def measure_inference_latency(model, X_test, repeat=3, sample_size=5000):
    """
    Ortalama örnek başına inference latency hesaplar.

    sample_size büyük datasetlerde ölçümü hızlandırmak için kullanılır.
    """

    if len(X_test) > sample_size:
        X_sample = X_test.sample(n=sample_size, random_state=42)
    else:
        X_sample = X_test

    latencies = []

    for _ in range(repeat):
        start = time.perf_counter()
        _ = model.predict(X_sample)
        end = time.perf_counter()

        total_ms = (end - start) * 1000
        per_sample_ms = total_ms / len(X_sample)
        latencies.append(per_sample_ms)

    return float(np.mean(latencies))


def save_roc_curve(roc_data, figures_dir):
    plt.figure(figsize=(8, 6))

    for model_name, data in roc_data.items():
        plt.plot(
            data["fpr"],
            data["tpr"],
            label=f"{model_name} (AUC={data['auc']:.4f})"
        )

    plt.plot([0, 1], [0, 1], linestyle="--", label="Random")
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("Baseline Models ROC Curve")
    plt.legend()
    plt.tight_layout()

    output_path = figures_dir / "baseline_roc_curve.png"
    plt.savefig(output_path, dpi=300)
    plt.close()

    return output_path


def save_bar_chart(metrics_df, metric_name, figures_dir, output_filename, title, ylabel):
    plot_df = metrics_df.sort_values(by=metric_name, ascending=False)

    plt.figure(figsize=(9, 5))
    plt.bar(plot_df["model"], plot_df[metric_name])
    plt.xlabel("Model")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()

    output_path = figures_dir / output_filename
    plt.savefig(output_path, dpi=300)
    plt.close()

    return output_path

def load_dataset(input_path):
    input_path = Path(input_path)

    if not input_path.exists():
        raise FileNotFoundError(f"Dataset bulunamadı: {input_path}")

    df = pd.read_csv(input_path, low_memory=False)
    df.columns = df.columns.str.strip()

    if "label" not in df.columns:
        raise ValueError("Dataset içinde 'label' kolonu bulunamadı.")

    y = df["label"].astype(int)
    X = df.drop(columns=["label"])

    # LightGBM/XGBoost uyumluluğu için feature isimlerini temizle
    X, feature_name_mapping = sanitize_dataframe_columns(X)

    # Tüm feature'ların numeric olduğundan emin olalım
    non_numeric = [
        col for col in X.columns
        if not pd.api.types.is_numeric_dtype(X[col])
    ]

    if non_numeric:
        raise ValueError(
            "Dataset içinde sayısal olmayan feature var. "
            f"Lütfen önce feature reduction/cleaning kontrol edin: {non_numeric}"
        )

    return X, y, feature_name_mapping

def train_and_evaluate(
    input_path,
    metrics_output,
    metrics_json,
    confusion_json,
    figures_dir,
    model_output_dir,
    test_size,
    random_state
):
    input_path = Path(input_path)
    metrics_output = Path(metrics_output)
    metrics_json = Path(metrics_json)
    confusion_json = Path(confusion_json)
    figures_dir = Path(figures_dir)
    model_output_dir = Path(model_output_dir)

    metrics_output.parent.mkdir(parents=True, exist_ok=True)
    metrics_json.parent.mkdir(parents=True, exist_ok=True)
    confusion_json.parent.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)
    model_output_dir.mkdir(parents=True, exist_ok=True)

    print(f"[INFO] Dataset okunuyor: {input_path}")
    X, y, feature_name_mapping = load_dataset(input_path)

    print(f"[INFO] Dataset shape: X={X.shape}, y={y.shape}")
    print("[INFO] Label distribution:")
    print(y.value_counts())

    feature_order = X.columns.tolist()
    feature_name_mapping_path = model_output_dir / "feature_name_mapping.json"

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=random_state,
        stratify=y,
    )

    print(f"[INFO] Train shape: {X_train.shape}")
    print(f"[INFO] Test shape : {X_test.shape}")

    models = get_models(random_state=random_state)

    results = []
    confusion_results = {}
    classification_reports = {}
    roc_data = {}

    best_model_name = None
    best_model = None
    best_f1 = -1.0

    for model_name, model in models.items():
        print(f"\n[INFO] Eğitim başladı: {model_name}")

        train_start = time.perf_counter()
        model.fit(X_train, y_train)
        train_end = time.perf_counter()

        training_time_sec = train_end - train_start

        print(f"[INFO] Eğitim tamamlandı: {model_name} ({training_time_sec:.2f} sn)")

        y_pred = model.predict(X_test)
        y_score = get_prediction_scores(model, X_test)

        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, zero_division=0)
        recall = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)

        try:
            auc = roc_auc_score(y_test, y_score)
        except ValueError:
            auc = 0.0

        cm_stats = calculate_fpr_far(y_test, y_pred)

        inference_latency_ms = measure_inference_latency(
            model=model,
            X_test=X_test,
            repeat=3,
            sample_size=5000,
        )

        result = {
            "model": model_name,
            "accuracy": float(accuracy),
            "precision": float(precision),
            "recall": float(recall),
            "f1_score": float(f1),
            "auc": float(auc),
            "fpr": float(cm_stats["fpr"]),
            "fnr": float(cm_stats["fnr"]),
            "far": float(cm_stats["far"]),
            "tn": cm_stats["tn"],
            "fp": cm_stats["fp"],
            "fn": cm_stats["fn"],
            "tp": cm_stats["tp"],
            "training_time_sec": float(training_time_sec),
            "inference_latency_ms_per_sample": float(inference_latency_ms),
            "feature_count": int(X.shape[1]),
            "train_rows": int(X_train.shape[0]),
            "test_rows": int(X_test.shape[0]),
        }

        results.append(result)

        confusion_results[model_name] = {
            "labels": [0, 1],
            "matrix": confusion_matrix(y_test, y_pred, labels=[0, 1]).tolist(),
            "tn": cm_stats["tn"],
            "fp": cm_stats["fp"],
            "fn": cm_stats["fn"],
            "tp": cm_stats["tp"],
        }

        classification_reports[model_name] = classification_report(
            y_test,
            y_pred,
            labels=[0, 1],
            target_names=["BENIGN", "ATTACK"],
            output_dict=True,
            zero_division=0,
        )

        try:
            fpr_values, tpr_values, _ = roc_curve(y_test, y_score)
            roc_data[model_name] = {
                "fpr": fpr_values,
                "tpr": tpr_values,
                "auc": auc,
            }
        except ValueError:
            pass

        print(
            f"[RESULT] {model_name} | "
            f"F1={f1:.6f} AUC={auc:.6f} FAR={cm_stats['far']:.6f} "
            f"FPR={cm_stats['fpr']:.6f} latency={inference_latency_ms:.6f} ms/sample"
        )

        if f1 > best_f1:
            best_f1 = f1
            best_model_name = model_name
            best_model = model

    metrics_df = pd.DataFrame(results)
    metrics_df.sort_values(
        by=["f1_score", "far", "auc"],
        ascending=[False, True, False],
        inplace=True,
    )

    metrics_df.to_csv(metrics_output, index=False)

    metrics_payload = {
        "input_path": str(input_path),
        "test_size": float(test_size),
        "random_state": int(random_state),
        "feature_count": int(X.shape[1]),
        "feature_order": feature_order,
    "feature_name_mapping": feature_name_mapping,
        "best_model": best_model_name,
        "best_f1_score": float(best_f1),
        "results": results,
        "classification_reports": classification_reports,
    }

    with metrics_json.open("w", encoding="utf-8") as f:
        json.dump(metrics_payload, f, indent=2, ensure_ascii=False)

    with confusion_json.open("w", encoding="utf-8") as f:
        json.dump(confusion_results, f, indent=2, ensure_ascii=False)

    # ROC ve karşılaştırma grafikleri
    if roc_data:
        save_roc_curve(roc_data, figures_dir)

    save_bar_chart(
        metrics_df,
        metric_name="f1_score",
        figures_dir=figures_dir,
        output_filename="baseline_f1_comparison.png",
        title="Baseline Models F1-Score Comparison",
        ylabel="F1-Score",
    )

    # FAR ve FPR düşük olması daha iyi olduğu için grafikte ascending sıralamak daha anlamlı olabilir.
    far_df = metrics_df.sort_values(by="far", ascending=True)

    plt.figure(figsize=(9, 5))
    plt.bar(far_df["model"], far_df["far"])
    plt.xlabel("Model")
    plt.ylabel("FAR")
    plt.title("Baseline Models FAR Comparison")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.savefig(figures_dir / "baseline_far_comparison.png", dpi=300)
    plt.close()

    fpr_df = metrics_df.sort_values(by="fpr", ascending=True)

    plt.figure(figsize=(9, 5))
    plt.bar(fpr_df["model"], fpr_df["fpr"])
    plt.xlabel("Model")
    plt.ylabel("FPR")
    plt.title("Baseline Models FPR Comparison")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.savefig(figures_dir / "baseline_fpr_comparison.png", dpi=300)
    plt.close()

    # En iyi modeli baseline alanına kaydet
    if best_model is not None:
        model_path = model_output_dir / "best_model.pkl"
        joblib.dump(best_model, model_path)

        with (model_output_dir / "feature_order.json").open("w", encoding="utf-8") as f:
            json.dump(feature_order, f, indent=2, ensure_ascii=False)
        with (model_output_dir / "feature_name_mapping.json").open("w", encoding="utf-8") as f:
             json.dump(feature_name_mapping, f, indent=2, ensure_ascii=False)
        with (model_output_dir / "label_mapping.json").open("w", encoding="utf-8") as f:
            json.dump({"BENIGN": 0, "ATTACK": 1}, f, indent=2, ensure_ascii=False)

        metadata = {
            "model_name": best_model_name,
            "task": "binary_ddos_detection",
            "dataset": str(input_path),
            "feature_count": int(X.shape[1]),
            "test_size": float(test_size),
            "random_state": int(random_state),
            "selection_stage": "baseline_no_metaheuristic_feature_selection",
            "best_f1_score": float(best_f1),
            "metrics_csv": str(metrics_output),
            "metrics_json": str(metrics_json),
            "feature_order_file": "feature_order.json",
            "feature_name_mapping_file": "feature_name_mapping.json"
        }

        with (model_output_dir / "model_metadata.json").open("w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        print(f"\n[INFO] En iyi baseline model: {best_model_name}")
        print(f"[INFO] Model kaydedildi: {model_path}")

    print(f"\n[INFO] Metrics CSV kaydedildi: {metrics_output}")
    print(f"[INFO] Metrics JSON kaydedildi: {metrics_json}")
    print(f"[INFO] Confusion matrices kaydedildi: {confusion_json}")
    print(f"[INFO] Figures kaydedildi: {figures_dir}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Train baseline ML models for CIC-DDoS2019 IDS pipeline."
    )

    parser.add_argument(
        "--input",
        required=True,
        help="Reduced dataset CSV yolu."
    )

    parser.add_argument(
        "--metrics-output",
        required=True,
        help="CSV metrik çıktı yolu."
    )

    parser.add_argument(
        "--metrics-json",
        required=True,
        help="JSON metrik çıktı yolu."
    )

    parser.add_argument(
        "--confusion-json",
        required=True,
        help="Confusion matrix JSON çıktı yolu."
    )

    parser.add_argument(
        "--figures-dir",
        required=True,
        help="Grafiklerin kaydedileceği klasör."
    )

    parser.add_argument(
        "--model-output-dir",
        required=True,
        help="En iyi baseline modelin kaydedileceği klasör."
    )

    parser.add_argument(
        "--test-size",
        type=float,
        default=0.30,
        help="Test oranı. Varsayılan: 0.30"
    )

    parser.add_argument(
        "--random-state",
        type=int,
        default=42,
        help="Random seed."
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    train_and_evaluate(
        input_path=args.input,
        metrics_output=args.metrics_output,
        metrics_json=args.metrics_json,
        confusion_json=args.confusion_json,
        figures_dir=args.figures_dir,
        model_output_dir=args.model_output_dir,
        test_size=args.test_size,
        random_state=args.random_state,
    )
