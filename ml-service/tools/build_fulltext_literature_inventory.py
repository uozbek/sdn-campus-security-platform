#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path


STOPWORDS = {
    "a", "an", "the", "and", "or", "of", "in", "on", "for", "to", "with",
    "using", "based", "by", "from", "into", "towards", "toward", "via",
    "et", "al", "vd", "ve"
}


def clean_cell(value) -> str:
    if value is None:
        return ""
    s = str(value)
    if s.lower() == "nan":
        return ""
    return s.strip()


def normalize_text(s: str) -> str:
    s = clean_cell(s).lower()
    s = s.replace("ı", "i")
    s = re.sub(r"[^a-z0-9ğüşöçıİĞÜŞÖÇ]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def tokens(s: str) -> set[str]:
    toks = normalize_text(s).split()
    return {t for t in toks if len(t) >= 3 and t not in STOPWORDS}


def token_jaccard(a: str, b: str) -> float:
    ta, tb = tokens(a), tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def seq_similarity(a: str, b: str) -> float:
    a = normalize_text(a)
    b = normalize_text(b)
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def file_size(path: Path) -> str:
    if not path.exists():
        return "missing"
    n = path.stat().st_size
    if n < 1024:
        return f"{n} B"
    if n < 1024 ** 2:
        return f"{n / 1024:.1f} KB"
    return f"{n / 1024 ** 2:.1f} MB"


def read_tracking_csv(path: Path) -> list[dict]:
    if not path.exists():
        raise SystemExit(f"[ERROR] Missing tracking CSV: {path}")
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def best_match_for_file(file_path: Path, rows: list[dict]) -> dict:
    stem = file_path.stem
    parent_name = file_path.parent.name
    filename_blob = f"{stem} {parent_name}"

    best = {
        "matched_id": "",
        "matched_title": "",
        "matched_year": "",
        "matched_relevance": "",
        "match_score": 0.0,
        "title_jaccard": 0.0,
        "seq_score": 0.0,
        "year_bonus": 0.0,
    }

    for row in rows:
        title = clean_cell(row.get("title", ""))
        year = clean_cell(row.get("year", "")).replace(".0", "")
        if not title:
            continue

        seq = seq_similarity(filename_blob, title)
        jac = token_jaccard(filename_blob, title)
        year_bonus = 0.08 if year and year in filename_blob else 0.0

        # Jaccard is more important than raw sequence similarity because Zotero filenames
        # often contain author-year-title patterns.
        score = (0.65 * jac) + (0.30 * seq) + year_bonus

        if score > best["match_score"]:
            best = {
                "matched_id": clean_cell(row.get("id", "")),
                "matched_title": title,
                "matched_year": year,
                "matched_relevance": clean_cell(row.get("relevance_to_this_thesis", "")),
                "match_score": round(score, 4),
                "title_jaccard": round(jac, 4),
                "seq_score": round(seq, 4),
                "year_bonus": round(year_bonus, 4),
            }

    return best


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def to_markdown(rows: list[dict], fieldnames: list[str]) -> str:
    lines = []
    lines.append("| " + " | ".join(fieldnames) + " |")
    lines.append("|" + "|".join(["---"] * len(fieldnames)) + "|")

    for row in rows:
        vals = []
        for col in fieldnames:
            val = clean_cell(row.get(col, "")).replace("\n", " ").replace("|", "/")
            if len(val) > 120:
                val = val[:117] + "..."
            vals.append(val)
        lines.append("| " + " | ".join(vals) + " |")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tracking-csv", default="docs/literature_review/literature_tracking_table.csv")
    parser.add_argument("--fulltext-dir", default="docs/literature_review/source_files/files")
    parser.add_argument("--output-dir", default="docs/literature_review/processed")
    parser.add_argument("--min-match-score", type=float, default=0.52)
    args = parser.parse_args()

    tracking_csv = Path(args.tracking_csv)
    fulltext_dir = Path(args.fulltext_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    rows = read_tracking_csv(tracking_csv)

    if not fulltext_dir.exists():
        raise SystemExit(f"[ERROR] Full-text directory not found: {fulltext_dir}")

    # Tez literatürü için HTML snapshot'ları dışarıda bırakıyoruz.
    allowed_suffixes = {".pdf", ".docx", ".doc"}
    files = sorted(
        [p for p in fulltext_dir.rglob("*") if p.is_file() and p.suffix.lower() in allowed_suffixes]
    )

    inventory = []
    for p in files:
        m = best_match_for_file(p, rows)
        matched = m["match_score"] >= args.min_match_score and m["title_jaccard"] >= 0.18

        inventory.append({
            "file_name": p.name,
            "relative_path": str(p),
            "extension": p.suffix.lower(),
            "size": file_size(p),
            "matched_id": m["matched_id"] if matched else "",
            "matched_title": m["matched_title"] if matched else "",
            "matched_year": m["matched_year"] if matched else "",
            "matched_relevance": m["matched_relevance"] if matched else "",
            "match_score": m["match_score"],
            "title_jaccard": m["title_jaccard"],
            "seq_score": m["seq_score"],
            "year_bonus": m["year_bonus"],
            "match_status": "matched" if matched else "needs_manual_review",
        })

    fieldnames = [
        "file_name",
        "relative_path",
        "extension",
        "size",
        "matched_id",
        "matched_title",
        "matched_year",
        "matched_relevance",
        "match_score",
        "title_jaccard",
        "seq_score",
        "year_bonus",
        "match_status",
    ]

    csv_out = output_dir / "fulltext_literature_inventory.csv"
    md_out = output_dir / "fulltext_literature_inventory.md"
    json_out = output_dir / "fulltext_literature_inventory.json"

    write_csv(csv_out, inventory, fieldnames)

    md_lines = []
    md_lines.append("# Full-Text Literature Inventory")
    md_lines.append("")
    md_lines.append(f"- Generated at UTC: `{datetime.utcnow().isoformat()}`")
    md_lines.append(f"- Full-text directory: `{fulltext_dir}`")
    md_lines.append(f"- Tracking CSV: `{tracking_csv}`")
    md_lines.append(f"- Full-text PDF/DOC/DOCX count: `{len(inventory)}`")
    md_lines.append(f"- Matched count: `{sum(1 for r in inventory if r['match_status'] == 'matched')}`")
    md_lines.append(f"- Needs manual review: `{sum(1 for r in inventory if r['match_status'] == 'needs_manual_review')}`")
    md_lines.append("")
    md_lines.append("## Inventory")
    md_lines.append("")
    md_lines.append(to_markdown(inventory, fieldnames))
    md_out.write_text("\n".join(md_lines), encoding="utf-8")

    json_out.write_text(
        json.dumps(
            {
                "generated_at_utc": datetime.utcnow().isoformat(),
                "tracking_csv": str(tracking_csv),
                "fulltext_dir": str(fulltext_dir),
                "file_count": len(inventory),
                "matched_count": sum(1 for r in inventory if r["match_status"] == "matched"),
                "needs_manual_review": sum(1 for r in inventory if r["match_status"] == "needs_manual_review"),
                "files": inventory,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print("[INFO] Full-text files:", len(inventory))
    print("[INFO] Matched:", sum(1 for r in inventory if r["match_status"] == "matched"))
    print("[INFO] Needs manual review:", sum(1 for r in inventory if r["match_status"] == "needs_manual_review"))
    print("[INFO] CSV:", csv_out)
    print("[INFO] MD :", md_out)
    print("[INFO] JSON:", json_out)


if __name__ == "__main__":
    main()
