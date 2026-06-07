#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path

import pandas as pd


DOMAIN_TERMS = [
    "sdn",
    "software defined",
    "software-defined",
    "openflow",
    "ryu",
    "mininet",
    "ddos",
    "dos attack",
    "intrusion detection",
    "ids",
    "ips",
    "network intrusion",
    "anomaly detection",
    "cybersecurity",
    "cyber security",
    "network security",
    "feature selection",
    "machine learning",
    "deep learning",
    "mitigation",
    "dataset",
    "cic-ddos",
    "cicddos",
    "cicids",
]

OUT_OF_SCOPE_TERMS = [
    "moodle",
    "learning management",
    "chatbot",
    "chatgpt",
    "education",
    "student",
    "scholarship",
    "international",
    "solar",
    "photovoltaic",
    "stock forecasting",
    "autism",
    "eeg",
    "landslide",
    "seru production",
    "biometric",
    "gene expression",
]


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


def text_blob(row) -> str:
    return " ".join([
        clean(row.get("title")),
        clean(row.get("authors")),
        clean(row.get("venue")),
        clean(row.get("selection_reason")),
        clean(row.get("category")),
        clean(row.get("priority_hits")),
    ]).lower()


def is_domain_relevant(row) -> bool:
    blob = text_blob(row)
    return any(t in blob for t in DOMAIN_TERMS)


def is_out_of_scope(row) -> bool:
    blob = text_blob(row)
    return any(t in blob for t in OUT_OF_SCOPE_TERMS)


def main() -> None:
    parser = argparse.ArgumentParser()
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
        "--canonical-override-csv",
        default="docs/citation_canonical_id_override.csv",
    )
    parser.add_argument(
        "--output-md",
        default="docs/compared_studies_bibliography_audit_refined.md",
    )
    parser.add_argument(
        "--output-csv",
        default="docs/compared_studies_bibliography_audit_refined.csv",
    )
    parser.add_argument(
        "--output-json",
        default="docs/compared_studies_bibliography_audit_refined.json",
    )
    args = parser.parse_args()

    synthesis = read_csv_safe(Path(args.synthesis_csv))
    refs = read_csv_safe(Path(args.references_csv))
    tracking = read_csv_safe(Path(args.tracking_csv))
    override = read_csv_safe(Path(args.canonical_override_csv))

    bibliography_ids = set()
    if not refs.empty and "id" in refs.columns:
        bibliography_ids = set(clean(x) for x in refs["id"].astype(str) if clean(x))

    inline_canonical_ids = set()
    if not override.empty and "canonical_id" in override.columns:
        inline_canonical_ids = set(clean(x) for x in override["canonical_id"].astype(str) if clean(x))

    tracking_by_id = {}
    if not tracking.empty and "id" in tracking.columns:
        tracking_by_id = {
            clean(row.get("id")): row
            for _, row in tracking.iterrows()
            if clean(row.get("id"))
        }

    rows = []

    if synthesis.empty:
        raise SystemExit(f"[ERROR] Synthesis CSV empty or missing: {args.synthesis_csv}")

    for _, srow in synthesis.iterrows():
        rid = clean(srow.get("id"))
        if not rid:
            continue

        trow = tracking_by_id.get(rid, srow)

        relevance = clean(trow.get("relevance_to_this_thesis")) or clean(srow.get("relevance_to_this_thesis"))
        title = clean(trow.get("title")) or clean(srow.get("title"))
        year = clean(trow.get("year")).replace(".0", "") or clean(srow.get("year")).replace(".0", "")
        authors = clean(trow.get("authors"))
        venue = clean(trow.get("venue"))

        merged = {
            "title": title,
            "authors": authors,
            "venue": venue,
            "selection_reason": clean(srow.get("selection_reason")),
            "category": clean(srow.get("category")),
            "priority_hits": clean(srow.get("priority_hits")),
        }

        domain_relevant = is_domain_relevant(merged)
        out_scope = is_out_of_scope(merged)
        in_bib = rid in bibliography_ids
        inline_canonical = rid in inline_canonical_ids

        if rid.startswith("MAN"):
            status = "manual_or_duplicate_check"
            required = False
        elif inline_canonical:
            status = "ok_inline_canonical" if in_bib else "missing_inline_canonical"
            required = True
        elif in_bib:
            status = "ok"
            required = True
        elif relevance in {"High", "Medium"} and domain_relevant and not out_scope:
            status = "missing_required_candidate"
            required = True
        elif relevance == "Low" or out_scope:
            status = "excluded_low_or_out_of_scope"
            required = False
        elif domain_relevant:
            status = "review_domain_relevant_but_not_selected"
            required = False
        else:
            status = "excluded_not_domain_relevant"
            required = False

        rows.append({
            "id": rid,
            "status": status,
            "required_for_bibliography": required,
            "in_bibliography": in_bib,
            "inline_canonical": inline_canonical,
            "domain_relevant": domain_relevant,
            "out_of_scope": out_scope,
            "relevance": relevance,
            "year": year,
            "authors": authors,
            "title": title,
            "venue": venue,
            "selection_reason": clean(srow.get("selection_reason")),
        })

    out = pd.DataFrame(rows).drop_duplicates(subset=["id"])
    status_counts = out["status"].value_counts().to_dict()
    required_missing = out[out["status"].isin(["missing_required_candidate", "missing_inline_canonical"])].copy()

    result = {
        "generated_at_utc": datetime.utcnow().isoformat(),
        "candidate_count": len(out),
        "bibliography_id_count": len(bibliography_ids),
        "required_missing_count": len(required_missing),
        "status_counts": status_counts,
    }

    Path(args.output_json).write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    out.to_csv(args.output_csv, index=False)

    md = []
    md.append("# Refined Compared Studies vs Bibliography Audit")
    md.append("")
    md.append(f"- Generated at UTC: `{result['generated_at_utc']}`")
    md.append(f"- Candidate count: `{result['candidate_count']}`")
    md.append(f"- Bibliography ID count: `{result['bibliography_id_count']}`")
    md.append(f"- Required missing count: `{result['required_missing_count']}`")
    md.append(f"- Status counts: `{status_counts}`")
    md.append("")
    md.append("## 1. Summary")
    md.append("")
    md.append("| Status | Count |")
    md.append("|---|---:|")
    for k, v in status_counts.items():
        md.append(f"| {k} | {v} |")

    md.append("")
    md.append("## 2. Missing Required Candidates")
    md.append("")
    if required_missing.empty:
        md.append("No required compared studies are missing from the bibliography.")
    else:
        md.append("| ID | Year | Relevance | Domain relevant | Title |")
        md.append("|---|---:|---|---|---|")
        for _, r in required_missing.iterrows():
            title = clean(r["title"]).replace("|", "\\|")
            md.append(
                f"| {r['id']} | {r['year']} | {r['relevance']} | "
                f"{r['domain_relevant']} | {title[:220]} |"
            )

    md.append("")
    md.append("## 3. Bibliography OK / Included")
    md.append("")
    ok = out[out["status"].isin(["ok", "ok_inline_canonical"])]
    md.append(f"Included bibliography-linked candidate count: `{len(ok)}`")
    md.append("")
    md.append("| ID | Year | Relevance | Title |")
    md.append("|---|---:|---|---|")
    for _, r in ok.sort_values(["year", "id"], ascending=[False, True]).iterrows():
        title = clean(r["title"]).replace("|", "\\|")
        md.append(f"| {r['id']} | {r['year']} | {r['relevance']} | {title[:180]} |")

    md.append("")
    md.append("## 4. Excluded Low / Out of Scope Examples")
    md.append("")
    excluded = out[out["status"].eq("excluded_low_or_out_of_scope")]
    md.append(f"Excluded count: `{len(excluded)}`")
    md.append("")
    md.append("| ID | Year | Relevance | Out of scope | Title |")
    md.append("|---|---:|---|---|---|")
    for _, r in excluded.head(40).iterrows():
        title = clean(r["title"]).replace("|", "\\|")
        md.append(f"| {r['id']} | {r['year']} | {r['relevance']} | {r['out_of_scope']} | {title[:160]} |")

    md.append("")
    md.append("## 5. Manual / Duplicate Check")
    md.append("")
    manual = out[out["status"].eq("manual_or_duplicate_check")]
    if manual.empty:
        md.append("No manual duplicate candidates.")
    else:
        md.append("| ID | Year | Relevance | Title |")
        md.append("|---|---:|---|---|")
        for _, r in manual.iterrows():
            title = clean(r["title"]).replace("|", "\\|")
            md.append(f"| {r['id']} | {r['year']} | {r['relevance']} | {title[:180]} |")

    Path(args.output_md).write_text("\n".join(md), encoding="utf-8")

    print("[INFO] MD:", args.output_md)
    print("[INFO] CSV:", args.output_csv)
    print("[INFO] JSON:", args.output_json)
    print("[INFO] Required missing:", len(required_missing))
    print("[INFO] Status counts:", status_counts)


if __name__ == "__main__":
    main()
