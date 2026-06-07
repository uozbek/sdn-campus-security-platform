#!/usr/bin/env python3
"""
Aşama 14.2-B — CIC-DDoS2019 Subset Preparation

Bu script, raw klasörü altındaki CIC-DDoS2019 CSV dosyalarını tarar,
SYN, UDP, UDP-Lag ve BENIGN içeren kayıtları seçer ve ilk ML pipeline
testi için birleşik bir CSV üretir.

Örnek kullanım:

python ml-service/training/00_prepare_cicddos_subset.py \
  --raw-dir ml-service/datasets/raw \
  --output ml-service/datasets/processed/cicddos2019_syn_udp_udplag_raw_subset.csv \
  --report ml-service/experiments/reports/subset_report.json \
  --max-rows-per-file 200000
"""

import argparse
import json
from pathlib import Path

import pandas as pd


TARGET_KEYWORDS = [
    "syn",
    "udp",
    "udplag",
    "udp-lag",
    "udp_lag"
]


def normalize_label(value):
    value_str = str(value).strip()

    if value_str.upper() in ["BENIGN", "NORMAL"]:
        return "BENIGN"

    lower = value_str.lower()

    if "syn" in lower:
        return "SYN"

    if "udp-lag" in lower or "udplag" in lower or "udp_lag" in lower:
        return "UDP-LAG"

    if "udp" in lower:
        return "UDP"

    return value_str


def find_label_column(df):
    candidates = ["Label", "label", "Class", "class", "Attack", "attack"]

    df.columns = df.columns.str.strip()

    for candidate in candidates:
        if candidate in df.columns:
            return candidate

    raise ValueError(f"Label kolonu bulunamadı. Mevcut kolonlar: {list(df.columns)}")


def should_include_file(path):
    name = path.name.lower()
    return any(keyword in name for keyword in TARGET_KEYWORDS)


def read_candidate_csv(path, max_rows_per_file=None):
    if max_rows_per_file and max_rows_per_file > 0:
        return pd.read_csv(path, low_memory=False, nrows=max_rows_per_file)

    return pd.read_csv(path, low_memory=False)


def prepare_subset(raw_dir, output_path, report_path, max_rows_per_file=None):
    raw_dir = Path(raw_dir)
    output_path = Path(output_path)
    report_path = Path(report_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    csv_files = sorted(raw_dir.rglob("*.csv"))

    if not csv_files:
        raise FileNotFoundError(f"CSV dosyası bulunamadı: {raw_dir}")

    selected_files = [p for p in csv_files if should_include_file(p)]

    if not selected_files:
        raise FileNotFoundError(
            "SYN / UDP / UDP-Lag içeren dosya adı bulunamadı. "
            "Dosya isimlerini kontrol edin veya scriptte TARGET_KEYWORDS listesini güncelleyin."
        )

    frames = []
    file_reports = []

    print("[INFO] Seçilen dosyalar:")

    for path in selected_files:
        print(f"  - {path}")

        df = read_candidate_csv(path, max_rows_per_file=max_rows_per_file)
        df.columns = df.columns.str.strip()

        label_col = find_label_column(df)

        before_rows = len(df)

        df[label_col] = df[label_col].apply(normalize_label)

        # Sadece BENIGN + SYN + UDP + UDP-LAG kayıtlarını al
        allowed_labels = {"BENIGN", "SYN", "UDP", "UDP-LAG"}
        df = df[df[label_col].isin(allowed_labels)].copy()

        after_rows = len(df)

        file_report = {
            "file": str(path),
            "rows_read": int(before_rows),
            "rows_selected": int(after_rows),
            "label_distribution": {
                str(k): int(v) for k, v in df[label_col].value_counts().to_dict().items()
            }
        }

        file_reports.append(file_report)

        if after_rows > 0:
            frames.append(df)

    if not frames:
        raise RuntimeError("Seçilen dosyalardan uygun label içeren kayıt bulunamadı.")

    combined = pd.concat(frames, ignore_index=True)

    # Kolon isimlerini normalize et
    combined.columns = combined.columns.str.strip()

    label_col = find_label_column(combined)

    # Label kolonunu standart isimle kaydet
    if label_col != "Label":
        combined.rename(columns={label_col: "Label"}, inplace=True)
        label_col = "Label"

    combined.to_csv(output_path, index=False)

    report = {
        "raw_dir": str(raw_dir),
        "output_path": str(output_path),
        "csv_files_found": len(csv_files),
        "selected_files_count": len(selected_files),
        "selected_files": [str(p) for p in selected_files],
        "max_rows_per_file": max_rows_per_file,
        "combined_shape": {
            "rows": int(combined.shape[0]),
            "columns": int(combined.shape[1])
        },
        "combined_label_distribution": {
            str(k): int(v) for k, v in combined["Label"].value_counts().to_dict().items()
        },
        "file_reports": file_reports
    }

    with report_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"[INFO] Birleşik subset kaydedildi: {output_path}")
    print(f"[INFO] Rapor kaydedildi: {report_path}")
    print(f"[INFO] Birleşik boyut: {combined.shape}")
    print("[INFO] Label dağılımı:")
    print(combined["Label"].value_counts())


def parse_args():
    parser = argparse.ArgumentParser(
        description="Prepare SYN/UDP/UDP-Lag subset from CIC-DDoS2019 CSV files."
    )

    parser.add_argument(
        "--raw-dir",
        required=True,
        help="Ham CIC-DDoS2019 CSV dosyalarının bulunduğu klasör."
    )

    parser.add_argument(
        "--output",
        required=True,
        help="Birleşik subset CSV çıktı yolu."
    )

    parser.add_argument(
        "--report",
        required=True,
        help="Subset hazırlama rapor dosyası."
    )

    parser.add_argument(
        "--max-rows-per-file",
        type=int,
        default=0,
        help="Her dosyadan okunacak maksimum satır sayısı. 0 verilirse tüm dosya okunur."
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    max_rows = args.max_rows_per_file if args.max_rows_per_file > 0 else None

    prepare_subset(
        raw_dir=args.raw_dir,
        output_path=args.output,
        report_path=args.report,
        max_rows_per_file=max_rows
    )
