#!/usr/bin/env python3
"""
Aşama 14.9-C — Selected Feature and Balanced Validation Report Figures

Bu script aşağıdaki metrik dosyalarından PNG, TikZ/PGFPlots ve LaTeX tablo çıktıları üretir:

1. selected_feature_model_metrics.csv
2. balanced_validation_lightgbm_metrics.csv
3. balanced_validation_pso_lightgbm_metrics.csv

Çıktılar:
- ml-service/experiments/figures/*.png
- reports/tikz/*.tex
- reports/latex_tables/*.tex
"""

from pathlib import Path

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


PROJECT_ROOT = Path(__file__).resolve().parents[2]

METRICS_DIR = PROJECT_ROOT / "ml-service" / "experiments" / "ml_metrics"
FIGURES_DIR = PROJECT_ROOT / "ml-service" / "experiments" / "figures"
TIKZ_DIR = PROJECT_ROOT / "reports" / "tikz"
TABLE_DIR = PROJECT_ROOT / "reports" / "latex_tables"

SELECTED_METRICS = METRICS_DIR / "selected_feature_model_metrics.csv"
BALANCED_BASELINE_METRICS = METRICS_DIR / "balanced_validation_lightgbm_metrics.csv"
BALANCED_PSO_METRICS = METRICS_DIR / "balanced_validation_pso_lightgbm_metrics.csv"


def escape_latex(text):
    return (
        str(text)
        .replace("_", "\\_")
        .replace("%", "\\%")
        .replace("&", "\\&")
    )


def ensure_dirs():
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    TIKZ_DIR.mkdir(parents=True, exist_ok=True)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)


def save_png_bar(df, x_col, y_col, output_path, title, ylabel, ascending=False):
    plot_df = df.sort_values(by=y_col, ascending=ascending)

    plt.figure(figsize=(9, 5))
    plt.bar(plot_df[x_col], plot_df[y_col])
    plt.xlabel(x_col)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.xticks(rotation=25, ha="right")
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()

    print("[INFO] PNG written:", output_path)


def save_tikz_bar(df, x_col, y_col, output_path, title, ylabel, ascending=False):
    plot_df = df.sort_values(by=y_col, ascending=ascending)

    labels = []
    coordinates = []

    for _, row in plot_df.iterrows():
        label = escape_latex(row[x_col])
        value = float(row[y_col])
        labels.append(label)
        coordinates.append(f"({label},{value:.8f})")

    xlabels = ",".join(labels)
    coords = "\n".join(coordinates)

    tex = rf"""\begin{{tikzpicture}}
\begin{{axis}}[
    ybar,
    width=0.95\linewidth,
    height=0.42\linewidth,
    bar width=10pt,
    symbolic x coords={{{xlabels}}},
    xtick=data,
    x tick label style={{rotate=35, anchor=east}},
    ymin=0,
    ylabel={{{ylabel}}},
    title={{{title}}},
    nodes near coords,
    nodes near coords align={{vertical}},
    grid=major,
]
\addplot coordinates {{
{coords}
}};
\end{{axis}}
\end{{tikzpicture}}
"""

    output_path.write_text(tex, encoding="utf-8")
    print("[INFO] TikZ written:", output_path)


def save_combined_bar_outputs(df, x_col, y_col, stem, title, ylabel, ascending=False):
    save_png_bar(
        df=df,
        x_col=x_col,
        y_col=y_col,
        output_path=FIGURES_DIR / f"{stem}.png",
        title=title,
        ylabel=ylabel,
        ascending=ascending,
    )

    save_tikz_bar(
        df=df,
        x_col=x_col,
        y_col=y_col,
        output_path=TIKZ_DIR / f"{stem}.tex",
        title=title,
        ylabel=ylabel,
        ascending=ascending,
    )


def save_selected_feature_table(df):
    cols = [
        "method",
        "model",
        "feature_count",
        "accuracy",
        "precision",
        "recall",
        "f1_score",
        "auc",
        "fpr",
        "far",
        "training_time_sec",
        "inference_latency_ms_per_sample",
    ]

    table_df = df[cols].copy()
    table_df = table_df.sort_values(
        by=["f1_score", "far", "feature_count"],
        ascending=[False, True, True],
    )

    lines = []
    lines.append(r"\begin{table}[ht]")
    lines.append(r"\centering")
    lines.append(r"\small")
    lines.append(r"\caption{Comparison of baseline and metaheuristic-selected LightGBM models.}")
    lines.append(r"\label{tab:selected_feature_model_metrics}")
    lines.append(r"\begin{tabular}{llrrrrrrrrrr}")
    lines.append(r"\hline")
    lines.append(r"Method & Model & Feat. & Acc. & Prec. & Rec. & F1 & AUC & FPR & FAR & Train(s) & Lat.(ms) \\")
    lines.append(r"\hline")

    for _, row in table_df.iterrows():
        lines.append(
            f"{escape_latex(row['method'])} & "
            f"{escape_latex(row['model'])} & "
            f"{int(row['feature_count'])} & "
            f"{row['accuracy']:.6f} & "
            f"{row['precision']:.6f} & "
            f"{row['recall']:.6f} & "
            f"{row['f1_score']:.6f} & "
            f"{row['auc']:.6f} & "
            f"{row['fpr']:.6f} & "
            f"{row['far']:.6f} & "
            f"{row['training_time_sec']:.3f} & "
            f"{row['inference_latency_ms_per_sample']:.6f} \\\\"
        )

    lines.append(r"\hline")
    lines.append(r"\end{tabular}")
    lines.append(r"\end{table}")

    output_path = TABLE_DIR / "selected_feature_model_metrics_table.tex"
    output_path.write_text("\n".join(lines), encoding="utf-8")
    print("[INFO] LaTeX table written:", output_path)


def save_balanced_validation_table(df, output_name, caption, label):
    cols = [
        "dataset",
        "rows",
        "class_0_benign",
        "class_1_attack",
        "feature_count",
        "accuracy",
        "precision",
        "recall",
        "f1_score",
        "auc",
        "fpr",
        "far",
        "training_time_sec",
        "inference_latency_ms_per_sample",
    ]

    table_df = df[cols].copy()

    lines = []
    lines.append(r"\begin{table}[ht]")
    lines.append(r"\centering")
    lines.append(r"\small")
    lines.append(rf"\caption{{{caption}}}")
    lines.append(rf"\label{{{label}}}")
    lines.append(r"\begin{tabular}{lrrrrrrrrrrrrr}")
    lines.append(r"\hline")
    lines.append(r"Dataset & Rows & Benign & Attack & Feat. & Acc. & Prec. & Rec. & F1 & AUC & FPR & FAR & Train(s) & Lat.(ms) \\")
    lines.append(r"\hline")

    for _, row in table_df.iterrows():
        lines.append(
            f"{escape_latex(row['dataset'])} & "
            f"{int(row['rows'])} & "
            f"{int(row['class_0_benign'])} & "
            f"{int(row['class_1_attack'])} & "
            f"{int(row['feature_count'])} & "
            f"{row['accuracy']:.6f} & "
            f"{row['precision']:.6f} & "
            f"{row['recall']:.6f} & "
            f"{row['f1_score']:.6f} & "
            f"{row['auc']:.6f} & "
            f"{row['fpr']:.6f} & "
            f"{row['far']:.6f} & "
            f"{row['training_time_sec']:.3f} & "
            f"{row['inference_latency_ms_per_sample']:.6f} \\\\"
        )

    lines.append(r"\hline")
    lines.append(r"\end{tabular}")
    lines.append(r"\end{table}")

    output_path = TABLE_DIR / output_name
    output_path.write_text("\n".join(lines), encoding="utf-8")
    print("[INFO] LaTeX table written:", output_path)


def process_selected_feature_metrics():
    if not SELECTED_METRICS.exists():
        print("[WARN] Missing:", SELECTED_METRICS)
        return

    df = pd.read_csv(SELECTED_METRICS)

    save_combined_bar_outputs(
        df=df,
        x_col="method",
        y_col="feature_count",
        stem="selected_feature_count_comparison",
        title="Selected Feature Count Comparison",
        ylabel="Feature Count",
        ascending=True,
    )

    save_combined_bar_outputs(
        df=df,
        x_col="method",
        y_col="f1_score",
        stem="selected_feature_f1_comparison",
        title="Selected Feature Models F1-Score Comparison",
        ylabel="F1-Score",
        ascending=False,
    )

    save_combined_bar_outputs(
        df=df,
        x_col="method",
        y_col="far",
        stem="selected_feature_far_comparison",
        title="Selected Feature Models FAR Comparison",
        ylabel="FAR",
        ascending=True,
    )

    save_combined_bar_outputs(
        df=df,
        x_col="method",
        y_col="fpr",
        stem="selected_feature_fpr_comparison",
        title="Selected Feature Models FPR Comparison",
        ylabel="FPR",
        ascending=True,
    )

    save_combined_bar_outputs(
        df=df,
        x_col="method",
        y_col="inference_latency_ms_per_sample",
        stem="selected_feature_latency_comparison",
        title="Selected Feature Models Inference Latency Comparison",
        ylabel="ms/sample",
        ascending=True,
    )

    save_selected_feature_table(df)


def process_balanced_validation_metrics():
    if BALANCED_BASELINE_METRICS.exists():
        df_base = pd.read_csv(BALANCED_BASELINE_METRICS)

        save_combined_bar_outputs(
            df=df_base,
            x_col="dataset",
            y_col="f1_score",
            stem="balanced_validation_lightgbm_f1_comparison",
            title="Balanced Validation LightGBM F1-Score Comparison",
            ylabel="F1-Score",
            ascending=False,
        )

        save_combined_bar_outputs(
            df=df_base,
            x_col="dataset",
            y_col="far",
            stem="balanced_validation_lightgbm_far_comparison",
            title="Balanced Validation LightGBM FAR Comparison",
            ylabel="FAR",
            ascending=True,
        )

        save_combined_bar_outputs(
            df=df_base,
            x_col="dataset",
            y_col="fpr",
            stem="balanced_validation_lightgbm_fpr_comparison",
            title="Balanced Validation LightGBM FPR Comparison",
            ylabel="FPR",
            ascending=True,
        )

        save_balanced_validation_table(
            df=df_base,
            output_name="balanced_validation_lightgbm_metrics_table.tex",
            caption="Balanced validation results for LightGBM using all reduced features.",
            label="tab:balanced_validation_lightgbm",
        )
    else:
        print("[WARN] Missing:", BALANCED_BASELINE_METRICS)

    if BALANCED_PSO_METRICS.exists():
        df_pso = pd.read_csv(BALANCED_PSO_METRICS)

        save_combined_bar_outputs(
            df=df_pso,
            x_col="dataset",
            y_col="f1_score",
            stem="balanced_validation_pso_f1_comparison",
            title="Balanced Validation PSO-LightGBM F1-Score Comparison",
            ylabel="F1-Score",
            ascending=False,
        )

        save_combined_bar_outputs(
            df=df_pso,
            x_col="dataset",
            y_col="far",
            stem="balanced_validation_pso_far_comparison",
            title="Balanced Validation PSO-LightGBM FAR Comparison",
            ylabel="FAR",
            ascending=True,
        )

        save_combined_bar_outputs(
            df=df_pso,
            x_col="dataset",
            y_col="fpr",
            stem="balanced_validation_pso_fpr_comparison",
            title="Balanced Validation PSO-LightGBM FPR Comparison",
            ylabel="FPR",
            ascending=True,
        )

        save_balanced_validation_table(
            df=df_pso,
            output_name="balanced_validation_pso_metrics_table.tex",
            caption="Balanced validation results for PSO-selected LightGBM model.",
            label="tab:balanced_validation_pso_lightgbm",
        )
    else:
        print("[WARN] Missing:", BALANCED_PSO_METRICS)


def main():
    ensure_dirs()
    process_selected_feature_metrics()
    process_balanced_validation_metrics()
    print("[INFO] Report figure/table generation completed.")


if __name__ == "__main__":
    main()
