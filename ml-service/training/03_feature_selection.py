#!/usr/bin/env python3
"""
Aşama 14.4-B — Metaheuristic Feature Selection

Bu script, reduced CIC-DDoS2019 dataset üzerinde metaheuristic feature selection uygular.

Desteklenen ilk yöntemler:
- PSO
- GWO
- HHO

Fitness yaklaşımı:
- Binary feature mask üretilir.
- Seçilen feature'larla LightGBM modeli eğitilir.
- Validation F1 ve FAR birlikte değerlendirilir.
- Amaç fonksiyonu minimize edilir.

Objective:
    loss = (1 - F1) + FAR + feature_penalty

feature_penalty:
    seçilen feature oranını cezalandırır.
    Böylece çok yüksek performans + daha az feature hedeflenir.

Örnek kullanım:

python ml-service/training/03_feature_selection.py \
  --input ml-service/datasets/processed/cicddos2019_syn_udp_udplag_reduced.csv \
  --output-dir ml-service/experiments/feature_selection \
  --algorithm hho \
  --epoch 20 \
  --pop-size 10 \
  --sample-size 80000 \
  --random-state 42
"""

import argparse
import json
import time
import re
from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.metrics import f1_score, confusion_matrix, roc_auc_score
from sklearn.model_selection import train_test_split
from lightgbm import LGBMClassifier

from mealpy import FloatVar
from mealpy.swarm_based.PSO import OriginalPSO
from mealpy.swarm_based.GWO import OriginalGWO
from mealpy.swarm_based.HHO import OriginalHHO

def sanitize_feature_name(name):
    """
    LightGBM özel karakter içeren feature isimlerini kabul etmeyebilir.
    Bu nedenle feature isimlerini güvenli hale getiriyoruz.

    Örnek:
    'Flow Bytes/s'   -> 'Flow_Bytes_s'
    'Down/Up Ratio' -> 'Down_Up_Ratio'
    """

    name = str(name).strip()
    name = re.sub(r"[^A-Za-z0-9_]+", "_", name)
    name = re.sub(r"_+", "_", name)
    name = name.strip("_")

    if not name:
        name = "feature"

    return name


def sanitize_dataframe_columns(df):
    """
    DataFrame kolonlarını LightGBM uyumlu hale getirir.
    Aynı isme dönüşen kolonlar olursa sonuna sıra numarası ekler.
    """

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

def calculate_fpr_far(y_true, y_pred):
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()

    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0
    far = (fpr + fnr) / 2.0

    return {
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp),
        "fpr": float(fpr),
        "fnr": float(fnr),
        "far": float(far),
    }


def continuous_to_binary_mask(solution, threshold=0.5):
    arr = np.asarray(solution)
    mask = arr >= threshold

    # Hiç feature seçilmezse en yüksek değerlere sahip birkaç feature seçilsin.
    if mask.sum() == 0:
        top_idx = np.argsort(arr)[-3:]
        mask[top_idx] = True

    return mask


def load_dataset(input_path, sample_size, random_state):
    df = pd.read_csv(input_path, low_memory=False)
    df.columns = df.columns.str.strip()

    if "label" not in df.columns:
        raise ValueError("Dataset içinde label kolonu bulunamadı.")

    if sample_size and sample_size > 0 and len(df) > sample_size:
        df = df.sample(n=sample_size, random_state=random_state)

    y = df["label"].astype(int)
    X = df.drop(columns=["label"])

    # LightGBM uyumluluğu için feature isimlerini güvenli hale getir
    X, feature_name_mapping = sanitize_dataframe_columns(X)

    # Tüm feature'lar numeric olmalı.
    non_numeric = [
        col for col in X.columns
      if not pd.api.types.is_numeric_dtype(X[col])
    ]

    if non_numeric:
        raise ValueError(f"Sayısal olmayan feature bulundu: {non_numeric}")

    return X, y, feature_name_mapping


def build_lightgbm(random_state):
    return LGBMClassifier(
        boosting_type="gbdt",
        n_estimators=120,
        learning_rate=0.07,
        num_leaves=31,
        class_weight="balanced",
        random_state=random_state,
        n_jobs=-1,
        verbose=-1,
    )


class FeatureSelectionObjective:
    def __init__(
        self,
        X_train,
        X_val,
        y_train,
        y_val,
        feature_names,
        random_state,
        feature_penalty_weight=0.01,
    ):
        self.X_train = X_train
        self.X_val = X_val
        self.y_train = y_train
        self.y_val = y_val
        self.feature_names = feature_names
        self.random_state = random_state
        self.feature_penalty_weight = feature_penalty_weight
        self.history = []
        self.eval_count = 0

    def __call__(self, solution):
        self.eval_count += 1

        mask = continuous_to_binary_mask(solution)
        selected_features = [f for f, keep in zip(self.feature_names, mask) if keep]

        X_train_sel = self.X_train[selected_features]
        X_val_sel = self.X_val[selected_features]

        model = build_lightgbm(random_state=self.random_state)

        start = time.perf_counter()
        model.fit(X_train_sel, self.y_train)
        train_time = time.perf_counter() - start

        y_pred = model.predict(X_val_sel)

        if hasattr(model, "predict_proba"):
            y_score = model.predict_proba(X_val_sel)[:, 1]
        else:
            y_score = y_pred

        f1 = f1_score(self.y_val, y_pred, zero_division=0)

        try:
            auc = roc_auc_score(self.y_val, y_score)
        except Exception:
            auc = 0.0

        cm_stats = calculate_fpr_far(self.y_val, y_pred)

        selected_ratio = len(selected_features) / len(self.feature_names)

        loss = (
            (1.0 - f1)
            + cm_stats["far"]
            + self.feature_penalty_weight * selected_ratio
        )

        record = {
            "eval_count": self.eval_count,
            "selected_feature_count": int(len(selected_features)),
            "selected_ratio": float(selected_ratio),
            "f1_score": float(f1),
            "auc": float(auc),
            "fpr": float(cm_stats["fpr"]),
            "far": float(cm_stats["far"]),
            "loss": float(loss),
            "training_time_sec": float(train_time),
        }

        self.history.append(record)

        print(
            f"[EVAL {self.eval_count}] "
            f"features={len(selected_features)} "
            f"F1={f1:.6f} FAR={cm_stats['far']:.6f} "
            f"AUC={auc:.6f} loss={loss:.6f}",
            flush=True,
        )

        return loss


def create_optimizer(algorithm, epoch, pop_size):
    algorithm = algorithm.lower()

    if algorithm == "pso":
        return OriginalPSO(epoch=epoch, pop_size=pop_size)

    if algorithm == "gwo":
        return OriginalGWO(epoch=epoch, pop_size=pop_size)

    if algorithm == "hho":
        return OriginalHHO(epoch=epoch, pop_size=pop_size)

    raise ValueError(
        f"Desteklenmeyen algorithm: {algorithm}. "
        "Desteklenenler: pso, gwo, hho"
    )


def run_feature_selection(
    input_path,
    output_dir,
    algorithm,
    epoch,
    pop_size,
    sample_size,
    random_state,
    feature_penalty_weight,
):
    input_path = Path(input_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("[INFO] Dataset okunuyor:", input_path)
    X, y, feature_name_mapping = load_dataset(input_path, sample_size, random_state)

    print("[INFO] Dataset shape:", X.shape)
    print("[INFO] Label distribution:")
    print(y.value_counts())

    feature_names = X.columns.tolist()
    n_features = len(feature_names)

    X_train, X_val, y_train, y_val = train_test_split(
        X,
        y,
        test_size=0.30,
        random_state=random_state,
        stratify=y,
    )

    objective = FeatureSelectionObjective(
        X_train=X_train,
        X_val=X_val,
        y_train=y_train,
        y_val=y_val,
        feature_names=feature_names,
        random_state=random_state,
        feature_penalty_weight=feature_penalty_weight,
    )

    problem = {
        "bounds": FloatVar(lb=[0.0] * n_features, ub=[1.0] * n_features),
        "minmax": "min",
        "obj_func": objective,
    }

    optimizer = create_optimizer(
        algorithm=algorithm,
        epoch=epoch,
        pop_size=pop_size,
    )

    print(
        f"[INFO] Feature selection başladı: "
        f"algorithm={algorithm}, epoch={epoch}, pop_size={pop_size}, "
        f"features={n_features}, sample_size={sample_size}"
    )

    start = time.perf_counter()
    best_agent = optimizer.solve(problem)
    total_time = time.perf_counter() - start

    # mealpy 3.x için best_agent.solution / best_agent.target
    try:
        best_solution = best_agent.solution
        best_loss = best_agent.target.fitness
    except AttributeError:
        # Eski sürümler için fallback
        best_solution = optimizer.g_best.solution
        best_loss = optimizer.g_best.target.fitness

    best_mask = continuous_to_binary_mask(best_solution)
    selected_features = [
        f for f, keep in zip(feature_names, best_mask)
        if keep
    ]

    selected_features_path = output_dir / f"selected_features_{algorithm}.json"
    history_path = output_dir / f"feature_selection_history_{algorithm}.csv"
    report_path = output_dir / f"feature_selection_report_{algorithm}.json"
    reduced_output_path = output_dir / f"dataset_selected_{algorithm}.csv"
    feature_mapping_path = output_dir / f"feature_name_mapping_{algorithm}.json"

    with selected_features_path.open("w", encoding="utf-8") as f:
        json.dump(selected_features, f, indent=2, ensure_ascii=False)
    with feature_mapping_path.open("w", encoding="utf-8") as f:
        json.dump(feature_name_mapping, f, indent=2, ensure_ascii=False)

    history_df = pd.DataFrame(objective.history)
    history_df.to_csv(history_path, index=False)

    selected_df = X[selected_features].copy()
    selected_df["label"] = y.values
    selected_df.to_csv(reduced_output_path, index=False)

    report = {
        "algorithm": algorithm,
        "input_path": str(input_path),
        "sample_size": int(sample_size),
        "random_state": int(random_state),
        "feature_name_mapping": feature_name_mapping,
        "epoch": int(epoch),
        "pop_size": int(pop_size),
        "feature_penalty_weight": float(feature_penalty_weight),
        "initial_feature_count": int(n_features),
        "selected_feature_count": int(len(selected_features)),
        "selected_features": selected_features,
        "best_loss": float(best_loss),
        "total_optimization_time_sec": float(total_time),
        "history_csv": str(history_path),
        "selected_features_json": str(selected_features_path),
        "feature_name_mapping_json": str(feature_mapping_path),
        "selected_dataset_csv": str(reduced_output_path),
    }

    with report_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print("[INFO] Feature selection tamamlandı.")
    print("[INFO] Selected feature count:", len(selected_features))
    print("[INFO] Selected features:", selected_features)
    print("[INFO] Report:", report_path)
    print("[INFO] Selected dataset:", reduced_output_path)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Metaheuristic feature selection for CIC-DDoS2019 IDS pipeline."
    )

    parser.add_argument(
        "--input",
        required=True,
        help="Reduced dataset CSV yolu."
    )

    parser.add_argument(
        "--output-dir",
        required=True,
        help="Feature selection çıktı klasörü."
    )

    parser.add_argument(
        "--algorithm",
        required=True,
        choices=["pso", "gwo", "hho"],
        help="Feature selection algoritması."
    )

    parser.add_argument(
        "--epoch",
        type=int,
        default=20,
        help="Optimization epoch sayısı."
    )

    parser.add_argument(
        "--pop-size",
        type=int,
        default=10,
        help="Population size."
    )

    parser.add_argument(
        "--sample-size",
        type=int,
        default=80000,
        help="Feature selection için kullanılacak örnek sayısı. 0 verilirse tüm veri kullanılır."
    )

    parser.add_argument(
        "--random-state",
        type=int,
        default=42,
        help="Random seed."
    )

    parser.add_argument(
        "--feature-penalty-weight",
        type=float,
        default=0.01,
        help="Daha az feature seçmeyi teşvik eden ceza katsayısı."
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    run_feature_selection(
        input_path=args.input,
        output_dir=args.output_dir,
        algorithm=args.algorithm,
        epoch=args.epoch,
        pop_size=args.pop_size,
        sample_size=args.sample_size,
        random_state=args.random_state,
        feature_penalty_weight=args.feature_penalty_weight,
    )
