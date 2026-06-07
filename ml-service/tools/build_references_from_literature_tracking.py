#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from datetime import datetime
from pathlib import Path

import pandas as pd


def clean(value) -> str:
    if value is None:
        return ""
    s = str(value)
    if s.lower() == "nan":
        return ""
    return re.sub(r"\s+", " ", s).strip()


def make_reference(row) -> str:
    rid = clean(row.get("id", ""))
    authors = clean(row.get("authors", ""))
    year = clean(row.get("year", ""))
    title = clean(row.get("title", ""))
    venue = clean(row.get("venue", ""))
    doi = clean(row.get("doi_url", ""))

    parts = []

    if authors:
        parts.append(authors)
    else:
        parts.append("Yazar bilgisi doğrulanmalı")

    if year:
        # 2025.0 gibi değerleri temizle
        year = year.replace(".0", "")
        parts.append(f"({year}).")

    if title:
        parts.append(title + ".")

    if venue and venue.lower() not in {"to verify from full text", "nan"}:
        parts.append(venue + ".")

    if doi:
        parts.append(doi)

    ref = " ".join(parts)
    return f"[{rid}] {ref}"


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
        "--chapter3-table",
        default="docs/literature_review/synthesis/table_chapter3_methodological_comparison.csv",
    )
    parser.add_argument(
        "--chapter5-table",
        default="docs/literature_review/synthesis/table_chapter5_result_functionality_comparison.csv",
    )
    parser.add_argument(
        "--output-md",
        default="docs/kaynakca_taslagi_literature_tracking.md",
    )
    parser.add_argument(
        "--output-csv",
        default="docs/kaynakca_taslagi_literature_tracking.csv",
    )
    parser.add_argument(
        "--exclude-ids-file",
        default="docs/reference_exclusion_ids.txt",
        help="Optional text file containing reference IDs to exclude from the generated reference draft.",
    )
    args = parser.parse_args()

    tracking_path = Path(args.tracking_csv)
    synthesis_path = Path(args.synthesis_csv)
    ch3_table_path = Path(args.chapter3_table)
    ch5_table_path = Path(args.chapter5_table)

    tracking = pd.read_csv(tracking_path).fillna("")

    used_ids = set()

    # 1) Karşılaştırma tablolarındaki ID'leri topla
    for p in [ch3_table_path, ch5_table_path]:
        if not p.exists():
            continue
        df = pd.read_csv(p).fillna("")
        for col in df.columns:
            for value in df[col].astype(str):
                for m in re.findall(r"\b(?:BIB|LR|MAN)\d{3}\b", value):
                    used_ids.add(m)

    # 2) Sentez tablosundan High/Medium kayıtları da ekle
    if synthesis_path.exists():
        synth = pd.read_csv(synthesis_path).fillna("")
        if "relevance_to_this_thesis" in synth.columns and "id" in synth.columns:
            sub = synth[synth["relevance_to_this_thesis"].isin(["High", "Medium"])]
            used_ids.update(sub["id"].astype(str).tolist())

    exclude_ids = set()
    exclude_file = Path(args.exclude_ids_file)
    if exclude_file.exists():
        for line in exclude_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            exclude_ids.add(line)

    used_ids = used_ids - exclude_ids

    refs = tracking[tracking["id"].astype(str).isin(sorted(used_ids))].copy()

    # Sort
    if "year" in refs.columns:
        refs["_year"] = pd.to_numeric(refs["year"], errors="coerce").fillna(0).astype(int)
    else:
        refs["_year"] = 0

    refs = refs.sort_values(by=["_year", "id"], ascending=[False, True]).drop(columns=["_year"])

    refs["reference_text"] = refs.apply(make_reference, axis=1)

    refs.to_csv(args.output_csv, index=False)

    md = []
    md.append("# Kaynakça Taslağı — Literature Tracking Tabanlı")
    md.append("")
    md.append(f"- Generated at UTC: `{datetime.utcnow().isoformat()}`")
    md.append(f"- Tracking CSV: `{tracking_path}`")
    md.append(f"- Used reference count: `{len(refs)}`")
    md.append("")
    md.append("Bu kaynakça taslağı, literatür takip tablosu ve Bölüm 3/5 karşılaştırma tablolarından çıkarılan kaynak kayıtlarına dayalıdır.")
    md.append("Nihai tez teslimi öncesinde kaynakların üniversite tez yazım kılavuzuna göre APA/IEEE vb. biçimde düzenlenmesi gerekir.")
    md.append("")
    md.append("## Kaynakça")
    md.append("")

    for ref in refs["reference_text"].tolist():
        md.append(ref)
        md.append("")

    Path(args.output_md).write_text("\n".join(md), encoding="utf-8")

    print("[INFO] Used reference count:", len(refs))
    print("[INFO] MD :", args.output_md)
    print("[INFO] CSV:", args.output_csv)


if __name__ == "__main__":
    main()
