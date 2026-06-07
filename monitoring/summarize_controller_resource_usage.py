#!/usr/bin/env python3

import argparse
import json
from pathlib import Path

import pandas as pd


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        default="logs/controller_resource_usage_observe_only.csv",
    )
    parser.add_argument(
        "--output",
        default="logs/controller_resource_usage_observe_only_summary.json",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        raise FileNotFoundError(f"Input not found: {input_path}")

    df = pd.read_csv(input_path)

    summary = {
        "input": str(input_path),
        "rows": int(len(df)),
        "cpu_percent": {
            "mean": float(df["cpu_percent"].mean()),
            "max": float(df["cpu_percent"].max()),
            "min": float(df["cpu_percent"].min()),
            "std": float(df["cpu_percent"].std()),
        },
        "memory_rss_mb": {
            "mean": float(df["memory_rss_mb"].mean()),
            "max": float(df["memory_rss_mb"].max()),
            "min": float(df["memory_rss_mb"].min()),
            "std": float(df["memory_rss_mb"].std()),
        },
        "memory_vms_mb": {
            "mean": float(df["memory_vms_mb"].mean()),
            "max": float(df["memory_vms_mb"].max()),
            "min": float(df["memory_vms_mb"].min()),
            "std": float(df["memory_vms_mb"].std()),
        },
        "num_threads": {
            "mean": float(df["num_threads"].mean()),
            "max": int(df["num_threads"].max()),
            "min": int(df["num_threads"].min()),
        },
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
