#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict

from docx import Document


CAPTION_RE = re.compile(r"^(Tablo|Şekil)\s+([0-9]+(?:\.[0-9xX]+)*)\s*[\.\-:]?\s+(.+)$")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--docx", default="docs/tez_ana_taslak_tr_guncel_sau_fbe.docx")
    parser.add_argument("--output-md", default="docs/caption_numbering_consistency_audit.md")
    parser.add_argument("--output-json", default="docs/caption_numbering_consistency_audit.json")
    args = parser.parse_args()

    doc = Document(args.docx)

    current_chapter = ""
    captions = []

    for idx, p in enumerate(doc.paragraphs, start=1):
        text = p.text.strip()
        if not text:
            continue

        if text.startswith("Bölüm "):
            current_chapter = text

        m = CAPTION_RE.match(text)
        if m:
            kind, number, title = m.groups()
            captions.append({
                "paragraph": idx,
                "chapter": current_chapter,
                "kind": kind,
                "number": number,
                "title": title,
                "text": text,
            })

    duplicate_numbers = []
    seen = defaultdict(list)
    for c in captions:
        seen[(c["kind"], c["number"])].append(c)

    for (kind, number), items in seen.items():
        if len(items) > 1:
            duplicate_numbers.append({
                "kind": kind,
                "number": number,
                "count": len(items),
                "paragraphs": ", ".join(str(x["paragraph"]) for x in items),
                "chapters": " || ".join(sorted(set(x["chapter"] for x in items))),
            })

    suspicious = []
    for c in captions:
        chapter_num = None
        cm = re.match(r"^Bölüm\s+([0-9]+)\.", c["chapter"])
        if cm:
            chapter_num = cm.group(1)

        # Bölüm başlığı biliniyorsa ve caption "1", "2" gibi düz sayı ise şüpheli say.
        if chapter_num and "." not in c["number"]:
            suspicious.append({
                **c,
                "issue": "plain_number_inside_chapter",
                "suggested_prefix": chapter_num,
            })

        # 3.x gibi geçici numaralar
        if "x" in c["number"].lower():
            suspicious.append({
                **c,
                "issue": "placeholder_x_number",
                "suggested_prefix": chapter_num or "",
            })

    md = []
    md.append("# Caption Numbering Consistency Audit")
    md.append("")
    md.append(f"- Generated at UTC: `{datetime.utcnow().isoformat()}`")
    md.append(f"- DOCX: `{args.docx}`")
    md.append(f"- Caption count: `{len(captions)}`")
    md.append(f"- Duplicate number groups: `{len(duplicate_numbers)}`")
    md.append(f"- Suspicious caption count: `{len(suspicious)}`")
    md.append("")

    md.append("## 1. Captions")
    md.append("")
    md.append("| Paragraph | Chapter | Kind | Number | Title |")
    md.append("|---:|---|---|---:|---|")
    for c in captions:
        title = c["title"].replace("|", "\\|")
        chapter = c["chapter"].replace("|", "\\|")
        md.append(f"| {c['paragraph']} | {chapter} | {c['kind']} | {c['number']} | {title[:160]} |")

    md.append("")
    md.append("## 2. Duplicate Number Groups")
    md.append("")
    if duplicate_numbers:
        md.append("| Kind | Number | Count | Paragraphs | Chapters |")
        md.append("|---|---:|---:|---|---|")
        for d in duplicate_numbers:
            md.append(f"| {d['kind']} | {d['number']} | {d['count']} | {d['paragraphs']} | {d['chapters']} |")
    else:
        md.append("No duplicate caption numbers detected.")

    md.append("")
    md.append("## 3. Suspicious Captions")
    md.append("")
    if suspicious:
        md.append("| Paragraph | Chapter | Kind | Number | Issue | Suggested chapter prefix | Text |")
        md.append("|---:|---|---|---:|---|---:|---|")
        for s in suspicious:
            chapter = s["chapter"].replace("|", "\\|")
            text = s["text"].replace("|", "\\|")
            md.append(
                f"| {s['paragraph']} | {chapter} | {s['kind']} | {s['number']} | "
                f"{s['issue']} | {s['suggested_prefix']} | {text[:160]} |"
            )
    else:
        md.append("No suspicious captions detected.")

    Path(args.output_md).write_text("\n".join(md), encoding="utf-8")

    import json
    Path(args.output_json).write_text(
        json.dumps({
            "generated_at_utc": datetime.utcnow().isoformat(),
            "docx": args.docx,
            "caption_count": len(captions),
            "duplicate_number_groups": duplicate_numbers,
            "suspicious": suspicious,
        }, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print("[INFO] MD:", args.output_md)
    print("[INFO] JSON:", args.output_json)
    print("[INFO] Caption count:", len(captions))
    print("[INFO] Duplicate groups:", len(duplicate_numbers))
    print("[INFO] Suspicious:", len(suspicious))


if __name__ == "__main__":
    main()
