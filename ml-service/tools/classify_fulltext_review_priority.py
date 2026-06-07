#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from datetime import datetime
import pandas as pd


def norm(s):
    return str(s or "").lower()


def score_row(row):
    title = norm(row.get("title", ""))
    abstract = norm(row.get("abstract", ""))
    keywords = " ".join([
        title,
        abstract,
        norm(row.get("doi", "")),
        norm(row.get("final_decision", "")),
        norm(row.get("relevance_to_this_thesis", "")),
    ])

    score = 0
    reasons = []

    core_terms = [
        ("software defined", 4),
        ("software-defined", 4),
        ("sdn", 4),
        ("ddos", 4),
        ("distributed denial", 4),
        ("ryu", 5),
        ("mininet", 5),
        ("openflow", 4),
        ("controller", 3),
        ("mitigation", 4),
        ("prevention", 4),
        ("cic-ddos2019", 6),
        ("cicddos2019", 6),
        ("cicflowmeter", 5),
        ("feature selection", 3),
        ("flow", 2),
        ("runtime", 4),
        ("real-time", 4),
        ("real time", 4),
        ("ids/ips", 5),
        ("intrusion detection", 3),
    ]

    method_terms = [
        ("harris hawks", 3),
        ("hho", 3),
        ("particle swarm", 3),
        ("pso", 3),
        ("grey wolf", 3),
        ("gwo", 3),
        ("dragonfly", 2),
        ("ensemble", 2),
        ("xgboost", 2),
        ("lightgbm", 2),
        ("random forest", 2),
        ("support vector", 1),
        ("svm", 1),
        ("auc", 1),
        ("false positive", 2),
        ("far", 2),
        ("fpr", 2),
    ]

    for term, pts in core_terms:
        if term in keywords:
            score += pts
            reasons.append(term)

    for term, pts in method_terms:
        if term in keywords:
            score += pts
            reasons.append(term)

    final_decision = norm(row.get("final_decision", ""))
    relevance = norm(row.get("relevance_to_this_thesis", ""))

    if "keep_core" in final_decision:
        score += 3
        reasons.append("decision:keep_core")
    if "keep_method" in final_decision:
        score += 1
        reasons.append("decision:method")
    if "high" in relevance:
        score += 3
        reasons.append("relevance:high")

    return score, sorted(set(reasons))


def nsl_policy(row):
    text = " ".join([
        norm(row.get("title", "")),
        norm(row.get("abstract", "")),
        norm(row.get("keywords", "")),
    ])

    if "nsl-kdd" in text or "nsl kdd" in text or "kdd cup" in text or "kddcup" in text:
        return (
            "historical_context_only",
            "NSL-KDD/KDD appears; do not use as thesis dataset or core experimental evidence."
        )

    return (
        "not_nsl_kdd_focused",
        "No NSL-KDD/KDD focus detected in title/abstract metadata."
    )


def priority_group(score, nsl_status, row):
    title = norm(row.get("title", ""))

    # NSL-KDD kaynakları sadece tarihsel bağlamda tutulacak.
    if nsl_status == "historical_context_only":
        if "cic-ddos2019" in title or "sdn" in title or "software-defined" in title or "software defined" in title:
            return "B_context_or_secondary"
        return "C_historical_context_only"

    if score >= 12:
        return "A_core_fulltext_review"
    if score >= 7:
        return "B_targeted_fulltext_review"
    return "C_supporting_or_background"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--inventory-csv",
        default="docs/literature_review/zotero_clean/fulltext_inventory_reviewed_refs.csv"
    )
    parser.add_argument(
        "--output-csv",
        default="docs/literature_review/zotero_clean/fulltext_review_priority.csv"
    )
    parser.add_argument(
        "--output-md",
        default="docs/literature_review/zotero_clean/fulltext_review_priority.md"
    )
    args = parser.parse_args()

    df = pd.read_csv(args.inventory_csv).fillna("")

    rows = []
    for _, row in df.iterrows():
        score, reasons = score_row(row)
        nsl_status, nsl_note = nsl_policy(row)
        group = priority_group(score, nsl_status, row)

        r = row.to_dict()
        r["fulltext_priority_score"] = score
        r["fulltext_priority_reasons"] = "; ".join(reasons)
        r["nsl_kdd_policy"] = nsl_status
        r["nsl_kdd_note"] = nsl_note
        r["fulltext_priority_group"] = group
        rows.append(r)

    out = pd.DataFrame(rows)
    out = out.sort_values(
        by=["fulltext_priority_group", "fulltext_priority_score", "year"],
        ascending=[True, False, False]
    )

    Path(args.output_csv).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.output_csv, index=False)

    counts = out["fulltext_priority_group"].value_counts().to_dict()
    nsl_counts = out["nsl_kdd_policy"].value_counts().to_dict()

    md = []
    md.append("# Full Text Review Priority")
    md.append("")
    md.append(f"- Generated at UTC: `{datetime.utcnow().isoformat()}`")
    md.append(f"- Input inventory: `{args.inventory_csv}`")
    md.append(f"- Output CSV: `{args.output_csv}`")
    md.append(f"- Total references: `{len(out)}`")
    md.append("")
    md.append("## 1. Priority Group Counts")
    md.append("")
    md.append("| Group | Count |")
    md.append("|---|---:|")
    for k, v in counts.items():
        md.append(f"| {k} | {v} |")

    md.append("")
    md.append("## 2. NSL-KDD Policy Counts")
    md.append("")
    md.append("| Policy | Count |")
    md.append("|---|---:|")
    for k, v in nsl_counts.items():
        md.append(f"| {k} | {v} |")

    md.append("")
    md.append("## 3. A Group — Core Full Text Review")
    md.append("")
    a = out[out["fulltext_priority_group"].eq("A_core_fulltext_review")]
    if len(a):
        md.append("| Key | Year | Score | Title | Reasons |")
        md.append("|---|---:|---:|---|---|")
        for _, r in a.iterrows():
            title = str(r.get("title", "")).replace("|", "\\|")
            reasons = str(r.get("fulltext_priority_reasons", "")).replace("|", "\\|")
            md.append(f"| {r.get('zotero_key','')} | {r.get('year','')} | {r.get('fulltext_priority_score','')} | {title[:120]} | {reasons[:160]} |")
    else:
        md.append("No A group references detected.")

    md.append("")
    md.append("## 4. NSL-KDD Historical / Context Only")
    md.append("")
    nsl = out[out["nsl_kdd_policy"].eq("historical_context_only")]
    if len(nsl):
        md.append("| Key | Year | Group | Title |")
        md.append("|---|---:|---|---|")
        for _, r in nsl.iterrows():
            title = str(r.get("title", "")).replace("|", "\\|")
            md.append(f"| {r.get('zotero_key','')} | {r.get('year','')} | {r.get('fulltext_priority_group','')} | {title[:140]} |")
    else:
        md.append("No NSL-KDD/KDD-focused references detected in title/abstract metadata.")

    Path(args.output_md).write_text("\n".join(md), encoding="utf-8")

    print("[INFO] Total:", len(out))
    print("[INFO] Priority counts:", counts)
    print("[INFO] NSL-KDD policy counts:", nsl_counts)
    print("[INFO] CSV:", args.output_csv)
    print("[INFO] MD:", args.output_md)


if __name__ == "__main__":
    main()
