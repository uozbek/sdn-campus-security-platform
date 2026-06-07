#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

import yaml


REQUIRED_FIELDS = [
    "university",
    "institute",
    "department",
    "program",
    "degree_type_tr",
    "degree_type_en",
    "title_tr",
    "title_en",
    "author",
    "student_id",
    "advisor",
    "city",
    "year",
]

REQUIRED_LIST_FIELDS = [
    "jury",
    "keywords_tr",
    "keywords_en",
]


def is_missing(value) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        s = value.strip()
        return not s or s.startswith("TODO") or "TODO_" in s
    return False


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--metadata", default="docs/thesis_metadata.yaml")
    parser.add_argument("--output-md", default="docs/thesis_metadata_quality_report.md")
    parser.add_argument("--output-json", default="docs/thesis_metadata_quality_report.json")
    args = parser.parse_args()

    meta_path = Path(args.metadata)
    if not meta_path.exists():
        raise SystemExit(f"[ERROR] Metadata file not found: {meta_path}")

    meta = yaml.safe_load(meta_path.read_text(encoding="utf-8")) or {}

    checks = []

    for field in REQUIRED_FIELDS:
        value = meta.get(field)
        checks.append({
            "field": field,
            "value": "" if value is None else str(value),
            "status": "check" if is_missing(value) else "ok",
            "note": "required scalar field",
        })

    for field in REQUIRED_LIST_FIELDS:
        value = meta.get(field)
        status = "ok"
        note = "required list field"

        if not isinstance(value, list) or len(value) == 0:
            status = "check"
            note = "missing or empty list"
        else:
            bad_items = [str(x) for x in value if is_missing(x)]
            if bad_items:
                status = "check"
                note = "contains TODO/missing items: " + ", ".join(bad_items)

        checks.append({
            "field": field,
            "value": json.dumps(value, ensure_ascii=False) if value is not None else "",
            "status": status,
            "note": note,
        })

    todo_hits = []
    for key, value in meta.items():
        if isinstance(value, str) and "TODO" in value:
            todo_hits.append({"field": key, "value": value})
        elif isinstance(value, list):
            for idx, item in enumerate(value):
                if isinstance(item, str) and "TODO" in item:
                    todo_hits.append({"field": f"{key}[{idx}]", "value": item})

    result = {
        "generated_at_utc": datetime.utcnow().isoformat(),
        "metadata": str(meta_path),
        "checks": checks,
        "todo_hits": todo_hits,
        "summary": {
            "ok": sum(1 for c in checks if c["status"] == "ok"),
            "check": sum(1 for c in checks if c["status"] != "ok"),
            "total": len(checks),
            "todo_count": len(todo_hits),
        },
    }

    Path(args.output_json).write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    md = []
    md.append("# Thesis Metadata Quality Report")
    md.append("")
    md.append(f"- Generated at UTC: `{result['generated_at_utc']}`")
    md.append(f"- Metadata: `{meta_path}`")
    md.append("")
    md.append("## 1. Summary")
    md.append("")
    md.append(f"- OK: `{result['summary']['ok']}`")
    md.append(f"- Check: `{result['summary']['check']}`")
    md.append(f"- Total: `{result['summary']['total']}`")
    md.append(f"- TODO count: `{result['summary']['todo_count']}`")
    md.append("")
    md.append("## 2. Field Checks")
    md.append("")
    md.append("| Field | Status | Value | Note |")
    md.append("|---|---|---|---|")
    for c in checks:
        val = c["value"].replace("|", "\\|")
        md.append(f"| {c['field']} | {c['status']} | {val[:180]} | {c['note']} |")

    md.append("")
    md.append("## 3. TODO Hits")
    md.append("")
    if todo_hits:
        md.append("| Field | Value |")
        md.append("|---|---|")
        for item in todo_hits:
            md.append(f"| {item['field']} | {item['value']} |")
    else:
        md.append("_No TODO fields found._")

    md.append("")
    md.append("## 4. Suggested Next Action")
    md.append("")
    md.append("Metadata içindeki `TODO_*` alanları doldurulduktan sonra `sau_fbe_frontmatter_generated.docx` ve `tez_ana_taslak_tr_sau_fbe.docx` yeniden üretilmelidir.")

    Path(args.output_md).write_text("\n".join(md), encoding="utf-8")

    print("[INFO] MD:", args.output_md)
    print("[INFO] JSON:", args.output_json)
    print("[INFO] Summary:", result["summary"])


if __name__ == "__main__":
    main()
