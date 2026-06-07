#!/usr/bin/env python3
"""
Generate figures and summary report for full candidate model comparison.

Inputs:
- ml-service/experiments/full_candidate_models/full_candidate_model_metrics.csv
- ml-service/experiments/full_candidate_models/full_candidate_confusion_matrices.json

Outputs:
- figures/full_candidate_models/*.png
- full_candidate_model_summary.md

Usage:
python ml-service/training/09b_generate_full_candidate_figures.py
"""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


METRICS_CSV = Path("ml-service/experiments/full_candidate_models/full_candidate_model_metrics.csv")
CM_JSON = Path("ml-service/experiments/full_candidate_models/full_candidate_confusion_matrices.json")

FIGURE_DIR = Path("ml-service/experiments/figures/full_candidate_models")
SUMMARY_MD = Path("ml-service/experiments/full_candidate_models/full_candidate_model_summary.md")


def ensure_dirs():
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    SUMMARY_MD.parent.mkdir(parents=True, exist_ok=True)


def normalize_model_name(name: str) -> str:
    return (
        str(name)
        .replace("soft_voting_lightgbm_xgboost_extra_trees", "SoftVoting")
        .replace("extra_trees", "ExtraTrees")
        .replace("xgboost", "XGBoost")
        .replace("lightgbm", "LightGBM")
    )


def load_data():
    df = pd.read_csv(METRICS_CSV)

    with CM_JSON.open("r", encoding="utf-8") as f:
        cm = json.load(f)

    df["model_label"] = df["model"].apply(normalize_model_name)

    return df, cm


def save_metric_comparison(df: pd.DataFrame):
    metrics = ["accuracy", "precision", "recall", "f1_score", "auc"]

    plot_df = df.set_index("model_label")[metrics]

    ax = plot_df.plot(kind="bar", figsize=(12, 6), rot=20)
    ax.set_title("Full Candidate Models: Main Metric Comparison")
    ax.set_ylabel("Metric Value")
    ax.set_xlabel("Model")
    ax.grid(axis="y", alpha=0.3)
    ax.legend(title="Metric", loc="lower right")

    plt.tight_layout()
    out = FIGURE_DIR / "full_candidate_model_metrics_comparison.png"
    plt.savefig(out, dpi=300)
    plt.close()

    print(f"[INFO] Written: {out}")


def save_error_rate_comparison(df: pd.DataFrame):
    metrics = ["fpr", "fnr", "far"]

    plot_df = df.set_index("model_label")[metrics]

    ax = plot_df.plot(kind="bar", figsize=(12, 6), rot=20)
    ax.set_title("Full Candidate Models: Error Rate Comparison")
    ax.set_ylabel("Rate")
    ax.set_xlabel("Model")
    ax.grid(axis="y", alpha=0.3)
    ax.legend(title="Error Metric")

    plt.tight_layout()
    out = FIGURE_DIR / "full_candidate_fpr_fnr_far_comparison.png"
    plt.savefig(out, dpi=300)
    plt.close()

    print(f"[INFO] Written: {out}")


def save_fp_fn_comparison(df: pd.DataFrame):
    plot_df = df.set_index("model_label")[["fp", "fn"]]

    ax = plot_df.plot(kind="bar", figsize=(11, 6), rot=20)
    ax.set_title("Full Candidate Models: False Positive vs False Negative Counts")
    ax.set_ylabel("Count")
    ax.set_xlabel("Model")
    ax.grid(axis="y", alpha=0.3)
    ax.legend(["False Positive", "False Negative"])

    plt.tight_layout()
    out = FIGURE_DIR / "full_candidate_fp_fn_comparison.png"
    plt.savefig(out, dpi=300)
    plt.close()

    print(f"[INFO] Written: {out}")


def save_training_latency_comparison(df: pd.DataFrame):
    cols = ["training_time_sec", "inference_latency_ms_per_sample"]
    plot_df = df.copy()

    # Ensembles may have NaN training/inference latency in this script.
    plot_df = plot_df.dropna(subset=["training_time_sec"], how="all")

    if plot_df.empty:
        return

    ax = plot_df.set_index("model_label")[cols].plot(kind="bar", figsize=(11, 6), rot=20)
    ax.set_title("Full Candidate Models: Training Time and Inference Latency")
    ax.set_ylabel("Value")
    ax.set_xlabel("Model")
    ax.grid(axis="y", alpha=0.3)
    ax.legend(["Training time (sec)", "Inference latency (ms/sample)"])

    plt.tight_layout()
    out = FIGURE_DIR / "full_candidate_training_latency_comparison.png"
    plt.savefig(out, dpi=300)
    plt.close()

    print(f"[INFO] Written: {out}")


def save_confusion_matrix(cm_data, model_key: str, filename: str):
    if model_key not in cm_data:
        print(f"[WARN] Confusion matrix not found for: {model_key}")
        return

    matrix = np.array(cm_data[model_key]["matrix"])
    labels = cm_data[model_key]["matrix_labels"]

    fig, ax = plt.subplots(figsize=(5.5, 5))

    im = ax.imshow(matrix)

    title_name = normalize_model_name(model_key)
    ax.set_title(f"Confusion Matrix - {title_name}")
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


def read_breakdown_if_exists(model_name: str):
    path = Path(f"ml-service/experiments/full_candidate_models/{model_name}_full_holdout_attack_type_error_breakdown.csv")
    if not path.exists():
        return None
    return pd.read_csv(path)


def write_summary(df: pd.DataFrame):
    best_xgb = df[df["model"] == "xgboost"]
    lightgbm = df[df["model"] == "lightgbm"]
    extra = df[df["model"] == "extra_trees"]
    ensemble = df[df["model"] == "soft_voting_lightgbm_xgboost_extra_trees"]

    def row_or_none(frame):
        return None if frame.empty else frame.iloc[0].to_dict()

    xgb = row_or_none(best_xgb)
    lgbm = row_or_none(lightgbm)
    et = row_or_none(extra)
    ens = row_or_none(ensemble)

    lines = []
    lines.append("# Full Candidate Model Comparison Summary")
    lines.append("")
    lines.append("## Experimental Setup")
    lines.append("")
    lines.append("- Dataset family: CIC-DDoS2019")
    lines.append("- Train source: CSV-01-12")
    lines.append("- Holdout source: CSV-03-11")
    lines.append("- Portmap / PortScan: excluded")
    lines.append("- Feature count: 69")
    lines.append("- Constant features: removed")
    lines.append("")
    lines.append("## Full Holdout Results")
    lines.append("")
    lines.append("| Model | Accuracy | Precision | Recall | F1-score | AUC | FPR | FNR | FP | FN |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")

    for _, r in df.iterrows():
        lines.append(
            f"| {normalize_model_name(r['model'])} "
            f"| {r['accuracy']:.6f} "
            f"| {r['precision']:.6f} "
            f"| {r['recall']:.6f} "
            f"| {r['f1_score']:.6f} "
            f"| {r['auc']:.6f} "
            f"| {r['fpr']:.6f} "
            f"| {r['fnr']:.6f} "
            f"| {int(r['fp']):,} "
            f"| {int(r['fn']):,} |"
        )

    lines.append("")

    if xgb and lgbm:
        fn_reduction = int(lgbm["fn"]) - int(xgb["fn"])
        fp_reduction = int(lgbm["fp"]) - int(xgb["fp"])

        lines.append("## Main Finding")
        lines.append("")
        lines.append(
            f"XGBoost reduced the full holdout false negatives from "
            f"{int(lgbm['fn']):,} to {int(xgb['fn']):,}, corresponding to a reduction of "
            f"{fn_reduction:,} missed attack flows."
        )
        lines.append("")
        lines.append(
            f"XGBoost also reduced false positives from {int(lgbm['fp']):,} to "
            f"{int(xgb['fp']):,}, corresponding to a reduction of {fp_reduction:,} false alarms."
        )
        lines.append("")
        lines.append(
            "This indicates that the LightGBM cross-day weakness was not an unavoidable "
            "dataset limitation; it was strongly model-family dependent."
        )
        lines.append("")

    if et and xgb:
        lines.append("## XGBoost vs ExtraTrees")
        lines.append("")
        lines.append(
            f"ExtraTrees achieved FN={int(et['fn']):,}, while XGBoost achieved FN={int(xgb['fn']):,}. "
            f"However, ExtraTrees produced FP={int(et['fp']):,}, compared with XGBoost FP={int(xgb['fp']):,}."
        )
        lines.append("")
        lines.append(
            "Therefore, ExtraTrees can be interpreted as a false-negative-minimizing model, "
            "whereas XGBoost provides a more balanced IDS/IPS trade-off."
        )
        lines.append("")

    if ens and xgb:
        lines.append("## Ensemble Observation")
        lines.append("")
        lines.append(
            f"The soft voting ensemble achieved FN={int(ens['fn']):,} and FP={int(ens['fp']):,}. "
            f"It did not improve over XGBoost, which achieved FN={int(xgb['fn']):,} and FP={int(xgb['fp']):,}."
        )
        lines.append("")
        lines.append(
            "For this reason, XGBoost is selected as the final full-feature candidate model, "
            "while the ensemble remains an additional comparative model."
        )
        lines.append("")

    lines.append("## Generated Figures")
    lines.append("")
    lines.append("- `full_candidate_model_metrics_comparison.png`")
    lines.append("- `full_candidate_fpr_fnr_far_comparison.png`")
    lines.append("- `full_candidate_fp_fn_comparison.png`")
    lines.append("- `full_candidate_training_latency_comparison.png`")
    lines.append("- `full_candidate_confusion_matrix_xgboost.png`")
    lines.append("- `full_candidate_confusion_matrix_extra_trees.png`")
    lines.append("- `full_candidate_confusion_matrix_soft_voting.png`")
    lines.append("")

    SUMMARY_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"[INFO] Written: {SUMMARY_MD}")


def main():
    ensure_dirs()

    df, cm = load_data()

    save_metric_comparison(df)
    save_error_rate_comparison(df)
    save_fp_fn_comparison(df)
    save_training_latency_comparison(df)

    save_confusion_matrix(
        cm,
        "xgboost",
        "full_candidate_confusion_matrix_xgboost.png",
    )

    save_confusion_matrix(
        cm,
        "extra_trees",
        "full_candidate_confusion_matrix_extra_trees.png",
    )

    save_confusion_matrix(
        cm,
        "lightgbm",
        "full_candidate_confusion_matrix_lightgbm.png",
    )

    save_confusion_matrix(
        cm,
        "soft_voting_lightgbm_xgboost_extra_trees",
        "full_candidate_confusion_matrix_soft_voting.png",
    )

    write_summary(df)

    print("[INFO] Full candidate figures generated.")


if __name__ == "__main__":
    main()
