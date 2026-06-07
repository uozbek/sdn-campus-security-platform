#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path

import pandas as pd
from pandas.errors import EmptyDataError




def read_csv_safe(path: str, columns: list[str] | None = None) -> pd.DataFrame:
    p = Path(path)
    if not p.exists() or p.stat().st_size == 0:
        return pd.DataFrame(columns=columns or [])
    try:
        return pd.read_csv(p).fillna("")
    except EmptyDataError:
        return pd.DataFrame(columns=columns or [])


def clean(value) -> str:
    if value is None:
        return ""
    s = str(value)
    if s.lower() == "nan":
        return ""
    return s.strip()


def norm(value: str) -> str:
    value = clean(value).lower()
    table = str.maketrans({
        "İ": "i", "I": "i", "ı": "i",
        "Ş": "s", "ş": "s",
        "Ğ": "g", "ğ": "g",
        "Ü": "u", "ü": "u",
        "Ö": "o", "ö": "o",
        "Ç": "c", "ç": "c",
        "á": "a", "à": "a", "ã": "a", "â": "a",
        "é": "e", "è": "e", "ê": "e",
        "í": "i", "ì": "i",
        "ó": "o", "ò": "o", "ô": "o",
        "ú": "u", "ù": "u",
    })
    return value.translate(table)


def citation_author_year(citation: str) -> tuple[str, str]:
    # Examples:
    # "Kalkan vd., 2017"
    # "Mitchell, 2013"
    # "Thaseen ve Kumar, 2017"
    m = re.search(r"(.+?),\s*((?:19|20)\d{2})", citation)
    if not m:
        return citation, ""
    authors = m.group(1).strip()
    year = m.group(2).strip()
    first_author = re.split(r"\s+vd\.|\s+ve\s+|\s+and\s+", authors)[0].strip()
    return first_author, year


def tracking_match(tracking: pd.DataFrame, author: str, year: str) -> list[dict]:
    if tracking.empty:
        return []

    author_n = norm(author)
    year_s = str(year).replace(".0", "")

    matches = []
    for _, row in tracking.iterrows():
        authors = clean(row.get("authors"))
        title = clean(row.get("title"))
        row_year = clean(row.get("year")).replace(".0", "")
        hay = norm(authors + " " + title)

        if row_year == year_s and author_n and author_n in hay:
            matches.append({
                "id": clean(row.get("id")),
                "year": row_year,
                "authors": authors,
                "title": title,
                "venue": clean(row.get("venue")),
                "relevance": clean(row.get("relevance_to_this_thesis")),
            })

    return matches


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apa-audit-csv", default="docs/apa_inline_citation_audit.csv")
    parser.add_argument("--tracking-csv", default="docs/literature_review/literature_tracking_table.csv")
    parser.add_argument("--canonical-override-csv", default="docs/citation_canonical_id_override.csv")
    parser.add_argument("--output-md", default="docs/citation_bibliography_consistency_report.md")
    parser.add_argument("--output-csv", default="docs/citation_bibliography_consistency_report.csv")
    parser.add_argument("--output-json", default="docs/citation_bibliography_consistency_report.json")
    args = parser.parse_args()

    audit = read_csv_safe(args.apa_audit_csv, columns=["file", "line", "citation_item", "parenthetical_group", "context"])
    tracking = read_csv_safe(args.tracking_csv)
    override_df = read_csv_safe(args.canonical_override_csv, columns=["citation", "canonical_id", "note"])

    override_map = {}
    if not override_df.empty:
        override_map = {
            clean(row.get("citation")): clean(row.get("canonical_id"))
            for _, row in override_df.iterrows()
            if clean(row.get("citation")) and clean(row.get("canonical_id"))
        }

    tracking_by_id = {}
    if not tracking.empty and "id" in tracking.columns:
        tracking_by_id = {
            clean(row.get("id")): row
            for _, row in tracking.iterrows()
            if clean(row.get("id"))
        }

    unique_citations = sorted(audit["citation_item"].unique()) if not audit.empty else []

    rows = []
    for citation in unique_citations:
        author, year = citation_author_year(citation)

        if citation in override_map and override_map[citation] in tracking_by_id:
            rid = override_map[citation]
            row = tracking_by_id[rid]
            matches = [{
                "id": rid,
                "year": clean(row.get("year")).replace(".0", ""),
                "authors": clean(row.get("authors")),
                "title": clean(row.get("title")),
                "venue": clean(row.get("venue")),
                "relevance": clean(row.get("relevance_to_this_thesis")),
            }]
            status = "matched_by_override"
        else:
            matches = tracking_match(tracking, author, year)
            status = "matched" if len(matches) == 1 else "multiple_matches" if len(matches) > 1 else "not_found"

        rows.append({
            "citation": citation,
            "parsed_author": author,
            "parsed_year": year,
            "status": status,
            "match_count": len(matches),
            "matched_ids": "; ".join(m["id"] for m in matches),
            "matched_titles": " || ".join(m["title"] for m in matches),
            "matched_relevance": "; ".join(m["relevance"] for m in matches),
        })

    out_columns = [
        "citation",
        "parsed_author",
        "parsed_year",
        "status",
        "match_count",
        "matched_ids",
        "matched_titles",
        "matched_relevance",
    ]
    out = pd.DataFrame(rows, columns=out_columns)
    Path(args.output_csv).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.output_csv, index=False)

    result = {
        "generated_at_utc": datetime.utcnow().isoformat(),
        "citation_count": len(unique_citations),
        "status_counts": out["status"].value_counts().to_dict() if not out.empty else {},
    }
    Path(args.output_json).write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    md = []
    md.append("# Citation–Bibliography Consistency Report")
    md.append("")
    md.append(f"- Generated at UTC: `{result['generated_at_utc']}`")
    md.append(f"- Citation count: `{result['citation_count']}`")
    md.append(f"- Status counts: `{result['status_counts']}`")
    md.append("")
    md.append("| Citation | Parsed author | Year | Status | Matched IDs | Matched titles |")
    md.append("|---|---|---:|---|---|---|")

    for _, r in out.iterrows():
        titles = clean(r["matched_titles"]).replace("|", "\\|")
        md.append(
            f"| {r['citation']} | {r['parsed_author']} | {r['parsed_year']} | "
            f"{r['status']} | {r['matched_ids']} | {titles[:220]} |"
        )

    md.append("")
    md.append("## Not")
    md.append("")
    md.append("`not_found` veya `multiple_matches` durumları manuel kontrol gerektirir. Bu rapor yalnızca metin içi atıfların tracking tablosunda karşılığının bulunup bulunmadığını kontrol eder; nihai APA7 biçim kontrolünün yerine geçmez.")

    Path(args.output_md).write_text("\n".join(md), encoding="utf-8")

    print("[INFO] MD:", args.output_md)
    print("[INFO] CSV:", args.output_csv)
    print("[INFO] JSON:", args.output_json)
    print("[INFO] Status counts:", result["status_counts"])


if __name__ == "__main__":
    main()
