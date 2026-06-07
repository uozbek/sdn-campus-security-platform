#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
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


def contains_any(row, terms) -> bool:
    blob = " ".join(clean(v).lower() for v in row.values)
    return any(t.lower() in blob for t in terms)


def compact_table(df: pd.DataFrame, columns: list[str], max_rows: int = 20) -> str:
    if df.empty:
        return "_No records found._"

    cols = [c for c in columns if c in df.columns]
    tmp = df[cols].copy().head(max_rows)

    for c in tmp.columns:
        tmp[c] = tmp[c].astype(str).replace("nan", "")
        tmp[c] = tmp[c].apply(lambda x: x[:140] + "..." if len(x) > 140 else x)

    return tmp.to_markdown(index=False)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--synthesis-csv",
        default="docs/literature_review/synthesis/chapter3_literature_synthesis_candidates.csv",
    )
    parser.add_argument(
        "--output-dir",
        default="docs/literature_review/synthesis",
    )
    args = parser.parse_args()

    synthesis_csv = Path(args.synthesis_csv)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not synthesis_csv.exists():
        raise SystemExit(f"[ERROR] Missing synthesis CSV: {synthesis_csv}")

    df = pd.read_csv(synthesis_csv).fillna("")

    # Category subsets
    sdn_ddos = df[df.apply(lambda r: contains_any(r, ["sdn", "software-defined", "software defined", "openflow", "ddos"]), axis=1)]
    ml_dl = df[df.apply(lambda r: contains_any(r, ["machine learning", "deep learning", "xgboost", "random forest", "svm", "lstm", "cnn", "ensemble"]), axis=1)]
    feature_selection = df[df.apply(lambda r: contains_any(r, ["feature selection", "metaheuristic", "pso", "gwo", "hho", "dfo", "top-20", "top k", "pca"]), axis=1)]
    runtime_controller = df[df.apply(lambda r: contains_any(r, ["runtime", "real-time", "real time", "controller", "ryu", "mininet", "openflow", "ovs", "open vswitch"]), axis=1)]
    mitigation = df[df.apply(lambda r: contains_any(r, ["mitigation", "drop", "rate-limit", "rate limit", "quarantine", "reroute", "prevention"]), axis=1)]
    datasets = df[df.apply(lambda r: contains_any(r, ["cic-ddos2019", "cicddos2019", "insdn", "nsl-kdd", "cicids", "unsw-nb15", "dataset"]), axis=1)]

    report = []
    report.append("# Chapter 3 Literature Synthesis Report")
    report.append("")
    report.append(f"- Generated at UTC: `{datetime.utcnow().isoformat()}`")
    report.append(f"- Source CSV: `{synthesis_csv}`")
    report.append(f"- Candidate count: `{len(df)}`")
    report.append("")
    report.append("Bu rapor, Bölüm 3 literatür taraması için seçilen aday kaynakları tematik olarak gruplandırır.")
    report.append("")

    report.append("## 1. Genel Sayısal Özet")
    report.append("")
    report.append("| Category | Count |")
    report.append("|---|---:|")
    report.append(f"| All synthesis candidates | {len(df)} |")
    report.append(f"| SDN/DDoS/OpenFlow related | {len(sdn_ddos)} |")
    report.append(f"| ML/DL related | {len(ml_dl)} |")
    report.append(f"| Feature selection related | {len(feature_selection)} |")
    report.append(f"| Runtime/controller/testbed related | {len(runtime_controller)} |")
    report.append(f"| Mitigation/prevention related | {len(mitigation)} |")
    report.append(f"| Dataset related | {len(datasets)} |")
    report.append("")

    cols = [
        "id", "year", "authors", "title", "venue",
        "dataset", "ml_dl_model", "mitigation_action",
        "real_time_or_offline", "relevance_to_this_thesis",
        "selection_reason"
    ]

    report.append("## 2. SDN / DDoS / OpenFlow Odaklı Çalışmalar")
    report.append("")
    report.append(compact_table(sdn_ddos, cols, 20))
    report.append("")

    report.append("## 3. Makine Öğrenmesi ve Derin Öğrenme Odaklı Çalışmalar")
    report.append("")
    report.append(compact_table(ml_dl, cols, 20))
    report.append("")

    report.append("## 4. Özellik Seçimi ve Hafif Model Tasarımı Çalışmaları")
    report.append("")
    report.append(compact_table(feature_selection, cols, 20))
    report.append("")

    report.append("## 5. Runtime / Controller / Testbed Entegrasyonu İçeren Çalışmalar")
    report.append("")
    report.append(compact_table(runtime_controller, cols, 20))
    report.append("")

    report.append("## 6. Mitigation / Prevention İçeren Çalışmalar")
    report.append("")
    report.append(compact_table(mitigation, cols, 20))
    report.append("")

    report.append("## 7. Veri Kümesi Odaklı Çalışmalar")
    report.append("")
    report.append(compact_table(datasets, cols, 20))
    report.append("")

    report.append("## 8. Bölüm 3 İçin Kullanım Notu")
    report.append("")
    report.append(
        "Bu rapordaki kaynaklar Bölüm 3 metninde doğrudan kategori bazlı kullanılmalıdır. "
        "Öncelikle SDN-DDoS tespiti, ML/DL tabanlı IDS, feature selection, controller entegrasyonu "
        "ve aktif mitigation başlıkları altında en yüksek ilişkili kaynaklar seçilmelidir."
    )
    report.append("")

    report_path = output_dir / "chapter3_literature_synthesis_report.md"
    report_path.write_text("\n".join(report), encoding="utf-8")

    gap = []
    gap.append("# Chapter 3 Literature Gap Analysis Draft")
    gap.append("")
    gap.append(f"- Generated at UTC: `{datetime.utcnow().isoformat()}`")
    gap.append("")
    gap.append("## Literatürde Gözlenen Ana Eğilimler")
    gap.append("")
    gap.append("- SDN tabanlı DDoS tespit çalışmaları genellikle merkezi denetleyici görünürlüğünden yararlanmaktadır.")
    gap.append("- ML/DL tabanlı çalışmalar yüksek sınıflandırma başarısı raporlamakta, ancak çoğu zaman çalışma zamanı entegrasyonu sınırlı kalmaktadır.")
    gap.append("- Özellik seçimi ve hafif model tasarımları runtime uygulanabilirlik açısından önemlidir.")
    gap.append("- Mininet, Ryu, OpenFlow ve Open vSwitch tabanlı deneysel çalışmalar literatürde önemli yer tutmaktadır.")
    gap.append("- Mitigation içeren çalışmalar bulunmakla birlikte rate-limit, drop ve quarantine aksiyonlarının birlikte ele alındığı uçtan uca prototipler sınırlıdır.")
    gap.append("")
    gap.append("## Literatürdeki Boşluklar")
    gap.append("")
    gap.append("1. Birçok çalışma offline classification başarısına odaklanmakta, SDN denetleyicisiyle runtime entegrasyonu sınırlı ele almaktadır.")
    gap.append("2. Model çıktısının OpenFlow tabanlı aksiyonlara nasıl dönüştürüldüğü her çalışmada açık değildir.")
    gap.append("3. Port-aware ve protocol-aware flow-level karşılaştırma çoğu çalışmada ayrıntılı tartışılmamaktadır.")
    gap.append("4. Rate-limit, drop ve quarantine aksiyonlarının birlikte üretildiği aktif IPS zinciri sınırlı sayıda çalışmada görülmektedir.")
    gap.append("5. Controller overhead, inference latency ve flow-stat polling maliyeti çoğu çalışmada ikincil planda kalmaktadır.")
    gap.append("")
    gap.append("## Bu Tezin Konumu")
    gap.append("")
    gap.append(
        "Bu tez çalışması, offline eğitilmiş Final XGBoost Top-20 modelini Ryu tabanlı SDN denetleyicisi, "
        "FastAPI inference servisi, PCAP tabanlı runtime feature extraction ve OpenFlow tabanlı enforcement "
        "mekanizmalarıyla bütünleştirerek literatürdeki runtime IDS/IPS boşluğuna odaklanmaktadır. "
        "Canonical run_05 deneyinde port-aware/protocol-aware karşılaştırma yapılmış ve rate-limit, drop, "
        "quarantine aksiyonları gözlenmiştir."
    )
    gap.append("")

    gap_path = output_dir / "chapter3_literature_gap_analysis.md"
    gap_path.write_text("\n".join(gap), encoding="utf-8")

    summary = {
        "generated_at_utc": datetime.utcnow().isoformat(),
        "source_csv": str(synthesis_csv),
        "candidate_count": len(df),
        "category_counts": {
            "sdn_ddos": len(sdn_ddos),
            "ml_dl": len(ml_dl),
            "feature_selection": len(feature_selection),
            "runtime_controller": len(runtime_controller),
            "mitigation": len(mitigation),
            "datasets": len(datasets),
        },
        "outputs": {
            "report_md": str(report_path),
            "gap_analysis_md": str(gap_path),
        }
    }

    summary_path = output_dir / "chapter3_literature_synthesis_report_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print("[INFO] Written:", report_path)
    print("[INFO] Written:", gap_path)
    print("[INFO] Written:", summary_path)
    print("[INFO] Candidate count:", len(df))
    print("[INFO] Category counts:", summary["category_counts"])


if __name__ == "__main__":
    main()
