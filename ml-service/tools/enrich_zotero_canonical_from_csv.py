#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path

import pandas as pd


def clean(value) -> str:
    if value is None:
        return ""
    s = str(value)
    if s.lower() == "nan":
        return ""
    return s.strip()


def clean_bib_braces(value: str) -> str:
    s = clean(value)
    s = s.replace("{", "").replace("}", "")
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def norm_title(value: str) -> str:
    s = clean_bib_braces(value).lower()
    s = re.sub(r"[^a-z0-9ğüşöçıİĞÜŞÖÇ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def norm_doi(value: str) -> str:
    s = clean(value).lower()
    s = s.replace("https://doi.org/", "").replace("http://dx.doi.org/", "")
    return s.strip().rstrip(".")


def sim(a: str, b: str) -> float:
    a = norm_title(a)
    b = norm_title(b)
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def pick_col(df: pd.DataFrame, *names: str) -> str | None:
    lower = {c.lower().strip(): c for c in df.columns}
    for n in names:
        if n.lower() in lower:
            return lower[n.lower()]
    for c in df.columns:
        lc = c.lower()
        if any(n.lower() in lc for n in names):
            return c
    return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--canonical-csv", default="docs/literature_review/zotero_clean/zotero_canonical_references.csv")
    parser.add_argument("--zotero-csv", default="docs/zotero_exports/sdn_ddos_thesis_clean.csv")
    parser.add_argument("--output-csv", default="docs/literature_review/zotero_clean/zotero_canonical_references.enriched.csv")
    parser.add_argument("--report-md", default="docs/literature_review/zotero_clean/zotero_csv_enrichment_report.md")
    args = parser.parse_args()

    canonical = pd.read_csv(args.canonical_csv).fillna("")
    zcsv = pd.read_csv(args.zotero_csv).fillna("")

    title_col = pick_col(zcsv, "Title")
    author_col = pick_col(zcsv, "Author")
    date_col = pick_col(zcsv, "Date", "Year")
    venue_col = pick_col(zcsv, "Publication Title", "Proceedings Title", "Book Title", "Publisher")
    doi_col = pick_col(zcsv, "DOI")
    url_col = pick_col(zcsv, "Url", "URL")
    abstract_col = pick_col(zcsv, "Abstract Note", "Abstract")
    item_type_col = pick_col(zcsv, "Item Type")

    if title_col is None:
        raise SystemExit("[ERROR] Zotero CSV Title column not found.")

    canonical["title_norm_for_match"] = canonical["title"].map(norm_title)
    canonical["doi_norm_for_match"] = canonical["doi"].map(norm_doi) if "doi" in canonical.columns else ""

    zcsv["title_norm_for_match"] = zcsv[title_col].map(norm_title)
    zcsv["doi_norm_for_match"] = zcsv[doi_col].map(norm_doi) if doi_col else ""

    # Build DOI index.
    z_by_doi = {}
    if doi_col:
        for _, r in zcsv.iterrows():
            d = clean(r.get("doi_norm_for_match"))
            if d:
                z_by_doi.setdefault(d, r)

    applied = []

    for idx, row in canonical.iterrows():
        cdoi = clean(row.get("doi_norm_for_match"))
        ctitle = clean(row.get("title"))

        match = None
        match_method = ""
        score = 0.0

        if cdoi and cdoi in z_by_doi:
            match = z_by_doi[cdoi]
            match_method = "doi"
            score = 1.0
        else:
            best = None
            best_score = 0.0
            for _, zr in zcsv.iterrows():
                s = sim(ctitle, clean(zr.get(title_col)))
                if s > best_score:
                    best = zr
                    best_score = s
            if best is not None and best_score >= 0.88:
                match = best
                match_method = "title_fuzzy"
                score = best_score

        if match is None:
            applied.append({
                "zotero_key": clean(row.get("zotero_key")),
                "status": "not_matched",
                "match_method": "",
                "score": 0,
                "old_title": clean(row.get("title")),
                "new_title": "",
            })
            continue

        # Preserve previous values once.
        for col in ["authors", "year", "title", "venue", "doi", "url", "abstract"]:
            prev_col = f"pre_csv_enrich_{col}"
            if prev_col not in canonical.columns:
                canonical[prev_col] = ""
            if not clean(canonical.at[idx, prev_col]):
                canonical.at[idx, prev_col] = clean(canonical.at[idx, col]) if col in canonical.columns else ""

        old_title = clean(canonical.at[idx, "title"])

        # Update with Zotero CSV values when present.
        if author_col and clean(match.get(author_col)):
            canonical.at[idx, "authors"] = clean(match.get(author_col))
        if date_col and clean(match.get(date_col)):
            canonical.at[idx, "year"] = clean(match.get(date_col))[:4]
        if title_col and clean(match.get(title_col)):
            canonical.at[idx, "title"] = clean(match.get(title_col))
        if venue_col and clean(match.get(venue_col)):
            canonical.at[idx, "venue"] = clean(match.get(venue_col))
        if doi_col and clean(match.get(doi_col)):
            canonical.at[idx, "doi"] = clean(match.get(doi_col))
        if url_col and clean(match.get(url_col)):
            canonical.at[idx, "url"] = clean(match.get(url_col))
        if abstract_col and clean(match.get(abstract_col)):
            canonical.at[idx, "abstract"] = clean(match.get(abstract_col))
        if item_type_col:
            canonical.at[idx, "zotero_csv_item_type"] = clean(match.get(item_type_col))

        canonical.at[idx, "csv_enrichment_status"] = "enriched"
        canonical.at[idx, "csv_enrichment_method"] = match_method
        canonical.at[idx, "csv_enrichment_score"] = score
        canonical.at[idx, "csv_enriched_at_utc"] = datetime.utcnow().isoformat()

        applied.append({
            "zotero_key": clean(row.get("zotero_key")),
            "status": "enriched",
            "match_method": match_method,
            "score": round(score, 3),
            "old_title": old_title,
            "new_title": clean(canonical.at[idx, "title"]),
        })

    # Remove temp columns.
    canonical = canonical.drop(columns=[c for c in ["title_norm_for_match", "doi_norm_for_match"] if c in canonical.columns])

    out = Path(args.output_csv)
    out.parent.mkdir(parents=True, exist_ok=True)
    canonical.to_csv(out, index=False)

    applied_df = pd.DataFrame(applied)
    counts = applied_df["status"].value_counts().to_dict()

    md = []
    md.append("# Zotero CSV Enrichment Report")
    md.append("")
    md.append(f"- Generated at UTC: `{datetime.utcnow().isoformat()}`")
    md.append(f"- Canonical input: `{args.canonical_csv}`")
    md.append(f"- Zotero CSV: `{args.zotero_csv}`")
    md.append(f"- Output CSV: `{out}`")
    md.append(f"- Status counts: `{counts}`")
    md.append("")
    md.append("## 1. Status Counts")
    md.append("")
    md.append("| Status | Count |")
    md.append("|---|---:|")
    for k, v in counts.items():
        md.append(f"| {k} | {v} |")

    md.append("")
    md.append("## 2. Not Matched")
    md.append("")
    not_matched = applied_df[applied_df["status"].eq("not_matched")]
    if not_matched.empty:
        md.append("All canonical records matched Zotero CSV.")
    else:
        md.append("| Zotero key | Old title |")
        md.append("|---|---|")
        for _, r in not_matched.iterrows():
            title = clean(r["old_title"]).replace("|", "\\|")
            md.append(f"| {r['zotero_key']} | {title[:180]} |")

    md.append("")
    md.append("## 3. Sample Enriched Records")
    md.append("")
    md.append("| Zotero key | Method | Score | New title |")
    md.append("|---|---|---:|---|")
    for _, r in applied_df[applied_df["status"].eq("enriched")].head(60).iterrows():
        title = clean(r["new_title"]).replace("|", "\\|")
        md.append(f"| {r['zotero_key']} | {r['match_method']} | {r['score']} | {title[:180]} |")

    Path(args.report_md).write_text("\n".join(md), encoding="utf-8")

    print("[INFO] Output:", out)
    print("[INFO] Report:", args.report_md)
    print("[INFO] Counts:", counts)


if __name__ == "__main__":
    main()
