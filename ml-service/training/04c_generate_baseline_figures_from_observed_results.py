#!/usr/bin/env python3

from pathlib import Path
import json
import pandas as pd
import matplotlib.pyplot as plt

metrics_dir = Path("ml-service/experiments/ml_metrics")
figures_dir = Path("ml-service/experiments/figures")

metrics_dir.mkdir(parents=True, exist_ok=True)
figures_dir.mkdir(parents=True, exist_ok=True)

results = [
    {
        "model": "logistic_regression",
        "f1_score": 0.999647,
        "auc": 0.999833,
        "far": 0.001832,
        "fpr": 0.002989,
        "training_time_sec": 45.27,
        "inference_latency_ms_per_sample": 0.001270,
        "feature_count": 38,
    },
    {
        "model": "random_forest",
        "f1_score": 0.999991,
        "auc": 1.000000,
        "far": 0.000305,
        "fpr": 0.000598,
        "training_time_sec": 23.16,
        "inference_latency_ms_per_sample": 0.019273,
        "feature_count": 38,
    },
    {
        "model": "extra_trees",
        "f1_score": 0.999991,
        "auc": 1.000000,
        "far": 0.000009,
        "fpr": 0.000000,
        "training_time_sec": 7.57,
        "inference_latency_ms_per_sample": 0.019846,
        "feature_count": 38,
    },
    {
        "model": "gradient_boosting",
        "f1_score": 0.999988,
        "auc": 1.000000,
        "far": 0.000308,
        "fpr": 0.000598,
        "training_time_sec": 272.72,
        "inference_latency_ms_per_sample": 0.001785,
        "feature_count": 38,
    },
    {
        "model": "lightgbm",
        "f1_score": 0.999994,
        "auc": 0.999995,
        "far": 0.000006,
        "fpr": 0.000000,
        "training_time_sec": 3.37,
        "inference_latency_ms_per_sample": 0.003971,
        "feature_count": 38,
    },
    {
        "model": "xgboost",
        "f1_score": 0.999988,
        "auc": 1.000000,
        "far": 0.000308,
        "fpr": 0.000598,
        "training_time_sec": 4.01,
        "inference_latency_ms_per_sample": 0.003219,
        "feature_count": 38,
    },
    {
        "model": "mlp",
        "f1_score": 0.999979,
        "auc": 0.999992,
        "far": 0.000317,
        "fpr": 0.000598,
        "training_time_sec": 24.70,
        "inference_latency_ms_per_sample": 0.001496,
        "feature_count": 38,
    },
]

df = pd.DataFrame(results)
df.sort_values(by=["f1_score", "far", "auc"], ascending=[False, True, False], inplace=True)

csv_path = metrics_dir / "baseline_model_metrics_observed.csv"
json_path = metrics_dir / "baseline_model_metrics_observed.json"

df.to_csv(csv_path, index=False)

with json_path.open("w", encoding="utf-8") as f:
    json.dump(
        {
            "source": "Observed terminal output from baseline training run",
            "warning": "These values are reconstructed from terminal output. For final publication, regenerate from fixed training script.",
            "results": results,
        },
        f,
        indent=2,
        ensure_ascii=False,
    )

def save_bar(metric, filename, title, ylabel, ascending=False):
    plot_df = df.sort_values(by=metric, ascending=ascending)

    plt.figure(figsize=(9, 5))
    plt.bar(plot_df["model"], plot_df[metric])
    plt.xlabel("Model")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.savefig(figures_dir / filename, dpi=300)
    plt.close()

save_bar(
    metric="f1_score",
    filename="baseline_f1_comparison_observed.png",
    title="Baseline Models F1-Score Comparison",
    ylabel="F1-Score",
    ascending=False,
)

save_bar(
    metric="far",
    filename="baseline_far_comparison_observed.png",
    title="Baseline Models FAR Comparison",
    ylabel="FAR",
    ascending=True,
)

save_bar(
    metric="fpr",
    filename="baseline_fpr_comparison_observed.png",
    title="Baseline Models FPR Comparison",
    ylabel="FPR",
    ascending=True,
)

save_bar(
    metric="training_time_sec",
    filename="baseline_training_time_comparison_observed.png",
    title="Baseline Models Training Time Comparison",
    ylabel="Training Time (sec)",
    ascending=True,
)

save_bar(
    metric="inference_latency_ms_per_sample",
    filename="baseline_inference_latency_comparison_observed.png",
    title="Baseline Models Inference Latency Comparison",
    ylabel="ms / sample",
    ascending=True,
)

print("[INFO] Observed metrics CSV:", csv_path)
print("[INFO] Observed metrics JSON:", json_path)
print("[INFO] Figures directory:", figures_dir)
