#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def clean(value) -> str:
    if value is None:
        return ""
    s = str(value)
    if s.lower() == "nan":
        return ""
    return s.strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--tracking-csv",
        default="docs/literature_review/literature_tracking_table.csv",
    )
    parser.add_argument(
        "--synthesis-csv",
        default="docs/literature_review/synthesis/chapter3_literature_synthesis_candidates.csv",
    )
    parser.add_argument(
        "--canonical-override-csv",
        default="docs/citation_canonical_id_override.csv",
    )
    parser.add_argument(
        "--output-csv",
        default="docs/expanded_bibliography_selection.csv",
    )
    parser.add_argument(
        "--output-md",
        default="docs/expanded_bibliography_selection.md",
    )
    args = parser.parse_args()

    tracking = pd.read_csv(args.tracking_csv).fillna("")
    synthesis = pd.read_csv(args.synthesis_csv).fillna("") if Path(args.synthesis_csv).exists() else pd.DataFrame()
    override = pd.read_csv(args.canonical_override_csv).fillna("") if Path(args.canonical_override_csv).exists() else pd.DataFrame()

    selected = {}

    # Include records that were promoted from MAN to canonical BIB IDs.
    # These records may not appear in the synthesis candidate CSV because they
    # were created after manual review.
    if "thesis_use_status" in tracking.columns and "id" in tracking.columns:
        for _, row in tracking.iterrows():
            rid = clean(row.get("id"))
            thesis_use_status = clean(row.get("thesis_use_status"))
            relevance = clean(row.get("relevance_to_this_thesis"))
            if rid and thesis_use_status == "canonical_from_manual":
                selected.setdefault(rid, "tracking_canonical_from_manual")
            elif rid and relevance == "MethodBackground" and thesis_use_status in {"keep_method_background", "canonical_from_manual"}:
                selected.setdefault(rid, "tracking_method_background")

    # 1. Always include canonical inline-cited sources.
    if not override.empty and "canonical_id" in override.columns:
        for rid in override["canonical_id"].astype(str):
            rid = clean(rid)
            if rid:
                selected[rid] = "inline_citation_canonical"

    # 2. Include synthesis candidates if they are High or Medium.
    if not synthesis.empty and "id" in synthesis.columns:
        for _, row in synthesis.iterrows():
            rid = clean(row.get("id"))
            relevance = clean(row.get("relevance_to_this_thesis"))
            reason = clean(row.get("selection_reason"))

            if not rid:
                continue

            thesis_use_status = clean(row.get("thesis_use_status"))

            if relevance in {"High", "Medium", "MethodBackground"}:
                selected.setdefault(rid, f"synthesis_{relevance.lower()}")

            if thesis_use_status == "canonical_from_manual":
                selected.setdefault(rid, "canonical_from_manual")

            # Also include explicitly fulltext/keyword/relevance selected records.
            if any(k in reason.lower() for k in ["relevance", "keyword", "fulltext"]):
                if relevance != "Low":
                    selected.setdefault(rid, f"synthesis_reason_{reason}")

    tracking_by_id = {
        clean(row.get("id")): row
        for _, row in tracking.iterrows()
        if clean(row.get("id"))
    }

    rows = []
    missing = []

    for rid, selection_source in selected.items():
        row = tracking_by_id.get(rid)
        if row is None:
            missing.append(rid)
            continue

        title = clean(row.get("title"))
        authors = clean(row.get("authors"))
        venue = clean(row.get("venue"))
        relevance = clean(row.get("relevance_to_this_thesis"))

        # Exclude obviously bad/manual/placeholder records.
        if rid.startswith("MAN"):
            continue
        if "to verify from full text" in venue.lower():
            continue
        if "to verify from full text" in title.lower():
            continue
        thesis_use_status = clean(row.get("thesis_use_status"))

        if thesis_use_status == "canonical_from_manual":
            pass
        elif relevance == "Low" and selection_source != "inline_citation_canonical":
            continue
        elif relevance in {"Excluded", "Duplicate", "Discarded"}:
            continue

        rows.append({
            "id": rid,
            "selection_source": selection_source,
            "year": clean(row.get("year")).replace(".0", ""),
            "authors": authors,
            "title": title,
            "venue": venue,
            "doi_url": clean(row.get("doi_url")),
            "relevance_to_this_thesis": relevance,
        })

    out = pd.DataFrame(rows)

    if not out.empty:
        out = out.drop_duplicates(subset=["id"])
        out = out.sort_values(["relevance_to_this_thesis", "year", "id"], ascending=[True, False, True])

    Path(args.output_csv).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.output_csv, index=False)

    md = []
    md.append("# Expanded Bibliography Selection")
    md.append("")
    md.append(f"- Selected reference count: `{len(out)}`")
    md.append(f"- Missing selected IDs in tracking table: `{missing}`")
    md.append("")
    md.append("## 1. Selection Summary")
    md.append("")
    if not out.empty:
        md.append("### By selection source")
        md.append("")
        md.append(out["selection_source"].value_counts().to_markdown())
        md.append("")
        md.append("### By relevance")
        md.append("")
        md.append(out["relevance_to_this_thesis"].value_counts().to_markdown())
        md.append("")

    md.append("## 2. Selected References")
    md.append("")
    md.append("| ID | Year | Relevance | Source | Title |")
    md.append("|---|---:|---|---|---|")

    for _, r in out.iterrows():
        title = clean(r["title"]).replace("|", "\\|")
        md.append(
            f"| {r['id']} | {r['year']} | {r['relevance_to_this_thesis']} | "
            f"{r['selection_source']} | {title[:180]} |"
        )

    Path(args.output_md).write_text("\n".join(md), encoding="utf-8")

    print("[INFO] CSV:", args.output_csv)
    print("[INFO] MD :", args.output_md)
    print("[INFO] Selected reference count:", len(out))
    print("[INFO] Missing IDs:", missing)


if __name__ == "__main__":
    main()
