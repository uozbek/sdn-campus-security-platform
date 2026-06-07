#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
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
    return s.strip()


def read_csv_safe(path: Path) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame()
    return pd.read_csv(path).fillna("")


def extract_ids_from_text(text: str) -> set[str]:
    return set(re.findall(r"\b(?:BIB|LR|MAN)\d{3}\b", text))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--chapter3-md",
        default="docs/bolum_3_literatur_taramasi_ve_ilgili_calismalar_tr.md",
    )
    parser.add_argument(
        "--chapter5-md",
        default="docs/bolum_5_tartisma_sinirliliklar_gelecek_calismalar_tr.md",
    )
    parser.add_argument(
        "--synthesis-csv",
        default="docs/literature_review/synthesis/chapter3_literature_synthesis_candidates.csv",
    )
    parser.add_argument(
        "--references-csv",
        default="docs/references_apa_like.csv",
    )
    parser.add_argument(
        "--tracking-csv",
        default="docs/literature_review/literature_tracking_table.csv",
    )
    parser.add_argument(
        "--output-md",
        default="docs/compared_studies_bibliography_audit.md",
    )
    parser.add_argument(
        "--output-json",
        default="docs/compared_studies_bibliography_audit.json",
    )
    args = parser.parse_args()

    chapter_paths = [Path(args.chapter3_md), Path(args.chapter5_md)]
    synthesis = read_csv_safe(Path(args.synthesis_csv))
    refs = read_csv_safe(Path(args.references_csv))
    tracking = read_csv_safe(Path(args.tracking_csv))

    compared_ids = set()

    # 1. Bölüm 3/5 metninde teknik ID hâlâ tablo hücrelerinde varsa yakala.
    text_sources = {}
    for p in chapter_paths:
        if p.exists():
            text = p.read_text(encoding="utf-8", errors="ignore")
            ids = extract_ids_from_text(text)
            text_sources[str(p)] = sorted(ids)
            compared_ids.update(ids)

    # 2. Synthesis candidates dosyası doğrudan karşılaştırma/literatür tablolarını besliyor.
    if not synthesis.empty and "id" in synthesis.columns:
        for rid in synthesis["id"].astype(str):
            rid = clean(rid)
            if rid:
                compared_ids.add(rid)

    # 3. Kaynakçadaki ID’ler
    bibliography_ids = set()
    if not refs.empty and "id" in refs.columns:
        bibliography_ids = set(clean(x) for x in refs["id"].astype(str) if clean(x))

    # 4. Tracking lookup
    tracking_by_id = {}
    if not tracking.empty and "id" in tracking.columns:
        tracking_by_id = {
            clean(row.get("id")): row
            for _, row in tracking.iterrows()
            if clean(row.get("id"))
        }

    rows = []
    for rid in sorted(compared_ids):
        row = tracking_by_id.get(rid)
        title = clean(row.get("title")) if row is not None else ""
        year = clean(row.get("year")).replace(".0", "") if row is not None else ""
        relevance = clean(row.get("relevance_to_this_thesis")) if row is not None else ""
        authors = clean(row.get("authors")) if row is not None else ""

        in_bib = rid in bibliography_ids

        # MAN kayıtları duplicate olabilir; doğrudan kaynakçada olmaması her zaman hata değil.
        if rid.startswith("MAN"):
            status = "manual_or_duplicate_check"
        elif in_bib:
            status = "ok"
        else:
            status = "missing_from_bibliography"

        rows.append({
            "id": rid,
            "status": status,
            "in_bibliography": in_bib,
            "year": year,
            "authors": authors,
            "title": title,
            "relevance": relevance,
        })

    out = pd.DataFrame(rows)
    status_counts = out["status"].value_counts().to_dict() if not out.empty else {}

    result = {
        "generated_at_utc": datetime.utcnow().isoformat(),
        "compared_id_count": len(compared_ids),
        "bibliography_id_count": len(bibliography_ids),
        "status_counts": status_counts,
        "text_sources": text_sources,
    }

    Path(args.output_json).write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    md = []
    md.append("# Compared Studies vs Bibliography Audit")
    md.append("")
    md.append(f"- Generated at UTC: `{result['generated_at_utc']}`")
    md.append(f"- Compared study ID count: `{result['compared_id_count']}`")
    md.append(f"- Bibliography ID count: `{result['bibliography_id_count']}`")
    md.append(f"- Status counts: `{status_counts}`")
    md.append("")
    md.append("## 1. Summary")
    md.append("")
    md.append("| Status | Count |")
    md.append("|---|---:|")
    for k, v in status_counts.items():
        md.append(f"| {k} | {v} |")

    md.append("")
    md.append("## 2. Missing From Bibliography")
    md.append("")
    missing = out[out["status"].eq("missing_from_bibliography")] if not out.empty else pd.DataFrame()
    if missing.empty:
        md.append("No missing compared studies found.")
    else:
        md.append("| ID | Year | Relevance | Title |")
        md.append("|---|---:|---|---|")
        for _, r in missing.iterrows():
            title = clean(r["title"]).replace("|", "\\|")
            md.append(f"| {r['id']} | {r['year']} | {r['relevance']} | {title[:220]} |")

    md.append("")
    md.append("## 3. Manual / Duplicate Check")
    md.append("")
    manual = out[out["status"].eq("manual_or_duplicate_check")] if not out.empty else pd.DataFrame()
    if manual.empty:
        md.append("No MAN/manual duplicate candidates found.")
    else:
        md.append("| ID | Year | Relevance | Title |")
        md.append("|---|---:|---|---|")
        for _, r in manual.iterrows():
            title = clean(r["title"]).replace("|", "\\|")
            md.append(f"| {r['id']} | {r['year']} | {r['relevance']} | {title[:220]} |")

    md.append("")
    md.append("## 4. All Compared IDs")
    md.append("")
    md.append("| ID | In bibliography | Status | Year | Title |")
    md.append("|---|---|---|---:|---|")
    for _, r in out.iterrows():
        title = clean(r["title"]).replace("|", "\\|")
        md.append(
            f"| {r['id']} | {r['in_bibliography']} | {r['status']} | "
            f"{r['year']} | {title[:180]} |"
        )

    Path(args.output_md).write_text("\n".join(md), encoding="utf-8")

    print("[INFO] MD:", args.output_md)
    print("[INFO] JSON:", args.output_json)
    print("[INFO] Compared IDs:", len(compared_ids))
    print("[INFO] Bibliography IDs:", len(bibliography_ids))
    print("[INFO] Status counts:", status_counts)


if __name__ == "__main__":
    main()
