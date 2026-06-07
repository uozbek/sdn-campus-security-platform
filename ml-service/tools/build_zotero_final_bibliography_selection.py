#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

import pandas as pd


INCLUDE_RELEVANCE = {"High", "Medium", "MethodBackground"}


def clean(value) -> str:
    if value is None:
        return ""
    s = str(value)
    if s.lower() == "nan":
        return ""
    return s.strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zotero-canonical-csv", default="docs/literature_review/zotero_clean/zotero_canonical_references.csv")
    parser.add_argument("--classification-csv", default="docs/literature_review/zotero_clean/zotero_thesis_reference_classification.csv")
    parser.add_argument("--output-csv", default="docs/literature_review/zotero_clean/zotero_final_bibliography_selection.csv")
    parser.add_argument("--output-md", default="docs/literature_review/zotero_clean/zotero_final_bibliography_selection.md")
    args = parser.parse_args()

    zotero = pd.read_csv(args.zotero_canonical_csv).fillna("")
    cls = pd.read_csv(args.classification_csv).fillna("")

    if "zotero_key" not in zotero.columns or "zotero_key" not in cls.columns:
        raise SystemExit("[ERROR] both CSV files must include zotero_key")

    cls_small = cls[[
        "zotero_key",
        "auto_relevance_to_this_thesis",
        "auto_thesis_use_status",
        "reason",
        "manual_decision",
        "manual_notes",
    ]].drop_duplicates("zotero_key")

    df = zotero.merge(cls_small, on="zotero_key", how="left")

    selected_rows = []

    for _, r in df.iterrows():
        key = clean(r.get("zotero_key"))
        auto_rel = clean(r.get("auto_relevance_to_this_thesis"))
        manual_decision = clean(r.get("manual_decision"))

        if manual_decision == "include":
            selected = True
            selection_reason = "manual_include"
        elif manual_decision == "exclude":
            selected = False
            selection_reason = "manual_exclude"
        elif auto_rel in INCLUDE_RELEVANCE:
            selected = True
            selection_reason = f"auto_{auto_rel}"
        else:
            selected = False
            selection_reason = f"auto_excluded_{auto_rel}"

        if not selected:
            continue

        # Critical metadata guard.
        if not clean(r.get("title")) or not clean(r.get("authors")) or not clean(r.get("year")):
            continue

        selected_rows.append({
            "zotero_key": key,
            "id": key,
            "year": clean(r.get("year")),
            "authors": clean(r.get("authors")),
            "title": clean(r.get("title")),
            "venue": clean(r.get("venue")),
            "doi": clean(r.get("doi")),
            "url": clean(r.get("url")),
            "entry_type": clean(r.get("entry_type")),
            "abstract": clean(r.get("abstract")),
            "keywords": clean(r.get("keywords")),
            "selection_reason": selection_reason,
            "relevance_to_this_thesis": auto_rel,
            "thesis_use_status": clean(r.get("auto_thesis_use_status")),
        })

    out = pd.DataFrame(selected_rows)

    # Sort by year desc, then title.
    if not out.empty:
        out["year_sort"] = pd.to_numeric(out["year"].astype(str).str[:4], errors="coerce").fillna(0)
        out = out.sort_values(["year_sort", "title"], ascending=[False, True]).drop(columns=["year_sort"])

    Path(args.output_csv).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.output_csv, index=False)

    md = []
    md.append("# Zotero Final Bibliography Selection")
    md.append("")
    md.append(f"- Generated at UTC: `{datetime.utcnow().isoformat()}`")
    md.append(f"- Selected count: `{len(out)}`")
    md.append(f"- Input Zotero canonical: `{args.zotero_canonical_csv}`")
    md.append(f"- Classification CSV: `{args.classification_csv}`")
    md.append("")
    md.append("## 1. Selection Reason Counts")
    md.append("")
    md.append("| Reason | Count |")
    md.append("|---|---:|")
    if not out.empty:
        for k, v in out["selection_reason"].value_counts().items():
            md.append(f"| {k} | {v} |")
    md.append("")
    md.append("## 2. Selected References")
    md.append("")
    md.append("| Key | Relevance | Year | Title |")
    md.append("|---|---|---:|---|")
    for _, r in out.iterrows():
        title = clean(r["title"]).replace("|", "\\|")
        md.append(f"| {r['zotero_key']} | {r['relevance_to_this_thesis']} | {r['year']} | {title[:200]} |")

    Path(args.output_md).write_text("\n".join(md), encoding="utf-8")

    print("[INFO] CSV:", args.output_csv)
    print("[INFO] MD:", args.output_md)
    print("[INFO] Selected count:", len(out))


if __name__ == "__main__":
    main()
