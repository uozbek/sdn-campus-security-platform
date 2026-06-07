#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path
from datetime import datetime

import pandas as pd


def clean(v) -> str:
    if v is None:
        return ""
    s = str(v)
    if s.lower() == "nan":
        return ""
    return s.strip()


def split_authors(authors: str):
    authors = clean(authors)
    if not authors:
        return []
    # Zotero/BibTeX tarafında çoğunlukla "and" kullanılır.
    parts = re.split(r"\s+and\s+|;", authors)
    return [p.strip() for p in parts if p.strip()]


def normalize_author(a: str) -> str:
    a = clean(a).lower()
    a = re.sub(r"[^a-zğüşöçıİĞÜŞÖÇ0-9]+", " ", a)
    return re.sub(r"\s+", " ", a).strip()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--references-csv",
        default="docs/references_zotero_apa_like_reviewed.csv",
    )
    parser.add_argument(
        "--output-md",
        default="docs/zotero_apa_reference_quality_audit.md",
    )
    parser.add_argument(
        "--output-csv",
        default="docs/zotero_apa_reference_quality_audit.csv",
    )
    args = parser.parse_args()

    df = pd.read_csv(args.references_csv).fillna("")

    rows = []
    for _, r in df.iterrows():
        key = clean(r.get("zotero_key") or r.get("id"))
        title = clean(r.get("title"))
        authors = clean(r.get("authors"))
        venue = clean(r.get("venue"))
        doi = clean(r.get("doi"))
        url = clean(r.get("url"))
        year = clean(r.get("year"))
        apa = clean(r.get("apa_like") or r.get("reference") or r.get("formatted_reference"))

        issues = []

        if not key:
            issues.append("missing_key")
        if not title:
            issues.append("missing_title")
        if not authors:
            issues.append("missing_authors")
        if not year:
            issues.append("missing_year")
        if not venue:
            issues.append("missing_venue")
        if not doi and not url:
            issues.append("missing_doi_and_url")

        author_list = split_authors(authors)
        norm_authors = [normalize_author(a) for a in author_list]
        if len(norm_authors) != len(set(norm_authors)):
            issues.append("duplicate_authors_in_metadata")

        if ".." in venue or ".." in apa:
            issues.append("double_period")

        if "{" in title or "}" in title or "{" in venue or "}" in venue:
            issues.append("bibtex_braces_remaining")

        if len(title) < 15:
            issues.append("possibly_truncated_title")

        if doi and not doi.lower().startswith("10."):
            issues.append("suspicious_doi")

        if "http" not in doi.lower() and doi and "/" not in doi:
            issues.append("suspicious_doi_format")

        rows.append({
            "zotero_key": key,
            "year": year,
            "title": title,
            "authors": authors,
            "venue": venue,
            "doi": doi,
            "url": url,
            "issue_count": len(issues),
            "issues": ";".join(issues),
        })

    out = pd.DataFrame(rows)
    out.to_csv(args.output_csv, index=False)

    issue_rows = out[out["issue_count"] > 0].copy()
    issue_counts = {}
    for issue_str in issue_rows["issues"]:
        for item in issue_str.split(";"):
            if item:
                issue_counts[item] = issue_counts.get(item, 0) + 1

    md = []
    md.append("# Zotero APA Reference Quality Audit")
    md.append("")
    md.append(f"- Generated at UTC: `{datetime.utcnow().isoformat()}`")
    md.append(f"- References CSV: `{args.references_csv}`")
    md.append(f"- Reference count: `{len(out)}`")
    md.append(f"- Records with issues: `{len(issue_rows)}`")
    md.append("")
    md.append("## 1. Issue Counts")
    md.append("")
    md.append("| Issue | Count |")
    md.append("|---|---:|")
    for k, v in sorted(issue_counts.items(), key=lambda x: (-x[1], x[0])):
        md.append(f"| {k} | {v} |")

    md.append("")
    md.append("## 2. Records Requiring Review")
    md.append("")
    if issue_rows.empty:
        md.append("No reference quality issues detected.")
    else:
        md.append("| Key | Year | Issues | Title |")
        md.append("|---|---:|---|---|")
        for _, r in issue_rows.iterrows():
            title = clean(r["title"]).replace("|", "\\|")
            md.append(f"| {r['zotero_key']} | {r['year']} | {r['issues']} | {title[:180]} |")

    Path(args.output_md).write_text("\n".join(md), encoding="utf-8")

    print("[INFO] MD:", args.output_md)
    print("[INFO] CSV:", args.output_csv)
    print("[INFO] Records with issues:", len(issue_rows))
    print("[INFO] Issue counts:", issue_counts)


if __name__ == "__main__":
    main()
