#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

import pandas as pd


CHAPTER_FILES = [
    "docs/bolum_1_giris_tr.md",
    "docs/bolum_2_kavramsal_kuramsal_arka_plan_tr.md",
    "docs/bolum_3_literatur_taramasi_ve_ilgili_calismalar_tr.md",
    "docs/bolum_4_yontem_ve_runtime_dogrulama_tr.md",
    "docs/bolum_5_tartisma_sinirliliklar_gelecek_calismalar_tr.md",
    "docs/bolum_6_sonuc_ve_oneriler_tr.md",
]

MARKER_RE = re.compile(r"\[(BIB\d{3}|LR\d{3}|MAN\d{3})\]")


def clean(value) -> str:
    if value is None:
        return ""
    s = str(value)
    if s.lower() == "nan":
        return ""
    return s.strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--tracking-csv",
        default="docs/literature_review/literature_tracking_table.csv",
    )
    parser.add_argument(
        "--output-md",
        default="docs/inline_reference_marker_audit.md",
    )
    parser.add_argument(
        "--output-csv",
        default="docs/inline_reference_marker_audit.csv",
    )
    parser.add_argument(
        "--output-json",
        default="docs/inline_reference_marker_audit.json",
    )
    args = parser.parse_args()

    tracking_path = Path(args.tracking_csv)
    tracking = pd.read_csv(tracking_path).fillna("") if tracking_path.exists() else pd.DataFrame()

    by_id = {}
    if not tracking.empty and "id" in tracking.columns:
        for _, row in tracking.iterrows():
            rid = clean(row.get("id"))
            if rid:
                by_id[rid] = {
                    "year": clean(row.get("year")),
                    "authors": clean(row.get("authors")),
                    "title": clean(row.get("title")),
                    "venue": clean(row.get("venue")),
                    "doi_url": clean(row.get("doi_url")),
                    "relevance": clean(row.get("relevance_to_this_thesis")),
                }

    rows = []
    counter = Counter()
    by_file = defaultdict(Counter)

    for f in CHAPTER_FILES:
        p = Path(f)
        if not p.exists():
            continue

        lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()
        for line_no, line in enumerate(lines, start=1):
            for m in MARKER_RE.finditer(line):
                rid = m.group(1)
                counter[rid] += 1
                by_file[f][rid] += 1

                meta = by_id.get(rid, {})
                rows.append({
                    "file": f,
                    "line": line_no,
                    "marker": rid,
                    "context": line.strip()[:500],
                    "year": meta.get("year", ""),
                    "authors": meta.get("authors", ""),
                    "title": meta.get("title", ""),
                    "venue": meta.get("venue", ""),
                    "relevance": meta.get("relevance", ""),
                    "doi_url": meta.get("doi_url", ""),
                    "found_in_tracking": bool(meta),
                })

    out_csv = Path(args.output_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out_csv, index=False)

    result = {
        "generated_at_utc": datetime.utcnow().isoformat(),
        "tracking_csv": str(tracking_path),
        "total_marker_occurrences": len(rows),
        "unique_marker_count": len(counter),
        "marker_counts": dict(counter.most_common()),
        "file_marker_counts": {
            f: dict(c.most_common()) for f, c in by_file.items()
        },
        "missing_tracking_ids": sorted([rid for rid in counter if rid not in by_id]),
    }

    Path(args.output_json).write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    md = []
    md.append("# Inline Reference Marker Audit")
    md.append("")
    md.append(f"- Generated at UTC: `{result['generated_at_utc']}`")
    md.append(f"- Total marker occurrences: `{result['total_marker_occurrences']}`")
    md.append(f"- Unique marker count: `{result['unique_marker_count']}`")
    md.append(f"- Missing tracking IDs: `{result['missing_tracking_ids']}`")
    md.append("")
    md.append("## 1. Marker Counts")
    md.append("")
    md.append("| Marker | Count | Found in tracking | Year | Title |")
    md.append("|---|---:|---|---:|---|")

    for rid, count in counter.most_common():
        meta = by_id.get(rid, {})
        title = meta.get("title", "").replace("|", "\\|")
        md.append(f"| {rid} | {count} | {bool(meta)} | {meta.get('year', '')} | {title[:180]} |")

    md.append("")
    md.append("## 2. Marker Occurrences")
    md.append("")
    md.append("| File | Line | Marker | Context |")
    md.append("|---|---:|---|---|")
    for row in rows:
        ctx = row["context"].replace("|", "\\|")
        md.append(f"| `{row['file']}` | {row['line']} | {row['marker']} | {ctx[:250]} |")

    md.append("")
    md.append("## 3. Suggested Use")
    md.append("")
    md.append("Bu rapor, tezde kullanılan teknik `[BIBxxx]`, `[LRxxx]`, `[MANxxx]` işaretlerinin hangi bölümlerde geçtiğini gösterir. Nihai tez öncesinde bu işaretler APA7 uyumlu metin içi atıflara dönüştürülmeli veya kaynakça yönetim sistemiyle eşleştirilmelidir.")

    Path(args.output_md).write_text("\n".join(md), encoding="utf-8")

    print("[INFO] MD:", args.output_md)
    print("[INFO] CSV:", args.output_csv)
    print("[INFO] JSON:", args.output_json)
    print("[INFO] Total marker occurrences:", len(rows))
    print("[INFO] Unique marker count:", len(counter))
    print("[INFO] Missing tracking IDs:", result["missing_tracking_ids"])


if __name__ == "__main__":
    main()
