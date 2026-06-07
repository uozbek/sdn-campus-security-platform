#!/usr/bin/env python3

from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

METRICS_PATH = PROJECT_ROOT / "ml-service" / "experiments" / "ml_metrics" / "baseline_model_metrics.csv"
TIKZ_DIR = PROJECT_ROOT / "reports" / "tikz"
TABLE_DIR = PROJECT_ROOT / "reports" / "latex_tables"


def escape_latex(text):
    return (
        str(text)
        .replace("_", "\\_")
        .replace("%", "\\%")
        .replace("&", "\\&")
    )


def generate_bar_pgfplots(df, metric, output_path, title, ylabel, sort_ascending=False):
    plot_df = df.sort_values(by=metric, ascending=sort_ascending)

    coordinates = []
    labels = []

    for _, row in plot_df.iterrows():
        model = row["model"]
        value = row[metric]
        labels.append(escape_latex(model))
        coordinates.append(f"({escape_latex(model)},{value:.8f})")

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


def generate_latex_table(df, output_path):
    cols = [
        "model",
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
    table_df = table_df.sort_values(by=["f1_score", "far"], ascending=[False, True])

    lines = []
    lines.append(r"\begin{table}[ht]")
    lines.append(r"\centering")
    lines.append(r"\small")
    lines.append(r"\caption{Baseline model performance on the reduced CIC-DDoS2019 subset.}")
    lines.append(r"\label{tab:baseline_model_metrics}")
    lines.append(r"\begin{tabular}{lrrrrrrrrr}")
    lines.append(r"\hline")
    lines.append(r"Model & Acc. & Prec. & Rec. & F1 & AUC & FPR & FAR & Train(s) & Lat.(ms) \\")
    lines.append(r"\hline")

    for _, row in table_df.iterrows():
        lines.append(
            f"{escape_latex(row['model'])} & "
            f"{row['accuracy']:.6f} & "
            f"{row['precision']:.6f} & "
            f"{row['recall']:.6f} & "
            f"{row['f1_score']:.6f} & "
            f"{row['auc']:.6f} & "
            f"{row['fpr']:.6f} & "
            f"{row['far']:.6f} & "
            f"{row['training_time_sec']:.2f} & "
            f"{row['inference_latency_ms_per_sample']:.6f} \\\\"
        )

    lines.append(r"\hline")
    lines.append(r"\end{tabular}")
    lines.append(r"\end{table}")

    output_path.write_text("\n".join(lines), encoding="utf-8")
    print("[INFO] LaTeX table written:", output_path)


def main():
    if not METRICS_PATH.exists():
        raise FileNotFoundError(f"Metrics file not found: {METRICS_PATH}")

    TIKZ_DIR.mkdir(parents=True, exist_ok=True)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(METRICS_PATH)

    generate_bar_pgfplots(
        df=df,
        metric="f1_score",
        output_path=TIKZ_DIR / "baseline_f1_comparison.tex",
        title="Baseline Models F1-Score Comparison",
        ylabel="F1-Score",
        sort_ascending=False,
    )

    generate_bar_pgfplots(
        df=df,
        metric="far",
        output_path=TIKZ_DIR / "baseline_far_comparison.tex",
        title="Baseline Models FAR Comparison",
        ylabel="FAR",
        sort_ascending=True,
    )

    generate_bar_pgfplots(
        df=df,
        metric="fpr",
        output_path=TIKZ_DIR / "baseline_fpr_comparison.tex",
        title="Baseline Models FPR Comparison",
        ylabel="FPR",
        sort_ascending=True,
    )

    generate_bar_pgfplots(
        df=df,
        metric="inference_latency_ms_per_sample",
        output_path=TIKZ_DIR / "baseline_inference_latency_comparison.tex",
        title="Baseline Models Inference Latency Comparison",
        ylabel="ms/sample",
        sort_ascending=True,
    )

    generate_latex_table(
        df=df,
        output_path=TABLE_DIR / "baseline_model_metrics_table.tex",
    )


if __name__ == "__main__":
    main()
