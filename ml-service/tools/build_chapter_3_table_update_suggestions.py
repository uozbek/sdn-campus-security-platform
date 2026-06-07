#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from datetime import datetime
import pandas as pd


def clean(s):
    return str(s or "").strip()


def compact_signals(r):
    signals = []

    if clean(r.get("dataset_signals", "")):
        signals.append("dataset=" + clean(r.get("dataset_signals", ""))[:80])
    if clean(r.get("sdn_testbed_signals", "")):
        signals.append("sdn/testbed=" + clean(r.get("sdn_testbed_signals", ""))[:100])
    if clean(r.get("mitigation_signals", "")):
        signals.append("mitigation=" + clean(r.get("mitigation_signals", ""))[:100])
    if clean(r.get("runtime_signals", "")):
        signals.append("runtime=" + clean(r.get("runtime_signals", ""))[:100])
    if clean(r.get("feature_selection_signals", "")):
        signals.append("feature_selection=" + clean(r.get("feature_selection_signals", ""))[:100])
    if clean(r.get("model_signals", "")):
        signals.append("model=" + clean(r.get("model_signals", ""))[:100])

    return "; ".join(signals)


def suggested_table_role(table, r):
    title = clean(r.get("title", "")).lower()
    sdn = clean(r.get("sdn_testbed_signals", "")).lower()
    mitigation = clean(r.get("mitigation_signals", "")).lower()
    runtime = clean(r.get("runtime_signals", "")).lower()
    fs = clean(r.get("feature_selection_signals", "")).lower()
    model = clean(r.get("model_signals", "")).lower()

    if table == "Tablo 3.4":
        return "Runtime/controller/testbed boyutunu güçlendirmek için kullanılabilir."
    if table == "Tablo 3.5":
        return "Tespit çıktısının önleme/mitigation aksiyonuna dönüşmesi açısından kullanılabilir."
    if table == "Tablo 3.7":
        parts = []
        if sdn:
            parts.append("controller/testbed")
        if runtime:
            parts.append("runtime validation")
        if mitigation:
            parts.append("mitigation/prevention")
        if fs:
            parts.append("feature selection")
        if model:
            parts.append("ML/DL model")
        if not parts:
            parts.append("literatür karşılaştırması")
        return "Yöntemsel karşılaştırmada " + ", ".join(parts) + " farkını göstermek için kullanılabilir."
    return "Destekleyici kaynak."


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--revision-plan-csv",
        default="docs/literature_review/zotero_clean/chapter_3_table_revision_plan.csv",
    )
    parser.add_argument(
        "--output-md",
        default="docs/literature_review/zotero_clean/chapter_3_table_update_suggestions.md",
    )
    parser.add_argument(
        "--output-csv",
        default="docs/literature_review/zotero_clean/chapter_3_table_update_suggestions.csv",
    )
    parser.add_argument("--top-n-per-table", type=int, default=10)
    args = parser.parse_args()

    p = Path(args.revision_plan_csv)
    if not p.exists():
        raise SystemExit(f"[ERROR] Missing file: {p}")

    df = pd.read_csv(p).fillna("")
    df["score"] = pd.to_numeric(df["priority_score"], errors="coerce").fillna(0)

    selected_tables = ["Tablo 3.4", "Tablo 3.5", "Tablo 3.7"]
    rows = []

    for table in selected_tables:
        sub = df[df["target_table"].eq(table)].copy()
        sub = sub.sort_values(["score", "year"], ascending=[False, False]).head(args.top_n_per_table)

        for _, r in sub.iterrows():
            rows.append({
                "target_table": table,
                "zotero_key": clean(r.get("zotero_key", "")),
                "year": clean(r.get("year", "")),
                "priority_score": clean(r.get("priority_score", "")),
                "title": clean(r.get("title", "")),
                "key_signals": compact_signals(r),
                "suggested_role": suggested_table_role(table, r),
            })

    out = pd.DataFrame(rows)
    Path(args.output_csv).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.output_csv, index=False)

    md = []
    md.append("# Chapter 3 Table Update Suggestions")
    md.append("")
    md.append(f"- Generated at UTC: `{datetime.utcnow().isoformat()}`")
    md.append(f"- Input: `{args.revision_plan_csv}`")
    md.append(f"- Output CSV: `{args.output_csv}`")
    md.append(f"- Top N per table: `{args.top_n_per_table}`")
    md.append("")
    md.append("## 1. Öneri Özeti")
    md.append("")
    md.append("Bu dosya, Bölüm 3 tablolarını full text evidence card sonuçlarına göre fiilen güncellemeden önce seçilecek güçlü aday kaynakları listeler.")
    md.append("")
    md.append("Öncelik sırası:")
    md.append("")
    md.append("1. Tablo 3.4 — Runtime/controller/testbed")
    md.append("2. Tablo 3.5 — Mitigation/prevention")
    md.append("3. Tablo 3.7 — Tezin literatürden yöntemsel farkı")
    md.append("")
    md.append("## 2. Tablo Bazlı Öneriler")
    md.append("")

    for table in selected_tables:
        sub = out[out["target_table"].eq(table)]
        md.append(f"### {table}")
        md.append("")
        md.append("| Key | Year | Score | Title | Suggested role |")
        md.append("|---|---:|---:|---|---|")
        for _, r in sub.iterrows():
            title = clean(r["title"]).replace("|", "\\|")
            role = clean(r["suggested_role"]).replace("|", "\\|")
            md.append(f"| {r['zotero_key']} | {r['year']} | {r['priority_score']} | {title[:120]} | {role} |")
        md.append("")

    md.append("## 3. Not")
    md.append("")
    md.append("Bu öneriler otomatik sinyal çıkarımına dayanır. Tabloya eklenecek nihai satırlar akademik denge, tekrar ve tez katkısına göre seçilmelidir.")

    Path(args.output_md).write_text("\n".join(md), encoding="utf-8")

    print("[INFO] Suggestions:", len(out))
    print("[INFO] CSV:", args.output_csv)
    print("[INFO] MD:", args.output_md)


if __name__ == "__main__":
    main()
