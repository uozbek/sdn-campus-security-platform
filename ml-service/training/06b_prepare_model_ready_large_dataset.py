#!/usr/bin/env python3
"""
Prepare model-ready CIC-DDoS2019 large cross-day datasets.

This script:
- Reads train and holdout sampled CSV files in chunks.
- Drops constant features detected during profiling.
- Keeps metadata/label columns.
- Writes model-ready train and holdout CSV files.
- Writes feature_order_all_features.json for all remaining usable features.

Usage:
python ml-service/training/06b_prepare_model_ready_large_dataset.py \
  --train ml-service/datasets/processed/cicddos2019_train_01_12_sampled.csv \
  --holdout ml-service/datasets/processed/cicddos2019_holdout_03_11_sampled.csv \
  --profile ml-service/datasets/metadata/profile_large/large_dataset_profile_report.json \
  --output-dir ml-service/datasets/processed \
  --metadata-dir ml-service/datasets/metadata/model_ready_large
"""

import argparse
import json
from pathlib import Path

import pandas as pd


PROTECTED_COLS = ["raw_label", "attack_type", "label", "source_file", "split"]


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_columns(path: Path):
    return list(pd.read_csv(path, nrows=0).columns)


def rewrite_without_dropped_features(src: Path, dst: Path, keep_cols, chunksize: int):
    if dst.exists():
        dst.unlink()

    print(f"[INFO] Writing: {dst}")

    for i, chunk in enumerate(pd.read_csv(src, chunksize=chunksize, low_memory=False)):
        missing = [c for c in keep_cols if c not in chunk.columns]
        if missing:
            raise ValueError(f"Missing columns in {src}: {missing}")

        chunk = chunk[keep_cols]
        chunk.to_csv(dst, mode="a", index=False, header=(i == 0))

        if i % 10 == 0:
            print(f"[INFO] {src.name}: chunk={i}")

    print(f"[INFO] Completed: {dst}")


def count_rows(path: Path, chunksize: int):
    total = 0
    for chunk in pd.read_csv(path, usecols=["label"], chunksize=chunksize):
        total += len(chunk)
    return total


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", required=True)
    parser.add_argument("--holdout", required=True)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--output-dir", default="ml-service/datasets/processed")
    parser.add_argument("--metadata-dir", default="ml-service/datasets/metadata/model_ready_large")
    parser.add_argument("--chunksize", type=int, default=100000)
    args = parser.parse_args()

    train_path = Path(args.train)
    holdout_path = Path(args.holdout)
    profile_path = Path(args.profile)
    output_dir = Path(args.output_dir)
    metadata_dir = Path(args.metadata_dir)

    output_dir.mkdir(parents=True, exist_ok=True)
    metadata_dir.mkdir(parents=True, exist_ok=True)

    profile = load_json(profile_path)

    train_constant = set(profile.get("train_constant_features", []))
    holdout_constant = set(profile.get("holdout_constant_features", []))

    # Drop features that are constant in both train and holdout.
    constant_to_drop = sorted(train_constant & holdout_constant)

    train_cols = get_columns(train_path)
    holdout_cols = get_columns(holdout_path)

    train_features = [c for c in train_cols if c not in PROTECTED_COLS]
    holdout_features = [c for c in holdout_cols if c not in PROTECTED_COLS]

    common_features = sorted(set(train_features) & set(holdout_features))
    selected_features = [c for c in common_features if c not in constant_to_drop]

    protected_existing = [c for c in PROTECTED_COLS if c in train_cols]

    keep_cols = selected_features + protected_existing

    train_out = output_dir / "cicddos2019_train_01_12_model_ready.csv"
    holdout_out = output_dir / "cicddos2019_holdout_03_11_model_ready.csv"

    print("[INFO] Original common feature count:", len(common_features))
    print("[INFO] Constant features to drop:", len(constant_to_drop))
    for c in constant_to_drop:
        print(" -", c)
    print("[INFO] Model-ready feature count:", len(selected_features))

    rewrite_without_dropped_features(train_path, train_out, keep_cols, args.chunksize)
    rewrite_without_dropped_features(holdout_path, holdout_out, keep_cols, args.chunksize)

    train_rows = count_rows(train_out, args.chunksize)
    holdout_rows = count_rows(holdout_out, args.chunksize)

    feature_order_path = metadata_dir / "feature_order_all_features.json"
    write_json(feature_order_path, selected_features)

    report = {
        "train_input": str(train_path),
        "holdout_input": str(holdout_path),
        "train_output": str(train_out),
        "holdout_output": str(holdout_out),
        "train_rows": train_rows,
        "holdout_rows": holdout_rows,
        "original_common_feature_count": len(common_features),
        "constant_feature_count": len(constant_to_drop),
        "constant_features_dropped": constant_to_drop,
        "model_ready_feature_count": len(selected_features),
        "feature_order_file": str(feature_order_path),
        "protected_columns": protected_existing,
    }

    write_json(metadata_dir / "model_ready_large_dataset_report.json", report)

    print("[INFO] Model-ready dataset preparation completed.")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
