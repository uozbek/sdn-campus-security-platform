#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

import pandas as pd


VALID_DECISIONS = {
    "",
    "exclude_from_thesis",
    "keep_method_background",
    "keep_domain_relevant",
    "canonical_duplicate",
    "promote_to_canonical",
    "discard_manual",
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


def load_decisions_from_xlsx(path: Path) -> pd.DataFrame:
    sheets = pd.read_excel(path, sheet_name=None)
    rows = []

    for sheet, df in sheets.items():
        df = df.fillna("")
        if "id" not in df.columns or "decision" not in df.columns:
            continue

        for _, row in df.iterrows():
            rid = clean(row.get("id"))
            decision = clean(row.get("decision"))
            if not rid or not decision:
                continue

            rows.append({
                "id": rid,
                "source_sheet": sheet,
                "decision": decision,
                "notes": clean(row.get("notes")),
                "final_action": clean(row.get("final_action")),
                "title": clean(row.get("title")),
                "relevance_to_this_thesis": clean(row.get("relevance_to_this_thesis")),
            })

    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--tracking-csv",
        default="docs/literature_review/literature_tracking_table.csv",
    )
    parser.add_argument(
        "--review-xlsx",
        default="docs/reference_cleanup_review_lists.xlsx",
    )
    parser.add_argument(
        "--output-tracking-csv",
        default="docs/literature_review/literature_tracking_table.cleaned.csv",
    )
    parser.add_argument(
        "--decision-log-csv",
        default="docs/reference_cleanup_decisions_applied.csv",
    )
    parser.add_argument(
        "--report-md",
        default="docs/reference_cleanup_decisions_applied.md",
    )
    args = parser.parse_args()

    tracking_path = Path(args.tracking_csv)
    review_path = Path(args.review_xlsx)
    output_tracking = Path(args.output_tracking_csv)

    if not tracking_path.exists():
        raise SystemExit(f"[ERROR] Tracking CSV not found: {tracking_path}")
    if not review_path.exists():
        raise SystemExit(f"[ERROR] Review XLSX not found: {review_path}")

    tracking = pd.read_csv(tracking_path).fillna("")
    decisions = load_decisions_from_xlsx(review_path)

    if decisions.empty:
        raise SystemExit("[ERROR] No non-empty decisions found in review XLSX.")

    invalid = sorted(set(decisions["decision"]) - VALID_DECISIONS)
    if invalid:
        raise SystemExit(f"[ERROR] Invalid decisions found: {invalid}")

    ensure_col(tracking, "thesis_use_status")
    ensure_col(tracking, "cleanup_decision")
    ensure_col(tracking, "cleanup_notes")
    ensure_col(tracking, "cleanup_source_sheet")
    ensure_col(tracking, "cleanup_applied_at_utc")
    ensure_col(tracking, "previous_relevance_to_this_thesis")

    tracking_index = {clean(row.get("id")): idx for idx, row in tracking.iterrows()}

    applied_rows = []
    missing_ids = []

    for _, d in decisions.iterrows():
        rid = clean(d["id"])
        decision = clean(d["decision"])
        notes = clean(d.get("notes"))
        sheet = clean(d.get("source_sheet"))

        if rid not in tracking_index:
            missing_ids.append(rid)
            continue

        idx = tracking_index[rid]
        previous_relevance = clean(tracking.at[idx, "relevance_to_this_thesis"])

        tracking.at[idx, "previous_relevance_to_this_thesis"] = previous_relevance
        tracking.at[idx, "cleanup_decision"] = decision
        tracking.at[idx, "cleanup_notes"] = notes
        tracking.at[idx, "cleanup_source_sheet"] = sheet
        tracking.at[idx, "cleanup_applied_at_utc"] = datetime.utcnow().isoformat()

        if decision == "exclude_from_thesis":
            tracking.at[idx, "relevance_to_this_thesis"] = "Excluded"
            tracking.at[idx, "thesis_use_status"] = "excluded_out_of_scope"

        elif decision == "keep_method_background":
            tracking.at[idx, "relevance_to_this_thesis"] = "MethodBackground"
            tracking.at[idx, "thesis_use_status"] = "keep_method_background"

        elif decision == "keep_domain_relevant":
            if previous_relevance in {"", "Low", "Excluded"}:
                tracking.at[idx, "relevance_to_this_thesis"] = "Medium"
            tracking.at[idx, "thesis_use_status"] = "keep_domain_relevant"

        elif decision == "canonical_duplicate":
            tracking.at[idx, "thesis_use_status"] = "duplicate_manual"
            if rid.startswith("MAN"):
                tracking.at[idx, "relevance_to_this_thesis"] = "Duplicate"

        elif decision == "promote_to_canonical":
            tracking.at[idx, "thesis_use_status"] = "promote_to_canonical_needed"
            if previous_relevance in {"", "Low", "Excluded", "Duplicate", "Discarded"}:
                tracking.at[idx, "relevance_to_this_thesis"] = "Medium"

        elif decision == "discard_manual":
            tracking.at[idx, "thesis_use_status"] = "discarded_manual"
            if rid.startswith("MAN"):
                tracking.at[idx, "relevance_to_this_thesis"] = "Discarded"

        applied_rows.append({
            "id": rid,
            "decision": decision,
            "source_sheet": sheet,
            "previous_relevance_to_this_thesis": previous_relevance,
            "new_relevance_to_this_thesis": clean(tracking.at[idx, "relevance_to_this_thesis"]),
            "thesis_use_status": clean(tracking.at[idx, "thesis_use_status"]),
            "notes": notes,
        })

    output_tracking.parent.mkdir(parents=True, exist_ok=True)
    tracking.to_csv(output_tracking, index=False)

    applied = pd.DataFrame(applied_rows)
    Path(args.decision_log_csv).parent.mkdir(parents=True, exist_ok=True)
    applied.to_csv(args.decision_log_csv, index=False)

    md = []
    md.append("# Reference Cleanup Decisions Applied")
    md.append("")
    md.append(f"- Generated at UTC: `{datetime.utcnow().isoformat()}`")
    md.append(f"- Review XLSX: `{review_path}`")
    md.append(f"- Input tracking CSV: `{tracking_path}`")
    md.append(f"- Output tracking CSV: `{output_tracking}`")
    md.append(f"- Applied decision count: `{len(applied)}`")
    md.append(f"- Missing IDs: `{missing_ids}`")
    md.append("")
    md.append("## 1. Decision Counts")
    md.append("")
    md.append("| Decision | Count |")
    md.append("|---|---:|")
    for k, v in applied["decision"].value_counts().items():
        md.append(f"| {k} | {v} |")

    md.append("")
    md.append("## 2. Thesis Use Status Counts")
    md.append("")
    md.append("| Thesis use status | Count |")
    md.append("|---|---:|")
    for k, v in applied["thesis_use_status"].value_counts().items():
        md.append(f"| {k} | {v} |")

    md.append("")
    md.append("## 3. Applied Decisions")
    md.append("")
    md.append("| ID | Decision | Previous relevance | New relevance | Thesis use status | Notes |")
    md.append("|---|---|---|---|---|---|")
    for _, r in applied.iterrows():
        notes = clean(r["notes"]).replace("|", "\\|")
        md.append(
            f"| {r['id']} | {r['decision']} | "
            f"{r['previous_relevance_to_this_thesis']} | "
            f"{r['new_relevance_to_this_thesis']} | "
            f"{r['thesis_use_status']} | {notes[:160]} |"
        )

    Path(args.report_md).write_text("\n".join(md), encoding="utf-8")

    print("[INFO] Output tracking:", output_tracking)
    print("[INFO] Decision log:", args.decision_log_csv)
    print("[INFO] Report:", args.report_md)
    print("[INFO] Applied decisions:", len(applied))
    print("[INFO] Missing IDs:", missing_ids)


if __name__ == "__main__":
    main()
