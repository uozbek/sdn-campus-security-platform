#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

import pandas as pd


VALID_DECISIONS = {
    "",
    "keep_corrected",
    "keep_as_is",
    "needs_manual_check",
    "exclude_from_thesis",
}


def clean(value) -> str:
    if value is None:
        return ""
    s = str(value)
    if s.lower() == "nan":
        return ""
    return s.strip()


def ensure_col(df: pd.DataFrame, col: str, default: str = "") -> None:
    if col not in df.columns:
        df[col] = default


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--zotero-canonical-csv",
        default="docs/literature_review/zotero_clean/zotero_canonical_references.csv",
    )
    parser.add_argument(
        "--corrections-csv",
        default="docs/literature_review/zotero_clean/zotero_missing_metadata_review.csv",
    )
    parser.add_argument(
        "--output-csv",
        default="docs/literature_review/zotero_clean/zotero_canonical_references.corrected.csv",
    )
    parser.add_argument(
        "--report-md",
        default="docs/literature_review/zotero_clean/zotero_metadata_corrections_applied.md",
    )
    args = parser.parse_args()

    canonical_path = Path(args.zotero_canonical_csv)
    corrections_path = Path(args.corrections_csv)

    if not canonical_path.exists():
        raise SystemExit(f"[ERROR] Missing canonical CSV: {canonical_path}")
    if not corrections_path.exists():
        raise SystemExit(f"[ERROR] Missing corrections CSV: {corrections_path}")

    canonical = pd.read_csv(canonical_path).fillna("")
    corrections = pd.read_csv(corrections_path).fillna("")

    if "zotero_key" not in canonical.columns:
        raise SystemExit("[ERROR] canonical CSV must include zotero_key")
    if "zotero_key" not in corrections.columns:
        raise SystemExit("[ERROR] corrections CSV must include zotero_key")

    ensure_col(canonical, "metadata_review_status")
    ensure_col(canonical, "metadata_notes")
    ensure_col(canonical, "metadata_corrected_at_utc")
    ensure_col(canonical, "previous_authors")
    ensure_col(canonical, "previous_year")
    ensure_col(canonical, "previous_title")
    ensure_col(canonical, "previous_venue")
    ensure_col(canonical, "previous_doi")
    ensure_col(canonical, "previous_url")

    valid = set(corrections.get("metadata_decision", pd.Series(dtype=str)).astype(str).map(clean))
    invalid = sorted(valid - VALID_DECISIONS)
    if invalid:
        raise SystemExit(f"[ERROR] Invalid metadata_decision values: {invalid}")

    idx_by_key = {clean(row.get("zotero_key")): idx for idx, row in canonical.iterrows()}

    applied = []
    missing_keys = []

    for _, row in corrections.iterrows():
        key = clean(row.get("zotero_key"))
        decision = clean(row.get("metadata_decision"))
        notes = clean(row.get("metadata_notes"))

        if not key:
            continue
        if key not in idx_by_key:
            missing_keys.append(key)
            continue

        idx = idx_by_key[key]

        canonical.at[idx, "metadata_review_status"] = decision or "reviewed_no_decision"
        canonical.at[idx, "metadata_notes"] = notes
        canonical.at[idx, "metadata_corrected_at_utc"] = datetime.utcnow().isoformat()

        if decision == "keep_corrected":
            # Preserve old values
            for col in ["authors", "year", "title", "venue", "doi", "url"]:
                canonical.at[idx, f"previous_{col}"] = clean(canonical.at[idx, col]) if col in canonical.columns else ""

            mapping = {
                "corrected_authors": "authors",
                "corrected_year": "year",
                "corrected_title": "title",
                "corrected_venue": "venue",
                "corrected_doi": "doi",
                "corrected_url": "url",
            }

            for src, dst in mapping.items():
                if src in corrections.columns and dst in canonical.columns:
                    val = clean(row.get(src))
                    if val:
                        canonical.at[idx, dst] = val

        elif decision == "keep_as_is":
            pass

        elif decision == "needs_manual_check":
            pass

        elif decision == "exclude_from_thesis":
            ensure_col(canonical, "thesis_use_status")
            canonical.at[idx, "thesis_use_status"] = "excluded_metadata_or_scope"

        applied.append({
            "zotero_key": key,
            "decision": decision,
            "title": clean(canonical.at[idx, "title"]),
            "doi": clean(canonical.at[idx, "doi"]),
            "venue": clean(canonical.at[idx, "venue"]),
            "notes": notes,
        })

    out = Path(args.output_csv)
    out.parent.mkdir(parents=True, exist_ok=True)
    canonical.to_csv(out, index=False)

    applied_df = pd.DataFrame(applied)
    counts = applied_df["decision"].value_counts().to_dict() if not applied_df.empty else {}

    md = []
    md.append("# Zotero Metadata Corrections Applied")
    md.append("")
    md.append(f"- Generated at UTC: `{datetime.utcnow().isoformat()}`")
    md.append(f"- Input canonical CSV: `{canonical_path}`")
    md.append(f"- Corrections CSV: `{corrections_path}`")
    md.append(f"- Output CSV: `{out}`")
    md.append(f"- Applied rows: `{len(applied_df)}`")
    md.append(f"- Missing keys: `{missing_keys}`")
    md.append("")
    md.append("## 1. Decision Counts")
    md.append("")
    md.append("| Decision | Count |")
    md.append("|---|---:|")
    for k, v in counts.items():
        md.append(f"| {k} | {v} |")

    md.append("")
    md.append("## 2. Applied Corrections")
    md.append("")
    md.append("| Zotero key | Decision | DOI | Venue | Title |")
    md.append("|---|---|---|---|---|")
    for _, r in applied_df.iterrows():
        title = clean(r["title"]).replace("|", "\\|")
        venue = clean(r["venue"]).replace("|", "\\|")
        md.append(f"| {r['zotero_key']} | {r['decision']} | {r['doi']} | {venue[:80]} | {title[:160]} |")

    Path(args.report_md).write_text("\n".join(md), encoding="utf-8")

    print("[INFO] Output CSV:", out)
    print("[INFO] Report:", args.report_md)
    print("[INFO] Applied rows:", len(applied_df))
    print("[INFO] Decision counts:", counts)
    print("[INFO] Missing keys:", missing_keys)


if __name__ == "__main__":
    main()
