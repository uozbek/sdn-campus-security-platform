#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from datetime import datetime
import pandas as pd


def clean(s):
    return str(s or "").strip()


def decision_for_row(r):
    status = clean(r.get("match_status", ""))
    text = clean(r.get("manuscript_row_text", ""))
    ref = clean(r.get("manuscript_ref", ""))
    zkey = clean(r.get("zotero_key", ""))
    lower = (text + " " + ref + " " + zkey).lower()

    if status == "proposed_model":
        return "manuscript_proposed_model_keep_as_article_result_not_reference"

    if "nsl-kdd" in lower:
        return "historical_context_only_do_not_expand_in_thesis"

    if status == "strong_surname_year_match":
        if any(x in lower for x in [
            "cic-ddos2019", "sdn", "ddos", "mitigation",
            "controller", "ryu", "openflow", "cic dos"
        ]):
            return "usable_for_thesis_literature_or_comparison"
        return "supporting_only"

    return "manual_check_before_use"


def target_section_for_row(r):
    text = clean(r.get("manuscript_row_text", "")).lower()
    status = clean(r.get("match_status", ""))

    if status == "proposed_model":
        return "Makale sonuç tablosu; kaynakça satırı değildir"

    if "nsl-kdd" in text:
        return "Bölüm 3 bağlamsal/tarihsel not; tezde genişletme, makalede azalt/çıkar"

    if any(x in text for x in ["mitigation", "prevention", "bandwidth", "protecting", "ddos"]):
        return "Bölüm 3 Tablo 3.5 / Tablo 3.7 veya Bölüm 5 tartışma"

    if any(x in text for x in ["cic-ddos2019", "feature", "selection", "lstm", "cnn", "xgboost", "ensemble"]):
        return "Bölüm 3 literatür karşılaştırması / Bölüm 4 yöntem gerekçesi"

    return "Bölüm 3 destekleyici literatür"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--alignment-csv",
        default="docs/literature_review/manuscript_alignment/manuscript_zotero_alignment_v2.csv",
    )
    parser.add_argument(
        "--output-csv",
        default="docs/literature_review/manuscript_alignment/manuscript_alignment_decisions.csv",
    )
    parser.add_argument(
        "--output-md",
        default="docs/literature_review/manuscript_alignment/manuscript_alignment_decision_report.md",
    )
    args = parser.parse_args()

    df = pd.read_csv(args.alignment_csv).fillna("")

    df["alignment_decision"] = df.apply(decision_for_row, axis=1)
    df["target_section"] = df.apply(target_section_for_row, axis=1)

    Path(args.output_csv).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.output_csv, index=False)

    md = []
    md.append("# Manuscript Alignment Decision Report")
    md.append("")
    md.append(f"- Generated at UTC: `{datetime.utcnow().isoformat()}`")
    md.append(f"- Input alignment CSV: `{args.alignment_csv}`")
    md.append(f"- Output CSV: `{args.output_csv}`")
    md.append(f"- Total rows: `{len(df)}`")
    md.append("")

    md.append("## 1. Match Status Counts")
    md.append("")
    md.append("| Status | Count |")
    md.append("|---|---:|")
    for k, v in df["match_status"].value_counts().items():
        md.append(f"| {k} | {v} |")
    md.append("")

    md.append("## 2. Alignment Decision Counts")
    md.append("")
    md.append("| Decision | Count |")
    md.append("|---|---:|")
    for k, v in df["alignment_decision"].value_counts().items():
        md.append(f"| {k} | {v} |")
    md.append("")

    md.append("## 3. Manual Check Required")
    md.append("")
    manual = df[df["alignment_decision"].eq("manual_check_before_use")]
    if len(manual) == 0:
        md.append("No manual-check rows detected.")
    else:
        md.append("| Table | Row | Manuscript ref | Best Zotero key | Best Zotero title | Note |")
        md.append("|---:|---:|---|---|---|---|")
        for _, r in manual.iterrows():
            md.append(
                f"| {r['table_no']} | {r['row_no']} | {clean(r['manuscript_ref'])} | "
                f"{clean(r['zotero_key'])} | {clean(r['zotero_title'])[:120]} | "
                f"{clean(r['review_note'])} |"
            )
    md.append("")

    md.append("## 4. NSL-KDD / Historical Context Rows")
    md.append("")
    nsl = df[df["alignment_decision"].eq("historical_context_only_do_not_expand_in_thesis")]
    if len(nsl) == 0:
        md.append("No NSL-KDD rows detected.")
    else:
        md.append("| Table | Row | Manuscript ref | Zotero key | Decision |")
        md.append("|---:|---:|---|---|---|")
        for _, r in nsl.iterrows():
            md.append(
                f"| {r['table_no']} | {r['row_no']} | {clean(r['manuscript_ref'])} | "
                f"{clean(r['zotero_key'])} | Tezde yalnızca tarihsel/bağlamsal; makalede çıkar/azalt |"
            )
    md.append("")

    md.append("## 5. Thesis-Usable Strong Matches")
    md.append("")
    usable = df[df["alignment_decision"].eq("usable_for_thesis_literature_or_comparison")]
    if len(usable) == 0:
        md.append("No thesis-usable rows detected.")
    else:
        md.append("| Table | Row | Manuscript ref | Zotero key | Zotero title | Target section |")
        md.append("|---:|---:|---|---|---|---|")
        for _, r in usable.iterrows():
            md.append(
                f"| {r['table_no']} | {r['row_no']} | {clean(r['manuscript_ref'])} | "
                f"{clean(r['zotero_key'])} | {clean(r['zotero_title'])[:120]} | "
                f"{clean(r['target_section'])} |"
            )
    md.append("")

    md.append("## 6. Proposed Model Rows")
    md.append("")
    proposed = df[df["match_status"].eq("proposed_model")]
    if len(proposed) == 0:
        md.append("No proposed model rows detected.")
    else:
        md.append("| Table | Row | Manuscript ref | Decision |")
        md.append("|---:|---:|---|---|")
        for _, r in proposed.iterrows():
            md.append(
                f"| {r['table_no']} | {r['row_no']} | {clean(r['manuscript_ref'])} | "
                f"Makale sonucu olarak kalmalı; Zotero kaynağı değildir. |"
            )

    Path(args.output_md).write_text("\n".join(md), encoding="utf-8")

    print("[INFO] Rows:", len(df))
    print("[INFO] Decisions:", df["alignment_decision"].value_counts().to_dict())
    print("[INFO] CSV:", args.output_csv)
    print("[INFO] MD:", args.output_md)


if __name__ == "__main__":
    main()
