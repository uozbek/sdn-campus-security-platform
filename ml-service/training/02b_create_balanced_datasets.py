#!/usr/bin/env python3
"""
Aşama 14.4-G — Balanced Dataset Creation

Bu script, reduced CIC-DDoS2019 subset içinden daha kontrollü deneyler için
balanced ve moderate-imbalance dataset üretir.

Girdi:
- cicddos2019_syn_udp_udplag_reduced.csv

Çıktılar:
- cicddos2019_syn_udp_udplag_balanced_1to1.csv
- cicddos2019_syn_udp_udplag_balanced_1to5.csv
- balanced_dataset_report.json
"""

import json
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_PATH = (
    PROJECT_ROOT
    / "ml-service"
    / "datasets"
    / "processed"
    / "cicddos2019_syn_udp_udplag_reduced.csv"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "ml-service"
    / "datasets"
    / "processed"
)

REPORT_PATH = (
    PROJECT_ROOT
    / "ml-service"
    / "experiments"
    / "reports"
    / "balanced_dataset_report.json"
)

RANDOM_STATE = 42


def create_dataset(df, benign_count, attack_multiplier, output_filename):
    benign_df = df[df["label"] == 0]
    attack_df = df[df["label"] == 1]

    attack_count = benign_count * attack_multiplier

    if len(attack_df) < attack_count:
        raise ValueError(
            f"Yeterli attack kaydı yok. İstenen={attack_count}, mevcut={len(attack_df)}"
        )

    benign_sample = benign_df.sample(
        n=benign_count,
        random_state=RANDOM_STATE,
        replace=False,
    )

    attack_sample = attack_df.sample(
        n=attack_count,
        random_state=RANDOM_STATE,
        replace=False,
    )

    out_df = pd.concat([benign_sample, attack_sample], ignore_index=True)

    out_df = out_df.sample(
        frac=1.0,
        random_state=RANDOM_STATE,
    ).reset_index(drop=True)

    output_path = OUTPUT_DIR / output_filename
    out_df.to_csv(output_path, index=False)

    distribution = {
        str(k): int(v) for k, v in out_df["label"].value_counts().to_dict().items()
    }

    return {
        "output_path": str(output_path),
        "rows": int(out_df.shape[0]),
        "columns": int(out_df.shape[1]),
        "benign_count": int((out_df["label"] == 0).sum()),
        "attack_count": int((out_df["label"] == 1).sum()),
        "class_distribution": distribution,
        "attack_multiplier": attack_multiplier,
    }


def main():
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Input dataset bulunamadı: {INPUT_PATH}")

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(INPUT_PATH, low_memory=False)
    df.columns = df.columns.str.strip()

    if "label" not in df.columns:
        raise ValueError("Dataset içinde label kolonu bulunamadı.")

    benign_df = df[df["label"] == 0]
    attack_df = df[df["label"] == 1]

    benign_count = len(benign_df)

    print("[INFO] Input dataset:", INPUT_PATH)
    print("[INFO] Input shape:", df.shape)
    print("[INFO] BENIGN count:", len(benign_df))
    print("[INFO] ATTACK count:", len(attack_df))

    if benign_count == 0:
        raise ValueError("BENIGN kayıt bulunamadı. Balanced dataset üretilemez.")

    report = {
        "input_path": str(INPUT_PATH),
        "input_shape": {
            "rows": int(df.shape[0]),
            "columns": int(df.shape[1]),
        },
        "input_distribution": {
            "BENIGN_0": int(len(benign_df)),
            "ATTACK_1": int(len(attack_df)),
        },
        "random_state": RANDOM_STATE,
        "datasets": {},
    }

    # 1:1 balanced
    report["datasets"]["balanced_1to1"] = create_dataset(
        df=df,
        benign_count=benign_count,
        attack_multiplier=1,
        output_filename="cicddos2019_syn_udp_udplag_balanced_1to1.csv",
    )

    # 1:5 moderate imbalance
    report["datasets"]["balanced_1to5"] = create_dataset(
        df=df,
        benign_count=benign_count,
        attack_multiplier=5,
        output_filename="cicddos2019_syn_udp_udplag_balanced_1to5.csv",
    )

    with REPORT_PATH.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print("[INFO] Balanced datasets created.")
    print("[INFO] Report:", REPORT_PATH)

    for name, info in report["datasets"].items():
        print(f"[INFO] {name}: {info['output_path']}")
        print(
            f"       rows={info['rows']} benign={info['benign_count']} "
            f"attack={info['attack_count']}"
        )


if __name__ == "__main__":
    main()
