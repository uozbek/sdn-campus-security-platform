#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from datetime import datetime
import pandas as pd


TABLE_NAMES = {
    "Tablo 3.1": "SDN/DDoS/OpenFlow Odaklı Seçilmiş Çalışmalar",
    "Tablo 3.2": "ML/DL Tabanlı Seçilmiş IDS Çalışmaları",
    "Tablo 3.3": "Özellik Seçimi Odaklı Seçilmiş Çalışmalar",
    "Tablo 3.4": "Runtime/Controller/Testbed Odaklı Seçilmiş Çalışmalar",
    "Tablo 3.5": "Mitigation/Prevention Odaklı Seçilmiş Çalışmalar",
    "Tablo 3.6": "Veri Kümesi Odaklı Çalışmalar",
    "Tablo 3.7": "SDN Tabanlı DDoS Tespit ve Önleme Çalışmalarının Yöntemsel Karşılaştırması",
}


def clean(s):
    return str(s or "").strip()


def split_tables(s):
    vals = []
    for item in clean(s).split(";"):
        item = item.strip()
        if item:
            vals.append(item)
    return vals


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--plan-csv",
        default="docs/literature_review/zotero_clean/chapter_3_5_fulltext_revision_plan.csv",
    )
    parser.add_argument(
        "--output-md",
        default="docs/literature_review/zotero_clean/chapter_3_table_revision_plan.md",
    )
    parser.add_argument(
        "--output-csv",
        default="docs/literature_review/zotero_clean/chapter_3_table_revision_plan.csv",
    )
    args = parser.parse_args()

    plan_path = Path(args.plan_csv)
    if not plan_path.exists():
        raise SystemExit(f"[ERROR] Missing plan CSV: {plan_path}")

    df = pd.read_csv(plan_path).fillna("")
    rows = []

    for _, r in df.iterrows():
        tables = split_tables(r.get("chapter_3_tables", ""))
        if not tables:
            continue

        for table in tables:
            # Bazı satırlarda "Tablo 3.1 / Tablo 3.4" birlikte geliyor.
            expanded = []
            if "/" in table:
                for part in table.split("/"):
                    part = part.strip()
                    if part.startswith("Tablo"):
                        expanded.append(part)
                    elif part.startswith("3."):
                        expanded.append("Tablo " + part)
            else:
                expanded.append(table)

            for t in expanded:
                t = t.strip()
                if not t.startswith("Tablo 3."):
                    continue

                rows.append({
                    "target_table": t,
                    "target_table_title": TABLE_NAMES.get(t, ""),
                    "zotero_key": clean(r.get("zotero_key", "")),
                    "year": clean(r.get("year", "")),
                    "priority_score": clean(r.get("priority_score", "")),
                    "title": clean(r.get("title", "")),
                    "dataset_signals": clean(r.get("dataset_signals", "")),
                    "sdn_testbed_signals": clean(r.get("sdn_testbed_signals", "")),
                    "mitigation_signals": clean(r.get("mitigation_signals", "")),
                    "runtime_signals": clean(r.get("runtime_signals", "")),
                    "feature_selection_signals": clean(r.get("feature_selection_signals", "")),
                    "model_signals": clean(r.get("model_signals", "")),
                    "metric_signals": clean(r.get("metric_signals", "")),
                    "recommended_action": clean(r.get("recommended_action", "")),
                })

    out = pd.DataFrame(rows)

    if len(out):
        out["priority_score_num"] = pd.to_numeric(out["priority_score"], errors="coerce").fillna(0)
        out = out.sort_values(
            ["target_table", "priority_score_num", "year"],
            ascending=[True, False, False],
        ).drop(columns=["priority_score_num"])

    Path(args.output_csv).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.output_csv, index=False)

    md = []
    md.append("# Chapter 3 Table Revision Plan")
    md.append("")
    md.append(f"- Generated at UTC: `{datetime.utcnow().isoformat()}`")
    md.append(f"- Input plan CSV: `{args.plan_csv}`")
    md.append(f"- Output CSV: `{args.output_csv}`")
    md.append(f"- Candidate table-source links: `{len(out)}`")
    md.append("")
    md.append("## 1. Table Target Counts")
    md.append("")
    md.append("| Table | Title | Candidate count |")
    md.append("|---|---|---:|")

    if len(out):
        counts = out["target_table"].value_counts().to_dict()
    else:
        counts = {}

    for table in sorted(TABLE_NAMES):
        md.append(f"| {table} | {TABLE_NAMES[table]} | {counts.get(table, 0)} |")

    md.append("")
    md.append("## 2. Revision Strategy")
    md.append("")
    md.append("- Bölüm 3 tabloları, yalnızca kaynak sayısını artırmak için değil, full text'te görülen yöntemsel sinyalleri daha doğru yansıtmak için güncellenmelidir.")
    md.append("- Her tabloya bütün adaylar eklenmemelidir; en yüksek öncelikli ve tezin argümanını güçlendiren kaynaklar seçilmelidir.")
    md.append("- NSL-KDD bu tezde deneysel omurga değildir; bu nedenle NSL-KDD içeren kaynaklar varsa yalnızca tarihsel/bağlamsal düzeyde değerlendirilmelidir.")
    md.append("- Tablo 3.7, tezin özgün katkısını göstermek için en kritik tablodur; detection-only, runtime validation ve mitigation/prevention ayrımı burada açık görünmelidir.")
    md.append("")

    md.append("## 3. Source-Level Table Targets")
    md.append("")
    for table in sorted(TABLE_NAMES):
        sub = out[out["target_table"].eq(table)] if len(out) else pd.DataFrame()
        md.append(f"### {table}. {TABLE_NAMES[table]}")
        md.append("")
        if len(sub) == 0:
            md.append("No candidates.")
            md.append("")
            continue

        md.append("| Key | Year | Score | Title | Key signals |")
        md.append("|---|---:|---:|---|---|")
        for _, r in sub.iterrows():
            signals = []
            if clean(r["sdn_testbed_signals"]):
                signals.append("SDN/testbed")
            if clean(r["mitigation_signals"]):
                signals.append("mitigation")
            if clean(r["runtime_signals"]):
                signals.append("runtime")
            if clean(r["feature_selection_signals"]):
                signals.append("feature selection")
            if clean(r["model_signals"]):
                signals.append("model")
            if clean(r["dataset_signals"]):
                signals.append("dataset")
            if clean(r["metric_signals"]):
                signals.append("metrics")

            title = clean(r["title"]).replace("|", "\\|")
            md.append(
                f"| {r['zotero_key']} | {r['year']} | {r['priority_score']} | "
                f"{title[:120]} | {', '.join(signals)} |"
            )
        md.append("")

    md.append("## 4. Recommended Immediate Changes")
    md.append("")
    md.append("1. Tablo 3.4 ve Tablo 3.5 özellikle kontrol edilmeli; çünkü tezin özgünlüğü runtime/controller/testbed ve mitigation/prevention ayrımında ortaya çıkmaktadır.")
    md.append("2. Tablo 3.7'ye detection-only / runtime validation / mitigation action / controller integration sütunlarının açık yansıdığından emin olunmalıdır.")
    md.append("3. Bölüm 3 metin sentezinde, yüksek accuracy raporlayan çalışmaların pratik SDN önleme davranışını her zaman göstermediği vurgulanmalıdır.")
    md.append("4. CIC-DDoS2019 ve CICFlowMeter-style feature tercihi, Tablo 3.6 ve Bölüm 4 yöntem gerekçesiyle uyumlu hale getirilmelidir.")

    Path(args.output_md).write_text("\n".join(md), encoding="utf-8")

    print("[INFO] Candidate links:", len(out))
    print("[INFO] CSV:", args.output_csv)
    print("[INFO] MD:", args.output_md)
    if len(out):
        print("[INFO] Table counts:", out["target_table"].value_counts().to_dict())


if __name__ == "__main__":
    main()
