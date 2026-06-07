#!/usr/bin/env python3
"""
Build cross-day CIC-DDoS2019 datasets.

Strategy:
- CSV-01-12 is used as train/validation source.
- CSV-03-11 is used as holdout testing source.
- Portmap and PortScan are excluded from the main DDoS pipeline.
- Labels are normalized to:
    attack_type: multiclass text label
    label: binary label, BENIGN=0, ATTACK=1
- Feature names are sanitized for LightGBM safety.

Usage:
python ml-service/training/05_build_large_cicddos_dataset.py \
  --manifest ml-service/config/cicddos2019_large_dataset_manifest.yaml
"""

import argparse
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import yaml


PROTECTED_COLS = ["raw_label", "attack_type", "label", "source_file", "split"]


def sanitize_feature_name(name: str) -> str:
    name = str(name).strip()
    name = re.sub(r"[^\w]+", "_", name)
    name = re.sub(r"_+", "_", name)
    name = name.strip("_")
    return name or "feature"


def make_unique_columns(columns: List[str]) -> List[str]:
    seen: Dict[str, int] = {}
    out: List[str] = []

    for col in columns:
        if col not in seen:
            seen[col] = 0
            out.append(col)
        else:
            seen[col] += 1
            out.append(f"{col}_{seen[col]}")

    return out


def load_manifest(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def list_csv_files(raw_dir: Path) -> List[Path]:
    return sorted(raw_dir.rglob("*.csv"))


def read_csv_safely(path: Path) -> pd.DataFrame:
    print(f"[INFO] Reading CSV: {path}")
    try:
        return pd.read_csv(path, low_memory=False)
    except UnicodeDecodeError:
        return pd.read_csv(path, encoding="latin1", low_memory=False)


def clean_column_names(df: pd.DataFrame, manifest: dict) -> pd.DataFrame:
    if manifest.get("cleaning", {}).get("strip_column_names", True):
        df.columns = [str(c).strip() for c in df.columns]
    return df


def find_label_column(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    for c in candidates:
        if c in df.columns:
            return c

    lower_map = {str(c).strip().lower(): c for c in df.columns}
    for c in candidates:
        key = str(c).strip().lower()
        if key in lower_map:
            return lower_map[key]

    return None


def normalize_attack_label(raw_label: str, manifest: dict) -> str:
    label = str(raw_label).strip()

    benign_values = set(manifest["binary_labels"]["benign_values"])
    if label in benign_values or label.lower() == "benign":
        return "benign"

    mapping = manifest.get("attack_type_normalization", {})

    for normalized_name, meta in mapping.items():
        aliases = meta.get("aliases", [])
        for alias in aliases:
            if label.lower() == str(alias).lower():
                return normalized_name

    fallback = re.sub(r"[^\w]+", "_", label.lower()).strip("_")
    return fallback or "unknown_attack"


def binary_label_from_attack_type(attack_type: str) -> int:
    return 0 if attack_type == "benign" else 1


def drop_configured_columns(df: pd.DataFrame, manifest: dict) -> pd.DataFrame:
    drop_cols = manifest.get("id_columns_to_drop", [])
    existing = [c for c in drop_cols if c in df.columns]

    if existing:
        print(f"[INFO] Dropping ID/time columns: {existing}")
        df = df.drop(columns=existing)

    return df


def sanitize_columns(df: pd.DataFrame, protected_cols: List[str]) -> Tuple[pd.DataFrame, Dict[str, str]]:
    mapping: Dict[str, str] = {}
    raw_new_cols: List[str] = []

    for col in df.columns:
        if col in protected_cols:
            new_col = col
        else:
            new_col = sanitize_feature_name(col)

        mapping[col] = new_col
        raw_new_cols.append(new_col)

    unique_cols = make_unique_columns(raw_new_cols)

    # If uniqueness changed names, reflect final mapping.
    final_mapping = {}
    for old, new in zip(df.columns, unique_cols):
        final_mapping[old] = new

    df = df.copy()
    df.columns = unique_cols

    return df, final_mapping


def clean_numeric_values(df: pd.DataFrame, manifest: dict, protected_cols: List[str]) -> pd.DataFrame:
    cleaning = manifest.get("cleaning", {})
    feature_cols = [c for c in df.columns if c not in protected_cols]

    for col in feature_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    if cleaning.get("replace_inf_with_nan", True):
        df[feature_cols] = df[feature_cols].replace([np.inf, -np.inf], np.nan)

    if cleaning.get("drop_all_nan_columns", True):
        all_nan_cols = [c for c in feature_cols if df[c].isna().all()]
        if all_nan_cols:
            print(f"[INFO] Dropping all-NaN feature columns: {all_nan_cols}")
            df = df.drop(columns=all_nan_cols)
            feature_cols = [c for c in feature_cols if c not in all_nan_cols]

    fill_value = cleaning.get("fill_numeric_nan_with", 0.0)
    df[feature_cols] = df[feature_cols].fillna(fill_value)

    return df


def filter_attack_types(df: pd.DataFrame, selected_attack_types: List[str], excluded_attack_types: List[str]) -> pd.DataFrame:
    selected = set(selected_attack_types)
    excluded = set(excluded_attack_types)

    before = len(df)

    keep = df["attack_type"].eq("benign")

    if selected:
        keep = keep | df["attack_type"].isin(selected)

    if excluded:
        keep = keep & (~df["attack_type"].isin(excluded))

    out = df[keep].copy()
    removed = before - len(out)

    if removed > 0:
        print(f"[INFO] Removed rows by selected/excluded attack filters: {removed}")

    return out


def apply_sampling(df: pd.DataFrame, manifest: dict, split_name: str) -> pd.DataFrame:
    sampling = manifest.get("sampling", {})
    if not sampling.get("enabled", False):
        return df

    random_state = int(sampling.get("random_state", 42))

    if split_name == "train":
        benign_max = sampling.get("train_benign_max_rows")
        attack_max = sampling.get("train_attack_max_rows_per_type")
    else:
        benign_max = sampling.get("holdout_benign_max_rows")
        attack_max = sampling.get("holdout_attack_max_rows_per_type")

    parts = []

    benign = df[df["attack_type"] == "benign"]
    if benign_max is not None and len(benign) > int(benign_max):
        benign = benign.sample(n=int(benign_max), random_state=random_state)
    parts.append(benign)

    attacks = df[df["attack_type"] != "benign"]

    for attack_type, g in attacks.groupby("attack_type"):
        if attack_max is not None and len(g) > int(attack_max):
            g = g.sample(n=int(attack_max), random_state=random_state)
        parts.append(g)

    if not parts:
        return df

    out = pd.concat(parts, axis=0, ignore_index=True)
    out = out.sample(frac=1.0, random_state=random_state).reset_index(drop=True)
    return out


def load_split(raw_dir: Path, split_name: str, manifest: dict) -> Tuple[pd.DataFrame, List[dict]]:
    csv_files = list_csv_files(raw_dir)

    if not csv_files:
        raise FileNotFoundError(f"No CSV files found for split={split_name}: {raw_dir}")

    print(f"[INFO] Split={split_name}, CSV files={len(csv_files)}")
    for f in csv_files:
        print(f" - {f.name}")

    label_candidates = manifest["label_columns"]["candidates"]

    frames = []
    reports = []

    for path in csv_files:
        df = read_csv_safely(path)
        df = clean_column_names(df, manifest)

        label_col = find_label_column(df, label_candidates)
        if label_col is None:
            print(f"[WARN] No label column found, skipping: {path}")
            continue

        original_rows = len(df)

        df["raw_label"] = df[label_col].astype(str).str.strip()
        df["attack_type"] = df["raw_label"].apply(lambda x: normalize_attack_label(x, manifest))
        df["label"] = df["attack_type"].apply(binary_label_from_attack_type)
        df["source_file"] = path.name
        df["split"] = split_name

        if label_col in df.columns:
            df = df.drop(columns=[label_col])

        frames.append(df)

        reports.append({
            "split": split_name,
            "file": str(path),
            "rows": int(original_rows),
            "label_column": label_col,
            "raw_label_counts": df["raw_label"].value_counts(dropna=False).to_dict(),
            "attack_type_counts": df["attack_type"].value_counts(dropna=False).to_dict(),
            "binary_label_counts": df["label"].value_counts(dropna=False).to_dict(),
        })

    if not frames:
        raise RuntimeError(f"No valid CSV files loaded for split={split_name}.")

    combined = pd.concat(frames, axis=0, ignore_index=True)
    print(f"[INFO] Split={split_name}, combined shape before filtering: {combined.shape}")

    if split_name == "train":
        selected = manifest.get("selected_train_attack_types", [])
    else:
        selected = manifest.get("selected_holdout_attack_types", [])

    excluded = manifest.get("excluded_attack_types", [])

    combined = filter_attack_types(combined, selected, excluded)
    print(f"[INFO] Split={split_name}, combined shape after filtering: {combined.shape}")

    return combined, reports


def align_train_holdout_features(train_df: pd.DataFrame, holdout_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, List[str]]:
    train_feature_cols = [c for c in train_df.columns if c not in PROTECTED_COLS]
    holdout_feature_cols = [c for c in holdout_df.columns if c not in PROTECTED_COLS]

    common_features = sorted(set(train_feature_cols) & set(holdout_feature_cols))

    train_only = sorted(set(train_feature_cols) - set(holdout_feature_cols))
    holdout_only = sorted(set(holdout_feature_cols) - set(train_feature_cols))

    if train_only:
        print(f"[WARN] Train-only feature columns dropped: {train_only}")

    if holdout_only:
        print(f"[WARN] Holdout-only feature columns dropped: {holdout_only}")

    train_protected = [c for c in PROTECTED_COLS if c in train_df.columns]
    holdout_protected = [c for c in PROTECTED_COLS if c in holdout_df.columns]

    train_df = train_df[common_features + train_protected]
    holdout_df = holdout_df[common_features + holdout_protected]

    return train_df, holdout_df, common_features


def write_distributions(df: pd.DataFrame, label_path: Path, attack_path: Path) -> None:
    label_path.parent.mkdir(parents=True, exist_ok=True)

    label_dist = df["label"].value_counts(dropna=False).rename_axis("label").reset_index(name="count")
    attack_dist = df["attack_type"].value_counts(dropna=False).rename_axis("attack_type").reset_index(name="count")

    label_dist.to_csv(label_path, index=False)
    attack_dist.to_csv(attack_path, index=False)

    print(f"[INFO] Label distribution written: {label_path}")
    print(label_dist.to_string(index=False))

    print(f"[INFO] Attack distribution written: {attack_path}")
    print(attack_dist.to_string(index=False))


def build_cross_day_dataset(manifest_path: Path) -> None:
    manifest = load_manifest(manifest_path)
    outputs = manifest["outputs"]

    train_dir = Path(manifest["paths"]["train_raw_csv_dir"])
    holdout_dir = Path(manifest["paths"]["holdout_raw_csv_dir"])

    train_raw, train_reports = load_split(train_dir, "train", manifest)
    holdout_raw, holdout_reports = load_split(holdout_dir, "holdout", manifest)

    print("[INFO] Dropping configured columns...")
    train_raw = drop_configured_columns(train_raw, manifest)
    holdout_raw = drop_configured_columns(holdout_raw, manifest)

    print("[INFO] Sanitizing feature columns...")
    train_sanitized, train_mapping = sanitize_columns(train_raw, PROTECTED_COLS)
    holdout_sanitized, holdout_mapping = sanitize_columns(holdout_raw, PROTECTED_COLS)

    print("[INFO] Cleaning numeric values...")
    train_clean = clean_numeric_values(train_sanitized, manifest, PROTECTED_COLS)
    holdout_clean = clean_numeric_values(holdout_sanitized, manifest, PROTECTED_COLS)

    print("[INFO] Aligning train and holdout feature columns...")
    train_clean, holdout_clean, feature_cols = align_train_holdout_features(train_clean, holdout_clean)

    print(f"[INFO] Common feature count: {len(feature_cols)}")

    print("[INFO] Applying sampling...")
    train_sampled = apply_sampling(train_clean, manifest, "train")
    holdout_sampled = apply_sampling(holdout_clean, manifest, "holdout")

    # Write full and sampled outputs.
    for key, df in [
        ("train_csv", train_clean),
        ("train_sampled_csv", train_sampled),
        ("holdout_csv", holdout_clean),
        ("holdout_sampled_csv", holdout_sampled),
    ]:
        path = Path(outputs[key])
        path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(path, index=False)
        print(f"[INFO] Written {key}: {path} shape={df.shape}")

    write_distributions(
        train_sampled,
        Path(outputs["train_label_distribution_csv"]),
        Path(outputs["train_attack_distribution_csv"]),
    )

    write_distributions(
        holdout_sampled,
        Path(outputs["holdout_label_distribution_csv"]),
        Path(outputs["holdout_attack_distribution_csv"]),
    )

    write_json(
        Path(outputs["feature_columns_json"]),
        {
            "feature_count": len(feature_cols),
            "feature_columns": feature_cols,
            "protected_columns": PROTECTED_COLS,
            "train_feature_name_mapping": train_mapping,
            "holdout_feature_name_mapping": holdout_mapping,
        },
    )

    write_json(Path(outputs["manifest_resolved_json"]), manifest)

    build_report = {
        "dataset_name": manifest.get("dataset_name"),
        "dataset_family": manifest.get("dataset_family"),
        "split_strategy": manifest.get("split_strategy"),
        "excluded_attack_types": manifest.get("excluded_attack_types", []),
        "train_raw_shape": list(train_raw.shape),
        "holdout_raw_shape": list(holdout_raw.shape),
        "train_clean_shape": list(train_clean.shape),
        "holdout_clean_shape": list(holdout_clean.shape),
        "train_sampled_shape": list(train_sampled.shape),
        "holdout_sampled_shape": list(holdout_sampled.shape),
        "feature_count": len(feature_cols),
        "train_label_distribution": train_sampled["label"].value_counts(dropna=False).to_dict(),
        "holdout_label_distribution": holdout_sampled["label"].value_counts(dropna=False).to_dict(),
        "train_attack_distribution": train_sampled["attack_type"].value_counts(dropna=False).to_dict(),
        "holdout_attack_distribution": holdout_sampled["attack_type"].value_counts(dropna=False).to_dict(),
        "train_source_reports": train_reports,
        "holdout_source_reports": holdout_reports,
        "outputs": outputs,
    }

    write_json(Path(outputs["build_report_json"]), build_report)

    print(f"[INFO] Build report written: {outputs['build_report_json']}")
    print("[INFO] Cross-day CIC-DDoS2019 dataset build completed.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--manifest",
        default="ml-service/config/cicddos2019_large_dataset_manifest.yaml",
    )
    args = parser.parse_args()

    build_cross_day_dataset(Path(args.manifest))


if __name__ == "__main__":
    main()
