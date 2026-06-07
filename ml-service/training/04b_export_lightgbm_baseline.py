#!/usr/bin/env python3

import json
import re
from pathlib import Path

import joblib
import pandas as pd

from sklearn.model_selection import train_test_split
from lightgbm import LGBMClassifier


def sanitize_feature_name(name):
    name = str(name).strip()
    name = re.sub(r"[^A-Za-z0-9_]+", "_", name)
    name = re.sub(r"_+", "_", name)
    name = name.strip("_")
    return name if name else "feature"


def sanitize_dataframe_columns(df):
    used = {}
    mapping = {}
    new_columns = []

    for col in df.columns:
        clean = sanitize_feature_name(col)

        if clean in used:
            used[clean] += 1
            clean_unique = f"{clean}_{used[clean]}"
        else:
            used[clean] = 0
            clean_unique = clean

        mapping[col] = clean_unique
        new_columns.append(clean_unique)

    df = df.copy()
    df.columns = new_columns

    return df, mapping


input_path = Path("ml-service/datasets/processed/cicddos2019_syn_udp_udplag_reduced.csv")
output_dir = Path("ml-service/models/baseline")
output_dir.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(input_path)
df.columns = df.columns.str.strip()

if "label" not in df.columns:
    raise ValueError("label kolonu bulunamadı.")

y = df["label"].astype(int)
X = df.drop(columns=["label"])

X, feature_name_mapping = sanitize_dataframe_columns(X)
feature_order = X.columns.tolist()

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.30,
    random_state=42,
    stratify=y
)

model = LGBMClassifier(
    boosting_type="gbdt",
    n_estimators=300,
    learning_rate=0.05,
    num_leaves=31,
    class_weight="balanced",
    random_state=42,
    n_jobs=-1,
)

print("[INFO] LightGBM baseline model eğitiliyor...")
model.fit(X_train, y_train)

joblib.dump(model, output_dir / "best_model.pkl")

with (output_dir / "feature_order.json").open("w", encoding="utf-8") as f:
    json.dump(feature_order, f, indent=2, ensure_ascii=False)

with (output_dir / "feature_name_mapping.json").open("w", encoding="utf-8") as f:
    json.dump(feature_name_mapping, f, indent=2, ensure_ascii=False)

with (output_dir / "label_mapping.json").open("w", encoding="utf-8") as f:
    json.dump({"BENIGN": 0, "ATTACK": 1}, f, indent=2, ensure_ascii=False)

metadata = {
    "model_name": "lightgbm",
    "task": "binary_ddos_detection",
    "dataset": str(input_path),
    "feature_count": len(feature_order),
    "test_size": 0.30,
    "random_state": 42,
    "selection_stage": "baseline_no_metaheuristic_feature_selection",
    "model_file": "best_model.pkl",
    "feature_order_file": "feature_order.json",
    "feature_name_mapping_file": "feature_name_mapping.json",
    "label_mapping_file": "label_mapping.json",
    "notes": "Exported after baseline comparison. LightGBM selected based on F1, AUC, FAR and FPR."
}

with (output_dir / "model_metadata.json").open("w", encoding="utf-8") as f:
    json.dump(metadata, f, indent=2, ensure_ascii=False)

print("[INFO] Export tamamlandı.")
print(f"[INFO] Model: {output_dir / 'best_model.pkl'}")
print(f"[INFO] Metadata: {output_dir / 'model_metadata.json'}")
