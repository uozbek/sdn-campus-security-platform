#!/usr/bin/env python3
"""
Aşama 14.7-F — Runtime LaTeX Tables and TikZ/PGFPlots Outputs

Bu script reports/runtime altındaki CSV özetlerinden LaTeX tablo
ve TikZ/PGFPlots grafik çıktıları üretir.

Girdi:
- reports/runtime/runtime_policy_action_distribution.csv
- reports/runtime/runtime_mitigation_latency_summary.csv
- reports/runtime/runtime_flow_rule_timing_summary.csv
- reports/runtime/runtime_controller_resource_summary.csv

Çıktı:
- reports/runtime/latex_tables/*.tex
- reports/runtime/tikz/*.tex
"""

from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

RUNTIME_DIR = PROJECT_ROOT / "reports" / "runtime"
LATEX_TABLE_DIR = RUNTIME_DIR / "latex_tables"
TIKZ_DIR = RUNTIME_DIR / "tikz"

POLICY_DIST_CSV = RUNTIME_DIR / "runtime_policy_action_distribution.csv"
MITIGATION_LATENCY_CSV = RUNTIME_DIR / "runtime_mitigation_latency_summary.csv"
FLOW_RULE_TIMING_CSV = RUNTIME_DIR / "runtime_flow_rule_timing_summary.csv"
RESOURCE_SUMMARY_CSV = RUNTIME_DIR / "runtime_controller_resource_summary.csv"


def ensure_dirs():
    LATEX_TABLE_DIR.mkdir(parents=True, exist_ok=True)
    TIKZ_DIR.mkdir(parents=True, exist_ok=True)


def escape_latex(value):
    text = str(value)
    return (
        text.replace("\\", "\\textbackslash{}")
        .replace("_", "\\_")
        .replace("%", "\\%")
        .replace("&", "\\&")
        .replace("#", "\\#")
    )


def read_csv(path):
    if not path.exists():
        print(f"[WARN] Missing input: {path}")
        return pd.DataFrame()

    try:
        df = pd.read_csv(path)
        print(f"[INFO] Loaded {path}: shape={df.shape}")
        return df
    except Exception as exc:
        print(f"[WARN] Could not read {path}: {exc}")
        return pd.DataFrame()


def write_text(path, content):
    path.write_text(content, encoding="utf-8")
    print(f"[INFO] Written: {path}")


def make_policy_action_table(df):
    if df.empty:
        return

    lines = []
    lines.append(r"\begin{table}[ht]")
    lines.append(r"\centering")
    lines.append(r"\small")
    lines.append(r"\caption{Runtime policy final action distribution.}")
    lines.append(r"\label{tab:runtime_policy_action_distribution}")
    lines.append(r"\begin{tabular}{lr}")
    lines.append(r"\hline")
    lines.append(r"Policy Action & Count \\")
    lines.append(r"\hline")

    for _, row in df.iterrows():
        action = escape_latex(row["policy_final_action"])
        count = int(row["count"])
        lines.append(f"{action} & {count} \\\\")

    lines.append(r"\hline")
    lines.append(r"\end{tabular}")
    lines.append(r"\end{table}")

    write_text(
        LATEX_TABLE_DIR / "runtime_policy_action_distribution_table.tex",
        "\n".join(lines),
    )


def make_mitigation_latency_table(df):
    if df.empty:
        return

    lines = []
    lines.append(r"\begin{table}[ht]")
    lines.append(r"\centering")
    lines.append(r"\small")
    lines.append(r"\caption{Controller-side mitigation latency by action.}")
    lines.append(r"\label{tab:runtime_mitigation_latency}")
    lines.append(r"\begin{tabular}{lrrrrr}")
    lines.append(r"\hline")
    lines.append(r"Mitigation Action & Count & Mean (ms) & Min (ms) & Max (ms) & Std (ms) \\")
    lines.append(r"\hline")

    for _, row in df.iterrows():
        action = escape_latex(row["mitigation_action"])
        count = int(row["count"])
        mean = float(row["mean"])
        min_v = float(row["min"])
        max_v = float(row["max"])
        std_v = 0.0 if pd.isna(row.get("std", 0.0)) else float(row.get("std", 0.0))
        lines.append(
            f"{action} & {count} & {mean:.6f} & {min_v:.6f} & {max_v:.6f} & {std_v:.6f} \\\\"
        )

    lines.append(r"\hline")
    lines.append(r"\end{tabular}")
    lines.append(r"\end{table}")

    write_text(
        LATEX_TABLE_DIR / "runtime_mitigation_latency_table.tex",
        "\n".join(lines),
    )


def make_flow_rule_timing_table(df):
    if df.empty:
        return

    lines = []
    lines.append(r"\begin{table}[ht]")
    lines.append(r"\centering")
    lines.append(r"\small")
    lines.append(r"\caption{Controller-side flow rule timing by rule type.}")
    lines.append(r"\label{tab:runtime_flow_rule_timing}")
    lines.append(r"\begin{tabular}{lrrrrr}")
    lines.append(r"\hline")
    lines.append(r"Rule Type & Count & Mean (ms) & Min (ms) & Max (ms) & Std (ms) \\")
    lines.append(r"\hline")

    for _, row in df.iterrows():
        rule_type = escape_latex(row["rule_type"])
        count = int(row["count"])
        mean = float(row["mean"])
        min_v = float(row["min"])
        max_v = float(row["max"])
        std_v = 0.0 if pd.isna(row.get("std", 0.0)) else float(row.get("std", 0.0))
        lines.append(
            f"{rule_type} & {count} & {mean:.6f} & {min_v:.6f} & {max_v:.6f} & {std_v:.6f} \\\\"
        )

    lines.append(r"\hline")
    lines.append(r"\end{tabular}")
    lines.append(r"\end{table}")

    write_text(
        LATEX_TABLE_DIR / "runtime_flow_rule_timing_table.tex",
        "\n".join(lines),
    )


def make_controller_resource_table(df):
    if df.empty:
        return

    lines = []
    lines.append(r"\begin{table}[ht]")
    lines.append(r"\centering")
    lines.append(r"\small")
    lines.append(r"\caption{Controller resource usage summary in observe-only mode.}")
    lines.append(r"\label{tab:runtime_controller_resource_summary}")
    lines.append(r"\begin{tabular}{lrrrr}")
    lines.append(r"\hline")
    lines.append(r"Metric & Mean & Min & Max & Std \\")
    lines.append(r"\hline")

    for _, row in df.iterrows():
        metric = escape_latex(row["metric"])
        mean = float(row["mean"])
        min_v = float(row["min"])
        max_v = float(row["max"])
        std_v = 0.0 if pd.isna(row.get("std", 0.0)) else float(row.get("std", 0.0))
        lines.append(
            f"{metric} & {mean:.6f} & {min_v:.6f} & {max_v:.6f} & {std_v:.6f} \\\\"
        )

    lines.append(r"\hline")
    lines.append(r"\end{tabular}")
    lines.append(r"\end{table}")

    write_text(
        LATEX_TABLE_DIR / "runtime_controller_resource_table.tex",
        "\n".join(lines),
    )


def make_tikz_bar(
    df,
    x_col,
    y_col,
    output_name,
    title,
    ylabel,
    xlabel,
    sort_by_y=False,
    ascending=False,
):
    if df.empty or x_col not in df.columns or y_col not in df.columns:
        print(f"[WARN] Skipped TikZ: {output_name}")
        return

    plot_df = df.copy()

    if sort_by_y:
        plot_df = plot_df.sort_values(by=y_col, ascending=ascending)

    labels = []
    coords = []

    for _, row in plot_df.iterrows():
        label = escape_latex(row[x_col])
        value = float(row[y_col])
        labels.append(label)
        coords.append(f"({label},{value:.8f})")

    xlabels = ",".join(labels)
    coord_text = "\n".join(coords)

    tex = rf"""\begin{{tikzpicture}}
\begin{{axis}}[
    ybar,
    width=0.95\linewidth,
    height=0.45\linewidth,
    bar width=12pt,
    symbolic x coords={{{xlabels}}},
    xtick=data,
    x tick label style={{rotate=30, anchor=east}},
    ymin=0,
    xlabel={{{xlabel}}},
    ylabel={{{ylabel}}},
    title={{{title}}},
    nodes near coords,
    nodes near coords align={{vertical}},
    grid=major,
]
\addplot coordinates {{
{coord_text}
}};
\end{{axis}}
\end{{tikzpicture}}
"""

    write_text(TIKZ_DIR / output_name, tex)


def main():
    ensure_dirs()

    policy_df = read_csv(POLICY_DIST_CSV)
    mitigation_df = read_csv(MITIGATION_LATENCY_CSV)
    flow_df = read_csv(FLOW_RULE_TIMING_CSV)
    resource_df = read_csv(RESOURCE_SUMMARY_CSV)

    make_policy_action_table(policy_df)
    make_mitigation_latency_table(mitigation_df)
    make_flow_rule_timing_table(flow_df)
    make_controller_resource_table(resource_df)

    make_tikz_bar(
        df=policy_df,
        x_col="policy_final_action",
        y_col="count",
        output_name="runtime_policy_action_distribution.tex",
        title="Runtime Policy Final Action Distribution",
        ylabel="Count",
        xlabel="Policy Action",
        sort_by_y=True,
        ascending=False,
    )

    make_tikz_bar(
        df=mitigation_df,
        x_col="mitigation_action",
        y_col="mean",
        output_name="runtime_mitigation_latency_by_action.tex",
        title="Controller-side Mitigation Latency by Action",
        ylabel="Mean Latency (ms)",
        xlabel="Mitigation Action",
        sort_by_y=False,
    )

    make_tikz_bar(
        df=flow_df,
        x_col="rule_type",
        y_col="mean",
        output_name="runtime_flow_rule_timing_by_type.tex",
        title="Controller-side Flow Rule Timing by Type",
        ylabel="Mean Duration (ms)",
        xlabel="Rule Type",
        sort_by_y=False,
    )

    # Controller resource için mean değerleri tek grafikte gösterilebilir.
    make_tikz_bar(
        df=resource_df,
        x_col="metric",
        y_col="mean",
        output_name="runtime_controller_resource_summary.tex",
        title="Controller Resource Usage Summary",
        ylabel="Mean Value",
        xlabel="Metric",
        sort_by_y=False,
    )

    print("[INFO] Runtime LaTeX/TikZ generation completed.")


if __name__ == "__main__":
    main()
