#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path
from datetime import datetime
from difflib import SequenceMatcher

import pandas as pd


MANUAL_SURNAME_MAP = {
    "revathi": "revathi",
    "malathi": "revathi",
    "thaseen": "thaseen",
    "kumar": "thaseen",
    "ye": "ye",
    "myint": "myint",
    "oo": "myint",
    "vinayakumar": "vinayakumar",
    "jia": "jia",
    "polat": "polat",
    "ravi": "ravi",
    "shalinie": "ravi",
    "perez": "perez",
    "pérez": "perez",
    "diaz": "perez",
    "díaz": "perez",
    "assis": "assis",
    "novaes": "novaes",
    "abreu": "abreu",
    "maranhao": "abreu",
    "maranhão": "abreu",
    "alamri": "alamri",
    "thayananthan": "alamri",
    "elsayed": "elsayed",
    "batchu": "batchu",
    "seetha": "batchu",
    "rehman": "rehman",
    "javeed": "javeed",
    "wei": "wei",
    "ahuja": "ahuja",
    "cil": "cil",
    "rajagopal": "rajagopal",
    "alghazzawi": "alghazzawi",
    "ghosh": "ghosh",
    "akgun": "akgun",
    "akgün": "akgun",
    "maheshwari": "maheshwari",
    "almiani": "almiani",
    "aydin": "aydin",
    "aydın": "aydin",
    "nie": "nie",
    "kaur": "kaur",
    "chouhan": "chouhan",
    "bakro": "bakro",
}


def clean(s: str) -> str:
    return re.sub(r"\s+", " ", str(s or "")).strip()


def norm(s: str) -> str:
    s = clean(s).lower()
    tr = str.maketrans({
        "ı": "i", "İ": "i", "ğ": "g", "Ğ": "g", "ü": "u", "Ü": "u",
        "ş": "s", "Ş": "s", "ö": "o", "Ö": "o", "ç": "c", "Ç": "c",
        "é": "e", "á": "a", "à": "a", "ã": "a", "â": "a",
    })
    s = s.translate(tr)
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def md_safe(s: str, max_len: int | None = None) -> str:
    s = clean(s).replace("|", "\\|")
    if max_len is not None:
        s = s[:max_len]
    return s


def sim(a: str, b: str) -> float:
    return SequenceMatcher(None, norm(a), norm(b)).ratio()


def year_from_text(s: str) -> str:
    m = re.search(r"(19|20)\d{2}", str(s))
    return m.group(0) if m else ""


def first_author_from_ref(ref: str) -> str:
    n = norm(ref)
    tokens = n.split()
    if not tokens:
        return ""

    for t in tokens:
        if t in {"and", "et", "al", "vd", "ve"}:
            continue
        if re.fullmatch(r"(19|20)\d{2}", t):
            continue
        return MANUAL_SURNAME_MAP.get(t, t)
    return ""


def ref_surname_from_authors(authors: str) -> str:
    authors = clean(authors)
    if not authors:
        return ""
    first = authors.split(";")[0].split(",")[0].strip()
    return first_author_from_ref(first)


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
    parser.add_argument("--references-csv", default="docs/references_zotero_apa_like_reviewed.csv")
    parser.add_argument("--output-csv", default="docs/literature_review/manuscript_alignment/manuscript_zotero_alignment_v2.csv")
    parser.add_argument("--output-md", default="docs/literature_review/manuscript_alignment/manuscript_zotero_alignment_report_v2.md")
    args = parser.parse_args()

    refs = pd.read_csv(args.references_csv).fillna("")

    ref_rows = []
    for _, r in refs.iterrows():
        authors = clean(r.get("authors", ""))
        apa_authors = clean(r.get("apa_authors", ""))
        surname = ref_surname_from_authors(authors) or ref_surname_from_authors(apa_authors)
        year = str(r.get("year", "")).replace(".0", "")

        ref_rows.append({
            "zotero_key": clean(r.get("zotero_key", "")),
            "year": year,
            "surname": surname,
            "title": clean(r.get("title", "")),
            "authors": apa_authors or authors,
            "doi": clean(r.get("doi", "")),
            "final_decision": clean(r.get("final_decision", "")),
            "relevance": clean(r.get("relevance_to_this_thesis", "")),
        })

    rows = []

    for table_path in args.tables:
        p = Path(table_path)
        if not p.exists():
            print(f"[WARN] Missing table: {p}")
            continue

        df = pd.read_csv(p, header=None).fillna("")
        if len(df) < 2:
            continue

        for idx, row in df.iloc[1:].iterrows():
            manuscript_ref = clean(row.iloc[0])
            manuscript_row_text = " ".join(clean(x) for x in row.tolist() if clean(x))

            if not manuscript_ref:
                continue

            table_no_match = re.search(r"table_(\d+)", str(p))
            table_no = table_no_match.group(1) if table_no_match else ""

            if norm(manuscript_ref).startswith("proposed model"):
                rows.append({
                    "table_file": str(p),
                    "table_no": table_no,
                    "row_no": int(idx) + 1,
                    "manuscript_ref": manuscript_ref,
                    "manuscript_year": "",
                    "manuscript_surname": "",
                    "match_status": "proposed_model",
                    "match_score": 1.0,
                    "surname_exact": False,
                    "year_exact": False,
                    "title_score": 0.0,
                    "ref_title_score": 0.0,
                    "zotero_key": "",
                    "zotero_year": "",
                    "zotero_title": "",
                    "zotero_authors": "",
                    "doi": "",
                    "final_decision": "",
                    "relevance": "",
                    "manuscript_row_text": manuscript_row_text,
                    "review_note": "Manuscript içindeki önerilen model satırı; Zotero kaynağı ile eşleştirilmez.",
                })
                continue

            myear = year_from_text(manuscript_ref)
            msurname = first_author_from_ref(manuscript_ref)

            candidates = []
            for rr in ref_rows:
                surname_exact = bool(msurname and rr["surname"] and msurname == rr["surname"])
                year_exact = bool(myear and rr["year"] and myear == rr["year"])

                title_score = sim(manuscript_row_text, rr["title"])
                ref_title_score = sim(manuscript_ref, rr["title"])

                score = 0.0
                if surname_exact:
                    score += 0.50
                if year_exact:
                    score += 0.25
                score += 0.15 * title_score
                score += 0.10 * ref_title_score

                candidates.append((score, surname_exact, year_exact, title_score, ref_title_score, rr))

            candidates.sort(key=lambda x: x[0], reverse=True)

            if not candidates:
                continue

            score, surname_exact, year_exact, title_score, ref_title_score, rr = candidates[0]

            if surname_exact and year_exact:
                status = "strong_surname_year_match"
            elif score >= 0.62:
                status = "strong_match"
            elif score >= 0.45:
                status = "possible_match"
            else:
                status = "no_confident_match"

            if status == "strong_surname_year_match":
                review_note = "İlk yazar soyadı ve yıl eşleşti; manuscript kısa referans formatı nedeniyle güçlü kabul edildi."
            elif status == "possible_match":
                review_note = "Olası eşleşme; manuel kontrol önerilir."
            else:
                review_note = "Güvenli eşleşme yok; kaynak Zotero final listesinde olmayabilir veya farklı başlıkla kayıtlı olabilir."

            rows.append({
                "table_file": str(p),
                "table_no": table_no,
                "row_no": int(idx) + 1,
                "manuscript_ref": manuscript_ref,
                "manuscript_year": myear,
                "manuscript_surname": msurname,
                "match_status": status,
                "match_score": round(score, 4),
                "surname_exact": surname_exact,
                "year_exact": year_exact,
                "title_score": round(title_score, 4),
                "ref_title_score": round(ref_title_score, 4),
                "zotero_key": rr["zotero_key"],
                "zotero_year": rr["year"],
                "zotero_title": rr["title"],
                "zotero_authors": rr["authors"],
                "doi": rr["doi"],
                "final_decision": rr["final_decision"],
                "relevance": rr["relevance"],
                "manuscript_row_text": manuscript_row_text,
                "review_note": review_note,
            })

    out = pd.DataFrame(rows)
    Path(args.output_csv).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.output_csv, index=False)

    md = []
    md.append("# Manuscript–Zotero Alignment Report v2")
    md.append("")
    md.append(f"- Generated at UTC: `{datetime.utcnow().isoformat()}`")
    md.append(f"- References CSV: `{args.references_csv}`")
    md.append(f"- Output CSV: `{args.output_csv}`")
    md.append(f"- Compared rows: `{len(out)}`")
    md.append("")

    md.append("## 1. Match Status Counts")
    md.append("")
    md.append("| Status | Count |")
    md.append("|---|---:|")
    if len(out):
        for k, v in out["match_status"].value_counts().items():
            md.append(f"| {k} | {v} |")
    md.append("")

    md.append("## 2. Matches by Table")
    md.append("")
    md.append("| Table | Status | Count |")
    md.append("|---:|---|---:|")
    if len(out):
        for (t, s), sub in out.groupby(["table_no", "match_status"]):
            md.append(f"| {t} | {s} | {len(sub)} |")
    md.append("")

    md.append("## 3. Rows Requiring Manual Review")
    md.append("")
    if len(out):
        weak = out[out["match_status"].isin(["possible_match", "no_confident_match"])]
    else:
        weak = pd.DataFrame()

    if len(weak) == 0:
        md.append("No manual review rows detected.")
    else:
        md.append("| Table | Row | Status | Score | Manuscript ref | Best Zotero key | Best Zotero title | Note |")
        md.append("|---:|---:|---|---:|---|---|---|---|")
        for _, r in weak.iterrows():
            manuscript_ref_safe = md_safe(r["manuscript_ref"], 80)
            zotero_title_safe = md_safe(r["zotero_title"], 100)
            review_note_safe = md_safe(r["review_note"])
            md.append(
                f"| {r['table_no']} | {r['row_no']} | {r['match_status']} | {r['match_score']} | "
                f"{manuscript_ref_safe} | {r['zotero_key']} | {zotero_title_safe} | {review_note_safe} |"
            )

    md.append("")
    md.append("## 4. Strong Surname-Year Matches")
    md.append("")
    if len(out):
        strong = out[out["match_status"].eq("strong_surname_year_match")]
    else:
        strong = pd.DataFrame()

    if len(strong) == 0:
        md.append("No strong surname-year matches.")
    else:
        md.append("| Table | Row | Manuscript ref | Zotero key | Zotero title |")
        md.append("|---:|---:|---|---|---|")
        for _, r in strong.iterrows():
            manuscript_ref_safe = md_safe(r["manuscript_ref"], 80)
            zotero_title_safe = md_safe(r["zotero_title"], 120)
            md.append(
                f"| {r['table_no']} | {r['row_no']} | {manuscript_ref_safe} | "
                f"{r['zotero_key']} | {zotero_title_safe} |"
            )

    md.append("")
    md.append("## 5. Proposed Model Rows")
    md.append("")
    if len(out):
        proposed = out[out["match_status"].eq("proposed_model")]
    else:
        proposed = pd.DataFrame()

    if len(proposed) == 0:
        md.append("No proposed model rows detected.")
    else:
        md.append("| Table | Row | Manuscript ref | Note |")
        md.append("|---:|---:|---|---|")
        for _, r in proposed.iterrows():
            md.append(
                f"| {r['table_no']} | {r['row_no']} | {md_safe(r['manuscript_ref'], 80)} | {md_safe(r['review_note'])} |"
            )

    Path(args.output_md).write_text("\n".join(md), encoding="utf-8")

    print("[INFO] Compared rows:", len(out))
    if len(out):
        print("[INFO] Match counts:", out["match_status"].value_counts().to_dict())
    print("[INFO] CSV:", args.output_csv)
    print("[INFO] MD:", args.output_md)


if __name__ == "__main__":
    main()
