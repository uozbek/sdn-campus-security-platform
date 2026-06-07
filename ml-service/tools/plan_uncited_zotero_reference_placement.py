#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from datetime import datetime

import pandas as pd


def clean(v) -> str:
    if v is None:
        return ""
    s = str(v)
    if s.lower() == "nan":
        return ""
    return s.strip()


def infer_target(row) -> tuple[str, str]:
    title = clean(row.get("title")).lower()
    decision = clean(row.get("final_decision"))
    relevance = clean(row.get("relevance_to_this_thesis"))

    method_terms = [
        "harris hawks", "grey wolf", "gray wolf", "dragonfly",
        "particle swarm", "ensemble methods", "feature selection",
        "bagging", "boosting", "svm", "support vector",
    ]
    dataset_terms = [
        "dataset", "datasets", "labeling network traffic",
        "kdd", "cic", "intrusion detection datasets",
    ]
    runtime_terms = [
        "real-time", "runtime", "online", "ryu", "mininet",
        "openflow", "ids/ips", "mitigation", "prevention",
        "controller", "flow", "bandwidth control",
    ]
    survey_terms = [
        "survey", "comprehensive survey", "review",
    ]
    sdn_ddos_terms = [
        "sdn", "software defined", "software-defined", "ddos",
        "distributed denial", "dos attack",
    ]

    if any(t in title for t in method_terms):
        return "Bölüm 2 veya Bölüm 4", "Yöntemsel arka plan / özellik seçimi / optimizasyon algoritması"
    if any(t in title for t in dataset_terms):
        return "Bölüm 2 ve Bölüm 5", "Veri kümesi, etiketleme, genellenebilirlik ve sınırlılık tartışması"
    if any(t in title for t in runtime_terms):
        return "Bölüm 3 ve Bölüm 5", "Runtime, controller, testbed veya mitigation karşılaştırması"
    if any(t in title for t in survey_terms):
        return "Bölüm 2 ve Bölüm 3", "Kavramsal çerçeve ve literatür sentezi"
    if any(t in title for t in sdn_ddos_terms):
        return "Bölüm 3", "SDN/DDoS literatür karşılaştırması"

    if decision == "keep_method_background" or relevance == "MethodBackground":
        return "Bölüm 2 veya Bölüm 4", "Yöntemsel arka plan"
    if decision == "keep_supporting":
        return "Bölüm 3 veya Bölüm 5", "Destekleyici literatür"
    return "Bölüm 3", "Genel literatür karşılaştırması"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--usage-csv", default="docs/bibliography_reference_usage_audit_zotero_reviewed.csv")
    parser.add_argument("--references-csv", default="docs/references_zotero_apa_like_reviewed.csv")
    parser.add_argument("--output-xlsx", default="docs/literature_review/zotero_clean/uncited_reference_placement_plan.xlsx")
    parser.add_argument("--output-md", default="docs/literature_review/zotero_clean/uncited_reference_placement_plan.md")
    args = parser.parse_args()

    usage = pd.read_csv(args.usage_csv).fillna("")
    refs = pd.read_csv(args.references_csv).fillna("")

    if "zotero_key" not in refs.columns and "id" in refs.columns:
        refs["zotero_key"] = refs["id"]

    merged = usage.merge(
        refs,
        on="zotero_key",
        how="left",
        suffixes=("_usage", "")
    )

    uncited = merged[merged["status"].eq("not_cited_or_not_mentioned")].copy()

    targets = uncited.apply(infer_target, axis=1)
    uncited["target_chapter"] = [t[0] for t in targets]
    uncited["placement_reason"] = [t[1] for t in targets]
    uncited["placement_decision"] = ""
    uncited["proposed_sentence_needed"] = "yes"
    uncited["fulltext_needed"] = uncited["final_decision"].astype(str).isin(["keep_core", "keep_supporting"]).map(lambda x: "yes" if x else "optional")

    cols = [
        "zotero_key",
        "year",
        "surname",
        "final_decision",
        "relevance_to_this_thesis",
        "target_chapter",
        "placement_reason",
        "fulltext_needed",
        "title",
        "venue",
        "doi",
        "placement_decision",
        "proposed_sentence_needed",
    ]
    uncited = uncited[[c for c in cols if c in uncited.columns]]

    out_xlsx = Path(args.output_xlsx)
    out_xlsx.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(out_xlsx, engine="openpyxl") as writer:
        uncited.to_excel(writer, sheet_name="uncited_placement", index=False)

    md = []
    md.append("# Uncited Zotero Reference Placement Plan")
    md.append("")
    md.append(f"- Generated at UTC: `{datetime.utcnow().isoformat()}`")
    md.append(f"- Uncited reference count: `{len(uncited)}`")
    md.append("")
    md.append("## 1. Target Chapter Counts")
    md.append("")
    md.append("| Target | Count |")
    md.append("|---|---:|")
    for k, v in uncited["target_chapter"].value_counts().items():
        md.append(f"| {k} | {v} |")

    md.append("")
    md.append("## 2. Placement Plan")
    md.append("")
    md.append("| Key | Decision | Target | Year | Title | Reason |")
    md.append("|---|---|---|---:|---|---|")
    for _, r in uncited.iterrows():
        title = clean(r.get("title")).replace("|", "\\|")
        reason = clean(r.get("placement_reason")).replace("|", "\\|")
        md.append(f"| {r.get('zotero_key')} | {r.get('final_decision')} | {r.get('target_chapter')} | {r.get('year')} | {title[:120]} | {reason} |")

    out_md = Path(args.output_md)
    out_md.write_text("\n".join(md), encoding="utf-8")

    print("[INFO] XLSX:", out_xlsx)
    print("[INFO] MD:", out_md)
    print("[INFO] Uncited count:", len(uncited))
    print(uncited["target_chapter"].value_counts().to_string())


if __name__ == "__main__":
    main()
