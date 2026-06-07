#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from datetime import datetime
from pathlib import Path

import pandas as pd


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


def next_bib_id(existing_ids: list[str], start: int = 900) -> str:
    nums = []
    for rid in existing_ids:
        m = re.match(r"^BIB(\d+)$", str(rid))
        if m:
            nums.append(int(m.group(1)))
    n = max(nums + [start - 1]) + 1
    return f"BIB{n:03d}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--tracking-csv",
        default="docs/literature_review/literature_tracking_table.csv",
    )
    parser.add_argument(
        "--decisions-csv",
        default="docs/reference_cleanup_decisions_applied.csv",
    )
    parser.add_argument(
        "--output-tracking-csv",
        default="docs/literature_review/literature_tracking_table.promoted.csv",
    )
    parser.add_argument(
        "--mapping-csv",
        default="docs/manual_to_canonical_promotion_map.csv",
    )
    parser.add_argument(
        "--report-md",
        default="docs/manual_to_canonical_promotion_report.md",
    )
    args = parser.parse_args()

    tracking_path = Path(args.tracking_csv)
    decisions_path = Path(args.decisions_csv)

    if not tracking_path.exists():
        raise SystemExit(f"[ERROR] Tracking CSV not found: {tracking_path}")
    if not decisions_path.exists():
        raise SystemExit(f"[ERROR] Decisions CSV not found: {decisions_path}")

    tracking = pd.read_csv(tracking_path).fillna("")
    decisions = pd.read_csv(decisions_path).fillna("")

    for col in [
        "thesis_use_status",
        "cleanup_decision",
        "cleanup_notes",
        "promoted_from_manual_id",
        "promoted_to_canonical_id",
        "canonical_promotion_status",
    ]:
        ensure_col(tracking, col)

    promote_ids = [
        clean(x)
        for x in decisions.loc[decisions["decision"].eq("promote_to_canonical"), "id"].tolist()
        if clean(x)
    ]

    if not promote_ids:
        print("[INFO] No promote_to_canonical records found.")
        tracking.to_csv(args.output_tracking_csv, index=False)
        pd.DataFrame().to_csv(args.mapping_csv, index=False)
        Path(args.report_md).write_text("# Manual to Canonical Promotion Report\n\nNo records promoted.\n", encoding="utf-8")
        return

    existing_ids = set(clean(x) for x in tracking["id"].astype(str))
    tracking_by_id = {clean(row.get("id")): idx for idx, row in tracking.iterrows()}

    new_rows = []
    mapping_rows = []

    for man_id in promote_ids:
        if man_id not in tracking_by_id:
            mapping_rows.append({
                "manual_id": man_id,
                "canonical_id": "",
                "status": "manual_id_missing_in_tracking",
                "title": "",
            })
            continue

        idx = tracking_by_id[man_id]
        source = tracking.loc[idx].copy()

        # Avoid duplicate promotion if already promoted before.
        already = tracking[
            tracking.get("promoted_from_manual_id", pd.Series([""] * len(tracking))).astype(str).eq(man_id)
        ]
        if not already.empty:
            canonical_id = clean(already.iloc[0].get("id"))
            mapping_rows.append({
                "manual_id": man_id,
                "canonical_id": canonical_id,
                "status": "already_promoted",
                "title": clean(source.get("title")),
            })
            continue

        canonical_id = next_bib_id(list(existing_ids))
        existing_ids.add(canonical_id)

        new_row = source.copy()
        new_row["id"] = canonical_id
        new_row["relevance_to_this_thesis"] = clean(source.get("relevance_to_this_thesis")) or "Medium"
        if new_row["relevance_to_this_thesis"] in {"Duplicate", "Discarded", "Excluded", "Low", ""}:
            new_row["relevance_to_this_thesis"] = "Medium"

        new_row["thesis_use_status"] = "canonical_from_manual"
        new_row["cleanup_decision"] = "promoted_from_manual"
        new_row["cleanup_notes"] = f"Promoted from {man_id} on {datetime.utcnow().isoformat()}"
        new_row["promoted_from_manual_id"] = man_id
        new_row["canonical_promotion_status"] = "active_canonical"

        # Original MAN record becomes duplicate/promoted source.
        tracking.at[idx, "thesis_use_status"] = "manual_promoted_to_canonical"
        tracking.at[idx, "promoted_to_canonical_id"] = canonical_id
        tracking.at[idx, "canonical_promotion_status"] = "promoted"
        tracking.at[idx, "relevance_to_this_thesis"] = "Duplicate"

        new_rows.append(new_row)

        mapping_rows.append({
            "manual_id": man_id,
            "canonical_id": canonical_id,
            "status": "promoted",
            "year": clean(source.get("year")).replace(".0", ""),
            "authors": clean(source.get("authors")),
            "title": clean(source.get("title")),
            "venue": clean(source.get("venue")),
            "doi_url": clean(source.get("doi_url")),
        })

    if new_rows:
        tracking = pd.concat([tracking, pd.DataFrame(new_rows)], ignore_index=True)

    tracking.to_csv(args.output_tracking_csv, index=False)
    mapping = pd.DataFrame(mapping_rows)
    mapping.to_csv(args.mapping_csv, index=False)

    md = []
    md.append("# Manual to Canonical Promotion Report")
    md.append("")
    md.append(f"- Generated at UTC: `{datetime.utcnow().isoformat()}`")
    md.append(f"- Input tracking: `{tracking_path}`")
    md.append(f"- Decisions CSV: `{decisions_path}`")
    md.append(f"- Output tracking: `{args.output_tracking_csv}`")
    md.append(f"- Mapping CSV: `{args.mapping_csv}`")
    md.append(f"- Promote decision count: `{len(promote_ids)}`")
    md.append(f"- New canonical records: `{len(new_rows)}`")
    md.append("")
    md.append("## 1. Promotion Map")
    md.append("")
    md.append("| Manual ID | Canonical ID | Status | Title |")
    md.append("|---|---|---|---|")
    for _, r in mapping.iterrows():
        title = clean(r.get("title")).replace("|", "\\|")
        md.append(f"| {r.get('manual_id')} | {r.get('canonical_id')} | {r.get('status')} | {title[:200]} |")

    Path(args.report_md).write_text("\n".join(md), encoding="utf-8")

    print("[INFO] Output tracking:", args.output_tracking_csv)
    print("[INFO] Mapping:", args.mapping_csv)
    print("[INFO] Report:", args.report_md)
    print("[INFO] Promote decision count:", len(promote_ids))
    print("[INFO] New canonical records:", len(new_rows))


if __name__ == "__main__":
    main()
