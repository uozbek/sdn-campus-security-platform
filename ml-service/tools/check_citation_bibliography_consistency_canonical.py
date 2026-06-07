#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

import pandas as pd
from pandas.errors import EmptyDataError


def read_csv_safe(path: str, columns=None) -> pd.DataFrame:
    p = Path(path)
    if not p.exists() or p.stat().st_size == 0:
        return pd.DataFrame(columns=columns or [])
    try:
        return pd.read_csv(p).fillna("")
    except EmptyDataError:
        return pd.DataFrame(columns=columns or [])


def clean(value) -> str:
    if value is None:
        return ""
    s = str(value)
    if s.lower() == "nan":
        return ""
    return s.strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apa-audit-csv", default="docs/apa_inline_citation_audit.csv")
    parser.add_argument("--tracking-csv", default="docs/literature_review/literature_tracking_table.csv")
    parser.add_argument("--canonical-override-csv", default="docs/citation_canonical_id_override.csv")
    parser.add_argument("--output-md", default="docs/citation_bibliography_consistency_report.md")
    parser.add_argument("--output-csv", default="docs/citation_bibliography_consistency_report.csv")
    parser.add_argument("--output-json", default="docs/citation_bibliography_consistency_report.json")
    args = parser.parse_args()

    audit = read_csv_safe(args.apa_audit_csv, columns=["citation_item"])
    tracking = read_csv_safe(args.tracking_csv)
    override = read_csv_safe(args.canonical_override_csv, columns=["citation", "canonical_id", "note"])

    tracking_by_id = {
        clean(row.get("id")): row
        for _, row in tracking.iterrows()
        if clean(row.get("id"))
    }

    override_map = {
        clean(row.get("citation")): {
            "canonical_id": clean(row.get("canonical_id")),
            "note": clean(row.get("note")),
        }
        for _, row in override.iterrows()
        if clean(row.get("citation")) and clean(row.get("canonical_id"))
    }

    citations = sorted(audit["citation_item"].dropna().astype(str).unique()) if "citation_item" in audit.columns else []

    rows = []
    for citation in citations:
        item = override_map.get(citation)
        if not item:
            rows.append({
                "citation": citation,
                "status": "missing_override",
                "matched_ids": "",
                "matched_titles": "",
                "note": "Citation not found in canonical override table.",
            })
            continue

        rid = item["canonical_id"]
        tr = tracking_by_id.get(rid)

        if tr is None:
            rows.append({
                "citation": citation,
                "status": "override_id_not_found",
                "matched_ids": rid,
                "matched_titles": "",
                "note": item["note"],
            })
            continue

        rows.append({
            "citation": citation,
            "status": "matched_by_override",
            "matched_ids": rid,
            "matched_titles": clean(tr.get("title")),
            "note": item["note"],
        })

    out = pd.DataFrame(rows, columns=["citation", "status", "matched_ids", "matched_titles", "note"])
    Path(args.output_csv).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.output_csv, index=False)

    status_counts = out["status"].value_counts().to_dict() if not out.empty else {}
    result = {
        "generated_at_utc": datetime.utcnow().isoformat(),
        "citation_count": len(citations),
        "status_counts": status_counts,
    }
    Path(args.output_json).write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    md = []
    md.append("# Citation–Bibliography Consistency Report")
    md.append("")
    md.append(f"- Generated at UTC: `{result['generated_at_utc']}`")
    md.append(f"- Citation count: `{result['citation_count']}`")
    md.append(f"- Status counts: `{status_counts}`")
    md.append("")
    md.append("| Citation | Status | Matched ID | Matched title | Note |")
    md.append("|---|---|---|---|---|")
    for _, r in out.iterrows():
        title = clean(r["matched_titles"]).replace("|", "\\|")
        note = clean(r["note"]).replace("|", "\\|")
        md.append(f"| {r['citation']} | {r['status']} | {r['matched_ids']} | {title[:220]} | {note} |")

    md.append("")
    md.append("## Not")
    md.append("")
    md.append("Bu rapor canonical override tablosunu esas alır. Duplicate MAN/BIB eşleşmeleri yerine tez için seçilen canonical kaynak ID’leri raporlanır.")

    Path(args.output_md).write_text("\n".join(md), encoding="utf-8")

    print("[INFO] MD:", args.output_md)
    print("[INFO] CSV:", args.output_csv)
    print("[INFO] JSON:", args.output_json)
    print("[INFO] Status counts:", status_counts)


if __name__ == "__main__":
    main()
