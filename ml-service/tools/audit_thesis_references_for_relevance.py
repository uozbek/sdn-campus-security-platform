#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path

import pandas as pd


CORE_TERMS = [
    "sdn",
    "software defined",
    "software-defined",
    "openflow",
    "ryu",
    "mininet",
    "ddos",
    "dos attack",
    "intrusion detection",
    "network intrusion",
    "ids",
    "ips",
    "cybersecurity",
    "network security",
    "feature selection",
    "machine learning",
    "deep learning",
    "cic-ddos",
    "cicddos",
    "cicids",
    "insdn",
    "mitigation",
    "prevention",
    "controller",
]

LIKELY_IRRELEVANT_TERMS = [
    "environmental modelling",
    "groundwater",
    "landslide",
    "solar photovoltaic",
    "banking sector",
    "software cost estimation",
    "bayes point machine",
]


def clean(v) -> str:
    if v is None:
        return ""
    s = str(v)
    if s.lower() == "nan":
        return ""
    return re.sub(r"\s+", " ", s).strip()


def blob(row) -> str:
    cols = [
        "id",
        "year",
        "authors",
        "title",
        "venue",
        "publisher_database",
        "study_type",
        "sdn_context",
        "controller_or_testbed",
        "dataset",
        "traffic_type",
        "attack_type",
        "feature_extraction",
        "feature_selection",
        "ml_dl_model",
        "real_time_or_offline",
        "mitigation_action",
        "metrics_reported",
        "main_results",
        "strengths",
        "limitations",
        "notes",
    ]
    return " ".join(clean(row.get(c, "")) for c in cols).lower()


def score_relevance(text: str) -> int:
    return sum(1 for t in CORE_TERMS if t in text)


def has_irrelevant_signal(text: str) -> bool:
    return any(t in text for t in LIKELY_IRRELEVANT_TERMS)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--tracking-csv",
        default="docs/literature_review/literature_tracking_table.csv",
    )
    parser.add_argument(
        "--references-csv",
        default="docs/kaynakca_taslagi_literature_tracking.csv",
    )
    parser.add_argument(
        "--output-md",
        default="docs/reference_relevance_audit_report.md",
    )
    parser.add_argument(
        "--output-csv",
        default="docs/reference_relevance_audit_candidates.csv",
    )
    parser.add_argument(
        "--output-json",
        default="docs/reference_relevance_audit_report.json",
    )
    parser.add_argument(
        "--keep-low-ids-file",
        default="docs/reference_keep_low_ids.txt",
        help="Optional text file containing low-relevance IDs that should be kept with justification.",
    )
    args = parser.parse_args()

    tracking_path = Path(args.tracking_csv)
    references_path = Path(args.references_csv)

    if not tracking_path.exists():
        raise SystemExit(f"[ERROR] Missing tracking CSV: {tracking_path}")

    tracking = pd.read_csv(tracking_path).fillna("")

    if references_path.exists():
        refs = pd.read_csv(references_path).fillna("")
        used_ids = set(refs["id"].astype(str))
        df = tracking[tracking["id"].astype(str).isin(used_ids)].copy()
    else:
        df = tracking.copy()

    keep_low_ids = set()
    keep_low_file = Path(args.keep_low_ids_file)
    if keep_low_file.exists():
        for line in keep_low_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            keep_low_ids.add(line.split()[0])

    rows = []
    for _, row in df.iterrows():
        text = blob(row)
        rel_score = score_relevance(text)
        irrelevant = has_irrelevant_signal(text)

        title = clean(row.get("title", ""))
        rid = clean(row.get("id", ""))
        relevance = clean(row.get("relevance_to_this_thesis", ""))

        duplicate_hint = False
        if rid.startswith("MAN"):
            duplicate_hint = True

        status = "keep"
        reason = []

        if irrelevant:
            status = "review_or_remove"
            reason.append("likely_irrelevant_domain")

        if rel_score == 0:
            status = "review_or_remove"
            reason.append("no_core_terms")

        if duplicate_hint:
            status = "manual_duplicate_check"
            reason.append("manual_record_possible_duplicate")

        if relevance.lower() in ["low", "not relevant", "irrelevant"]:
            status = "review_or_remove"
            reason.append("low_relevance_field")

        if rid in keep_low_ids and status == "review_or_remove":
            status = "keep_low_with_justification"
            reason.append("kept_by_reference_keep_low_ids")

        rows.append({
            "id": rid,
            "year": clean(row.get("year", "")),
            "authors": clean(row.get("authors", ""))[:120],
            "title": title,
            "venue": clean(row.get("venue", ""))[:120],
            "relevance_to_this_thesis": relevance,
            "relevance_score": rel_score,
            "status": status,
            "reason": ";".join(reason),
        })

    audit = pd.DataFrame(rows)
    candidates = audit[~audit["status"].isin(["keep", "keep_low_with_justification"])].copy()
    candidates = candidates.sort_values(by=["status", "relevance_score", "year"], ascending=[True, True, False])

    Path(args.output_csv).parent.mkdir(parents=True, exist_ok=True)
    candidates.to_csv(args.output_csv, index=False)

    result = {
        "generated_at_utc": datetime.utcnow().isoformat(),
        "tracking_csv": str(tracking_path),
        "references_csv": str(references_path),
        "total_references_checked": len(audit),
        "candidate_count": len(candidates),
        "status_counts": candidates["status"].value_counts(dropna=False).to_dict() if len(candidates) else {},
    }

    Path(args.output_json).write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    md = []
    md.append("# Reference Relevance Audit Report")
    md.append("")
    md.append(f"- Generated at UTC: `{result['generated_at_utc']}`")
    md.append(f"- Checked references: `{result['total_references_checked']}`")
    md.append(f"- Candidate count: `{result['candidate_count']}`")
    md.append("")
    md.append("## 1. Status Counts")
    md.append("")
    md.append("```json")
    md.append(json.dumps(result["status_counts"], indent=2, ensure_ascii=False))
    md.append("```")
    md.append("")
    md.append("## 2. Review Candidates")
    md.append("")
    if len(candidates):
        md.append(candidates.to_markdown(index=False))
    else:
        md.append("_No candidates found._")
    md.append("")
    md.append("## 3. Suggested Actions")
    md.append("")
    md.append("- `review_or_remove`: Tez konusu dışı ise tracking/reference havuzundan çıkarılmalı veya relevance `Low` yapılmalı.")
    md.append("- `manual_duplicate_check`: Aynı makalenin BIB/LR karşılığı varsa MAN kaydı kaynakçadan çıkarılmalı.")
    md.append("- SDN/DDoS/IDS/feature-selection/metrik temeli olan genel ML kaynakları korunabilir; ancak konu dışı domain makaleleri kaynakçaya girmemelidir.")

    Path(args.output_md).write_text("\n".join(md), encoding="utf-8")

    print("[INFO] MD:", args.output_md)
    print("[INFO] CSV:", args.output_csv)
    print("[INFO] JSON:", args.output_json)
    print("[INFO] Candidate count:", len(candidates))


if __name__ == "__main__":
    main()
