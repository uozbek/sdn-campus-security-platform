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

# Captures parenthetical author-year citations such as:
# (Kalkan vd., 2017), (Mitchell, 2013), (Batool vd., 2025; Ganeshan vd., 2026)
CITATION_PAREN_RE = re.compile(r"\(([^()]*?\b(?:19|20)\d{2}[^()]*)\)")


def split_citation_items(paren_content: str) -> list[str]:
    parts = [p.strip() for p in paren_content.split(";") if p.strip()]
    return parts


def normalize_item(item: str) -> str:
    item = re.sub(r"\s+", " ", item.strip())
    item = item.replace(".0", "")
    return item


def is_valid_author_year_citation(item: str) -> bool:
    item = normalize_item(item)

    # Exclude year-only values accidentally captured from tables, e.g. 2020 or 2020.0.
    if re.fullmatch(r"(?:19|20)\d{2}", item):
        return False

    # Require a comma before the year: Author, 2020 / Author vd., 2020.
    if not re.search(r",\s*(?:19|20)\d{2}", item):
        return False

    # Require at least one alphabetic character before the comma.
    left = item.split(",", 1)[0]
    return bool(re.search(r"[A-Za-zÇĞİÖŞÜçğıöşü]", left))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-md", default="docs/apa_inline_citation_audit.md")
    parser.add_argument("--output-csv", default="docs/apa_inline_citation_audit.csv")
    parser.add_argument("--output-json", default="docs/apa_inline_citation_audit.json")
    args = parser.parse_args()

    rows = []
    counter = Counter()
    file_counter = defaultdict(Counter)

    for f in CHAPTER_FILES:
        p = Path(f)
        if not p.exists():
            continue

        lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()
        for line_no, line in enumerate(lines, start=1):
            for m in CITATION_PAREN_RE.finditer(line):
                content = m.group(1)
                items = split_citation_items(content)
                for item in items:
                    item_norm = normalize_item(item)
                    if not is_valid_author_year_citation(item_norm):
                        continue
                    counter[item_norm] += 1
                    file_counter[f][item_norm] += 1
                    rows.append({
                        "file": f,
                        "line": line_no,
                        "citation_item": item_norm,
                        "parenthetical_group": "(" + content + ")",
                        "context": line.strip()[:700],
                    })

    out_csv = Path(args.output_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    out_columns = ["file", "line", "citation_item", "parenthetical_group", "context"]
    pd.DataFrame(rows, columns=out_columns).to_csv(out_csv, index=False)

    result = {
        "generated_at_utc": datetime.utcnow().isoformat(),
        "total_citation_items": len(rows),
        "unique_citation_items": len(counter),
        "citation_counts": dict(counter.most_common()),
        "file_citation_counts": {k: dict(v.most_common()) for k, v in file_counter.items()},
    }

    Path(args.output_json).write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    md = []
    md.append("# APA Inline Citation Audit")
    md.append("")
    md.append(f"- Generated at UTC: `{result['generated_at_utc']}`")
    md.append(f"- Total citation items: `{result['total_citation_items']}`")
    md.append(f"- Unique citation items: `{result['unique_citation_items']}`")
    md.append("")
    md.append("## 1. Citation Counts")
    md.append("")
    md.append("| Citation | Count |")
    md.append("|---|---:|")
    for citation, count in counter.most_common():
        md.append(f"| {citation} | {count} |")

    md.append("")
    md.append("## 2. Occurrences")
    md.append("")
    md.append("| File | Line | Citation | Context |")
    md.append("|---|---:|---|---|")
    for row in rows:
        ctx = row["context"].replace("|", "\\|")
        md.append(f"| `{row['file']}` | {row['line']} | {row['citation_item']} | {ctx[:300]} |")

    Path(args.output_md).write_text("\n".join(md), encoding="utf-8")

    print("[INFO] MD:", args.output_md)
    print("[INFO] CSV:", args.output_csv)
    print("[INFO] JSON:", args.output_json)
    print("[INFO] Total citation items:", len(rows))
    print("[INFO] Unique citation items:", len(counter))


if __name__ == "__main__":
    main()
