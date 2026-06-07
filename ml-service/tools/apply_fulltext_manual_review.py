#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def clean(value) -> str:
    if value is None:
        return ""
    s = str(value)
    if s.lower() == "nan":
        return ""
    return s.strip()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Apply manual full-text review decisions to the full-text literature inventory."
    )
    parser.add_argument(
        "--inventory",
        default="docs/literature_review/processed/fulltext_literature_inventory.csv",
        help="Original full-text inventory CSV.",
    )
    parser.add_argument(
        "--tracking-csv",
        default="docs/literature_review/literature_tracking_table.csv",
        help="Literature tracking table CSV.",
    )
    parser.add_argument(
        "--manual-review",
        default="docs/literature_review/processed/fulltext_priority_manual_review.csv",
        help="Manual review CSV with correct_literature_id and decision columns.",
    )
    parser.add_argument(
        "--output",
        default="docs/literature_review/processed/fulltext_literature_inventory_reviewed.csv",
        help="Reviewed full-text inventory output CSV.",
    )
    args = parser.parse_args()

    inv_path = Path(args.inventory)
    tracking_path = Path(args.tracking_csv)
    review_path = Path(args.manual_review)
    output_path = Path(args.output)

    if not inv_path.exists():
        raise SystemExit(f"[ERROR] Inventory file not found: {inv_path}")
    if not tracking_path.exists():
        raise SystemExit(f"[ERROR] Tracking CSV not found: {tracking_path}")
    if not review_path.exists():
        raise SystemExit(f"[ERROR] Manual review file not found: {review_path}")

    inv = pd.read_csv(inv_path).fillna("")
    tracking = pd.read_csv(tracking_path).fillna("")
    review = pd.read_csv(review_path).fillna("")

    required_review_cols = {"relative_path", "correct_literature_id", "decision"}
    missing_cols = required_review_cols - set(review.columns)
    if missing_cols:
        raise SystemExit(f"[ERROR] Manual review CSV missing columns: {sorted(missing_cols)}")

    required_inv_cols = {"relative_path", "matched_id", "matched_title", "match_status"}
    missing_inv_cols = required_inv_cols - set(inv.columns)
    if missing_inv_cols:
        raise SystemExit(f"[ERROR] Inventory CSV missing columns: {sorted(missing_inv_cols)}")

    title_by_id = dict(zip(tracking["id"].astype(str), tracking["title"].astype(str)))
    year_by_id = dict(zip(tracking["id"].astype(str), tracking["year"].astype(str)))
    rel_by_id = dict(zip(tracking["id"].astype(str), tracking["relevance_to_this_thesis"].astype(str)))

    valid_ids = set(tracking["id"].astype(str))

    review_map = {}
    for _, row in review.iterrows():
        rel_path = clean(row.get("relative_path", ""))
        decision = clean(row.get("decision", ""))
        if rel_path and decision:
            review_map[rel_path] = row

    applied = 0
    ignored = 0
    duplicate_ignored = 0
    wrong_match = 0
    new_needed = 0
    invalid_id = 0

    for idx, row in inv.iterrows():
        rel_path = clean(row.get("relative_path", ""))
        if rel_path not in review_map:
            continue

        rr = review_map[rel_path]
        decision = clean(rr.get("decision", ""))
        correct_id = clean(rr.get("correct_literature_id", ""))

        if decision == "correct":
            if not correct_id:
                inv.at[idx, "match_status"] = "manual_error_missing_correct_id"
                invalid_id += 1
                continue

            if correct_id not in valid_ids:
                inv.at[idx, "match_status"] = "manual_error_invalid_correct_id"
                inv.at[idx, "matched_id"] = correct_id
                invalid_id += 1
                continue

            inv.at[idx, "matched_id"] = correct_id
            inv.at[idx, "matched_title"] = title_by_id.get(correct_id, "")
            inv.at[idx, "matched_year"] = year_by_id.get(correct_id, "")
            inv.at[idx, "matched_relevance"] = rel_by_id.get(correct_id, "")
            inv.at[idx, "match_status"] = "matched_manual"
            applied += 1

        elif decision == "ignore_not_relevant":
            inv.at[idx, "match_status"] = "ignored_not_relevant"
            inv.at[idx, "matched_id"] = ""
            inv.at[idx, "matched_title"] = ""
            ignored += 1

        elif decision == "duplicate_ignore":
            inv.at[idx, "match_status"] = "duplicate_ignored"
            inv.at[idx, "matched_id"] = ""
            inv.at[idx, "matched_title"] = ""
            duplicate_ignored += 1

        elif decision == "wrong_match":
            inv.at[idx, "match_status"] = "needs_manual_review"
            inv.at[idx, "matched_id"] = ""
            inv.at[idx, "matched_title"] = ""
            wrong_match += 1

        elif decision == "new_record_needed":
            inv.at[idx, "match_status"] = "new_tracking_record_needed"
            inv.at[idx, "matched_id"] = ""
            inv.at[idx, "matched_title"] = ""
            new_needed += 1

        else:
            inv.at[idx, "match_status"] = f"manual_error_unknown_decision:{decision}"
            invalid_id += 1

    output_path.parent.mkdir(parents=True, exist_ok=True)
    inv.to_csv(output_path, index=False)

    print("[INFO] Written:", output_path)
    print("[INFO] Manual decisions loaded:", len(review_map))
    print("[INFO] Applied manual matches:", applied)
    print("[INFO] Ignored not relevant:", ignored)
    print("[INFO] Duplicate ignored:", duplicate_ignored)
    print("[INFO] Wrong match reset:", wrong_match)
    print("[INFO] New records needed:", new_needed)
    print("[INFO] Manual errors:", invalid_id)

    print("\n[INFO] Match status distribution:")
    print(inv["match_status"].value_counts(dropna=False).to_string())


if __name__ == "__main__":
    main()
