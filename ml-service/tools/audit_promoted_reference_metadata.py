#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from datetime import datetime
import json
import re

import pandas as pd


BAD_TITLE_PATTERNS = [
    r"\bBas$",
    r"\bFeatur$",
    r"\bcontrolle$",
    r"\bDistri$",
    r"\bSchem$",
    r"\bin$",
    r"\bDataset$",
    r"\bof$",
    r"\bsyste$",
    r"\bNetwork$",
    r"\bFro$",
    r"\bA$",
    r"\bidentificati$",
    r"\bServi$",
    r"\bsqua$",
]


def clean(value) -> str:
    if value is None:
        return ""
    s = str(value)
    if s.lower() == "nan":
        return ""
    return s.strip()


def has_bad_title(title: str) -> bool:
    title = clean(title)
    if len(title) < 35:
        return True
    for pat in BAD_TITLE_PATTERNS:
        if re.search(pat, title, flags=re.IGNORECASE):
            return True
    return False


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--tracking-csv",
        default="docs/literature_review/literature_tracking_table.csv",
    )
    parser.add_argument(
        "--promotion-map-csv",
        default="docs/manual_to_canonical_promotion_map.csv",
    )
    parser.add_argument(
        "--references-csv",
        default="docs/references_apa_like.csv",
    )
    parser.add_argument(
        "--output-md",
        default="docs/promoted_reference_metadata_audit.md",
    )
    parser.add_argument(
        "--output-csv",
        default="docs/promoted_reference_metadata_audit.csv",
    )
    parser.add_argument(
        "--output-json",
        default="docs/promoted_reference_metadata_audit.json",
    )
    args = parser.parse_args()

    tracking = pd.read_csv(args.tracking_csv).fillna("")
    promotion = pd.read_csv(args.promotion_map_csv).fillna("")
    refs = pd.read_csv(args.references_csv).fillna("") if Path(args.references_csv).exists() else pd.DataFrame()

    ref_ids = set(refs["id"].astype(str)) if not refs.empty and "id" in refs.columns else set()

    tracking_by_id = {
        clean(row.get("id")): row
        for _, row in tracking.iterrows()
        if clean(row.get("id"))
    }

    rows = []

    for _, m in promotion.iterrows():
        man_id = clean(m.get("manual_id"))
        bib_id = clean(m.get("canonical_id"))
        status = clean(m.get("status"))

        row = tracking_by_id.get(bib_id)
        if row is None:
            rows.append({
                "manual_id": man_id,
                "canonical_id": bib_id,
                "in_tracking": False,
                "in_bibliography": bib_id in ref_ids,
                "status": "missing_in_tracking",
                "issues": "missing_in_tracking",
            })
            continue

        title = clean(row.get("title"))
        authors = clean(row.get("authors"))
        year = clean(row.get("year")).replace(".0", "")
        venue = clean(row.get("venue"))
        doi_url = clean(row.get("doi_url"))

        issues = []

        if not authors:
            issues.append("missing_authors")
        if not year:
            issues.append("missing_year")
        if not title:
            issues.append("missing_title")
        elif has_bad_title(title):
            issues.append("possibly_truncated_title")
        if not venue or "to verify" in venue.lower():
            issues.append("missing_or_unverified_venue")
        if not doi_url:
            issues.append("missing_doi_url")
        if bib_id not in ref_ids:
            issues.append("not_in_bibliography")

        quality = "ok" if not issues else "check"

        rows.append({
            "manual_id": man_id,
            "canonical_id": bib_id,
            "promotion_status": status,
            "in_tracking": True,
            "in_bibliography": bib_id in ref_ids,
            "quality": quality,
            "issues": ";".join(issues),
            "year": year,
            "authors": authors,
            "title": title,
            "venue": venue,
            "doi_url": doi_url,
            "relevance_to_this_thesis": clean(row.get("relevance_to_this_thesis")),
            "thesis_use_status": clean(row.get("thesis_use_status")),
        })

    out = pd.DataFrame(rows)
    out.to_csv(args.output_csv, index=False)

    summary = {
        "generated_at_utc": datetime.utcnow().isoformat(),
        "promoted_count": len(out),
        "quality_counts": out["quality"].value_counts().to_dict() if "quality" in out.columns else {},
        "issue_counts": {},
    }

    issue_counts = {}
    for issues in out.get("issues", pd.Series(dtype=str)).astype(str):
        for issue in issues.split(";"):
            issue = issue.strip()
            if issue:
                issue_counts[issue] = issue_counts.get(issue, 0) + 1
    summary["issue_counts"] = issue_counts

    Path(args.output_json).write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    md = []
    md.append("# Promoted Reference Metadata Audit")
    md.append("")
    md.append(f"- Generated at UTC: `{summary['generated_at_utc']}`")
    md.append(f"- Promoted count: `{summary['promoted_count']}`")
    md.append(f"- Quality counts: `{summary['quality_counts']}`")
    md.append(f"- Issue counts: `{summary['issue_counts']}`")
    md.append("")
    md.append("## 1. Promoted Records")
    md.append("")
    md.append("| Manual ID | Canonical ID | In bibliography | Quality | Issues | Year | Title |")
    md.append("|---|---|---|---|---|---:|---|")

    for _, r in out.iterrows():
        title = clean(r.get("title")).replace("|", "\\|")
        md.append(
            f"| {r.get('manual_id')} | {r.get('canonical_id')} | {r.get('in_bibliography')} | "
            f"{r.get('quality')} | {r.get('issues')} | {r.get('year')} | {title[:220]} |"
        )

    md.append("")
    md.append("## 2. Action Guidance")
    md.append("")
    md.append("- `possibly_truncated_title`: tracking tablosundaki başlık tam makale başlığı ile güncellenmeli.")
    md.append("- `missing_or_unverified_venue`: dergi/konferans adı doğrulanmalı.")
    md.append("- `missing_doi_url`: DOI veya güvenilir URL eklenmeli.")
    md.append("- `not_in_bibliography`: selection filtresi veya relevance/thesis_use_status kontrol edilmeli.")

    Path(args.output_md).write_text("\n".join(md), encoding="utf-8")

    print("[INFO] MD:", args.output_md)
    print("[INFO] CSV:", args.output_csv)
    print("[INFO] JSON:", args.output_json)
    print("[INFO] Quality counts:", summary["quality_counts"])
    print("[INFO] Issue counts:", summary["issue_counts"])


if __name__ == "__main__":
    main()
