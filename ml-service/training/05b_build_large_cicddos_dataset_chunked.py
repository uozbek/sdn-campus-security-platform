#!/usr/bin/env python3
"""
Chunk-based CIC-DDoS2019 cross-day dataset builder.

Why:
The full CIC-DDoS2019 CSV files are large. Reading all files into memory may
cause OOM/Killed errors. This script reads CSV files in chunks and samples
rows per attack type while keeping memory usage bounded.

Strategy:
- CSV-01-12 -> train/validation source
- CSV-03-11 -> holdout source
- Portmap/PortScan excluded
- LightGBM-safe feature names
- Binary label:
    BENIGN = 0
    ATTACK = 1
- attack_type preserved
- source_file and split preserved
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
    seen = {}
    out = []
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


def find_label_column(columns: List[str], candidates: List[str]) -> Optional[str]:
    for c in candidates:
        if c in columns:
            return c

    lower_map = {str(c).strip().lower(): c for c in columns}
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


def clean_chunk_columns(df: pd.DataFrame, manifest: dict) -> pd.DataFrame:
    if manifest.get("cleaning", {}).get("strip_column_names", True):
        df.columns = [str(c).strip() for c in df.columns]
    return df


def drop_configured_columns(df: pd.DataFrame, manifest: dict) -> pd.DataFrame:
    drop_cols = manifest.get("id_columns_to_drop", [])
    existing = [c for c in drop_cols if c in df.columns]
    if existing:
        df = df.drop(columns=existing)
    return df


def sanitize_columns(df: pd.DataFrame, protected_cols: List[str]) -> Tuple[pd.DataFrame, Dict[str, str]]:
    raw_new_cols = []
    mapping = {}

    for col in df.columns:
        if col in protected_cols:
            new_col = col
        else:
            new_col = sanitize_feature_name(col)

        raw_new_cols.append(new_col)
        mapping[col] = new_col

    unique_cols = make_unique_columns(raw_new_cols)

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

    fill_value = cleaning.get("fill_numeric_nan_with", 0.0)
    df[feature_cols] = df[feature_cols].fillna(fill_value)

    return df


def allowed_attack_types_for_split(manifest: dict, split_name: str) -> set:
    if split_name == "train":
        selected = set(manifest.get("selected_train_attack_types", []))
    else:
        selected = set(manifest.get("selected_holdout_attack_types", []))

    return selected


def max_rows_for_split_and_type(manifest: dict, split_name: str, attack_type: str) -> Optional[int]:
    sampling = manifest.get("sampling", {})

    if not sampling.get("enabled", False):
        return None

    if split_name == "train":
        benign_max = sampling.get("train_benign_max_rows")
        attack_max = sampling.get("train_attack_max_rows_per_type")
    else:
        benign_max = sampling.get("holdout_benign_max_rows")
        attack_max = sampling.get("holdout_attack_max_rows_per_type")

    if attack_type == "benign":
        return None if benign_max is None else int(benign_max)

    return None if attack_max is None else int(attack_max)


def process_split_to_csv(
    split_name: str,
    raw_dir: Path,
    output_csv: Path,
    manifest: dict,
) -> Dict:
    csv_files = list_csv_files(raw_dir)
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found for split={split_name}: {raw_dir}")

    label_candidates = manifest["label_columns"]["candidates"]
    excluded = set(manifest.get("excluded_attack_types", []))
    allowed = allowed_attack_types_for_split(manifest, split_name)

    sampling = manifest.get("sampling", {})
    chunk_size = int(sampling.get("chunk_size", 100000))
    random_state = int(sampling.get("random_state", 42))

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    if output_csv.exists():
        output_csv.unlink()

    counters: Dict[str, int] = {}
    raw_rows_total = 0
    written_rows_total = 0
    source_reports = []
    feature_mapping = None
    final_columns = None

    print(f"[INFO] Processing split={split_name}")
    print(f"[INFO] Raw dir: {raw_dir}")
    print(f"[INFO] CSV files: {len(csv_files)}")

    for file_idx, path in enumerate(csv_files):
        print(f"[INFO] Reading file: {path.name}")

        file_raw_rows = 0
        file_written_rows = 0
        file_attack_counts: Dict[str, int] = {}

        try:
            reader = pd.read_csv(path, chunksize=chunk_size, low_memory=False)
        except UnicodeDecodeError:
            reader = pd.read_csv(path, chunksize=chunk_size, encoding="latin1", low_memory=False)

        for chunk_idx, chunk in enumerate(reader):
            chunk = clean_chunk_columns(chunk, manifest)

            label_col = find_label_column(list(chunk.columns), label_candidates)
            if label_col is None:
                print(f"[WARN] No label column found in {path.name}, skipping chunk.")
                continue

            file_raw_rows += len(chunk)
            raw_rows_total += len(chunk)

            chunk["raw_label"] = chunk[label_col].astype(str).str.strip()
            chunk["attack_type"] = chunk["raw_label"].apply(lambda x: normalize_attack_label(x, manifest))
            chunk["label"] = chunk["attack_type"].apply(binary_label_from_attack_type)
            chunk["source_file"] = path.name
            chunk["split"] = split_name

            if label_col in chunk.columns:
                chunk = chunk.drop(columns=[label_col])

            # Filter selected/excluded attack types.
            keep = chunk["attack_type"].eq("benign")

            if allowed:
                keep = keep | chunk["attack_type"].isin(allowed)

            if excluded:
                keep = keep & (~chunk["attack_type"].isin(excluded))

            chunk = chunk[keep].copy()
            if chunk.empty:
                continue

            # Per attack_type cap.
            selected_parts = []
            for attack_type, g in chunk.groupby("attack_type"):
                max_rows = max_rows_for_split_and_type(manifest, split_name, attack_type)
                already = counters.get(attack_type, 0)

                if max_rows is not None:
                    remaining = max_rows - already
                    if remaining <= 0:
                        continue

                    if len(g) > remaining:
                        g = g.sample(
                            n=remaining,
                            random_state=random_state + file_idx + chunk_idx,
                        )

                counters[attack_type] = already + len(g)
                file_attack_counts[attack_type] = file_attack_counts.get(attack_type, 0) + len(g)
                selected_parts.append(g)

            if not selected_parts:
                continue

            out_chunk = pd.concat(selected_parts, axis=0, ignore_index=True)

            out_chunk = drop_configured_columns(out_chunk, manifest)
            out_chunk, mapping = sanitize_columns(out_chunk, PROTECTED_COLS)
            out_chunk = clean_numeric_values(out_chunk, manifest, PROTECTED_COLS)

            if feature_mapping is None:
                feature_mapping = mapping
                final_columns = list(out_chunk.columns)
            else:
                # Align to first chunk columns.
                for col in final_columns:
                    if col not in out_chunk.columns:
                        out_chunk[col] = 0.0

                extra_cols = [c for c in out_chunk.columns if c not in final_columns]
                if extra_cols:
                    out_chunk = out_chunk.drop(columns=extra_cols)

                out_chunk = out_chunk[final_columns]

            write_header = not output_csv.exists()
            out_chunk.to_csv(output_csv, mode="a", index=False, header=write_header)

            file_written_rows += len(out_chunk)
            written_rows_total += len(out_chunk)

            print(
                f"[INFO] split={split_name} file={path.name} "
                f"chunk={chunk_idx} written_total={written_rows_total} counters={counters}"
            )

        source_reports.append({
            "split": split_name,
            "file": str(path),
            "raw_rows": int(file_raw_rows),
            "written_rows": int(file_written_rows),
            "written_attack_counts": file_attack_counts,
        })

    print(f"[INFO] Split={split_name} output written: {output_csv}")
    print(f"[INFO] Split={split_name} raw rows: {raw_rows_total}")
    print(f"[INFO] Split={split_name} written rows: {written_rows_total}")
    print(f"[INFO] Split={split_name} counters: {counters}")

    return {
        "split": split_name,
        "raw_dir": str(raw_dir),
        "output_csv": str(output_csv),
        "raw_rows_total": int(raw_rows_total),
        "written_rows_total": int(written_rows_total),
        "attack_type_counts": counters,
        "source_reports": source_reports,
        "feature_mapping": feature_mapping or {},
        "columns": final_columns or [],
    }


def read_small_distribution(csv_path: Path) -> Tuple[pd.DataFrame, pd.DataFrame]:
    usecols = ["label", "attack_type"]
    df = pd.read_csv(csv_path, usecols=usecols)

    label_dist = df["label"].value_counts(dropna=False).rename_axis("label").reset_index(name="count")
    attack_dist = df["attack_type"].value_counts(dropna=False).rename_axis("attack_type").reset_index(name="count")

    return label_dist, attack_dist


def write_distribution_files(csv_path: Path, label_path: Path, attack_path: Path) -> None:
    label_dist, attack_dist = read_small_distribution(csv_path)

    label_path.parent.mkdir(parents=True, exist_ok=True)

    label_dist.to_csv(label_path, index=False)
    attack_dist.to_csv(attack_path, index=False)

    print(f"[INFO] Distribution for {csv_path}")
    print(label_dist.to_string(index=False))
    print(attack_dist.to_string(index=False))


def align_feature_columns(train_csv: Path, holdout_csv: Path, manifest: dict) -> Dict:
    """
    Align train/holdout columns after chunked writing.
    Since we sanitize each split independently, columns should be identical for
    CIC-DDoS2019. This function checks and rewrites aligned files if needed.
    """
    print("[INFO] Checking train/holdout column alignment...")

    train_cols = list(pd.read_csv(train_csv, nrows=0).columns)
    holdout_cols = list(pd.read_csv(holdout_csv, nrows=0).columns)

    train_features = [c for c in train_cols if c not in PROTECTED_COLS]
    holdout_features = [c for c in holdout_cols if c not in PROTECTED_COLS]

    common_features = sorted(set(train_features) & set(holdout_features))
    train_only = sorted(set(train_features) - set(holdout_features))
    holdout_only = sorted(set(holdout_features) - set(train_features))

    if train_only:
        print(f"[WARN] Train-only features: {train_only}")
    if holdout_only:
        print(f"[WARN] Holdout-only features: {holdout_only}")

    aligned_cols = common_features + [c for c in PROTECTED_COLS if c in train_cols or c in holdout_cols]

    def rewrite_aligned(src: Path, dst: Path):
        if dst.exists():
            dst.unlink()

        chunk_size = int(manifest.get("sampling", {}).get("chunk_size", 100000))
        for i, chunk in enumerate(pd.read_csv(src, chunksize=chunk_size, low_memory=False)):
            for col in aligned_cols:
                if col not in chunk.columns:
                    chunk[col] = 0.0
            chunk = chunk[aligned_cols]
            chunk.to_csv(dst, mode="a", index=False, header=(i == 0))

    train_aligned = train_csv
    holdout_aligned = holdout_csv

    if train_only or holdout_only:
        train_aligned = train_csv.with_name(train_csv.stem + "_aligned.csv")
        holdout_aligned = holdout_csv.with_name(holdout_csv.stem + "_aligned.csv")
        rewrite_aligned(train_csv, train_aligned)
        rewrite_aligned(holdout_csv, holdout_aligned)

    return {
        "train_csv": str(train_aligned),
        "holdout_csv": str(holdout_aligned),
        "feature_count": len(common_features),
        "feature_columns": common_features,
        "train_only_features": train_only,
        "holdout_only_features": holdout_only,
    }


def build(manifest_path: Path) -> None:
    manifest = load_manifest(manifest_path)
    outputs = manifest["outputs"]

    train_dir = Path(manifest["paths"]["train_raw_csv_dir"])
    holdout_dir = Path(manifest["paths"]["holdout_raw_csv_dir"])

    train_csv = Path(outputs["train_sampled_csv"])
    holdout_csv = Path(outputs["holdout_sampled_csv"])

    train_report = process_split_to_csv("train", train_dir, train_csv, manifest)
    holdout_report = process_split_to_csv("holdout", holdout_dir, holdout_csv, manifest)

    alignment_report = align_feature_columns(train_csv, holdout_csv, manifest)

    # For chunked build, sampled/full are same outputs for now.
    Path(outputs["train_csv"]).parent.mkdir(parents=True, exist_ok=True)
    Path(outputs["holdout_csv"]).parent.mkdir(parents=True, exist_ok=True)

    # Avoid duplicate huge copies: write pointer reports instead of copying full files.
    write_distribution_files(
        Path(alignment_report["train_csv"]),
        Path(outputs["train_label_distribution_csv"]),
        Path(outputs["train_attack_distribution_csv"]),
    )
    write_distribution_files(
        Path(alignment_report["holdout_csv"]),
        Path(outputs["holdout_label_distribution_csv"]),
        Path(outputs["holdout_attack_distribution_csv"]),
    )

    write_json(
        Path(outputs["feature_columns_json"]),
        {
            "feature_count": alignment_report["feature_count"],
            "feature_columns": alignment_report["feature_columns"],
            "protected_columns": PROTECTED_COLS,
            "alignment_report": alignment_report,
        },
    )

    write_json(Path(outputs["manifest_resolved_json"]), manifest)

    build_report = {
        "dataset_name": manifest.get("dataset_name"),
        "dataset_family": manifest.get("dataset_family"),
        "split_strategy": manifest.get("split_strategy"),
        "excluded_attack_types": manifest.get("excluded_attack_types", []),
        "train_report": train_report,
        "holdout_report": holdout_report,
        "alignment_report": alignment_report,
        "outputs": outputs,
    }

    write_json(Path(outputs["build_report_json"]), build_report)

    print("[INFO] Chunked cross-day build completed.")
    print(f"[INFO] Train CSV  : {alignment_report['train_csv']}")
    print(f"[INFO] Holdout CSV: {alignment_report['holdout_csv']}")
    print(f"[INFO] Feature count: {alignment_report['feature_count']}")
    print(f"[INFO] Build report: {outputs['build_report_json']}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--manifest",
        default="ml-service/config/cicddos2019_large_dataset_manifest.yaml",
    )
    args = parser.parse_args()

    build(Path(args.manifest))


if __name__ == "__main__":
    main()
