#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import datetime
from pathlib import Path

import pandas as pd


BIB_ENTRY_RE = re.compile(r"@\w+\s*\{\s*([^,\s]+)\s*,", re.MULTILINE)
BIB_FIELD_RE = re.compile(r"^\s*(\w+)\s*=\s*[\{\"](.+?)[\}\"]\s*,?\s*$", re.MULTILINE)


def clean(value) -> str:
    if value is None:
        return ""
    s = str(value)
    if s.lower() == "nan":
        return ""
    return s.strip()


def normalize_title(title: str) -> str:
    title = clean(title).lower()
    title = re.sub(r"[^a-z0-9ğüşöçıİĞÜŞÖÇ]+", " ", title)
    return re.sub(r"\s+", " ", title).strip()


def parse_bib_entries(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    entries = []

    # Basit ama yeterli BibTeX entry ayırıcı.
    chunks = re.split(r"\n@", "\n" + text)
    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue
        if not chunk.startswith("@"):
            chunk = "@" + chunk

        m = re.match(r"@(\w+)\s*\{\s*([^,\s]+)\s*,", chunk)
        if not m:
            continue

        entry_type = m.group(1)
        key = m.group(2)

        fields = {}
        # Çok satırlı field'lar için basit parser.
        body = chunk[m.end():]
        current_field = None
        current_value = []
        brace_level = 0

        for raw_line in body.splitlines():
            line = raw_line.strip()
            if not line or line == "}":
                continue

            if current_field is None:
                fm = re.match(r"(\w+)\s*=\s*[\{\"]?(.*)", line)
                if not fm:
                    continue
                current_field = fm.group(1).lower()
                rest = fm.group(2).strip()
                current_value = [rest]
                brace_level = rest.count("{") - rest.count("}")

                if line.endswith(",") and brace_level <= 0:
                    value = " ".join(current_value).rstrip(",").strip().strip("{}\"")
                    fields[current_field] = value
                    current_field = None
                    current_value = []
            else:
                current_value.append(line)
                brace_level += line.count("{") - line.count("}")
                if line.endswith(",") and brace_level <= 0:
                    value = " ".join(current_value).rstrip(",").strip().strip("{}\"")
                    fields[current_field] = value
                    current_field = None
                    current_value = []

        if current_field is not None:
            value = " ".join(current_value).rstrip(",").strip().strip("{}\"")
            fields[current_field] = value

        entries.append({
            "zotero_key": key,
            "entry_type": entry_type,
            "title": clean(fields.get("title")),
            "authors": clean(fields.get("author")),
            "year": clean(fields.get("year") or fields.get("date"))[:4],
            "venue": clean(fields.get("journaltitle") or fields.get("journal") or fields.get("booktitle") or fields.get("publisher")),
            "doi": clean(fields.get("doi")),
            "url": clean(fields.get("url")),
            "abstract": clean(fields.get("abstract")),
            "keywords": clean(fields.get("keywords") or fields.get("keyword")),
            "file": clean(fields.get("file")),
            "raw_fields": json.dumps(fields, ensure_ascii=False),
        })

    return entries


def detect_csv_columns(df: pd.DataFrame) -> dict:
    lower_map = {c.lower().strip(): c for c in df.columns}

    def pick(*names):
        for n in names:
            if n.lower() in lower_map:
                return lower_map[n.lower()]
        # fuzzy contains
        for c in df.columns:
            lc = c.lower()
            if any(n.lower() in lc for n in names):
                return c
        return None

    return {
        "title": pick("title"),
        "authors": pick("author", "creators"),
        "year": pick("year", "date"),
        "publication": pick("publication title", "journal", "proceedings title", "book title"),
        "doi": pick("doi"),
        "url": pick("url"),
        "abstract": pick("abstract note", "abstract"),
        "item_type": pick("item type", "type"),
        "file_attachments": pick("file attachments", "attachments"),
        "manual_tags": pick("manual tags", "tags"),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--export-dir", default="docs/zotero_exports")
    parser.add_argument("--bib", default="docs/zotero_exports/sdn_ddos_thesis_clean.bib")
    parser.add_argument("--csv", default="docs/zotero_exports/sdn_ddos_thesis_clean.csv")
    parser.add_argument("--rdf", default="docs/zotero_exports/sdn_ddos_thesis_clean.rdf")
    parser.add_argument("--files-dir", default="docs/zotero_exports/files")
    parser.add_argument("--output-csv", default="docs/literature_review/zotero_clean/zotero_canonical_references.csv")
    parser.add_argument("--output-md", default="docs/literature_review/zotero_clean/zotero_export_quality_audit.md")
    parser.add_argument("--output-json", default="docs/literature_review/zotero_clean/zotero_export_quality_audit.json")
    args = parser.parse_args()

    export_dir = Path(args.export_dir)
    bib_path = Path(args.bib)
    csv_path = Path(args.csv)
    rdf_path = Path(args.rdf)
    files_dir = Path(args.files_dir)

    bib_entries = parse_bib_entries(bib_path) if bib_path.exists() else []
    bib_df = pd.DataFrame(bib_entries)

    csv_df = pd.read_csv(csv_path).fillna("") if csv_path.exists() else pd.DataFrame()
    csv_cols = detect_csv_columns(csv_df) if not csv_df.empty else {}

    # Full-text file inventory
    file_paths = []
    if files_dir.exists():
        file_paths = [p for p in files_dir.rglob("*") if p.is_file()]

    pdf_paths = [p for p in file_paths if p.suffix.lower() == ".pdf"]
    html_paths = [p for p in file_paths if p.suffix.lower() in {".html", ".htm"}]

    # Quality flags from BibTeX canonical parse
    if not bib_df.empty:
        bib_df["title_norm"] = bib_df["title"].map(normalize_title)
        bib_df["missing_title"] = bib_df["title"].eq("")
        bib_df["missing_authors"] = bib_df["authors"].eq("")
        bib_df["missing_year"] = bib_df["year"].eq("")
        bib_df["missing_venue"] = bib_df["venue"].eq("")
        bib_df["missing_doi"] = bib_df["doi"].eq("")
        bib_df["missing_url"] = bib_df["url"].eq("")
        bib_df["missing_abstract"] = bib_df["abstract"].eq("")
        bib_df["has_file_field"] = ~bib_df["file"].eq("")
        bib_df["duplicate_doi"] = bib_df["doi"].ne("") & bib_df.duplicated("doi", keep=False)
        bib_df["duplicate_title"] = bib_df["title_norm"].ne("") & bib_df.duplicated("title_norm", keep=False)

        bib_df["zotero_source"] = "bib"
        bib_df["thesis_use_status"] = ""
        bib_df["relevance_to_this_thesis"] = ""
        bib_df["chapter_suggestion"] = ""
        bib_df["metadata_review_status"] = ""
        bib_df["metadata_notes"] = ""

    out_csv = Path(args.output_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    bib_df.to_csv(out_csv, index=False)

    summary = {
        "generated_at_utc": datetime.utcnow().isoformat(),
        "export_dir": str(export_dir),
        "bib_exists": bib_path.exists(),
        "csv_exists": csv_path.exists(),
        "rdf_exists": rdf_path.exists(),
        "files_dir_exists": files_dir.exists(),
        "bib_entry_count": len(bib_df),
        "csv_row_count": len(csv_df),
        "rdf_size_bytes": rdf_path.stat().st_size if rdf_path.exists() else 0,
        "file_count": len(file_paths),
        "pdf_count": len(pdf_paths),
        "html_count": len(html_paths),
        "csv_columns": csv_df.columns.tolist() if not csv_df.empty else [],
        "csv_detected_columns": csv_cols,
    }

    if not bib_df.empty:
        summary["quality_counts"] = {
            "missing_title": int(bib_df["missing_title"].sum()),
            "missing_authors": int(bib_df["missing_authors"].sum()),
            "missing_year": int(bib_df["missing_year"].sum()),
            "missing_venue": int(bib_df["missing_venue"].sum()),
            "missing_doi": int(bib_df["missing_doi"].sum()),
            "missing_url": int(bib_df["missing_url"].sum()),
            "missing_abstract": int(bib_df["missing_abstract"].sum()),
            "has_file_field": int(bib_df["has_file_field"].sum()),
            "duplicate_doi": int(bib_df["duplicate_doi"].sum()),
            "duplicate_title": int(bib_df["duplicate_title"].sum()),
        }

    out_json = Path(args.output_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    md = []
    md.append("# Zotero Export Quality Audit")
    md.append("")
    md.append(f"- Generated at UTC: `{summary['generated_at_utc']}`")
    md.append(f"- Export dir: `{export_dir}`")
    md.append(f"- BIB: `{bib_path}`")
    md.append(f"- CSV: `{csv_path}`")
    md.append(f"- RDF: `{rdf_path}`")
    md.append(f"- Files dir: `{files_dir}`")
    md.append("")
    md.append("## 1. Inventory")
    md.append("")
    md.append("| Item | Value |")
    md.append("|---|---:|")
    md.append(f"| BibTeX entries | {summary['bib_entry_count']} |")
    md.append(f"| CSV rows | {summary['csv_row_count']} |")
    md.append(f"| Exported files | {summary['file_count']} |")
    md.append(f"| PDF files | {summary['pdf_count']} |")
    md.append(f"| HTML files | {summary['html_count']} |")
    md.append("")
    md.append("## 2. BibTeX Metadata Quality")
    md.append("")
    md.append("| Check | Count |")
    md.append("|---|---:|")
    for k, v in summary.get("quality_counts", {}).items():
        md.append(f"| {k} | {v} |")

    md.append("")
    md.append("## 3. CSV Columns")
    md.append("")
    md.append("Detected columns:")
    md.append("")
    for k, v in csv_cols.items():
        md.append(f"- `{k}` → `{v}`")

    md.append("")
    md.append("## 4. Duplicate DOI / Title Examples")
    md.append("")
    if not bib_df.empty:
        dup = bib_df[bib_df["duplicate_doi"] | bib_df["duplicate_title"]]
        if dup.empty:
            md.append("No duplicate DOI/title records detected.")
        else:
            md.append("| Key | Year | DOI | Title |")
            md.append("|---|---:|---|---|")
            for _, r in dup.head(40).iterrows():
                title = clean(r["title"]).replace("|", "\\|")
                md.append(f"| {r['zotero_key']} | {r['year']} | {r['doi']} | {title[:180]} |")

    md.append("")
    md.append("## 5. Missing Metadata Examples")
    md.append("")
    if not bib_df.empty:
        miss = bib_df[
            bib_df["missing_title"]
            | bib_df["missing_authors"]
            | bib_df["missing_year"]
            | bib_df["missing_venue"]
            | bib_df["missing_doi"]
        ]
        if miss.empty:
            md.append("No important missing metadata detected.")
        else:
            md.append("| Key | Missing | Year | Title |")
            md.append("|---|---|---:|---|")
            for _, r in miss.head(80).iterrows():
                missing = []
                for c in ["missing_title", "missing_authors", "missing_year", "missing_venue", "missing_doi"]:
                    if bool(r[c]):
                        missing.append(c.replace("missing_", ""))
                title = clean(r["title"]).replace("|", "\\|")
                md.append(f"| {r['zotero_key']} | {', '.join(missing)} | {r['year']} | {title[:180]} |")

    Path(args.output_md).write_text("\n".join(md), encoding="utf-8")

    print("[INFO] Canonical CSV:", out_csv)
    print("[INFO] MD:", args.output_md)
    print("[INFO] JSON:", args.output_json)
    print("[INFO] Summary:", summary)


if __name__ == "__main__":
    main()
