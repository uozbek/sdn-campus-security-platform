#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

import pandas as pd


VALID_DECISIONS = {
    "",
    "keep_core",
    "keep_supporting",
    "keep_method_background",
    "exclude_from_final_bibliography",
    "needs_fulltext_check",
}


def clean(value) -> str:
    if value is None:
        return ""
    s = str(value)
    if s.lower() == "nan":
        return ""
    return s.strip()


def fallback_decision(suggested: str) -> str:
    suggested = clean(suggested)
    if suggested == "keep_core":
        return "keep_core"
    if suggested == "keep_supporting":
        return "keep_supporting"
    if suggested == "keep_if_cited_in_method":
        return "keep_method_background"
    if suggested == "review_or_exclude":
        return "needs_fulltext_check"
    return "needs_fulltext_check"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--review-xlsx",
        default="docs/literature_review/zotero_clean/zotero_final_bibliography_review.xlsx",
    )
    parser.add_argument(
        "--canonical-csv",
        default="docs/literature_review/zotero_clean/zotero_canonical_references.csv",
    )
    parser.add_argument(
        "--output-selection-csv",
        default="docs/literature_review/zotero_clean/zotero_final_bibliography_selection_reviewed.csv",
    )
    parser.add_argument(
        "--output-review-csv",
        default="docs/literature_review/zotero_clean/zotero_final_bibliography_review_decisions.csv",
    )
    parser.add_argument(
        "--report-md",
        default="docs/literature_review/zotero_clean/zotero_final_bibliography_review_applied.md",
    )
    args = parser.parse_args()

    review = pd.read_excel(args.review_xlsx, sheet_name="review").fillna("")
    canonical = pd.read_csv(args.canonical_csv).fillna("")

    if "zotero_key" not in review.columns:
        raise SystemExit("[ERROR] review xlsx must include zotero_key")
    if "zotero_key" not in canonical.columns:
        raise SystemExit("[ERROR] canonical csv must include zotero_key")

    decisions = set(review["final_decision"].astype(str).map(clean).unique())
    invalid = sorted(decisions - VALID_DECISIONS)
    if invalid:
        raise SystemExit(f"[ERROR] Invalid final_decision values: {invalid}")

    review["effective_decision"] = review.apply(
        lambda r: clean(r.get("final_decision")) or fallback_decision(r.get("suggested_decision")),
        axis=1,
    )

    review_out = Path(args.output_review_csv)
    review_out.parent.mkdir(parents=True, exist_ok=True)
    review.to_csv(review_out, index=False)

    decision_map = {
        clean(r["zotero_key"]): {
            "effective_decision": clean(r["effective_decision"]),
            "suggested_decision": clean(r.get("suggested_decision")),
            "chapter_target": clean(r.get("chapter_target")),
            "notes": clean(r.get("notes")),
        }
        for _, r in review.iterrows()
        if clean(r.get("zotero_key"))
    }

    selected = []

    for _, row in canonical.iterrows():
        key = clean(row.get("zotero_key"))
        d = decision_map.get(key)

        if not d:
            continue

        decision = d["effective_decision"]

        include = decision in {
            "keep_core",
            "keep_supporting",
            "keep_method_background",
            "needs_fulltext_check",
        }

        if not include:
            continue

        if not clean(row.get("title")) or not clean(row.get("authors")) or not clean(row.get("year")):
            continue

        selected.append({
            "zotero_key": key,
            "id": key,
            "year": clean(row.get("year")),
            "authors": clean(row.get("authors")),
            "title": clean(row.get("title")),
            "venue": clean(row.get("venue")),
            "doi": clean(row.get("doi")),
            "url": clean(row.get("url")),
            "entry_type": clean(row.get("entry_type")),
            "abstract": clean(row.get("abstract")),
            "keywords": clean(row.get("keywords")),
            "final_decision": decision,
            "suggested_decision": d["suggested_decision"],
            "chapter_target": d["chapter_target"],
            "notes": d["notes"],
            "selection_reason": f"review_{decision}",
            "relevance_to_this_thesis": {
                "keep_core": "High",
                "keep_supporting": "Medium",
                "keep_method_background": "MethodBackground",
                "needs_fulltext_check": "NeedsFulltextCheck",
            }.get(decision, "Review"),
        })

    out = pd.DataFrame(selected)

    if not out.empty:
        out["year_sort"] = pd.to_numeric(out["year"].astype(str).str[:4], errors="coerce").fillna(0)
        out = out.sort_values(["year_sort", "title"], ascending=[False, True]).drop(columns=["year_sort"])

    selection_out = Path(args.output_selection_csv)
    selection_out.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(selection_out, index=False)

    counts = out["final_decision"].value_counts().to_dict() if not out.empty else {}
    all_counts = review["effective_decision"].value_counts().to_dict()

    md = []
    md.append("# Zotero Final Bibliography Review Applied")
    md.append("")
    md.append(f"- Generated at UTC: `{datetime.utcnow().isoformat()}`")
    md.append(f"- Review XLSX: `{args.review_xlsx}`")
    md.append(f"- Canonical CSV: `{args.canonical_csv}`")
    md.append(f"- Output selection CSV: `{args.output_selection_csv}`")
    md.append(f"- Review decision CSV: `{args.output_review_csv}`")
    md.append(f"- Selected reference count: `{len(out)}`")
    md.append("")
    md.append("## 1. All Effective Decision Counts")
    md.append("")
    md.append("| Decision | Count |")
    md.append("|---|---:|")
    for k, v in all_counts.items():
        md.append(f"| {k} | {v} |")

    md.append("")
    md.append("## 2. Selected Decision Counts")
    md.append("")
    md.append("| Decision | Count |")
    md.append("|---|---:|")
    for k, v in counts.items():
        md.append(f"| {k} | {v} |")

    md.append("")
    md.append("## 3. Selected References")
    md.append("")
    md.append("| Key | Decision | Chapter target | Year | Title |")
    md.append("|---|---|---|---:|---|")
    for _, r in out.iterrows():
        title = clean(r["title"]).replace("|", "\\|")
        md.append(
            f"| {r['zotero_key']} | {r['final_decision']} | {r['chapter_target']} | "
            f"{r['year']} | {title[:200]} |"
        )

    md.append("")
    md.append("## 4. Excluded / Not Selected")
    md.append("")
    excluded = review[review["effective_decision"].eq("exclude_from_final_bibliography")]
    if excluded.empty:
        md.append("No excluded records.")
    else:
        md.append("| Key | Suggested | Title |")
        md.append("|---|---|---|")
        for _, r in excluded.iterrows():
            title = clean(r.get("title")).replace("|", "\\|")
            md.append(f"| {r['zotero_key']} | {r.get('suggested_decision')} | {title[:180]} |")

    report = Path(args.report_md)
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("\n".join(md), encoding="utf-8")

    print("[INFO] Selection CSV:", args.output_selection_csv)
    print("[INFO] Review CSV:", args.output_review_csv)
    print("[INFO] Report:", args.report_md)
    print("[INFO] Selected count:", len(out))
    print("[INFO] Selected decision counts:", counts)


if __name__ == "__main__":
    main()
