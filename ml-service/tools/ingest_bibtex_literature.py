#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import datetime
from pathlib import Path


TRACKING_COLUMNS = [
    "id",
    "year",
    "authors",
    "title",
    "venue",
    "publisher_database",
    "doi_url",
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
    "relevance_to_this_thesis",
    "notes"
]


def clean_value(value: str) -> str:
    value = value.strip().strip(",").strip()
    if value.startswith("{") and value.endswith("}"):
        value = value[1:-1]
    if value.startswith('"') and value.endswith('"'):
        value = value[1:-1]
    value = value.replace("\n", " ")
    value = re.sub(r"\s+", " ", value)
    value = value.replace("{", "").replace("}", "")
    return value.strip()


def split_bib_entries(text: str) -> list[str]:
    entries = []
    i = 0
    n = len(text)

    while i < n:
        at = text.find("@", i)
        if at == -1:
            break

        brace = text.find("{", at)
        if brace == -1:
            break

        level = 0
        j = brace
        while j < n:
            if text[j] == "{":
                level += 1
            elif text[j] == "}":
                level -= 1
                if level == 0:
                    entries.append(text[at:j + 1])
                    i = j + 1
                    break
            j += 1
        else:
            break

    return entries


def parse_entry(entry: str) -> dict:
    first = re.match(r"@(?P<type>\w+)\s*\{\s*(?P<key>[^,]+),", entry, re.S)
    if not first:
        return {}

    entry_type = first.group("type").strip()
    key = first.group("key").strip()

    body = entry[first.end():].strip()
    if body.endswith("}"):
        body = body[:-1]

    fields = {
        "entry_type": entry_type,
        "bibtex_key": key,
    }

    # Captures common BibTeX fields written as field = {value} or field = "value".
    pattern = re.compile(
        r"(?P<field>[A-Za-z0-9_\-]+)\s*=\s*(?P<value>\{(?:[^{}]|\{[^{}]*\})*\}|\"[^\"]*\"|[^,\n]+)\s*,?",
        re.S
    )

    for m in pattern.finditer(body):
        field = m.group("field").lower().strip()
        value = clean_value(m.group("value"))
        fields[field] = value

    return fields


def classify_relevance(title: str, abstract: str, keywords: str) -> str:
    text = f"{title} {abstract} {keywords}".lower()

    high_terms = [
        "software defined networking",
        "software-defined networking",
        "sdn",
        "ddos",
        "intrusion detection",
        "ids",
        "mitigation",
        "openflow",
        "ryu",
        "mininet",
        "machine learning",
        "deep learning",
    ]

    score = sum(1 for t in high_terms if t in text)

    if score >= 5:
        return "High"
    if score >= 3:
        return "Medium"
    return "Low"


def infer_dataset(text: str) -> str:
    low = text.lower()
    datasets = []
    for name in [
        "CIC-DDoS2019",
        "NSL-KDD",
        "CICIDS2017",
        "CICIDS 2017",
        "UNSW-NB15",
        "InSDN",
        "KDDCup99",
        "Kyoto",
        "CSE-CIC-IDS2018",
    ]:
        if name.lower() in low:
            datasets.append(name)
    return " / ".join(dict.fromkeys(datasets))


def infer_models(text: str) -> str:
    low = text.lower()
    models = []
    candidates = [
        ("XGBoost", "xgboost"),
        ("Random Forest", "random forest"),
        ("RF", " rf "),
        ("SVM", "svm"),
        ("LSTM", "lstm"),
        ("CNN", "cnn"),
        ("GRU", "gru"),
        ("MLP", "mlp"),
        ("Decision Tree", "decision tree"),
        ("Ensemble", "ensemble"),
        ("Deep Learning", "deep learning"),
        ("Machine Learning", "machine learning"),
    ]
    padded = f" {low} "
    for label, term in candidates:
        if term in padded:
            models.append(label)
    return " / ".join(dict.fromkeys(models))


def bib_to_tracking_row(entry: dict, idx: int) -> dict:
    title = entry.get("title", "")
    abstract = entry.get("abstract", "")
    keywords = entry.get("keywords", "")
    full_text = f"{title} {abstract} {keywords}"

    doi = entry.get("doi", "")
    url = entry.get("url", "")
    doi_url = f"https://doi.org/{doi}" if doi and not doi.startswith("http") else doi
    if not doi_url:
        doi_url = url

    venue = (
        entry.get("booktitle")
        or entry.get("journal")
        or entry.get("journaltitle")
        or entry.get("publisher")
        or ""
    )

    entry_type = entry.get("entry_type", "")
    study_type = {
        "article": "Research article",
        "inproceedings": "Conference paper",
        "conference": "Conference paper",
        "book": "Book",
        "phdthesis": "Thesis",
        "mastersthesis": "Thesis",
    }.get(entry_type.lower(), entry_type)

    return {
        "id": f"BIB{idx:03d}",
        "year": entry.get("year", ""),
        "authors": entry.get("author", ""),
        "title": title,
        "venue": venue,
        "publisher_database": "Imported from SDN-ML-Security_Referans.bib",
        "doi_url": doi_url,
        "study_type": study_type,
        "sdn_context": "To verify; imported from BibTeX",
        "controller_or_testbed": "",
        "dataset": infer_dataset(full_text),
        "traffic_type": "",
        "attack_type": "DDoS / IDS / network security context to verify",
        "feature_extraction": "",
        "feature_selection": "",
        "ml_dl_model": infer_models(full_text),
        "real_time_or_offline": "To verify",
        "mitigation_action": "To verify",
        "metrics_reported": "",
        "main_results": "",
        "strengths": "",
        "limitations": "",
        "relevance_to_this_thesis": classify_relevance(title, abstract, keywords),
        "notes": f"BibTeX key: {entry.get('bibtex_key', '')}; entry type: {entry_type}"
    }


def read_existing_tracking(path: Path) -> list[dict]:
    if not path.exists():
        return []

    with path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def write_tracking(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=TRACKING_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({c: row.get(c, "") for c in TRACKING_COLUMNS})


def rows_to_markdown(rows: list[dict], max_rows: int | None = None) -> str:
    selected = rows if max_rows is None else rows[:max_rows]
    cols = [
        "id",
        "year",
        "authors",
        "title",
        "venue",
        "study_type",
        "dataset",
        "ml_dl_model",
        "relevance_to_this_thesis",
        "doi_url",
    ]

    lines = []
    lines.append("| " + " | ".join(cols) + " |")
    lines.append("|" + "|".join(["---"] * len(cols)) + "|")

    for row in selected:
        vals = []
        for c in cols:
            val = str(row.get(c, "")).replace("\n", " ").replace("|", "/").strip()
            if len(val) > 120:
                val = val[:117] + "..."
            vals.append(val)
        lines.append("| " + " | ".join(vals) + " |")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--bib",
        default="docs/literature_review/source_files/SDN-ML-Security_Referans.bib",
        help="Input BibTeX file.",
    )
    parser.add_argument(
        "--tracking-csv",
        default="docs/literature_review/literature_tracking_table.csv",
        help="Literature tracking CSV to update.",
    )
    parser.add_argument(
        "--output-dir",
        default="docs/literature_review/processed",
        help="Output directory for processed files.",
    )
    parser.add_argument(
        "--prefix",
        default="BIB",
        help="ID prefix. Currently informational.",
    )
    args = parser.parse_args()

    bib_path = Path(args.bib)
    tracking_csv = Path(args.tracking_csv)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not bib_path.exists():
        raise SystemExit(f"[ERROR] BibTeX file not found: {bib_path}")

    text = bib_path.read_text(encoding="utf-8", errors="ignore")
    raw_entries = split_bib_entries(text)
    parsed_entries = [parse_entry(e) for e in raw_entries]
    parsed_entries = [e for e in parsed_entries if e]

    imported_rows = [
        bib_to_tracking_row(entry, idx)
        for idx, entry in enumerate(parsed_entries, start=1)
    ]

    raw_json = output_dir / "bibtex_references_raw.json"
    raw_csv = output_dir / "bibtex_references_raw.csv"
    summary_md = output_dir / "bibtex_references_summary.md"

    raw_json.write_text(json.dumps(parsed_entries, indent=2, ensure_ascii=False), encoding="utf-8")

    raw_columns = sorted({k for e in parsed_entries for k in e.keys()})
    with raw_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=raw_columns)
        writer.writeheader()
        writer.writerows(parsed_entries)

    existing_rows = read_existing_tracking(tracking_csv)

    # Remove the empty template row if present.
    cleaned_existing = []
    for row in existing_rows:
        if row.get("id") == "LR001" and not row.get("title", "").strip():
            continue
        cleaned_existing.append(row)

    existing_keys = {
        (row.get("title", "").strip().lower(), row.get("year", "").strip())
        for row in cleaned_existing
    }

    merged = list(cleaned_existing)
    added = 0
    for row in imported_rows:
        key = (row.get("title", "").strip().lower(), row.get("year", "").strip())
        if key not in existing_keys:
            merged.append(row)
            existing_keys.add(key)
            added += 1

    write_tracking(tracking_csv, merged)

    md_lines = []
    md_lines.append("# BibTeX References Summary")
    md_lines.append("")
    md_lines.append(f"- Generated at UTC: `{datetime.utcnow().isoformat()}`")
    md_lines.append(f"- Input BibTeX: `{bib_path}`")
    md_lines.append(f"- Parsed entries: `{len(parsed_entries)}`")
    md_lines.append(f"- Added to tracking table: `{added}`")
    md_lines.append(f"- Tracking CSV: `{tracking_csv}`")
    md_lines.append("")
    md_lines.append("## Imported References")
    md_lines.append("")
    md_lines.append(rows_to_markdown(imported_rows))
    md_lines.append("")

    summary_md.write_text("\n".join(md_lines), encoding="utf-8")

    report = {
        "generated_at_utc": datetime.utcnow().isoformat(),
        "bib_path": str(bib_path),
        "parsed_entries": len(parsed_entries),
        "added_to_tracking_table": added,
        "tracking_csv": str(tracking_csv),
        "raw_json": str(raw_json),
        "raw_csv": str(raw_csv),
        "summary_md": str(summary_md),
    }

    report_json = output_dir / "bibtex_ingest_report.json"
    report_json.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print("[INFO] BibTeX parsed entries:", len(parsed_entries))
    print("[INFO] Added to tracking table:", added)
    print("[INFO] Updated tracking CSV:", tracking_csv)
    print("[INFO] Raw JSON:", raw_json)
    print("[INFO] Raw CSV:", raw_csv)
    print("[INFO] Summary MD:", summary_md)
    print("[INFO] Report JSON:", report_json)


if __name__ == "__main__":
    main()
