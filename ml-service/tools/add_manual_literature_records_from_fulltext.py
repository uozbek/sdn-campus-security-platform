#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

import pandas as pd


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


def clean(value) -> str:
    if value is None:
        return ""
    s = str(value)
    if s.lower() == "nan":
        return ""
    return s.strip()


def parse_author_year_title(file_name: str):
    stem = Path(file_name).stem

    # Typical Zotero filename:
    # Author et al. - 2020 - Title...
    parts = stem.split(" - ")

    authors = ""
    year = ""
    title = stem

    if len(parts) >= 3:
        authors = parts[0].strip()
        year_part = parts[1].strip()
        title = " - ".join(parts[2:]).strip()

        m = re.search(r"(19|20)\d{2}", year_part)
        if m:
            year = m.group(0)

    else:
        m = re.search(r"(19|20)\d{2}", stem)
        if m:
            year = m.group(0)

    title = title.replace("_", " ").strip()
    title = re.sub(r"\s+", " ", title)

    return authors, year, title


def infer_fields(title: str, file_name: str):
    text = f"{title} {file_name}".lower()

    sdn_context = ""
    controller = ""
    dataset = ""
    attack_type = ""
    feature_selection = ""
    ml_model = ""
    runtime = ""
    mitigation = ""
    relevance = "Medium"

    if "sdn" in text or "software defined" in text or "software-defined" in text:
        sdn_context = "Yes; SDN-related study"
        relevance = "High"

    if "ryu" in text:
        controller = "Ryu"
        relevance = "High"
    elif "mininet" in text:
        controller = "Mininet"
        relevance = "High"
    elif "openflow" in text:
        controller = "OpenFlow"

    if "ddos" in text or "denial of service" in text:
        attack_type = "DDoS"
        relevance = "High"

    if "cic-ddos2019" in text or "cicddos2019" in text:
        dataset = "CIC-DDoS2019"
    elif "cicids" in text:
        dataset = "CICIDS"
    elif "insdn" in text:
        dataset = "InSDN"
    elif "nsl-kdd" in text:
        dataset = "NSL-KDD"

    if "feature selection" in text:
        feature_selection = "Feature selection"
    if "hho" in text or "harris hawks" in text:
        feature_selection = "HHO / feature selection"
    if "pso" in text or "particle swarm" in text:
        feature_selection = "PSO / feature selection"
    if "gwo" in text or "grey wolf" in text:
        feature_selection = "GWO / feature selection"
    if "dragonfly" in text or "dfo" in text:
        feature_selection = "DFO / feature selection"

    models = []
    for label, terms in [
        ("XGBoost", ["xgboost", "extreme gradient"]),
        ("Random Forest", ["random forest"]),
        ("SVM", ["svm", "support vector"]),
        ("LSTM", ["lstm", "long short"]),
        ("GRU", ["gru"]),
        ("CNN", ["cnn", "convolution"]),
        ("Deep Learning", ["deep learning"]),
        ("Machine Learning", ["machine learning"]),
        ("Neural Network", ["neural network"]),
    ]:
        if any(t in text for t in terms):
            models.append(label)

    ml_model = " / ".join(dict.fromkeys(models))

    if "real-time" in text or "real time" in text or "near real-time" in text or "near real time" in text:
        runtime = "Runtime / near-real-time"
        relevance = "High"

    if "mitigation" in text or "prevention" in text or "defense" in text:
        mitigation = "Mitigation / prevention"
        relevance = "High"

    return {
        "sdn_context": sdn_context,
        "controller_or_testbed": controller,
        "dataset": dataset,
        "traffic_type": "To verify from full text",
        "attack_type": attack_type or "To verify from full text",
        "feature_extraction": "To verify from full text",
        "feature_selection": feature_selection,
        "ml_dl_model": ml_model,
        "real_time_or_offline": runtime or "To verify from full text",
        "mitigation_action": mitigation or "To verify from full text",
        "metrics_reported": "To verify from full text",
        "relevance_to_this_thesis": relevance,
    }


def next_manual_id(existing_ids: set[str], counter: int) -> str:
    while True:
        candidate = f"MAN{counter:03d}"
        if candidate not in existing_ids:
            return candidate
        counter += 1


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--tracking-csv",
        default="docs/literature_review/literature_tracking_table.csv",
    )
    parser.add_argument(
        "--reviewed-inventory",
        default="docs/literature_review/processed/fulltext_literature_inventory_reviewed.csv",
    )
    parser.add_argument(
        "--output-tracking-csv",
        default="docs/literature_review/literature_tracking_table.csv",
    )
    parser.add_argument(
        "--manual-records-csv",
        default="docs/literature_review/processed/manual_literature_records_added.csv",
    )
    args = parser.parse_args()

    tracking_path = Path(args.tracking_csv)
    reviewed_path = Path(args.reviewed_inventory)
    output_tracking = Path(args.output_tracking_csv)
    manual_records_path = Path(args.manual_records_csv)

    tracking = pd.read_csv(tracking_path).fillna("")
    reviewed = pd.read_csv(reviewed_path).fillna("")

    existing_ids = set(tracking["id"].astype(str))
    existing_titles = set(tracking["title"].astype(str).str.lower())

    candidates = reviewed[reviewed["match_status"] == "new_tracking_record_needed"].copy()

    manual_rows = []
    counter = 1

    for _, r in candidates.iterrows():
        file_name = clean(r.get("file_name", ""))
        relative_path = clean(r.get("relative_path", ""))

        authors, year, title = parse_author_year_title(file_name)

        if not title or title.lower() in existing_titles:
            continue

        mid = next_manual_id(existing_ids, counter)
        existing_ids.add(mid)
        counter += 1

        inferred = infer_fields(title, file_name)

        row = {
            "id": mid,
            "year": year,
            "authors": authors,
            "title": title,
            "venue": "To verify from full text",
            "publisher_database": "Manual record from Zotero full-text file",
            "doi_url": "",
            "study_type": "Research article / to verify",
            "sdn_context": inferred["sdn_context"],
            "controller_or_testbed": inferred["controller_or_testbed"],
            "dataset": inferred["dataset"],
            "traffic_type": inferred["traffic_type"],
            "attack_type": inferred["attack_type"],
            "feature_extraction": inferred["feature_extraction"],
            "feature_selection": inferred["feature_selection"],
            "ml_dl_model": inferred["ml_dl_model"],
            "real_time_or_offline": inferred["real_time_or_offline"],
            "mitigation_action": inferred["mitigation_action"],
            "metrics_reported": inferred["metrics_reported"],
            "main_results": "To extract from full text",
            "strengths": "To extract from full text",
            "limitations": "To extract from full text",
            "relevance_to_this_thesis": inferred["relevance_to_this_thesis"],
            "notes": f"Manual record generated from full-text file: {relative_path}",
        }

        manual_rows.append(row)

    if manual_rows:
        tracking_out = pd.concat([tracking, pd.DataFrame(manual_rows)], ignore_index=True)
    else:
        tracking_out = tracking

    # Ensure column order
    for col in TRACKING_COLUMNS:
        if col not in tracking_out.columns:
            tracking_out[col] = ""

    tracking_out = tracking_out[TRACKING_COLUMNS]

    output_tracking.parent.mkdir(parents=True, exist_ok=True)
    tracking_out.to_csv(output_tracking, index=False)

    manual_records_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(manual_rows, columns=TRACKING_COLUMNS).to_csv(manual_records_path, index=False)

    print("[INFO] Manual records added:", len(manual_rows))
    print("[INFO] Updated tracking CSV:", output_tracking)
    print("[INFO] Manual records CSV:", manual_records_path)

    if manual_rows:
        print(pd.DataFrame(manual_rows)[["id", "year", "authors", "title", "relevance_to_this_thesis"]].to_string(index=False))


if __name__ == "__main__":
    main()
