#!/usr/bin/env python3
"""
Generate figures for Large LightGBM baseline results.

Inputs:
- large_lightgbm_baseline_metrics.csv
- large_lightgbm_confusion_matrices.json

Outputs:
- validation vs holdout metric comparison
- validation confusion matrix
- holdout confusion matrix
- false positive / false negative comparison
- summary markdown

Usage:
python ml-service/training/07b_generate_large_lightgbm_figures.py
"""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np


METRICS_CSV = Path("ml-service/experiments/ml_metrics/large_lightgbm_baseline_metrics.csv")
CM_JSON = Path("ml-service/experiments/ml_metrics/large_lightgbm_confusion_matrices.json")

FIGURE_DIR = Path("ml-service/experiments/figures/large_lightgbm")
SUMMARY_MD = Path("ml-service/experiments/ml_metrics/large_lightgbm_baseline_summary.md")


def ensure_dirs():
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    SUMMARY_MD.parent.mkdir(parents=True, exist_ok=True)


def save_metric_comparison(df: pd.DataFrame):
    metrics = ["accuracy", "precision", "recall", "f1_score", "auc", "fpr", "fnr", "far"]

    plot_df = df.set_index("split")[metrics].T

    ax = plot_df.plot(kind="bar", figsize=(12, 6), rot=45)
    ax.set_title("Large LightGBM Baseline: Validation vs Holdout Metrics")
    ax.set_ylabel("Metric Value")
    ax.set_xlabel("Metric")
    ax.grid(axis="y", alpha=0.3)
    ax.legend(title="Split")

    plt.tight_layout()
    out = FIGURE_DIR / "large_lightgbm_validation_vs_holdout_metrics.png"
    plt.savefig(out, dpi=300)
    plt.close()

    print(f"[INFO] Written: {out}")


def save_error_rate_comparison(df: pd.DataFrame):
    metrics = ["fpr", "fnr", "far"]

    plot_df = df.set_index("split")[metrics].T

    ax = plot_df.plot(kind="bar", figsize=(10, 5), rot=0)
    ax.set_title("Large LightGBM Baseline: Error Rate Comparison")
    ax.set_ylabel("Rate")
    ax.set_xlabel("Error Metric")
    ax.grid(axis="y", alpha=0.3)
    ax.legend(title="Split")

    plt.tight_layout()
    out = FIGURE_DIR / "large_lightgbm_error_rate_comparison.png"
    plt.savefig(out, dpi=300)
    plt.close()

    print(f"[INFO] Written: {out}")


def save_confusion_matrix(cm_data, split_key: str, filename: str):
    matrix = np.array(cm_data[split_key]["matrix"])
    labels = cm_data[split_key]["matrix_labels"]

    fig, ax = plt.subplots(figsize=(5.5, 5))

    im = ax.imshow(matrix)

    ax.set_title(f"Confusion Matrix - {split_key}")
    ax.set_xticks(np.arange(len(labels)))
    ax.set_yticks(np.arange(len(labels)))
    ax.set_xticklabels([f"Pred {x}" for x in labels])
    ax.set_yticklabels([f"True {x}" for x in labels])

    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            ax.text(
                j,
                i,
                f"{matrix[i, j]:,}",
                ha="center",
                va="center",
                fontsize=11,
            )

    ax.set_xlabel("Predicted Label")
    ax.set_ylabel("True Label")

    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

    plt.tight_layout()
    out = FIGURE_DIR / filename
    plt.savefig(out, dpi=300)
    plt.close()

    print(f"[INFO] Written: {out}")


def save_fp_fn_count_comparison(df: pd.DataFrame):
    plot_df = df.set_index("split")[["fp", "fn"]].copy()

    ax = plot_df.plot(kind="bar", figsize=(9, 5), rot=0)
    ax.set_title("Large LightGBM Baseline: FP vs FN Counts")
    ax.set_ylabel("Count")
    ax.set_xlabel("Split")
    ax.grid(axis="y", alpha=0.3)
    ax.legend(["False Positive", "False Negative"])

    plt.tight_layout()
    out = FIGURE_DIR / "large_lightgbm_fp_fn_counts.png"
    plt.savefig(out, dpi=300)
    plt.close()

    print(f"[INFO] Written: {out}")


def write_summary(df: pd.DataFrame, cm_data):
    val = df[df["split"] == "validation_01_12"].iloc[0].to_dict()
    holdout = df[df["split"] == "holdout_03_11"].iloc[0].to_dict()

    text = f"""# Large LightGBM Baseline Summary

## Dataset

- Train/validation source: CIC-DDoS2019 CSV-01-12
- Holdout source: CIC-DDoS2019 CSV-03-11
- Feature count: {int(holdout["feature_count"])}
- Portmap / PortScan: excluded
- Constant features: removed

## Validation Results

| Metric | Value |
|---|---:|
| Rows | {int(val["rows"]):,} |
| Accuracy | {val["accuracy"]:.6f} |
| Precision | {val["precision"]:.6f} |
| Recall | {val["recall"]:.6f} |
| F1-score | {val["f1_score"]:.6f} |
| AUC | {val["auc"]:.6f} |
| FPR | {val["fpr"]:.6f} |
| FNR | {val["fnr"]:.6f} |
| FAR | {val["far"]:.6f} |
| TN | {int(val["tn"]):,} |
| FP | {int(val["fp"]):,} |
| FN | {int(val["fn"]):,} |
| TP | {int(val["tp"]):,} |

## Holdout Results

| Metric | Value |
|---|---:|
| Rows | {int(holdout["rows"]):,} |
| Accuracy | {holdout["accuracy"]:.6f} |
| Precision | {holdout["precision"]:.6f} |
| Recall | {holdout["recall"]:.6f} |
| F1-score | {holdout["f1_score"]:.6f} |
| AUC | {holdout["auc"]:.6f} |
| FPR | {holdout["fpr"]:.6f} |
| FNR | {holdout["fnr"]:.6f} |
| FAR | {holdout["far"]:.6f} |
| TN | {int(holdout["tn"]):,} |
| FP | {int(holdout["fp"]):,} |
| FN | {int(holdout["fn"]):,} |
| TP | {int(holdout["tp"]):,} |

## Interpretation

The model achieves near-perfect validation performance on CSV-01-12. However, cross-day holdout performance on CSV-03-11 is lower, especially in terms of false negatives.

The holdout false positive count is low, but the false negative count is comparatively higher. This suggests that cross-day generalization mainly needs improvement on attack recall rather than benign protection.

## Generated Figures

- `large_lightgbm_validation_vs_holdout_metrics.png`
- `large_lightgbm_error_rate_comparison.png`
- `large_lightgbm_confusion_matrix_validation.png`
- `large_lightgbm_confusion_matrix_holdout.png`
- `large_lightgbm_fp_fn_counts.png`
"""

    SUMMARY_MD.write_text(text, encoding="utf-8")
    print(f"[INFO] Written: {SUMMARY_MD}")


def main():
    ensure_dirs()

    df = pd.read_csv(METRICS_CSV)

    with CM_JSON.open("r", encoding="utf-8") as f:
        cm_data = json.load(f)

    save_metric_comparison(df)
    save_error_rate_comparison(df)
    save_fp_fn_count_comparison(df)

    save_confusion_matrix(
        cm_data,
        "validation_01_12",
        "large_lightgbm_confusion_matrix_validation.png",
    )

    save_confusion_matrix(
        cm_data,
        "holdout_03_11",
        "large_lightgbm_confusion_matrix_holdout.png",
    )

    write_summary(df, cm_data)

    print("[INFO] Large LightGBM baseline figures generated.")


if __name__ == "__main__":
    main()
