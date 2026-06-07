#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import datetime
from pathlib import Path


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        raise SystemExit(f"[ERROR] Missing CSV: {path}")
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({col: row.get(col, "") for col in fieldnames})


def clean_cell(value) -> str:
    if value is None:
        return ""
    s = str(value)
    if s.lower() == "nan":
        return ""
    return s.strip()


def norm(value) -> str:
    s = clean_cell(value).lower()
    s = s.replace("ı", "i")
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def has_any(text: str, terms: list[str]) -> bool:
    low = norm(text)
    return any(t.lower() in low for t in terms)


def to_markdown(rows: list[dict], fieldnames: list[str]) -> str:
    lines = []
    lines.append("| " + " | ".join(fieldnames) + " |")
    lines.append("|" + "|".join(["---"] * len(fieldnames)) + "|")

    for row in rows:
        vals = []
        for col in fieldnames:
            val = clean_cell(row.get(col, "")).replace("\n", " ").replace("|", "/")
            if len(val) > 140:
                val = val[:137] + "..."
            vals.append(val)
        lines.append("| " + " | ".join(vals) + " |")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--tracking-csv",
        default="docs/literature_review/literature_tracking_table.csv",
    )
    parser.add_argument(
        "--fulltext-inventory",
        default="docs/literature_review/processed/fulltext_literature_inventory.csv",
    )
    parser.add_argument(
        "--output-dir",
        default="docs/literature_review/synthesis",
    )
    parser.add_argument(
        "--fallback-limit",
        type=int,
        default=30,
        help="If no candidate is selected, include first N records for manual screening.",
    )
    args = parser.parse_args()

    tracking_csv = Path(args.tracking_csv)
    fulltext_inventory_path = Path(args.fulltext_inventory)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    rows = read_csv(tracking_csv)

    fulltext_rows = []
    if fulltext_inventory_path.exists():
        fulltext_rows = read_csv(fulltext_inventory_path)

    fulltext_by_id = {}
    for r in fulltext_rows:
        mid = clean_cell(r.get("matched_id", ""))
        if mid:
            fulltext_by_id.setdefault(mid, []).append(clean_cell(r.get("relative_path", "")))

    keyword_terms = [
        "sdn",
        "software-defined",
        "software defined",
        "ddos",
        "dos attack",
        "intrusion detection",
        "ids",
        "ips",
        "openflow",
        "ryu",
        "mininet",
        "ovs",
        "open vswitch",
        "cic-ddos2019",
        "cicddos2019",
        "cicids",
        "insdn",
        "nsl-kdd",
        "mitigation",
        "rate-limit",
        "rate limit",
        "quarantine",
        "drop",
        "machine learning",
        "deep learning",
        "xgboost",
        "random forest",
        "feature selection",
        "metaheuristic",
    ]

    selected = []
    debug_reasons = []

    for r in rows:
        row_id = clean_cell(r.get("id", ""))
        title = clean_cell(r.get("title", ""))

        blob = " ".join([
            clean_cell(r.get("title", "")),
            clean_cell(r.get("venue", "")),
            clean_cell(r.get("study_type", "")),
            clean_cell(r.get("sdn_context", "")),
            clean_cell(r.get("controller_or_testbed", "")),
            clean_cell(r.get("dataset", "")),
            clean_cell(r.get("traffic_type", "")),
            clean_cell(r.get("attack_type", "")),
            clean_cell(r.get("feature_extraction", "")),
            clean_cell(r.get("feature_selection", "")),
            clean_cell(r.get("ml_dl_model", "")),
            clean_cell(r.get("real_time_or_offline", "")),
            clean_cell(r.get("mitigation_action", "")),
            clean_cell(r.get("metrics_reported", "")),
            clean_cell(r.get("main_results", "")),
            clean_cell(r.get("strengths", "")),
            clean_cell(r.get("limitations", "")),
            clean_cell(r.get("notes", "")),
        ])

        relevance = norm(r.get("relevance_to_this_thesis", ""))
        relevance_hit = relevance in {"high", "medium", "yüksek", "orta"}
        keyword_hit = has_any(blob, keyword_terms)
        fulltext_hit = row_id in fulltext_by_id

        reasons = []
        if relevance_hit:
            reasons.append("relevance")
        if keyword_hit:
            reasons.append("keyword")
        if fulltext_hit:
            reasons.append("fulltext")

        if reasons:
            item = dict(r)
            item["fulltext_files"] = " ; ".join(fulltext_by_id.get(row_id, []))
            item["selection_reason"] = "+".join(reasons)
            selected.append(item)
            debug_reasons.append((row_id, title, "+".join(reasons)))

    # Fallback: if strict selection returns zero, include first N non-empty title records.
    if not selected:
        fallback_rows = [r for r in rows if clean_cell(r.get("title", ""))][:args.fallback_limit]
        for r in fallback_rows:
            item = dict(r)
            item["fulltext_files"] = " ; ".join(fulltext_by_id.get(clean_cell(r.get("id", "")), []))
            item["selection_reason"] = "fallback_needs_manual_screening"
            selected.append(item)

    def sort_key(r):
        relevance = clean_cell(r.get("relevance_to_this_thesis", ""))
        rel_rank = {"High": 0, "Medium": 1, "Low": 2, "": 3}.get(relevance, 3)
        try:
            year = int(float(clean_cell(r.get("year", "0")) or 0))
        except Exception:
            year = 0
        return (rel_rank, -year, clean_cell(r.get("title", "")))

    selected = sorted(selected, key=sort_key)

    synthesis_fields = [
        "id",
        "year",
        "authors",
        "title",
        "venue",
        "study_type",
        "sdn_context",
        "controller_or_testbed",
        "dataset",
        "attack_type",
        "feature_extraction",
        "feature_selection",
        "ml_dl_model",
        "real_time_or_offline",
        "mitigation_action",
        "metrics_reported",
        "relevance_to_this_thesis",
        "selection_reason",
        "fulltext_files",
        "notes",
    ]

    csv_out = output_dir / "chapter3_literature_synthesis_candidates.csv"
    md_out = output_dir / "chapter3_literature_synthesis_candidates.md"
    json_out = output_dir / "chapter3_literature_synthesis_candidates.json"

    write_csv(csv_out, selected, synthesis_fields)

    md_lines = []
    md_lines.append("# Chapter 3 Literature Synthesis Candidates")
    md_lines.append("")
    md_lines.append(f"- Generated at UTC: `{datetime.utcnow().isoformat()}`")
    md_lines.append(f"- Source tracking CSV: `{tracking_csv}`")
    md_lines.append(f"- Full-text inventory: `{fulltext_inventory_path}`")
    md_lines.append(f"- Candidate count: `{len(selected)}`")
    md_lines.append("")
    md_lines.append("Bu tablo, Bölüm 3 literatür taraması için öncelikli olarak incelenecek kaynakları göstermektedir.")
    md_lines.append("")
    md_lines.append(to_markdown(selected, synthesis_fields))
    md_out.write_text("\n".join(md_lines), encoding="utf-8")

    json_out.write_text(
        json.dumps(
            {
                "generated_at_utc": datetime.utcnow().isoformat(),
                "source_tracking_csv": str(tracking_csv),
                "fulltext_inventory": str(fulltext_inventory_path),
                "candidate_count": len(selected),
                "debug_selected_reasons": debug_reasons[:100],
                "records": selected,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print("[INFO] Candidate count:", len(selected))
    print("[INFO] CSV:", csv_out)
    print("[INFO] MD :", md_out)
    print("[INFO] JSON:", json_out)


if __name__ == "__main__":
    main()
