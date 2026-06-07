#!/usr/bin/env python3
"""
Profile large cross-day CIC-DDoS2019 datasets.

Inputs:
- Train sampled CSV
- Holdout sampled CSV

Outputs:
- JSON profile report
- CSV feature summary
- CSV label / attack distributions

Usage:
python ml-service/training/06_profile_large_dataset.py \
  --train ml-service/datasets/processed/cicddos2019_train_01_12_sampled.csv \
  --holdout ml-service/datasets/processed/cicddos2019_holdout_03_11_sampled.csv \
  --output-dir ml-service/datasets/metadata/profile_large
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


PROTECTED_COLS = ["raw_label", "attack_type", "label", "source_file", "split"]


def read_header(path: Path):
    return list(pd.read_csv(path, nrows=0).columns)


def count_rows(path: Path, chunksize: int = 200000) -> int:
    total = 0
    for chunk in pd.read_csv(path, usecols=["label"], chunksize=chunksize):
        total += len(chunk)
    return total


def distribution(path: Path, column: str, chunksize: int = 200000):
    counts = {}
    for chunk in pd.read_csv(path, usecols=[column], chunksize=chunksize):
        vc = chunk[column].value_counts(dropna=False)
        for k, v in vc.items():
            key = str(k)
            counts[key] = counts.get(key, 0) + int(v)
    return counts


def profile_features(path: Path, feature_cols, chunksize: int = 100000):
    total_rows = 0

    nan_counts = {c: 0 for c in feature_cols}
    inf_counts = {c: 0 for c in feature_cols}
    zero_counts = {c: 0 for c in feature_cols}

    min_values = {c: None for c in feature_cols}
    max_values = {c: None for c in feature_cols}
    sum_values = {c: 0.0 for c in feature_cols}
    sumsq_values = {c: 0.0 for c in feature_cols}

    for chunk in pd.read_csv(path, usecols=feature_cols, chunksize=chunksize, low_memory=False):
        total_rows += len(chunk)

        for col in feature_cols:
            s = pd.to_numeric(chunk[col], errors="coerce")

            nan_counts[col] += int(s.isna().sum())

            finite_mask = np.isfinite(s.fillna(0.0).to_numpy())
            # Since NaN is filled only for finite check, count explicit inf from original conversion:
            arr = s.to_numpy()
            inf_counts[col] += int(np.isinf(arr[~pd.isna(arr)]).sum())

            s_clean = s.replace([np.inf, -np.inf], np.nan).fillna(0.0)

            zero_counts[col] += int((s_clean == 0).sum())

            col_min = float(s_clean.min()) if len(s_clean) else 0.0
            col_max = float(s_clean.max()) if len(s_clean) else 0.0

            if min_values[col] is None or col_min < min_values[col]:
                min_values[col] = col_min

            if max_values[col] is None or col_max > max_values[col]:
                max_values[col] = col_max

            sum_values[col] += float(s_clean.sum())
            sumsq_values[col] += float((s_clean ** 2).sum())

    rows = []

    for col in feature_cols:
        mean = sum_values[col] / total_rows if total_rows else 0.0
        variance = (sumsq_values[col] / total_rows) - (mean ** 2) if total_rows else 0.0
        variance = max(variance, 0.0)

        rows.append({
            "feature": col,
            "rows": total_rows,
            "nan_count": nan_counts[col],
            "inf_count": inf_counts[col],
            "zero_count": zero_counts[col],
            "zero_ratio": zero_counts[col] / total_rows if total_rows else 0.0,
            "min": min_values[col],
            "max": max_values[col],
            "mean": mean,
            "std": variance ** 0.5,
            "is_constant_by_minmax": min_values[col] == max_values[col],
        })

    return pd.DataFrame(rows)


def write_json(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", required=True)
    parser.add_argument("--holdout", required=True)
    parser.add_argument("--output-dir", default="ml-service/datasets/metadata/profile_large")
    parser.add_argument("--chunksize", type=int, default=100000)
    args = parser.parse_args()

    train_path = Path(args.train)
    holdout_path = Path(args.holdout)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    train_cols = read_header(train_path)
    holdout_cols = read_header(holdout_path)

    train_features = [c for c in train_cols if c not in PROTECTED_COLS]
    holdout_features = [c for c in holdout_cols if c not in PROTECTED_COLS]

    common_features = sorted(set(train_features) & set(holdout_features))
    train_only = sorted(set(train_features) - set(holdout_features))
    holdout_only = sorted(set(holdout_features) - set(train_features))

    print("[INFO] Counting rows...")
    train_rows = count_rows(train_path, chunksize=args.chunksize)
    holdout_rows = count_rows(holdout_path, chunksize=args.chunksize)

    print("[INFO] Computing distributions...")
    train_label_dist = distribution(train_path, "label", chunksize=args.chunksize)
    holdout_label_dist = distribution(holdout_path, "label", chunksize=args.chunksize)
    train_attack_dist = distribution(train_path, "attack_type", chunksize=args.chunksize)
    holdout_attack_dist = distribution(holdout_path, "attack_type", chunksize=args.chunksize)

    print("[INFO] Profiling train features...")
    train_feature_profile = profile_features(train_path, common_features, chunksize=args.chunksize)
    train_feature_profile.to_csv(output_dir / "train_feature_profile.csv", index=False)

    print("[INFO] Profiling holdout features...")
    holdout_feature_profile = profile_features(holdout_path, common_features, chunksize=args.chunksize)
    holdout_feature_profile.to_csv(output_dir / "holdout_feature_profile.csv", index=False)

    train_label_df = pd.DataFrame([
        {"label": k, "count": v} for k, v in train_label_dist.items()
    ])
    holdout_label_df = pd.DataFrame([
        {"label": k, "count": v} for k, v in holdout_label_dist.items()
    ])
    train_attack_df = pd.DataFrame([
        {"attack_type": k, "count": v} for k, v in train_attack_dist.items()
    ])
    holdout_attack_df = pd.DataFrame([
        {"attack_type": k, "count": v} for k, v in holdout_attack_dist.items()
    ])

    train_label_df.to_csv(output_dir / "train_label_distribution.csv", index=False)
    holdout_label_df.to_csv(output_dir / "holdout_label_distribution.csv", index=False)
    train_attack_df.to_csv(output_dir / "train_attack_distribution.csv", index=False)
    holdout_attack_df.to_csv(output_dir / "holdout_attack_distribution.csv", index=False)

    report = {
        "train_path": str(train_path),
        "holdout_path": str(holdout_path),
        "train_rows": train_rows,
        "holdout_rows": holdout_rows,
        "train_column_count": len(train_cols),
        "holdout_column_count": len(holdout_cols),
        "common_feature_count": len(common_features),
        "train_only_features": train_only,
        "holdout_only_features": holdout_only,
        "train_label_distribution": train_label_dist,
        "holdout_label_distribution": holdout_label_dist,
        "train_attack_distribution": train_attack_dist,
        "holdout_attack_distribution": holdout_attack_dist,
        "train_constant_features": train_feature_profile[
            train_feature_profile["is_constant_by_minmax"] == True
        ]["feature"].tolist(),
        "holdout_constant_features": holdout_feature_profile[
            holdout_feature_profile["is_constant_by_minmax"] == True
        ]["feature"].tolist(),
    }

    write_json(output_dir / "large_dataset_profile_report.json", report)

    print("[INFO] Profile completed.")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
