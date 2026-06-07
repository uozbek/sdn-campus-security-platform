#!/usr/bin/env python3
"""
Compare extracted runtime flow CSV schema with active model feature_order.json.

Usage:
python ml-service/tools/compare_runtime_flow_schema.py \
  --flow-csv experiments/flow_features/flows.csv \
  --feature-order ml-service/models/active/feature_order.json
"""

import argparse
import json
import re
from pathlib import Path

import pandas as pd


def sanitize_feature_name(name: str) -> str:
    name = str(name).strip()
    name = re.sub(r"[^\w]+", "_", name)
    name = re.sub(r"_+", "_", name)
    name = name.strip("_")
    return name


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--flow-csv", required=True)
    parser.add_argument(
        "--feature-order",
        default="ml-service/models/active/feature_order.json",
    )
    args = parser.parse_args()

    flow_csv = Path(args.flow_csv)
    feature_order_path = Path(args.feature_order)

    df = pd.read_csv(flow_csv)

    with feature_order_path.open("r", encoding="utf-8") as f:
        expected = json.load(f)

    original_cols = list(df.columns)
    sanitized_cols = [sanitize_feature_name(c) for c in original_cols]

    expected_set = set(expected)
    sanitized_set = set(sanitized_cols)

    missing = sorted(expected_set - sanitized_set)
    extra = sorted(sanitized_set - expected_set)
    matched = sorted(expected_set & sanitized_set)

    print("[INFO] Flow CSV:", flow_csv)
    print("[INFO] Shape:", df.shape)
    print("[INFO] Expected feature count:", len(expected))
    print("[INFO] Sanitized CSV feature count:", len(sanitized_cols))
    print("[INFO] Matched:", len(matched))
    print("[INFO] Missing:", len(missing))
    print("[INFO] Extra:", len(extra))

    print("\n[MATCHED]")
    for x in matched:
        print("  ", x)

    print("\n[MISSING EXPECTED FEATURES]")
    for x in missing:
        print("  ", x)

    print("\n[EXTRA CSV FEATURES SAMPLE]")
    for x in extra[:80]:
        print("  ", x)

    # Save report
    out = flow_csv.with_suffix(".schema_report.json")
    report = {
        "flow_csv": str(flow_csv),
        "shape": list(df.shape),
        "expected_feature_count": len(expected),
        "sanitized_csv_feature_count": len(sanitized_cols),
        "matched": matched,
        "missing": missing,
        "extra_sample": extra[:200],
        "original_columns": original_cols,
        "sanitized_columns": sanitized_cols,
    }

    with out.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print("\n[INFO] Report written:", out)


if __name__ == "__main__":
    main()
