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


def clean_title(value: str) -> str:
    s = clean(value)
    s = s.replace("{", "").replace("}", "")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def format_authors(authors: str) -> str:
    authors = clean(authors)
    if not authors:
        return ""

    # BibTeX style: A and B and C
    parts = [p.strip() for p in re.split(r"\s+and\s+", authors) if p.strip()]

    # Zotero CSV style can be semicolon-separated.
    if len(parts) == 1 and ";" in authors:
        parts = [p.strip() for p in authors.split(";") if p.strip()]

    formatted = []
    for p in parts:
        p = clean(p)
        if "," in p:
            surname, given = [x.strip() for x in p.split(",", 1)]
            initials = " ".join([g[0] + "." for g in given.replace("-", " ").split() if g])
            formatted.append(f"{surname}, {initials}".strip())
        else:
            tokens = p.split()
            if len(tokens) >= 2:
                surname = tokens[-1]
                given = tokens[:-1]
                initials = " ".join([g[0] + "." for g in given if g])
                formatted.append(f"{surname}, {initials}".strip())
            else:
                formatted.append(p)

    if len(formatted) == 1:
        return formatted[0]
    if len(formatted) <= 20:
        return ", ".join(formatted[:-1]) + " ve " + formatted[-1]
    return ", ".join(formatted[:19]) + " ve diğerleri"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selection-csv", default="docs/literature_review/zotero_clean/zotero_final_bibliography_selection.csv")
    parser.add_argument("--output-md", default="docs/references_zotero_apa_like.md")
    parser.add_argument("--output-csv", default="docs/references_zotero_apa_like.csv")
    args = parser.parse_args()

    df = pd.read_csv(args.selection_csv).fillna("")

    rows = []
    for _, r in df.iterrows():
        authors = format_authors(clean(r.get("authors")))
        year = clean(r.get("year"))[:4] or "t.y."
        title = clean_title(clean(r.get("title")))
        venue = clean_title(clean(r.get("venue")))
        doi = clean(r.get("doi"))
        url = clean(r.get("url"))

        tail = ""
        if doi:
            tail = doi if doi.startswith("http") else f"https://doi.org/{doi}"
        elif url:
            tail = url

        ref = f"{authors} ({year}). {title}."
        if venue:
            ref += f" {venue}."
        if tail:
            ref += f" {tail}"

        rows.append({
            "id": clean(r.get("zotero_key")),
            "zotero_key": clean(r.get("zotero_key")),
            "year": year,
            "authors": clean(r.get("authors")),
            "formatted_authors": authors,
            "title": title,
            "venue": venue,
            "doi": doi,
            "url": url,
            "apa_like_reference": ref,
            "selection_reason": clean(r.get("selection_reason")),
            "relevance_to_this_thesis": clean(r.get("relevance_to_this_thesis")),
        })

    out = pd.DataFrame(rows)

    # Sort alphabetically by formatted reference.
    if not out.empty:
        out = out.sort_values("apa_like_reference")

    Path(args.output_csv).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.output_csv, index=False)

    md = []
    md.append("# Kaynakça")
    md.append("")
    md.append("> Not: Bu kaynakça Zotero clean export temel alınarak APA7’ye yakın biçimde otomatik üretilmiştir. Nihai teslim öncesinde SAÜ FBE ve APA7 ayrıntılarına göre manuel kontrol edilmelidir.")
    md.append("")
    for _, r in out.iterrows():
        md.append(f"- {r['apa_like_reference']}")

    Path(args.output_md).write_text("\n".join(md), encoding="utf-8")

    print("[INFO] MD:", args.output_md)
    print("[INFO] CSV:", args.output_csv)
    print("[INFO] Reference count:", len(out))


if __name__ == "__main__":
    main()
