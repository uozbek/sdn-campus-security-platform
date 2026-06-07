#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path
from datetime import datetime
import pandas as pd

try:
    from pypdf import PdfReader
except Exception:
    PdfReader = None


KEYWORD_GROUPS = {
    "dataset_signals": [
        "CIC-DDoS2019", "CICDDoS2019", "CICIDS2017", "CSE-CIC-IDS2018",
        "NSL-KDD", "KDD Cup", "UNSW-NB15", "CAIDA", "Bot-IoT", "ToN_IoT",
        "ISCX", "self-generated", "real traffic", "benchmark dataset"
    ],
    "sdn_testbed_signals": [
        "SDN", "software-defined", "software defined", "OpenFlow", "Ryu",
        "Mininet", "POX", "Floodlight", "ONOS", "OpenDaylight", "controller",
        "switch", "flow rule", "testbed"
    ],
    "mitigation_signals": [
        "mitigation", "prevention", "drop", "block", "rate limit", "rate-limit",
        "quarantine", "blacklist", "flow rule", "countermeasure", "defense"
    ],
    "runtime_signals": [
        "real-time", "real time", "near real-time", "online", "runtime",
        "latency", "throughput", "controller overhead", "CPU", "memory",
        "response time", "detection time"
    ],
    "feature_selection_signals": [
        "feature selection", "feature extraction", "PSO", "particle swarm",
        "HHO", "Harris hawks", "GWO", "grey wolf", "DFO", "dragonfly",
        "genetic algorithm", "chi-square", "information gain", "PCA"
    ],
    "model_signals": [
        "Random Forest", "XGBoost", "LightGBM", "SVM", "Support Vector",
        "Decision Tree", "KNN", "Naive Bayes", "ANN", "DNN", "CNN", "LSTM",
        "GRU", "Autoencoder", "ensemble", "voting", "boosting", "bagging"
    ],
    "metric_signals": [
        "accuracy", "precision", "recall", "F1", "F1-score", "AUC", "ROC",
        "false positive", "false negative", "FPR", "FAR", "TPR", "detection rate",
        "latency", "throughput"
    ],
}


def clean_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def read_pdf_text(path: Path, max_pages: int = 30) -> tuple[str, str]:
    if PdfReader is None:
        return "", "pypdf_not_available"

    try:
        reader = PdfReader(str(path))
        pages = []
        for i, page in enumerate(reader.pages[:max_pages]):
            try:
                pages.append(page.extract_text() or "")
            except Exception:
                pages.append("")
        text = clean_text("\n".join(pages))
        if not text:
            return "", "empty_text"
        return text, "ok"
    except Exception as e:
        return "", f"read_error:{type(e).__name__}"


def count_terms(text_lower: str, terms: list[str]) -> tuple[int, list[str]]:
    found = []
    count = 0
    for term in terms:
        term_l = term.lower()
        if term_l in text_lower:
            found.append(term)
            count += text_lower.count(term_l)
    return count, sorted(set(found))


def sentence_windows(text: str, terms: list[str], max_items: int = 4) -> list[str]:
    # Basit cümle bölme; PDF metninde yeterli ön tarama sağlar.
    sentences = re.split(r"(?<=[.!?])\s+", text)
    hits = []
    terms_l = [t.lower() for t in terms]
    for s in sentences:
        sl = s.lower()
        if any(t in sl for t in terms_l):
            s = clean_text(s)
            if 80 <= len(s) <= 450:
                hits.append(s)
        if len(hits) >= max_items:
            break
    return hits


def classify_thesis_use(row, signal_hits):
    title = str(row.get("title", "")).lower()
    all_found = " ".join(sum((v for v in signal_hits.values()), [])).lower()

    if "nsl-kdd" in all_found or "kdd cup" in all_found or "nsl-kdd" in title:
        nsl_policy = "context_only_if_needed"
    else:
        nsl_policy = "not_nsl_kdd_focused"

    if any(x in all_found for x in ["ryu", "mininet", "openflow", "controller", "mitigation", "prevention", "rate-limit", "quarantine"]):
        target = "Bölüm 3 / Bölüm 5"
    elif any(x in all_found for x in ["feature selection", "pso", "hho", "gwo", "dragonfly", "random forest", "xgboost", "lightgbm"]):
        target = "Bölüm 2 / Bölüm 4"
    elif any(x in all_found for x in ["dataset", "cic-ddos2019", "cicids2017", "cse-cic-ids2018"]):
        target = "Bölüm 2 / Bölüm 5"
    else:
        target = "Bölüm 3"

    return nsl_policy, target


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--priority-csv", default="docs/literature_review/zotero_clean/fulltext_review_priority.csv")
    parser.add_argument("--group", default="A_core_fulltext_review")
    parser.add_argument("--limit", type=int, default=47)
    parser.add_argument("--max-pages", type=int, default=30)
    parser.add_argument("--output-csv", default="docs/literature_review/zotero_clean/fulltext_evidence_cards_A_core.csv")
    parser.add_argument("--output-md", default="docs/literature_review/zotero_clean/fulltext_evidence_cards_A_core.md")
    args = parser.parse_args()

    df = pd.read_csv(args.priority_csv).fillna("")
    sub = df[df["fulltext_priority_group"].eq(args.group)].copy()
    sub = sub.sort_values("fulltext_priority_score", ascending=False).head(args.limit)

    rows = []
    for _, row in sub.iterrows():
        pdf_path = Path(str(row.get("pdf_candidate", "")))
        text, status = read_pdf_text(pdf_path, max_pages=args.max_pages) if pdf_path.exists() else ("", "pdf_missing")
        text_lower = text.lower()

        signal_counts = {}
        signal_hits = {}
        evidence_snippets = {}

        for group_name, terms in KEYWORD_GROUPS.items():
            c, found = count_terms(text_lower, terms)
            signal_counts[group_name] = c
            signal_hits[group_name] = found
            evidence_snippets[group_name] = sentence_windows(text, terms, max_items=3)

        nsl_policy, thesis_target = classify_thesis_use(row, signal_hits)

        rows.append({
            "zotero_key": row.get("zotero_key", ""),
            "year": row.get("year", ""),
            "title": row.get("title", ""),
            "authors": row.get("authors", ""),
            "doi": row.get("doi", ""),
            "final_decision": row.get("final_decision", ""),
            "relevance_to_this_thesis": row.get("relevance_to_this_thesis", ""),
            "fulltext_priority_score": row.get("fulltext_priority_score", ""),
            "pdf_path": str(pdf_path),
            "pdf_extract_status": status,
            "text_chars_extracted": len(text),
            "nsl_kdd_policy_after_fulltext": nsl_policy,
            "recommended_thesis_target": thesis_target,
            **{f"{k}_count": v for k, v in signal_counts.items()},
            **{f"{k}_found": "; ".join(v) for k, v in signal_hits.items()},
            **{f"{k}_snippets": " || ".join(v) for k, v in evidence_snippets.items()},
        })

    out = pd.DataFrame(rows)
    Path(args.output_csv).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.output_csv, index=False)

    md = []
    md.append("# Full Text Evidence Cards — A Core")
    md.append("")
    md.append(f"- Generated at UTC: `{datetime.utcnow().isoformat()}`")
    md.append(f"- Priority CSV: `{args.priority_csv}`")
    md.append(f"- Group: `{args.group}`")
    md.append(f"- Limit: `{args.limit}`")
    md.append(f"- Max pages per PDF: `{args.max_pages}`")
    md.append(f"- Output CSV: `{args.output_csv}`")
    md.append(f"- Card count: `{len(out)}`")
    md.append("")
    md.append("## 1. Extraction Status")
    md.append("")
    md.append("| Status | Count |")
    md.append("|---|---:|")
    for k, v in out["pdf_extract_status"].value_counts().items():
        md.append(f"| {k} | {v} |")

    md.append("")
    md.append("## 2. NSL-KDD Policy After Full Text")
    md.append("")
    md.append("| Policy | Count |")
    md.append("|---|---:|")
    for k, v in out["nsl_kdd_policy_after_fulltext"].value_counts().items():
        md.append(f"| {k} | {v} |")

    md.append("")
    md.append("## 3. Evidence Cards")
    md.append("")
    for _, r in out.iterrows():
        md.append(f"### {r['zotero_key']} — {r['title']}")
        md.append("")
        md.append(f"- Year: `{r['year']}`")
        md.append(f"- Priority score: `{r['fulltext_priority_score']}`")
        md.append(f"- PDF status: `{r['pdf_extract_status']}`")
        md.append(f"- Text chars extracted: `{r['text_chars_extracted']}`")
        md.append(f"- NSL-KDD policy: `{r['nsl_kdd_policy_after_fulltext']}`")
        md.append(f"- Recommended thesis target: `{r['recommended_thesis_target']}`")
        md.append(f"- Dataset signals: `{r['dataset_signals_found']}`")
        md.append(f"- SDN/testbed signals: `{r['sdn_testbed_signals_found']}`")
        md.append(f"- Mitigation signals: `{r['mitigation_signals_found']}`")
        md.append(f"- Runtime signals: `{r['runtime_signals_found']}`")
        md.append(f"- Feature selection signals: `{r['feature_selection_signals_found']}`")
        md.append(f"- Model signals: `{r['model_signals_found']}`")
        md.append(f"- Metric signals: `{r['metric_signals_found']}`")
        md.append("")
        if r["sdn_testbed_signals_snippets"]:
            md.append("**SDN/Testbed evidence snippets**")
            md.append("")
            for s in str(r["sdn_testbed_signals_snippets"]).split(" || ")[:2]:
                md.append(f"- {s[:500]}")
            md.append("")
        if r["mitigation_signals_snippets"]:
            md.append("**Mitigation/runtime evidence snippets**")
            md.append("")
            for s in str(r["mitigation_signals_snippets"]).split(" || ")[:2]:
                md.append(f"- {s[:500]}")
            md.append("")
        if r["feature_selection_signals_snippets"]:
            md.append("**Feature/model evidence snippets**")
            md.append("")
            for s in str(r["feature_selection_signals_snippets"]).split(" || ")[:2]:
                md.append(f"- {s[:500]}")
            md.append("")

    Path(args.output_md).write_text("\n".join(md), encoding="utf-8")

    print("[INFO] Cards:", len(out))
    print("[INFO] Extraction status:", out["pdf_extract_status"].value_counts().to_dict())
    print("[INFO] NSL-KDD policy:", out["nsl_kdd_policy_after_fulltext"].value_counts().to_dict())
    print("[INFO] CSV:", args.output_csv)
    print("[INFO] MD:", args.output_md)


if __name__ == "__main__":
    main()
