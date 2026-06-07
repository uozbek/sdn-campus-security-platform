#!/usr/bin/env python3
"""
Aşama 14.3 — Feature Reduction

Bu script, temizlenmiş CIC-DDoS2019 dataset'i üzerinde
metaheuristic feature selection öncesi temel feature reduction uygular.

Yapılan işlemler:
- Düşük varyanslı feature'ları kaldırma
- Yüksek korelasyonlu feature'ları kaldırma
- Mutual Information tabanlı feature ranking üretme
- Reduced dataset ve JSON rapor üretme

Örnek kullanım:

python ml-service/training/02_feature_reduction.py \
  --input ml-service/datasets/processed/cicddos2019_syn_udp_udplag_clean.csv \
  --output ml-service/datasets/processed/cicddos2019_syn_udp_udplag_reduced.csv \
  --report ml-service/experiments/reports/feature_reduction_report.json \
  --mi-output ml-service/experiments/ml_metrics/mutual_information_ranking.csv \
  --variance-threshold 0.0 \
  --correlation-threshold 0.95
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.feature_selection import VarianceThreshold, mutual_info_classif
from sklearn.preprocessing import StandardScaler


def load_dataset(input_path: Path) -> pd.DataFrame:
    if not input_path.exists():
        raise FileNotFoundError(f"Girdi dosyası bulunamadı: {input_path}")

    df = pd.read_csv(input_path, low_memory=False)
    df.columns = df.columns.str.strip()

    if "label" not in df.columns:
        raise ValueError("Dataset içinde 'label' kolonu bulunamadı.")

    return df


def remove_non_numeric_features(X: pd.DataFrame):
    non_numeric_cols = [
        col for col in X.columns
        if not pd.api.types.is_numeric_dtype(X[col])
    ]

    X_numeric = X.drop(columns=non_numeric_cols)

    return X_numeric, non_numeric_cols


def remove_low_variance_features(X: pd.DataFrame, threshold: float):
    selector = VarianceThreshold(threshold=threshold)
    selector.fit(X)

    kept_mask = selector.get_support()
    kept_features = X.columns[kept_mask].tolist()
    removed_features = X.columns[~kept_mask].tolist()

    X_reduced = X[kept_features].copy()

    return X_reduced, removed_features


def remove_high_correlation_features(X: pd.DataFrame, threshold: float):
    """
    Yüksek korelasyonlu feature çiftlerinde ikinci feature'ı kaldırır.
    Bu basit ve deterministik bir yaklaşımdır.
    """

    corr_matrix = X.corr().abs()

    upper_triangle = corr_matrix.where(
        np.triu(np.ones(corr_matrix.shape), k=1).astype(bool)
    )

    features_to_remove = [
        column for column in upper_triangle.columns
        if any(upper_triangle[column] > threshold)
    ]

    X_reduced = X.drop(columns=features_to_remove)

    return X_reduced, features_to_remove


def compute_mutual_information_ranking(X: pd.DataFrame, y: pd.Series):
    """
    Mutual Information, feature ile hedef değişken arasındaki bağımlılığı ölçer.
    Skor ne kadar yüksekse feature o kadar bilgilendiricidir.
    """

    # MI hesaplaması ölçekten çok etkilenmez; yine de sayısal kararlılık için scaler kullanılabilir.
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    mi_scores = mutual_info_classif(
        X_scaled,
        y,
        random_state=42,
        discrete_features=False
    )

    ranking = pd.DataFrame({
        "feature": X.columns,
        "mutual_information": mi_scores
    })

    ranking.sort_values(
        by="mutual_information",
        ascending=False,
        inplace=True
    )

    ranking.reset_index(drop=True, inplace=True)
    ranking["rank"] = ranking.index + 1

    return ranking[["rank", "feature", "mutual_information"]]


def feature_reduction(
    input_path: Path,
    output_path: Path,
    report_path: Path,
    mi_output_path: Path,
    variance_threshold: float,
    correlation_threshold: float,
    top_k: int = 0
):
    input_path = Path(input_path)
    output_path = Path(output_path)
    report_path = Path(report_path)
    mi_output_path = Path(mi_output_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    mi_output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"[INFO] Dataset okunuyor: {input_path}")
    df = load_dataset(input_path)

    initial_shape = df.shape

    y = df["label"].astype(int)
    X = df.drop(columns=["label"])

    initial_feature_count = X.shape[1]

    print(f"[INFO] İlk dataset boyutu: {df.shape}")
    print(f"[INFO] İlk feature sayısı: {initial_feature_count}")

    # 1. Sayısal olmayan feature kaldırma
    X_numeric, non_numeric_removed = remove_non_numeric_features(X)

    print(f"[INFO] Sayısal olmayan kaldırılan feature sayısı: {len(non_numeric_removed)}")

    # 2. Low variance feature kaldırma
    X_var, low_variance_removed = remove_low_variance_features(
        X_numeric,
        threshold=variance_threshold
    )

    print(f"[INFO] Düşük varyans kaldırılan feature sayısı: {len(low_variance_removed)}")

    # 3. High correlation feature kaldırma
    X_corr, high_corr_removed = remove_high_correlation_features(
        X_var,
        threshold=correlation_threshold
    )

    print(f"[INFO] Yüksek korelasyon kaldırılan feature sayısı: {len(high_corr_removed)}")

    # 4. Mutual Information ranking
    print("[INFO] Mutual Information ranking hesaplanıyor...")
    mi_ranking = compute_mutual_information_ranking(X_corr, y)

    mi_ranking.to_csv(mi_output_path, index=False)

    # 5. İsteğe bağlı top-k seçimi
    if top_k and top_k > 0:
        selected_features = mi_ranking.head(top_k)["feature"].tolist()
        X_final = X_corr[selected_features].copy()
        top_k_applied = True
    else:
        selected_features = X_corr.columns.tolist()
        X_final = X_corr.copy()
        top_k_applied = False

    # 6. Reduced dataset kaydet
    reduced_df = X_final.copy()
    reduced_df["label"] = y.values

    reduced_df.to_csv(output_path, index=False)

    final_shape = reduced_df.shape

    print(f"[INFO] Reduced dataset kaydedildi: {output_path}")
    print(f"[INFO] Final dataset boyutu: {final_shape}")
    print(f"[INFO] Final feature sayısı: {len(selected_features)}")
    print(f"[INFO] MI ranking kaydedildi: {mi_output_path}")

    # 7. Rapor
    report = {
        "input_path": str(input_path),
        "output_path": str(output_path),
        "mi_output_path": str(mi_output_path),
        "initial_shape": {
            "rows": int(initial_shape[0]),
            "columns": int(initial_shape[1])
        },
        "final_shape": {
            "rows": int(final_shape[0]),
            "columns": int(final_shape[1])
        },
        "initial_feature_count": int(initial_feature_count),
        "final_feature_count": int(len(selected_features)),
        "variance_threshold": float(variance_threshold),
        "correlation_threshold": float(correlation_threshold),
        "top_k_applied": top_k_applied,
        "top_k": int(top_k),
        "removed_features": {
            "non_numeric": non_numeric_removed,
            "low_variance": low_variance_removed,
            "high_correlation": high_corr_removed
        },
        "removed_feature_counts": {
            "non_numeric": len(non_numeric_removed),
            "low_variance": len(low_variance_removed),
            "high_correlation": len(high_corr_removed),
            "total_removed_before_top_k": (
                len(non_numeric_removed)
                + len(low_variance_removed)
                + len(high_corr_removed)
            )
        },
        "selected_features": selected_features,
        "top_20_mutual_information_features": mi_ranking.head(20).to_dict(orient="records"),
        "class_distribution": {
            str(k): int(v) for k, v in reduced_df["label"].value_counts().to_dict().items()
        }
    }

    with report_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"[INFO] Feature reduction raporu kaydedildi: {report_path}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Feature reduction for CIC-DDoS2019 ML pipeline."
    )

    parser.add_argument(
        "--input",
        required=True,
        help="Temizlenmiş input CSV dosyası."
    )

    parser.add_argument(
        "--output",
        required=True,
        help="Reduced dataset CSV çıktı yolu."
    )

    parser.add_argument(
        "--report",
        required=True,
        help="Feature reduction JSON rapor yolu."
    )

    parser.add_argument(
        "--mi-output",
        required=True,
        help="Mutual Information ranking CSV çıktı yolu."
    )

    parser.add_argument(
        "--variance-threshold",
        type=float,
        default=0.0,
        help="VarianceThreshold değeri. 0.0 yalnızca sabit feature'ları kaldırır."
    )

    parser.add_argument(
        "--correlation-threshold",
        type=float,
        default=0.95,
        help="Yüksek korelasyon eşiği. Örn: 0.95"
    )

    parser.add_argument(
        "--top-k",
        type=int,
        default=0,
        help="MI ranking'e göre en iyi K feature seçilsin mi? 0 verilirse uygulanmaz."
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    feature_reduction(
        input_path=Path(args.input),
        output_path=Path(args.output),
        report_path=Path(args.report),
        mi_output_path=Path(args.mi_output),
        variance_threshold=args.variance_threshold,
        correlation_threshold=args.correlation_threshold,
        top_k=args.top_k
    )
