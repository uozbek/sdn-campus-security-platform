#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from datetime import datetime
from pathlib import Path

import pandas as pd


DOMAIN_TERMS_HIGH = [
    "software defined network", "software-defined network", "sdn",
    "ddos", "distributed denial", "denial of service",
    "openflow", "ryu", "mininet",
    "intrusion detection", "intrusion prevention",
    "ids", "ips",
    "network intrusion",
    "anomaly detection",
    "flow-based",
    "network attack",
    "mitigation",
]

DOMAIN_TERMS_MEDIUM = [
    "cybersecurity", "cyber security", "network security",
    "machine learning", "deep learning",
    "feature selection", "ensemble", "xgboost", "lightgbm",
    "support vector", "svm", "random forest",
    "dataset", "cic", "nsl-kdd", "kdd",
]

METHOD_TERMS = [
    "machine learning",
    "support vector",
    "svm",
    "random forest",
    "decision forest",
    "bagging",
    "boosting",
    "ensemble",
    "feature selection",
    "particle swarm",
    "grey wolf",
    "gray wolf",
    "harris hawks",
    "dragonfly",
    "metaheuristic",
    "data preprocessing",
    "xgboost",
    "lightgbm",
]

OUT_OF_SCOPE_TERMS = [
    "autism",
    "photovoltaic",
    "solar",
    "stock",
    "biometric",
    "gene expression",
    "education",
    "chatbot",
    "moodle",
    "scholarship",
    "student",
    "electronic nose",
    "bayes point machine",
    "kernel interpolation",
]


def clean(value) -> str:
    if value is None:
        return ""
    s = str(value)
    if s.lower() == "nan":
        return ""
    return s.strip()


def blob(row) -> str:
    parts = [
        clean(row.get("title")),
        clean(row.get("abstract")),
        clean(row.get("keywords")),
        clean(row.get("venue")),
        clean(row.get("entry_type")),
    ]
    return " ".join(parts).lower()


def count_terms(text: str, terms: list[str]) -> int:
    return sum(1 for t in terms if t in text)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-csv", default="docs/literature_review/zotero_clean/zotero_canonical_references.csv")
    parser.add_argument("--output-csv", default="docs/literature_review/zotero_clean/zotero_thesis_reference_classification.csv")
    parser.add_argument("--output-md", default="docs/literature_review/zotero_clean/zotero_thesis_reference_classification.md")
    args = parser.parse_args()

    df = pd.read_csv(args.input_csv).fillna("")

    rows = []

    for _, row in df.iterrows():
        text = blob(row)
        key = clean(row.get("zotero_key"))
        metadata_status = clean(row.get("metadata_review_status"))
        thesis_status = clean(row.get("thesis_use_status"))

        high = count_terms(text, DOMAIN_TERMS_HIGH)
        medium = count_terms(text, DOMAIN_TERMS_MEDIUM)
        method = count_terms(text, METHOD_TERMS)
        out = count_terms(text, OUT_OF_SCOPE_TERMS)

        missing_critical = (
            not clean(row.get("title"))
            or not clean(row.get("authors"))
            or not clean(row.get("year"))
        )

        if metadata_status == "exclude_from_thesis" or thesis_status == "excluded_metadata_or_scope":
            relevance = "Excluded"
            use_status = "excluded_by_metadata_review"
            reason = "metadata_review_excluded"

        elif metadata_status == "needs_manual_check" or missing_critical:
            relevance = "ManualReview"
            use_status = "needs_manual_metadata_check"
            reason = "needs_manual_check_or_missing_critical_metadata"

        elif out >= 1 and high == 0:
            relevance = "Excluded"
            use_status = "excluded_out_of_scope_candidate"
            reason = "out_of_scope_terms"

        elif high >= 2:
            relevance = "High"
            use_status = "candidate_core_reference"
            reason = f"high_domain_terms={high}"

        elif high == 1 and medium >= 1:
            relevance = "Medium"
            use_status = "candidate_supporting_reference"
            reason = f"high={high};medium={medium}"

        elif method >= 1 and medium >= 1:
            relevance = "MethodBackground"
            use_status = "candidate_method_background"
            reason = f"method={method};medium={medium}"

        elif high == 1:
            relevance = "Medium"
            use_status = "candidate_supporting_reference"
            reason = f"high_domain_terms={high}"

        elif method >= 1:
            relevance = "MethodBackground"
            use_status = "candidate_method_background"
            reason = f"method_terms={method}"

        else:
            relevance = "ManualReview"
            use_status = "needs_scope_review"
            reason = "weak_domain_signal"

        rows.append({
            "zotero_key": key,
            "year": clean(row.get("year")),
            "authors": clean(row.get("authors")),
            "title": clean(row.get("title")),
            "venue": clean(row.get("venue")),
            "doi": clean(row.get("doi")),
            "url": clean(row.get("url")),
            "entry_type": clean(row.get("entry_type")),
            "metadata_review_status": metadata_status,
            "auto_relevance_to_this_thesis": relevance,
            "auto_thesis_use_status": use_status,
            "reason": reason,
            "high_domain_signal_count": high,
            "medium_domain_signal_count": medium,
            "method_signal_count": method,
            "out_of_scope_signal_count": out,
            "manual_decision": "",
            "manual_notes": "",
        })

    out_df = pd.DataFrame(rows)
    Path(args.output_csv).parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(args.output_csv, index=False)

    counts = out_df["auto_relevance_to_this_thesis"].value_counts().to_dict()

    md = []
    md.append("# Zotero Thesis Reference Classification")
    md.append("")
    md.append(f"- Generated at UTC: `{datetime.utcnow().isoformat()}`")
    md.append(f"- Input CSV: `{args.input_csv}`")
    md.append(f"- Output CSV: `{args.output_csv}`")
    md.append(f"- Total records: `{len(out_df)}`")
    md.append(f"- Relevance counts: `{counts}`")
    md.append("")
    md.append("## 1. Summary")
    md.append("")
    md.append("| Relevance | Count |")
    md.append("|---|---:|")
    for k, v in counts.items():
        md.append(f"| {k} | {v} |")

    md.append("")
    md.append("## 2. High / Medium / MethodBackground Candidates")
    md.append("")
    keep = out_df[out_df["auto_relevance_to_this_thesis"].isin(["High", "Medium", "MethodBackground"])]
    md.append("| Key | Relevance | Year | Title |")
    md.append("|---|---|---:|---|")
    for _, r in keep.sort_values(["auto_relevance_to_this_thesis", "year"], ascending=[True, False]).iterrows():
        title = clean(r["title"]).replace("|", "\\|")
        md.append(f"| {r['zotero_key']} | {r['auto_relevance_to_this_thesis']} | {r['year']} | {title[:180]} |")

    md.append("")
    md.append("## 3. Manual Review / Excluded")
    md.append("")
    review = out_df[out_df["auto_relevance_to_this_thesis"].isin(["ManualReview", "Excluded"])]
    md.append("| Key | Relevance | Reason | Year | Title |")
    md.append("|---|---|---|---:|---|")
    for _, r in review.iterrows():
        title = clean(r["title"]).replace("|", "\\|")
        md.append(f"| {r['zotero_key']} | {r['auto_relevance_to_this_thesis']} | {r['reason']} | {r['year']} | {title[:180]} |")

    Path(args.output_md).write_text("\n".join(md), encoding="utf-8")

    print("[INFO] CSV:", args.output_csv)
    print("[INFO] MD:", args.output_md)
    print("[INFO] Counts:", counts)


if __name__ == "__main__":
    main()
