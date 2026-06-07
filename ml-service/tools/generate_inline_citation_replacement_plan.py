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


def first_author_label(authors: str) -> str:
    authors = clean(authors)
    if not authors:
        return ""

    # Common separators from BibTeX exports / generated records.
    for sep in [" and ", ";", ", and "]:
        if sep in authors:
            first = authors.split(sep)[0].strip()
            break
    else:
        first = authors.split(",")[0].strip()

    # If author is "Surname, Name", take surname.
    if "," in first:
        first = first.split(",")[0].strip()

    # If generated Turkish "vd." already exists, keep leading part.
    first = first.replace("vd.", "").replace("et al.", "").strip()

    return first


def apa_inline(authors: str, year: str) -> str:
    label = first_author_label(authors)
    year = clean(year).replace(".0", "")
    if label and year:
        return f"({label} vd., {year})"
    if label:
        return f"({label} vd.)"
    if year:
        return f"({year})"
    return "(Yazar, yıl)"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--marker-audit-csv",
        default="docs/inline_reference_marker_audit.csv",
    )
    parser.add_argument(
        "--tracking-csv",
        default="docs/literature_review/literature_tracking_table.csv",
    )
    parser.add_argument(
        "--output-csv",
        default="docs/inline_citation_replacement_plan.csv",
    )
    parser.add_argument(
        "--output-md",
        default="docs/inline_citation_replacement_plan.md",
    )
    args = parser.parse_args()

    audit = pd.read_csv(args.marker_audit_csv).fillna("")
    tracking = pd.read_csv(args.tracking_csv).fillna("")

    tracking_by_id = {
        clean(row.get("id")): row
        for _, row in tracking.iterrows()
        if clean(row.get("id"))
    }

    markers = sorted(audit["marker"].unique()) if not audit.empty else []

    rows = []
    for marker in markers:
        t = tracking_by_id.get(marker)
        occurrences = int((audit["marker"] == marker).sum())

        if t is None:
            rows.append({
                "marker": marker,
                "occurrences": occurrences,
                "suggested_inline_citation": "",
                "authors": "",
                "year": "",
                "title": "",
                "status": "missing_tracking_record",
                "note": "Marker was used in chapter text but not found in tracking CSV.",
            })
            continue

        authors = clean(t.get("authors"))
        year = clean(t.get("year"))
        title = clean(t.get("title"))

        rows.append({
            "marker": marker,
            "occurrences": occurrences,
            "suggested_inline_citation": apa_inline(authors, year),
            "authors": authors,
            "year": year.replace(".0", ""),
            "title": title,
            "status": "proposal_only",
            "note": "Review manually before replacement.",
        })

    out = pd.DataFrame(rows)
    Path(args.output_csv).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.output_csv, index=False)

    md = []
    md.append("# Inline Citation Replacement Plan")
    md.append("")
    md.append("Bu dosya, teknik `[BIBxxx]`, `[LRxxx]`, `[MANxxx]` işaretleri için APA7’ye yakın metin içi atıf önerileri üretir. Bu aşamada otomatik değiştirme yapılmamıştır.")
    md.append("")
    md.append("| Marker | Count | Suggested inline citation | Year | Title | Status |")
    md.append("|---|---:|---|---:|---|---|")

    for _, row in out.iterrows():
        title = clean(row["title"]).replace("|", "\\|")
        md.append(
            f"| {row['marker']} | {row['occurrences']} | {row['suggested_inline_citation']} | "
            f"{row['year']} | {title[:180]} | {row['status']} |"
        )

    md.append("")
    md.append("## Not")
    md.append("")
    md.append("Türkçe tez metni için önerilen genel biçim `(Yazar vd., Yıl)` biçimidir. Tek yazarlı kaynaklarda nihai düzenleme sırasında `(Yazar, Yıl)` tercih edilebilir. Bu dosya otomatik öneri üretir; nihai APA7 kontrolü manuel yapılmalıdır.")

    Path(args.output_md).write_text("\n".join(md), encoding="utf-8")

    print("[INFO] CSV:", args.output_csv)
    print("[INFO] MD:", args.output_md)
    print("[INFO] Rows:", len(out))


if __name__ == "__main__":
    main()
