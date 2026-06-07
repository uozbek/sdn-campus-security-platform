#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

from docx import Document


BAD_PATTERNS = [
    r"\[(BIB|LR|MAN)\d{3}\]",
    r"\bal\.,",
    r"To verify from full text",
]

REFERENCE_HINTS = [
    "Kaynakça",
    "References",
    "Bibliography",
]


def paragraph_style_name(p) -> str:
    try:
        return p.style.name or ""
    except Exception:
        return ""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--docx",
        default="docs/tez_ana_taslak_tr_guncel_sau_fbe.docx",
    )
    parser.add_argument(
        "--output-md",
        default="docs/docx_reference_cleanup_audit.md",
    )
    parser.add_argument(
        "--output-json",
        default="docs/docx_reference_cleanup_audit.json",
    )
    args = parser.parse_args()

    docx_path = Path(args.docx)
    if not docx_path.exists():
        raise SystemExit(f"[ERROR] DOCX not found: {docx_path}")

    doc = Document(docx_path)

    paragraphs = doc.paragraphs
    non_empty = []
    empty_runs = 0
    empty_paragraph_indices = []

    for i, p in enumerate(paragraphs, start=1):
        text = p.text.strip()
        if text:
            non_empty.append((i, text, paragraph_style_name(p)))
        else:
            empty_paragraph_indices.append(i)
            empty_runs += 1

    bad_hits = []
    for i, text, style in non_empty:
        for pat in BAD_PATTERNS:
            if re.search(pat, text):
                bad_hits.append({
                    "paragraph": i,
                    "pattern": pat,
                    "style": style,
                    "text": text[:500],
                })

    heading_hits = []
    for i, text, style in non_empty:
        if text.strip().lower() in {"kaynakça", "kaynaklar", "references", "bibliography"}:
            heading_hits.append({
                "paragraph": i,
                "text": text,
                "style": style,
            })

    # Find reference-looking paragraphs.
    reference_like = []
    author_year_re = re.compile(r"^[A-ZÇĞİÖŞÜ][^\\n]{2,120}\((19|20)\d{2}\)\.")
    doi_re = re.compile(r"https?://doi\.org/|https?://")
    for i, text, style in non_empty:
        if author_year_re.search(text) or doi_re.search(text):
            reference_like.append({
                "paragraph": i,
                "style": style,
                "text": text[:500],
            })

    duplicate_reference_counter = Counter([x["text"] for x in reference_like])
    duplicate_reference_like = [
        {"text": text, "count": count}
        for text, count in duplicate_reference_counter.items()
        if count > 1
    ]

    # Consecutive empty paragraph runs
    empty_runs_info = []
    current = []
    prev = None
    for idx in empty_paragraph_indices:
        if prev is None or idx == prev + 1:
            current.append(idx)
        else:
            if len(current) >= 3:
                empty_runs_info.append({
                    "start": current[0],
                    "end": current[-1],
                    "count": len(current),
                })
            current = [idx]
        prev = idx
    if len(current) >= 3:
        empty_runs_info.append({
            "start": current[0],
            "end": current[-1],
            "count": len(current),
        })

    summary = {
        "generated_at_utc": datetime.utcnow().isoformat(),
        "docx": str(docx_path),
        "paragraph_count": len(paragraphs),
        "non_empty_paragraph_count": len(non_empty),
        "empty_paragraph_count": len(empty_paragraph_indices),
        "bad_hit_count": len(bad_hits),
        "reference_heading_count": len(heading_hits),
        "reference_like_count": len(reference_like),
        "duplicate_reference_like_count": len(duplicate_reference_like),
        "long_empty_runs_count": len(empty_runs_info),
        "bad_hits": bad_hits,
        "reference_headings": heading_hits,
        "reference_like_examples": reference_like[:30],
        "duplicate_reference_like": duplicate_reference_like[:30],
        "long_empty_runs": empty_runs_info[:30],
    }

    Path(args.output_json).write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    md = []
    md.append("# DOCX Reference Cleanup Audit")
    md.append("")
    md.append(f"- Generated at UTC: `{summary['generated_at_utc']}`")
    md.append(f"- DOCX: `{summary['docx']}`")
    md.append("")
    md.append("## 1. Summary")
    md.append("")
    md.append("| Metric | Value |")
    md.append("|---|---:|")
    for key in [
        "paragraph_count",
        "non_empty_paragraph_count",
        "empty_paragraph_count",
        "bad_hit_count",
        "reference_heading_count",
        "reference_like_count",
        "duplicate_reference_like_count",
        "long_empty_runs_count",
    ]:
        md.append(f"| {key} | {summary[key]} |")

    md.append("")
    md.append("## 2. Bad Pattern Hits")
    md.append("")
    if bad_hits:
        md.append("| Paragraph | Pattern | Text |")
        md.append("|---:|---|---|")
        for hit in bad_hits:
            t = hit["text"].replace("|", "\\|")
            md.append(f"| {hit['paragraph']} | `{hit['pattern']}` | {t[:250]} |")
    else:
        md.append("No bad pattern hits found.")

    md.append("")
    md.append("## 3. Reference Headings")
    md.append("")
    if heading_hits:
        md.append("| Paragraph | Text | Style |")
        md.append("|---:|---|---|")
        for h in heading_hits:
            md.append(f"| {h['paragraph']} | {h['text']} | {h['style']} |")
    else:
        md.append("No reference heading found.")

    md.append("")
    md.append("## 4. Reference-Like Paragraph Examples")
    md.append("")
    if reference_like:
        md.append("| Paragraph | Text |")
        md.append("|---:|---|")
        for r in reference_like[:30]:
            t = r["text"].replace("|", "\\|")
            md.append(f"| {r['paragraph']} | {t[:300]} |")
    else:
        md.append("No reference-like paragraphs found.")

    md.append("")
    md.append("## 5. Duplicate Reference-Like Paragraphs")
    md.append("")
    if duplicate_reference_like:
        md.append("| Count | Text |")
        md.append("|---:|---|")
        for d in duplicate_reference_like:
            t = d["text"].replace("|", "\\|")
            md.append(f"| {d['count']} | {t[:300]} |")
    else:
        md.append("No duplicate reference-like paragraphs found.")

    md.append("")
    md.append("## 6. Long Empty Paragraph Runs")
    md.append("")
    if empty_runs_info:
        md.append("| Start | End | Count |")
        md.append("|---:|---:|---:|")
        for r in empty_runs_info:
            md.append(f"| {r['start']} | {r['end']} | {r['count']} |")
    else:
        md.append("No long empty paragraph runs found.")

    Path(args.output_md).write_text("\n".join(md), encoding="utf-8")

    print("[INFO] MD:", args.output_md)
    print("[INFO] JSON:", args.output_json)
    print("[INFO] Bad hits:", len(bad_hits))
    print("[INFO] Reference headings:", len(heading_hits))
    print("[INFO] Reference-like paragraphs:", len(reference_like))
    print("[INFO] Long empty runs:", len(empty_runs_info))


if __name__ == "__main__":
    main()
