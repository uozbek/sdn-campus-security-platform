#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd


def clean(value) -> str:
    if value is None:
        return ""
    s = str(value)
    if s.lower() == "nan":
        return ""
    return s.strip()


def normalize_year(year: str) -> str:
    return clean(year).replace(".0", "")


def author_to_apaish(authors: str) -> str:
    authors = clean(authors)
    if not authors:
        return ""

    parts = [p.strip() for p in re.split(r"\s+and\s+|;", authors) if p.strip()]
    if not parts:
        return authors

    formatted = []
    for a in parts[:8]:
        # Basic BibTeX style: Surname, Name
        if "," in a:
            surname, rest = [x.strip() for x in a.split(",", 1)]
            initials = " ".join([x[0] + "." for x in rest.split() if x])
            formatted.append(f"{surname}, {initials}".strip())
        else:
            tokens = a.split()
            if len(tokens) >= 2:
                surname = tokens[-1]
                initials = " ".join([x[0] + "." for x in tokens[:-1] if x])
                formatted.append(f"{surname}, {initials}".strip())
            else:
                formatted.append(a)

    if len(parts) > 8:
        formatted.append("vd.")

    if len(formatted) == 1:
        return formatted[0]
    if len(formatted) == 2:
        return " ve ".join(formatted)
    return ", ".join(formatted[:-1]) + " ve " + formatted[-1]


def apa_like_reference(row) -> str:
    authors = author_to_apaish(row.get("authors", ""))
    year = normalize_year(row.get("year", ""))
    title = clean(row.get("title"))
    venue = clean(row.get("venue"))
    doi_url = clean(row.get("doi_url"))

    parts = []
    if authors:
        parts.append(authors)
    if year:
        parts.append(f"({year}).")
    if title:
        parts.append(f"{title}.")
    if venue:
        parts.append(f"{venue}.")
    if doi_url:
        parts.append(doi_url)

    return " ".join(parts).strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tracking-csv", default="docs/literature_review/literature_tracking_table.csv")
    parser.add_argument("--citation-consistency-csv", default="docs/citation_bibliography_consistency_report.csv")
    parser.add_argument("--canonical-override-csv", default="docs/citation_canonical_id_override.csv")
    parser.add_argument("--reference-override-csv", default="docs/reference_apa_manual_override.csv")
    parser.add_argument("--output-md", default="docs/references_apa_like.md")
    parser.add_argument("--output-csv", default="docs/references_apa_like.csv")
    args = parser.parse_args()

    tracking = pd.read_csv(args.tracking_csv).fillna("")
    consistency = pd.read_csv(args.citation_consistency_csv).fillna("") if Path(args.citation_consistency_csv).exists() else pd.DataFrame()
    override = pd.read_csv(args.canonical_override_csv).fillna("") if Path(args.canonical_override_csv).exists() else pd.DataFrame()
    reference_override = pd.read_csv(args.reference_override_csv).fillna("") if Path(args.reference_override_csv).exists() else pd.DataFrame()

    reference_override_map = {}
    if not reference_override.empty and {"id", "apa_like_reference"}.issubset(reference_override.columns):
        reference_override_map = {
            clean(row.get("id")): clean(row.get("apa_like_reference"))
            for _, row in reference_override.iterrows()
            if clean(row.get("id")) and clean(row.get("apa_like_reference"))
        }

    used_ids = []

    # Primary source: canonical override table. This prevents MAN duplicate records
    # and ambiguous multiple_matches from entering the bibliography.
    if not override.empty and "canonical_id" in override.columns:
        for rid in override["canonical_id"].astype(str).tolist():
            rid = rid.strip()
            if rid and rid not in used_ids:
                used_ids.append(rid)

    # Fallback: consistency report IDs, but only if override is unavailable.
    if not used_ids and not consistency.empty:
        for ids in consistency.get("matched_ids", []):
            for rid in str(ids).split(";"):
                rid = rid.strip()
                if rid and rid not in used_ids:
                    used_ids.append(rid)

    if used_ids:
        refs = tracking[tracking["id"].astype(str).isin(used_ids)].copy()
        refs["_canonical_order"] = refs["id"].astype(str).apply(
            lambda x: used_ids.index(x) if x in used_ids else 9999
        )
    else:
        # fallback: high/medium relevant references
        refs = tracking[tracking.get("relevance_to_this_thesis", "").astype(str).isin(["High", "Medium"])].copy()
        refs["_canonical_order"] = 9999

    # Remove generated/manual duplicate records and incomplete verification records.
    refs = refs[~refs["id"].astype(str).str.startswith("MAN")].copy()
    refs = refs[~refs["venue"].astype(str).str.contains("To verify from full text", case=False, na=False)].copy()
    refs = refs[~refs["title"].astype(str).str.contains("To verify from full text", case=False, na=False)].copy()

    refs["year_sort"] = refs["year"].astype(str).str.replace(".0", "", regex=False)
    refs["first_author_sort"] = refs["authors"].astype(str).str.lower()
    refs = refs.sort_values(["first_author_sort", "year_sort", "title"], ascending=[True, True, True])

    refs["apa_like_reference"] = refs.apply(
        lambda row: reference_override_map.get(clean(row.get("id")), apa_like_reference(row)),
        axis=1,
    )

    Path(args.output_csv).parent.mkdir(parents=True, exist_ok=True)
    refs[["id", "year", "authors", "title", "venue", "doi_url", "apa_like_reference"]].to_csv(args.output_csv, index=False)

    md = []
    md.append("# Kaynakça")
    md.append("")
    md.append("> Not: Bu kaynakça otomatik olarak APA7’ye yakın biçimde üretilmiştir. Nihai teslim öncesinde SAÜ FBE kılavuzu ve APA7 ayrıntılarına göre manuel kontrol edilmelidir.")
    md.append("")

    for ref in refs["apa_like_reference"].tolist():
        if ref:
            md.append(f"- {ref}")

    Path(args.output_md).write_text("\n".join(md), encoding="utf-8")

    print("[INFO] MD:", args.output_md)
    print("[INFO] CSV:", args.output_csv)
    print("[INFO] Reference count:", len(refs))


if __name__ == "__main__":
    main()
