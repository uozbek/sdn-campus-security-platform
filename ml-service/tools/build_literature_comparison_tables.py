#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path

import pandas as pd


def clean(value) -> str:
    if value is None:
        return ""
    s = str(value)
    if s.lower() == "nan":
        return ""
    return s.strip()


def blob(row) -> str:
    return " ".join(clean(v).lower() for v in row.values)


def has_any(text: str, terms: list[str]) -> bool:
    low = text.lower()
    return any(t.lower() in low for t in terms)


def short_title(title: str, n: int = 85) -> str:
    title = clean(title)
    return title if len(title) <= n else title[: n - 3] + "..."


def infer_yes_no(text: str, terms: list[str]) -> str:
    return "Var" if has_any(text, terms) else "Belirsiz/Yok"


def infer_controller(row) -> str:
    v = clean(row.get("controller_or_testbed", ""))
    if v:
        return v

    text = blob(row)
    vals = []
    if "ryu" in text:
        vals.append("Ryu")
    if "mininet" in text:
        vals.append("Mininet")
    if "openflow" in text:
        vals.append("OpenFlow")
    if "open vswitch" in text or "ovs" in text:
        vals.append("OVS")

    return " / ".join(vals) if vals else "Belirsiz"


def infer_dataset(row) -> str:
    v = clean(row.get("dataset", ""))
    if v:
        return v

    text = blob(row)
    vals = []
    for label, terms in [
        ("CIC-DDoS2019", ["cic-ddos2019", "cicddos2019"]),
        ("CICIDS", ["cicids", "cic ids"]),
        ("InSDN", ["insdn"]),
        ("NSL-KDD", ["nsl-kdd", "nsl kdd"]),
        ("UNSW-NB15", ["unsw-nb15", "unsw nb15"]),
    ]:
        if has_any(text, terms):
            vals.append(label)

    return " / ".join(vals) if vals else "Belirsiz"


def infer_model(row) -> str:
    v = clean(row.get("ml_dl_model", ""))
    if v:
        return v

    text = blob(row)
    vals = []
    for label, terms in [
        ("XGBoost", ["xgboost", "extreme gradient"]),
        ("Random Forest", ["random forest"]),
        ("SVM", ["svm", "support vector"]),
        ("Decision Tree", ["decision tree"]),
        ("LSTM", ["lstm", "long short"]),
        ("GRU", ["gru"]),
        ("CNN", ["cnn", "convolution"]),
        ("DNN", ["dnn", "deep neural"]),
        ("Deep Learning", ["deep learning"]),
        ("Machine Learning", ["machine learning"]),
        ("Ensemble", ["ensemble", "voting"]),
    ]:
        if has_any(text, terms):
            vals.append(label)

    return " / ".join(dict.fromkeys(vals)) if vals else "Belirsiz"


def infer_feature_selection(row) -> str:
    v = clean(row.get("feature_selection", ""))
    if v and "verify" not in v.lower():
        return v

    text = blob(row)
    vals = []
    for label, terms in [
        ("Feature selection", ["feature selection"]),
        ("HHO", ["hho", "harris hawks"]),
        ("PSO", ["pso", "particle swarm"]),
        ("GWO", ["gwo", "grey wolf"]),
        ("DFO/Dragonfly", ["dfo", "dragonfly"]),
        ("PCA", ["pca"]),
    ]:
        if has_any(text, terms):
            vals.append(label)

    return " / ".join(dict.fromkeys(vals)) if vals else "Yok/Belirsiz"


def infer_runtime(row) -> str:
    v = clean(row.get("real_time_or_offline", ""))
    text = blob(row)

    if has_any(v, ["runtime", "real-time", "real time", "near-real-time", "near real-time"]):
        return "Var"
    if has_any(text, ["runtime", "real-time", "real time", "near-real-time", "near real-time", "online"]):
        return "Var"
    if has_any(text, ["offline"]):
        return "Offline"
    return "Belirsiz"


def infer_mitigation(row) -> str:
    v = clean(row.get("mitigation_action", ""))
    text = blob(row)

    vals = []
    if has_any(f"{v} {text}", ["rate-limit", "rate limit", "meter"]):
        vals.append("Rate-limit")
    if has_any(f"{v} {text}", ["drop", "blocking", "block"]):
        vals.append("Drop")
    if has_any(f"{v} {text}", ["quarantine", "isolation"]):
        vals.append("Quarantine")
    if has_any(f"{v} {text}", ["reroute", "redirect"]):
        vals.append("Reroute")
    if has_any(f"{v} {text}", ["mitigation", "prevention", "defense"]):
        vals.append("Mitigation/Prevention")

    return " / ".join(dict.fromkeys(vals)) if vals else "Yok/Belirsiz"


def infer_port_protocol(row) -> str:
    text = blob(row)
    if has_any(text, ["port-aware", "protocol-aware", "port aware", "protocol aware", "src_port", "dst_port"]):
        return "Var"
    return "Yok/Belirsiz"


def select_representative_literature(df: pd.DataFrame, limit: int = 18) -> pd.DataFrame:
    df = df.copy().fillna("")

    def score(row) -> int:
        text = blob(row)
        s = 0

        rel = clean(row.get("relevance_to_this_thesis", ""))
        if rel == "High":
            s += 8
        elif rel == "Medium":
            s += 4

        if has_any(text, ["sdn", "software-defined", "software defined", "openflow"]):
            s += 5
        if has_any(text, ["ddos", "denial of service"]):
            s += 5
        if has_any(text, ["mitigation", "prevention", "defense", "drop", "rate-limit", "quarantine"]):
            s += 4
        if has_any(text, ["runtime", "real-time", "real time", "near-real-time", "online", "ryu", "mininet"]):
            s += 4
        if has_any(text, ["feature selection", "hho", "pso", "gwo", "dragonfly", "dfo"]):
            s += 2
        if has_any(text, ["cic-ddos2019", "cicddos2019", "cicids", "insdn"]):
            s += 2

        # Prefer newer studies, but do not exclude older foundational work.
        try:
            year = int(float(clean(row.get("year", "0")) or 0))
        except Exception:
            year = 0
        if year >= 2020:
            s += 2
        if year >= 2023:
            s += 1

        return s

    df["_score"] = df.apply(score, axis=1)
    df["_year"] = pd.to_numeric(df.get("year", 0), errors="coerce").fillna(0).astype(int)

    # Remove very generic unrelated records if title clearly not network/security related.
    candidate = df[df["_score"] >= 8].copy()
    if len(candidate) < limit:
        candidate = df.copy()

    candidate = candidate.sort_values(by=["_score", "_year"], ascending=[False, False])
    return candidate.head(limit).drop(columns=[c for c in ["_score", "_year"] if c in candidate.columns])


def load_own_results(thesis_artifact_dir: Path) -> dict:
    results = {
        "model": "Final XGBoost Top-20",
        "dataset": "CIC-DDoS2019 tabanlı seçilmiş veri + runtime PCAP",
        "f1_auc": "Offline model metrikleri: önceki deneylerde yüksek F1/AUC; runtime deneyde BENIGN/ATTACK ayrımı doğrulandı",
        "runtime": "Var",
        "controller_integration": "Var",
        "mitigation": "Rate-limit / Drop / Quarantine",
        "port_protocol": "Var",
        "notes": "run_05 port-aware/protocol-aware canonical runtime validation",
    }

    summary = thesis_artifact_dir / "thesis_artifacts_summary.json"
    if summary.exists():
        try:
            data = json.loads(summary.read_text(encoding="utf-8"))
            rows = data.get("row_counts", {})
            results["runtime_rows"] = (
                f"policy_decisions={rows.get('policy_decisions', '')}, "
                f"runtime_predictions={rows.get('final_runtime_predictions', '')}, "
                f"mitigation_log={rows.get('mitigation_log', '')}, "
                f"quarantine_log={rows.get('quarantine_log', '')}, "
                f"rate_limit_log={rows.get('rate_limit_log', '')}"
            )
        except Exception:
            results["runtime_rows"] = ""

    return results


def write_md_table(path: Path, df: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(df.to_markdown(index=False), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--synthesis-csv",
        default="docs/literature_review/synthesis/chapter3_literature_synthesis_candidates.csv",
    )
    parser.add_argument(
        "--thesis-artifact-dir",
        default="experiments/results/thesis_artifacts/run_05_port_aware_runtime_validation",
    )
    parser.add_argument(
        "--output-dir",
        default="docs/literature_review/synthesis",
    )
    parser.add_argument("--limit", type=int, default=18)
    args = parser.parse_args()

    synthesis_csv = Path(args.synthesis_csv)
    thesis_artifact_dir = Path(args.thesis_artifact_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not synthesis_csv.exists():
        raise SystemExit(f"[ERROR] Missing synthesis CSV: {synthesis_csv}")

    df = pd.read_csv(synthesis_csv).fillna("")
    selected = select_representative_literature(df, args.limit)

    chapter3_rows = []
    for _, r in selected.iterrows():
        text = blob(r)

        chapter3_rows.append({
            "Çalışma": f"{clean(r.get('id', ''))} — {short_title(clean(r.get('title', '')))}",
            "Yıl": clean(r.get("year", "")),
            "SDN bağlamı": "Var" if has_any(text, ["sdn", "software-defined", "software defined", "openflow"]) else "Belirsiz",
            "Denetleyici/Testbed": infer_controller(r),
            "Veri kümesi": infer_dataset(r),
            "Model/Yöntem": infer_model(r),
            "Özellik seçimi": infer_feature_selection(r),
            "Runtime doğrulama": infer_runtime(r),
            "Controller entegrasyonu": infer_yes_no(text, ["controller", "ryu", "openflow", "mininet"]),
            "Mitigation/Prevention": infer_mitigation(r),
            "Port/Protocol-aware karşılaştırma": infer_port_protocol(r),
            "Tezle ilişkisi": clean(r.get("relevance_to_this_thesis", "")) or "Belirsiz",
        })

    own = load_own_results(thesis_artifact_dir)

    chapter3_rows.append({
        "Çalışma": "Bu tez çalışması",
        "Yıl": "2026",
        "SDN bağlamı": "Var",
        "Denetleyici/Testbed": "Mininet / Open vSwitch / Ryu / OpenFlow",
        "Veri kümesi": own["dataset"],
        "Model/Yöntem": own["model"],
        "Özellik seçimi": "Final Top-20 selected features",
        "Runtime doğrulama": "Var",
        "Controller entegrasyonu": "Var",
        "Mitigation/Prevention": own["mitigation"],
        "Port/Protocol-aware karşılaştırma": "Var",
        "Tezle ilişkisi": "Önerilen çalışma",
    })

    chapter3_df = pd.DataFrame(chapter3_rows)

    chapter5_rows = []
    for _, r in selected.iterrows():
        text = blob(r)

        chapter5_rows.append({
            "Çalışma": f"{clean(r.get('id', ''))} — {short_title(clean(r.get('title', '')), 75)}",
            "Model/Yöntem": infer_model(r),
            "Veri kümesi": infer_dataset(r),
            "Raporlanan metrikler": clean(r.get("metrics_reported", "")) or "Belirsiz",
            "Runtime test": infer_runtime(r),
            "Controller-side mitigation": infer_mitigation(r),
            "Rate-limit/Drop/Quarantine": infer_mitigation(r),
            "Port/Protocol-aware analiz": infer_port_protocol(r),
            "Güçlü yön": clean(r.get("strengths", "")) or "Literatürde ilgili yaklaşımı temsil eder",
            "Sınırlılık": clean(r.get("limitations", "")) or "Ayrıntı full-text üzerinden doğrulanmalı",
        })

    chapter5_rows.append({
        "Çalışma": "Bu tez çalışması",
        "Model/Yöntem": own["model"],
        "Veri kümesi": own["dataset"],
        "Raporlanan metrikler": own.get("runtime_rows", "") or "Runtime action validation + offline ML metrics",
        "Runtime test": "Var",
        "Controller-side mitigation": "Var",
        "Rate-limit/Drop/Quarantine": "Rate-limit / Drop / Quarantine gözlendi",
        "Port/Protocol-aware analiz": "Var",
        "Güçlü yön": "Offline ML modelini canlı SDN runtime enforcement zinciriyle bütünleştirir",
        "Sınırlılık": "Kontrollü Mininet ortamı; daha geniş trafik profilleriyle doğrulama gerektirir",
    })

    chapter5_df = pd.DataFrame(chapter5_rows)

    ch3_csv = output_dir / "table_chapter3_methodological_comparison.csv"
    ch3_md = output_dir / "table_chapter3_methodological_comparison.md"
    ch5_csv = output_dir / "table_chapter5_result_functionality_comparison.csv"
    ch5_md = output_dir / "table_chapter5_result_functionality_comparison.md"

    chapter3_df.to_csv(ch3_csv, index=False)
    write_md_table(ch3_md, chapter3_df)

    chapter5_df.to_csv(ch5_csv, index=False)
    write_md_table(ch5_md, chapter5_df)

    summary = {
        "generated_at_utc": datetime.utcnow().isoformat(),
        "synthesis_csv": str(synthesis_csv),
        "selected_literature_rows": len(selected),
        "chapter3_table_csv": str(ch3_csv),
        "chapter3_table_md": str(ch3_md),
        "chapter5_table_csv": str(ch5_csv),
        "chapter5_table_md": str(ch5_md),
        "own_results_source": str(thesis_artifact_dir),
    }

    summary_path = output_dir / "literature_comparison_tables_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print("[INFO] Selected literature rows:", len(selected))
    print("[INFO] Chapter 3 CSV:", ch3_csv)
    print("[INFO] Chapter 3 MD :", ch3_md)
    print("[INFO] Chapter 5 CSV:", ch5_csv)
    print("[INFO] Chapter 5 MD :", ch5_md)
    print("[INFO] Summary:", summary_path)


if __name__ == "__main__":
    main()
