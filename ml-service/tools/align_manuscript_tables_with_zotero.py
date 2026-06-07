#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path
from datetime import datetime
from difflib import SequenceMatcher

import pandas as pd


def clean(s: str) -> str:
    s = str(s or "")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def norm(s: str) -> str:
    s = clean(s).lower()
    s = s.replace("ı", "i").replace("İ", "i")
    s = re.sub(r"[^a-z0-9ğüşöçıİĞÜŞÖÇ ]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def sim(a: str, b: str) -> float:
    return SequenceMatcher(None, norm(a), norm(b)).ratio()


def year_from_text(s: str) -> str:
    m = re.search(r"(19|20)\d{2}", str(s))
    return m.group(0) if m else ""


def surname_from_authors(authors: str) -> str:
    authors = clean(authors)
    if not authors:
        return ""
    first = authors.split(";")[0].split(",")[0].strip()
    return first


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--tables",
        nargs="+",
        default=[
            "docs/literature_review/manuscript_alignment/manuscript_table_05.csv",
            "docs/literature_review/manuscript_alignment/manuscript_table_06.csv",
            "docs/literature_review/manuscript_alignment/manuscript_table_01.csv",
        ],
    )
    parser.add_argument(
        "--references-csv",
        default="docs/references_zotero_apa_like_reviewed.csv",
    )
    parser.add_argument(
        "--output-csv",
        default="docs/literature_review/manuscript_alignment/manuscript_zotero_alignment.csv",
    )
    parser.add_argument(
        "--output-md",
        default="docs/literature_review/manuscript_alignment/manuscript_zotero_alignment_report.md",
    )
    args = parser.parse_args()

    refs = pd.read_csv(args.references_csv).fillna("")
    ref_rows = []

    for _, r in refs.iterrows():
        title = clean(r.get("title", ""))
        year = str(r.get("year", "")).replace(".0", "")
        authors = clean(r.get("authors", ""))
        apa_authors = clean(r.get("apa_authors", ""))
        surname = surname_from_authors(authors) or surname_from_authors(apa_authors)
        ref_rows.append({
            "zotero_key": clean(r.get("zotero_key", r.get("key", ""))),
            "year": year,
            "title": title,
            "authors": authors,
            "apa_authors": apa_authors,
            "surname": surname,
            "doi": clean(r.get("doi", "")),
            "final_decision": clean(r.get("final_decision", "")),
            "relevance": clean(r.get("relevance_to_this_thesis", "")),
        })

    all_matches = []

    for table_path in args.tables:
        p = Path(table_path)
        if not p.exists():
            print(f"[WARN] Missing table: {p}")
            continue

        df = pd.read_csv(p, header=None).fillna("")
        if len(df) < 2:
            continue

        header = [clean(x) for x in df.iloc[0].tolist()]
        rows = df.iloc[1:].copy()

        # İlk kolon genelde Ref. and Year / Reference and Year
        ref_col = 0

        for idx, row in rows.iterrows():
            manuscript_ref = clean(row.iloc[ref_col])
            if not manuscript_ref:
                continue

            manuscript_year = year_from_text(manuscript_ref)
            manuscript_text = " ".join(clean(x) for x in row.tolist() if clean(x))

            scored = []
            for rr in ref_rows:
                title_score = sim(manuscript_text, rr["title"])
                ref_score = sim(manuscript_ref, rr["title"])
                surname_score = 0.0
                if rr["surname"] and norm(rr["surname"]) in norm(manuscript_ref):
                    surname_score = 1.0

                year_score = 1.0 if manuscript_year and rr["year"] and manuscript_year == rr["year"] else 0.0

                total = (
                    0.45 * title_score +
                    0.30 * ref_score +
                    0.15 * surname_score +
                    0.10 * year_score
                )

                scored.append((total, title_score, ref_score, surname_score, year_score, rr))

            scored.sort(key=lambda x: x[0], reverse=True)
            best = scored[0] if scored else None

            if best:
                total, title_score, ref_score, surname_score, year_score, rr = best
                if total >= 0.62:
                    status = "strong_match"
                elif total >= 0.45:
                    status = "possible_match"
                else:
                    status = "no_confident_match"

                all_matches.append({
                    "table_file": str(p),
                    "table_no": re.search(r"table_(\d+)", str(p)).group(1) if re.search(r"table_(\d+)", str(p)) else "",
                    "row_no": int(idx) + 1,
                    "manuscript_ref": manuscript_ref,
                    "manuscript_year": manuscript_year,
                    "manuscript_row_text": manuscript_text,
                    "match_status": status,
                    "match_score": round(total, 4),
                    "title_score": round(title_score, 4),
                    "ref_score": round(ref_score, 4),
                    "surname_score": round(surname_score, 4),
                    "year_score": round(year_score, 4),
                    "zotero_key": rr["zotero_key"],
                    "zotero_year": rr["year"],
                    "zotero_title": rr["title"],
                    "zotero_authors": rr["apa_authors"] or rr["authors"],
                    "doi": rr["doi"],
                    "final_decision": rr["final_decision"],
                    "relevance": rr["relevance"],
                })

    out = pd.DataFrame(all_matches)
    Path(args.output_csv).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.output_csv, index=False)

    md = []
    md.append("# Manuscript–Zotero Alignment Report")
    md.append("")
    md.append(f"- Generated at UTC: `{datetime.utcnow().isoformat()}`")
    md.append(f"- References CSV: `{args.references_csv}`")
    md.append(f"- Output CSV: `{args.output_csv}`")
    md.append(f"- Compared rows: `{len(out)}`")
    md.append("")

    if len(out):
        md.append("## 1. Match Status Counts")
        md.append("")
        md.append("| Status | Count |")
        md.append("|---|---:|")
        for k, v in out["match_status"].value_counts().items():
            md.append(f"| {k} | {v} |")
        md.append("")

        md.append("## 2. Matches by Table")
        md.append("")
        md.append("| Table | Status | Count |")
        md.append("|---:|---|---:|")
        for (table_no, status), sub in out.groupby(["table_no", "match_status"]):
            md.append(f"| {table_no} | {status} | {len(sub)} |")
        md.append("")

        md.append("## 3. Possible / Weak Matches Requiring Review")
        md.append("")
        weak = out[out["match_status"].ne("strong_match")].copy()
        if len(weak) == 0:
            md.append("No weak matches detected.")
        else:
            md.append("| Table | Row | Status | Score | Manuscript ref | Best Zotero key | Best Zotero title |")
            md.append("|---:|---:|---|---:|---|---|---|")
            for _, r in weak.iterrows():
                mref = clean(r["manuscript_ref"]).replace("|", "\\|")
                ztitle = clean(r["zotero_title"]).replace("|", "\\|")
                md.append(
                    f"| {r['table_no']} | {r['row_no']} | {r['match_status']} | {r['match_score']} | "
                    f"{mref[:100]} | {r['zotero_key']} | {ztitle[:120]} |"
                )
        md.append("")

        md.append("## 4. Strong Match Examples")
        md.append("")
        strong = out[out["match_status"].eq("strong_match")].head(30)
        if len(strong) == 0:
            md.append("No strong matches detected.")
        else:
            md.append("| Table | Row | Score | Manuscript ref | Zotero key | Zotero title |")
            md.append("|---:|---:|---:|---|---|---|")
            for _, r in strong.iterrows():
                mref = clean(r["manuscript_ref"]).replace("|", "\\|")
                ztitle = clean(r["zotero_title"]).replace("|", "\\|")
                md.append(
                    f"| {r['table_no']} | {r['row_no']} | {r['match_score']} | "
                    f"{mref[:100]} | {r['zotero_key']} | {ztitle[:120]} |"
                )
    else:
        md.append("No rows compared.")

    Path(args.output_md).write_text("\n".join(md), encoding="utf-8")

    print("[INFO] Compared rows:", len(out))
    if len(out):
        print("[INFO] Match counts:", out["match_status"].value_counts().to_dict())
    print("[INFO] CSV:", args.output_csv)
    print("[INFO] MD:", args.output_md)


if __name__ == "__main__":
    main()
