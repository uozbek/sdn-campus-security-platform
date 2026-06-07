#!/usr/bin/env python3

from pathlib import Path
import json

import pandas as pd
import matplotlib.pyplot as plt


PROJECT_ROOT = Path(__file__).resolve().parents[2]

METRICS_PATH = PROJECT_ROOT / "ml-service" / "experiments" / "ml_metrics" / "baseline_model_metrics.csv"
CONFUSION_PATH = PROJECT_ROOT / "ml-service" / "experiments" / "ml_metrics" / "baseline_confusion_matrices.json"
FIGURES_DIR = PROJECT_ROOT / "ml-service" / "experiments" / "figures"


def save_bar_chart(df, metric, filename, title, ylabel, ascending=False):
    plot_df = df.sort_values(by=metric, ascending=ascending)

    plt.figure(figsize=(10, 5))
    plt.bar(plot_df["model"], plot_df[metric])
    plt.xlabel("Model")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()

    output_path = FIGURES_DIR / filename
    plt.savefig(output_path, dpi=300)
    plt.close()

    print(f"[INFO] Saved: {output_path}")


def save_confusion_matrix_chart(confusion_data, model_name):
    if model_name not in confusion_data:
        print(f"[WARN] Confusion matrix not found for {model_name}")
        return

    matrix = confusion_data[model_name]["matrix"]

    fig, ax = plt.subplots(figsize=(5, 4))
    im = ax.imshow(matrix)

    ax.set_title(f"Confusion Matrix - {model_name}")
    ax.set_xlabel("Predicted Label")
    ax.set_ylabel("True Label")

    ax.set_xticks([0, 1])
    ax.set_yticks([0, 1])
    ax.set_xticklabels(["BENIGN", "ATTACK"])
    ax.set_yticklabels(["BENIGN", "ATTACK"])

    for i in range(2):
        for j in range(2):
            ax.text(j, i, str(matrix[i][j]), ha="center", va="center")

    fig.colorbar(im)
    plt.tight_layout()

    output_path = FIGURES_DIR / f"confusion_matrix_{model_name}.png"
    plt.savefig(output_path, dpi=300)
    plt.close()

    print(f"[INFO] Saved: {output_path}")


def main():
    if not METRICS_PATH.exists():
        raise FileNotFoundError(f"Metrics dosyası bulunamadı: {METRICS_PATH}")

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(METRICS_PATH)

    print("[INFO] Metrics loaded:", METRICS_PATH)
    print("[INFO] Metrics shape:", df.shape)
    print("[INFO] Columns:", list(df.columns))

    required_columns = {
        "model",
        "accuracy",
        "precision",
        "recall",
        "f1_score",
        "auc",
        "far",
        "fpr",
        "training_time_sec",
        "inference_latency_ms_per_sample",
    }

    missing = required_columns - set(df.columns)
    if missing:
        raise ValueError(f"Metrics CSV içinde eksik kolonlar var: {missing}")

    save_bar_chart(
        df=df,
        metric="accuracy",
        filename="baseline_accuracy_comparison.png",
        title="Baseline Models Accuracy Comparison",
        ylabel="Accuracy",
        ascending=False,
    )

    save_bar_chart(
        df=df,
        metric="precision",
        filename="baseline_precision_comparison.png",
        title="Baseline Models Precision Comparison",
        ylabel="Precision",
        ascending=False,
    )

    save_bar_chart(
        df=df,
        metric="recall",
        filename="baseline_recall_comparison.png",
        title="Baseline Models Recall Comparison",
        ylabel="Recall",
        ascending=False,
    )

    save_bar_chart(
        df=df,
        metric="f1_score",
        filename="baseline_f1_comparison.png",
        title="Baseline Models F1-Score Comparison",
        ylabel="F1-Score",
        ascending=False,
    )

    save_bar_chart(
        df=df,
        metric="auc",
        filename="baseline_auc_comparison.png",
        title="Baseline Models AUC Comparison",
        ylabel="AUC",
        ascending=False,
    )

    save_bar_chart(
        df=df,
        metric="far",
        filename="baseline_far_comparison.png",
        title="Baseline Models FAR Comparison",
        ylabel="FAR",
        ascending=True,
    )

    save_bar_chart(
        df=df,
        metric="fpr",
        filename="baseline_fpr_comparison.png",
        title="Baseline Models FPR Comparison",
        ylabel="FPR",
        ascending=True,
    )

    save_bar_chart(
        df=df,
        metric="training_time_sec",
        filename="baseline_training_time_comparison.png",
        title="Baseline Models Training Time Comparison",
        ylabel="Training Time (seconds)",
        ascending=True,
    )

    save_bar_chart(
        df=df,
        metric="inference_latency_ms_per_sample",
        filename="baseline_inference_latency_comparison.png",
        title="Baseline Models Inference Latency Comparison",
        ylabel="Inference Latency (ms/sample)",
        ascending=True,
    )

    if CONFUSION_PATH.exists():
        with CONFUSION_PATH.open("r", encoding="utf-8") as f:
            confusion_data = json.load(f)

        best_model = df.sort_values(
            by=["f1_score", "far", "auc"],
            ascending=[False, True, False]
        ).iloc[0]["model"]

        save_confusion_matrix_chart(confusion_data, best_model)

    print("[INFO] Figure generation completed.")
    print("[INFO] Output directory:", FIGURES_DIR)


if __name__ == "__main__":
    main()
