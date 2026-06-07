#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from datetime import datetime
import pandas as pd


def yes(s):
    return bool(str(s or "").strip())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--targets-csv",
        default="docs/literature_review/zotero_clean/fulltext_thesis_revision_targets.csv",
    )
    parser.add_argument(
        "--output-md",
        default="docs/literature_review/zotero_clean/chapter_3_5_fulltext_revision_plan.md",
    )
    parser.add_argument(
        "--output-csv",
        default="docs/literature_review/zotero_clean/chapter_3_5_fulltext_revision_plan.csv",
    )
    args = parser.parse_args()

    p = Path(args.targets_csv)
    if not p.exists():
        raise SystemExit(f"[ERROR] Missing targets CSV: {p}")

    df = pd.read_csv(p).fillna("")

    rows = []

    for _, r in df.iterrows():
        targets = str(r.get("revision_targets", ""))
        title = str(r.get("title", ""))
        key = str(r.get("zotero_key", ""))
        year = str(r.get("year", ""))
        score = r.get("priority_score", "")

        sdn = str(r.get("sdn_testbed_signals_found", ""))
        mitigation = str(r.get("mitigation_signals_found", ""))
        runtime = str(r.get("runtime_signals_found", ""))
        dataset = str(r.get("dataset_signals_found", ""))
        fs = str(r.get("feature_selection_signals_found", ""))
        model = str(r.get("model_signals_found", ""))
        metrics = str(r.get("metric_signals_found", ""))

        suggested_table = []
        suggested_discussion = []

        if "Bölüm 3" in targets:
            if yes(sdn) and ("OpenFlow" in sdn or "Ryu" in sdn or "Mininet" in sdn or "controller" in sdn):
                suggested_table.append("Tablo 3.1 / Tablo 3.4")
            if yes(model):
                suggested_table.append("Tablo 3.2")
            if yes(fs):
                suggested_table.append("Tablo 3.3")
            if yes(mitigation):
                suggested_table.append("Tablo 3.5")
            if yes(dataset):
                suggested_table.append("Tablo 3.6")
            suggested_table.append("Tablo 3.7")

        if "Bölüm 5" in targets:
            if yes(mitigation):
                suggested_discussion.append("Detection-only çalışmalar ile mitigation/prevention üreten çalışmalar ayrımı")
            if yes(runtime):
                suggested_discussion.append("Runtime validation, latency, online/near-real-time değerlendirme boşluğu")
            if yes(sdn):
                suggested_discussion.append("Controller/testbed entegrasyonu ve pratik uygulanabilirlik")
            if yes(metrics):
                suggested_discussion.append("Accuracy dışı metrikler: F1, AUC, FPR/FAR, yanlış pozitif etkisi")
            if yes(dataset):
                suggested_discussion.append("Veri seti güncelliği, trafik çeşitliliği ve genellenebilirlik")

        if suggested_table or suggested_discussion:
            rows.append({
                "zotero_key": key,
                "year": year,
                "priority_score": score,
                "title": title,
                "chapter_3_tables": "; ".join(sorted(set(suggested_table))),
                "chapter_5_discussion_use": "; ".join(sorted(set(suggested_discussion))),
                "dataset_signals": dataset,
                "sdn_testbed_signals": sdn,
                "mitigation_signals": mitigation,
                "runtime_signals": runtime,
                "feature_selection_signals": fs,
                "model_signals": model,
                "metric_signals": metrics,
                "recommended_action": r.get("recommended_action", ""),
            })

    out = pd.DataFrame(rows)
    out.to_csv(args.output_csv, index=False)

    md = []
    md.append("# Chapter 3–5 Full Text Revision Plan")
    md.append("")
    md.append(f"- Generated at UTC: `{datetime.utcnow().isoformat()}`")
    md.append(f"- Input: `{args.targets_csv}`")
    md.append(f"- Output CSV: `{args.output_csv}`")
    md.append(f"- Source count: `{len(out)}`")
    md.append("")
    md.append("## 1. Amaç")
    md.append("")
    md.append("Bu plan, A Grubu full text evidence card çıktılarından hareketle Bölüm 3 literatür tabloları ve Bölüm 5 tartışma/sınırlılık bölümü için kullanılabilecek kaynakları hedefler.")
    md.append("")
    md.append("NSL-KDD tez omurgasına alınmayacaktır. Bu veri seti yalnızca tarihsel/bağlamsal bir örnek olarak yüzeysel anılabilir; deneysel yöntem ve bulgu anlatımı CIC-DDoS2019 / CICFlowMeter-style özellikler / SDN runtime doğrulama hattına dayandırılacaktır.")
    md.append("")
    md.append("## 2. Bölüm 3 Tablo Güncelleme Mantığı")
    md.append("")
    md.append("- `Tablo 3.1`: SDN/DDoS/OpenFlow/controller odaklı çalışmalar.")
    md.append("- `Tablo 3.2`: ML/DL tabanlı IDS modelleri.")
    md.append("- `Tablo 3.3`: Özellik seçimi/meta-sezgisel optimizasyon çalışmaları.")
    md.append("- `Tablo 3.4`: Runtime/controller/testbed doğrulaması yapan çalışmalar.")
    md.append("- `Tablo 3.5`: Mitigation/prevention aksiyonu içeren çalışmalar.")
    md.append("- `Tablo 3.6`: Veri kümesi ve trafik özellikleri odaklı çalışmalar.")
    md.append("- `Tablo 3.7`: Bu tez ile literatür arasındaki yöntemsel farkların sentezi.")
    md.append("")
    md.append("## 3. Bölüm 5 Tartışma Odakları")
    md.append("")
    md.append("- Detection-only ve prevention/mitigation üreten çalışmalar ayrımı.")
    md.append("- Offline sınıflandırma başarımı ile SDN runtime uygulanabilirliği arasındaki boşluk.")
    md.append("- Controller/testbed entegrasyonu, latency ve overhead tartışması.")
    md.append("- Accuracy dışı metriklerin, özellikle FPR/FAR ve yanlış pozitiflerin IDS/IPS açısından önemi.")
    md.append("- Veri seti güncelliği, CIC-DDoS2019 tercihi ve genellenebilirlik sınırlılıkları.")
    md.append("")
    md.append("## 4. Kaynak Bazlı Revizyon Planı")
    md.append("")
    md.append("| Key | Year | Score | Bölüm 3 tablo hedefi | Bölüm 5 kullanım | Title |")
    md.append("|---|---:|---:|---|---|---|")
    for _, r in out.iterrows():
        title = str(r["title"]).replace("|", "\\|")
        table = str(r["chapter_3_tables"]).replace("|", "\\|")
        disc = str(r["chapter_5_discussion_use"]).replace("|", "\\|")
        md.append(f"| {r['zotero_key']} | {r['year']} | {r['priority_score']} | {table[:120]} | {disc[:160]} | {title[:120]} |")

    md.append("")
    md.append("## 5. Uygulama Notu")
    md.append("")
    md.append("Bu plan doğrudan tez metnine otomatik ekleme yapmaz. Önce hangi tablo ve paragrafların güçlendirileceği belirlenmeli, ardından Bölüm 3 ve Bölüm 5 metinleri kontrollü biçimde revize edilmelidir.")

    Path(args.output_md).write_text("\n".join(md), encoding="utf-8")

    print("[INFO] Sources:", len(out))
    print("[INFO] CSV:", args.output_csv)
    print("[INFO] MD:", args.output_md)


if __name__ == "__main__":
    main()
