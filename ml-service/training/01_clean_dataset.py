#!/usr/bin/env python3
"""
Yapılan işlemler:
- CSV okuma
- Kolon adı temizleme
- NaN / infinity temizleme
- Tekrarlı satırları kaldırma
- Sabit / tek-değerli feature'ları kaldırma
- Label kolonunu binary hale getirme
- Temizlenmiş dataset ve temizlik raporu üretme

Örnek kullanım:

python ml-service/training/01_clean_dataset.py \
  --input ml-service/datasets/raw/cicddos2019.csv \
  --output ml-service/datasets/processed/cicddos2019_clean.csv \
  --report ml-service/experiments/reports/cleaning_report.json
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


def normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Kolon isimlerindeki baş/son boşlukları temizler.
    CIC-DDoS2019 dosyalarında kolon isimlerinde bazen başta boşluk olabiliyor.
    Örnek: ' Label' -> 'Label'
    """
    df = df.copy()
    df.columns = df.columns.str.strip()
    return df


def find_label_column(df: pd.DataFrame) -> str:
    """
    Label kolonunu otomatik bulmaya çalışır.
    CIC-DDoS2019 dosyalarında genellikle 'Label' kullanılır.
    Bazı işlenmiş dosyalarda 'class' veya 'Class' olabilir.
    """
    possible_label_columns = ["Label", "label", "Class", "class", "Attack", "attack"]

    for col in possible_label_columns:
        if col in df.columns:
            return col

    raise ValueError(
        "Label kolonu bulunamadı. Beklenen kolonlardan biri olmalı: "
        f"{possible_label_columns}. Mevcut kolonlar: {list(df.columns)}"
    )


def binary_encode_labels(series: pd.Series) -> pd.Series:
    """
    Label kolonunu binary hale getirir.

    BENIGN / benign / Normal / normal -> 0
    Diğer tüm sınıflar -> 1

    Böylece ilk aşamada binary IDS modeli kurulur:
    0 = BENIGN
    1 = ATTACK
    """
    benign_values = {
        "BENIGN",
        "Benign",
        "benign",
        "NORMAL",
        "Normal",
        "normal",
        "0",
        0
    }

    return series.apply(lambda x: 0 if x in benign_values else 1)


def clean_dataset(input_path: Path, output_path: Path, report_path: Path) -> None:
    input_path = Path(input_path)
    output_path = Path(output_path)
    report_path = Path(report_path)

    if not input_path.exists():
        raise FileNotFoundError(f"Girdi dosyası bulunamadı: {input_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"[INFO] Dataset okunuyor: {input_path}")
    df = pd.read_csv(input_path, low_memory=False)

    initial_shape = df.shape
    initial_rows = df.shape[0]
    initial_columns = df.shape[1]

    print(f"[INFO] İlk boyut: {initial_rows} satır, {initial_columns} kolon")

    # 1. Kolon isimlerini temizle
    df = normalize_column_names(df)

    # 2. Label kolonunu bul
    label_col = find_label_column(df)
    print(f"[INFO] Label kolonu: {label_col}")

    # 3. Sonsuz değerleri NaN'e çevir
    df.replace([np.inf, -np.inf], np.nan, inplace=True)

    # 4. NaN kayıtları kaldır
    missing_before = int(df.isna().sum().sum())
    rows_before_dropna = df.shape[0]
    df.dropna(inplace=True)
    rows_after_dropna = df.shape[0]

    dropped_na_rows = rows_before_dropna - rows_after_dropna

    print(f"[INFO] Toplam eksik/sonsuz değer sayısı: {missing_before}")
    print(f"[INFO] NaN/inf nedeniyle silinen satır: {dropped_na_rows}")

    # 5. Tekrarlı satırları kaldır
    rows_before_duplicates = df.shape[0]
    df.drop_duplicates(inplace=True)
    rows_after_duplicates = df.shape[0]

    duplicate_rows_removed = rows_before_duplicates - rows_after_duplicates

    print(f"[INFO] Tekrarlı satır nedeniyle silinen satır: {duplicate_rows_removed}")

    # 6. Label kolonunu ayır
    y_raw = df[label_col].copy()
    X = df.drop(columns=[label_col]).copy()

    # 7. Sayısal olmayan feature'ları tespit et
    # CIC-DDoS2019 çoğunlukla sayısal feature içerir; yine de güvenlik için kontrol ediyoruz.
    non_numeric_columns = []
    for col in X.columns:
        if not pd.api.types.is_numeric_dtype(X[col]):
            non_numeric_columns.append(col)

    # Sayısal olmayan kolonları mümkünse numeric'e çevir
    converted_numeric_columns = []
    dropped_non_numeric_columns = []

    for col in non_numeric_columns:
        converted = pd.to_numeric(X[col], errors="coerce")

        if converted.isna().sum() == 0:
            X[col] = converted
            converted_numeric_columns.append(col)
        else:
            X.drop(columns=[col], inplace=True)
            dropped_non_numeric_columns.append(col)

    # 8. Sabit / tek-değerli feature'ları kaldır
    constant_columns = [col for col in X.columns if X[col].nunique(dropna=False) <= 1]
    X.drop(columns=constant_columns, inplace=True)

    print(f"[INFO] Sayısal olmayan kolonlar: {non_numeric_columns}")
    print(f"[INFO] Numeric'e çevrilen kolonlar: {converted_numeric_columns}")
    print(f"[INFO] Silinen sayısal olmayan kolonlar: {dropped_non_numeric_columns}")
    print(f"[INFO] Silinen sabit/tek-değerli kolon sayısı: {len(constant_columns)}")

    # 9. Label binary encode
    y = binary_encode_labels(y_raw)

    # 10. Temizlenmiş dataframe oluştur
    clean_df = X.copy()
    clean_df["label"] = y.values

    final_shape = clean_df.shape

    # 11. Sınıf dağılımı
    class_distribution = clean_df["label"].value_counts().to_dict()
    class_distribution = {str(k): int(v) for k, v in class_distribution.items()}

    # 12. Temizlenmiş dataset kaydet
    clean_df.to_csv(output_path, index=False)

    print(f"[INFO] Temizlenmiş dataset kaydedildi: {output_path}")
    print(f"[INFO] Final boyut: {final_shape[0]} satır, {final_shape[1]} kolon")
    print(f"[INFO] Sınıf dağılımı: {class_distribution}")

    # 13. Rapor üret
    report = {
        "input_path": str(input_path),
        "output_path": str(output_path),
        "initial_shape": {
            "rows": int(initial_shape[0]),
            "columns": int(initial_shape[1])
        },
        "final_shape": {
            "rows": int(final_shape[0]),
            "columns": int(final_shape[1])
        },
        "label_column_detected": label_col,
        "missing_or_infinite_values_before_cleaning": missing_before,
        "rows_removed_due_to_missing_or_infinite": int(dropped_na_rows),
        "duplicate_rows_removed": int(duplicate_rows_removed),
        "non_numeric_columns_detected": non_numeric_columns,
        "converted_numeric_columns": converted_numeric_columns,
        "dropped_non_numeric_columns": dropped_non_numeric_columns,
        "constant_columns_removed": constant_columns,
        "constant_columns_removed_count": len(constant_columns),
        "class_distribution": class_distribution,
        "target_label_mapping": {
            "BENIGN": 0,
            "ATTACK": 1
        }
    }

    with report_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"[INFO] Temizlik raporu kaydedildi: {report_path}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Clean CIC-DDoS2019 dataset for SDN IDS/IPS ML pipeline."
    )

    parser.add_argument(
        "--input",
        required=True,
        help="Ham CSV dataset yolu."
    )

    parser.add_argument(
        "--output",
        required=True,
        help="Temizlenmiş CSV çıktı yolu."
    )

    parser.add_argument(
        "--report",
        required=True,
        help="JSON temizlik raporu yolu."
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    clean_dataset(
        input_path=Path(args.input),
        output_path=Path(args.output),
        report_path=Path(args.report)
    )
