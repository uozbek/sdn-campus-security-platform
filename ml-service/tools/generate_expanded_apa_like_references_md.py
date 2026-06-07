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


def author_to_apaish(authors: str) -> str:
    authors = clean(authors)
    if not authors:
        return ""

    # Fix common "et al." records; manual override handles most LR cases.
    if authors.lower().endswith(" et al."):
        first = authors[:-7].strip()
        return f"{first} ve diğerleri"

    if authors.lower().endswith(" et al"):
        first = authors[:-6].strip()
        return f"{first} ve diğerleri"

    parts = [p.strip() for p in re.split(r"\s+and\s+|;", authors) if p.strip()]
    if not parts:
        return authors

    formatted = []
    for a in parts[:8]:
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


def apa_like(row, manual_override: dict[str, str]) -> str:
    rid = clean(row.get("id"))
    if rid in manual_override:
        return manual_override[rid]

    authors = author_to_apaish(row.get("authors", ""))
    year = clean(row.get("year")).replace(".0", "")
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
    parser.add_argument("--selection-csv", default="docs/expanded_bibliography_selection.csv")
    parser.add_argument("--reference-override-csv", default="docs/reference_apa_manual_override.csv")
    parser.add_argument("--output-md", default="docs/references_apa_like.md")
    parser.add_argument("--output-csv", default="docs/references_apa_like.csv")
    args = parser.parse_args()

    refs = pd.read_csv(args.selection_csv).fillna("")
    override = pd.read_csv(args.reference_override_csv).fillna("") if Path(args.reference_override_csv).exists() else pd.DataFrame()

    manual_override = {}
    if not override.empty and {"id", "apa_like_reference"}.issubset(override.columns):
        manual_override = {
            clean(row.get("id")): clean(row.get("apa_like_reference"))
            for _, row in override.iterrows()
            if clean(row.get("id")) and clean(row.get("apa_like_reference"))
        }

    if refs.empty:
        raise SystemExit("[ERROR] Selection CSV is empty.")

    # Exclude bad placeholders and duplicates.
    refs = refs[~refs["id"].astype(str).str.startswith("MAN")].copy()
    refs = refs[~refs["venue"].astype(str).str.contains("To verify from full text", case=False, na=False)].copy()
    refs = refs[~refs["title"].astype(str).str.contains("To verify from full text", case=False, na=False)].copy()

    refs["apa_like_reference"] = refs.apply(lambda row: apa_like(row, manual_override), axis=1)

    # Remove obviously malformed references.
    refs = refs[~refs["apa_like_reference"].str.contains(r"\bal\.,", regex=True, na=False)].copy()
    refs = refs[~refs["apa_like_reference"].str.contains("To verify from full text", case=False, na=False)].copy()

    refs["author_sort"] = refs["apa_like_reference"].str.lower()
    refs = refs.sort_values(["author_sort", "year", "title"])

    Path(args.output_csv).parent.mkdir(parents=True, exist_ok=True)
    refs.to_csv(args.output_csv, index=False)

    md = []
    md.append("# Kaynakça")
    md.append("")
    md.append("> Not: Bu kaynakça otomatik olarak APA7’ye yakın biçimde üretilmiştir. Nihai teslim öncesinde SAÜ FBE kılavuzu ve APA7 ayrıntılarına göre manuel kontrol edilmelidir.")
    md.append("")

    for ref in refs["apa_like_reference"].tolist():
        md.append(f"- {ref}")

    Path(args.output_md).write_text("\n".join(md), encoding="utf-8")

    print("[INFO] MD:", args.output_md)
    print("[INFO] CSV:", args.output_csv)
    print("[INFO] Reference count:", len(refs))


if __name__ == "__main__":
    main()
