#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

import pandas as pd


def read_csv_if_exists(path: Path) -> pd.DataFrame:
    if path.exists():
        return pd.read_csv(path).fillna("")
    return pd.DataFrame()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate thesis-defense-oriented critical review for runtime validation experiments."
    )
    parser.add_argument(
        "--canonical-agg-csv",
        default="experiments/results/mixed_traffic_experiments/canonical_runtime_validation_runs/aggregate_reports/mixed_traffic_multi_run_summary_20260519_193527.csv",
    )
    parser.add_argument(
        "--flow-comparison-csv",
        default="experiments/results/thesis_artifacts/run_05_port_aware_runtime_validation/tables/table_flow_level_model_controller_comparison.csv",
    )
    parser.add_argument(
        "--attack-probability-csv",
        default="experiments/results/thesis_artifacts/run_05_port_aware_runtime_validation/tables/table_protocol_aware_attack_probability_summary.csv",
    )
    parser.add_argument(
        "--enforcement-summary-csv",
        default="experiments/results/thesis_artifacts/run_05_port_aware_runtime_validation/tables/table_enforcement_action_summary.csv",
    )
    parser.add_argument(
        "--controller-action-csv",
        default="experiments/results/thesis_artifacts/run_05_port_aware_runtime_validation/tables/table_controller_action_distribution.csv",
    )
    parser.add_argument(
        "--output-md",
        default="docs/experimental_defense_review_report.md",
    )
    parser.add_argument(
        "--output-json",
        default="docs/experimental_defense_review_report.json",
    )
    args = parser.parse_args()

    canonical = read_csv_if_exists(Path(args.canonical_agg_csv))
    flow_cmp = read_csv_if_exists(Path(args.flow_comparison_csv))
    attack_prob = read_csv_if_exists(Path(args.attack_probability_csv))
    enforcement = read_csv_if_exists(Path(args.enforcement_summary_csv))
    controller = read_csv_if_exists(Path(args.controller_action_csv))

    summary = {
        "canonical_run_count": len(canonical),
        "flow_comparison_rows": len(flow_cmp),
        "attack_probability_rows": len(attack_prob),
        "enforcement_rows": len(enforcement),
        "controller_action_rows": len(controller),
    }

    if not flow_cmp.empty:
        for col in [
            "matched_controller_exact",
            "security_compatible_action",
            "matched_mitigation_drop",
            "matched_quarantine",
            "matched_rate_limit",
        ]:
            if col in flow_cmp.columns:
                vals = flow_cmp[col].astype(str).str.lower()
                summary[col + "_true"] = int(vals.isin(["true", "1", "yes"]).sum())
                summary[col + "_total"] = int(len(flow_cmp))

    if not attack_prob.empty and "prediction" in attack_prob.columns:
        summary["attack_prediction_count"] = int((attack_prob["prediction"].astype(str).str.upper() == "ATTACK").sum())
        summary["benign_prediction_count"] = int((attack_prob["prediction"].astype(str).str.upper() == "BENIGN").sum())

    if not controller.empty and "policy_final_action" in controller.columns:
        summary["controller_actions"] = {
            str(row["policy_final_action"]): int(row["count"])
            for _, row in controller.iterrows()
            if "count" in controller.columns
        }

    if not enforcement.empty and "enforcement_type" in enforcement.columns:
        summary["enforcement_actions"] = {
            str(row["enforcement_type"]): int(row["count"])
            for _, row in enforcement.iterrows()
            if "count" in enforcement.columns
        }

    md = []
    md.append("# Deneysel Sonuçlar İçin Savunma/Jüri Perspektifi Değerlendirme Raporu")
    md.append("")
    md.append(f"- Generated at UTC: `{datetime.utcnow().isoformat()}`")
    md.append(f"- Canonical aggregate CSV: `{args.canonical_agg_csv}`")
    md.append(f"- Flow comparison CSV: `{args.flow_comparison_csv}`")
    md.append("")
    md.append("## 1. Deneysel Kanıtın Özeti")
    md.append("")
    md.append(f"- Canonical run sayısı: `{summary.get('canonical_run_count', 0)}`")
    md.append(f"- Flow-level karşılaştırma satırı: `{summary.get('flow_comparison_rows', 0)}`")
    md.append(f"- Runtime prediction satırı: `{summary.get('attack_probability_rows', 0)}`")
    md.append(f"- Controller action satırı: `{summary.get('controller_action_rows', 0)}`")
    md.append(f"- Enforcement summary satırı: `{summary.get('enforcement_rows', 0)}`")
    md.append("")
    md.append("Bu deneysel yapı, yalnızca offline makine öğrenmesi başarımını değil, model çıktılarının SDN denetleyicisi tarafında politika kararlarına ve önleme aksiyonlarına bağlanıp bağlanamadığını değerlendirmektedir.")
    md.append("")
    md.append("## 2. Jüri Sorusu: Neden run_05 ana deney olarak seçildi?")
    md.append("")
    md.append("`run_05_port_aware_repeat_validation`, port-aware ve protocol-aware eşleştirme için en güçlü canonical koşudur. Bu koşuda model çıktıları yalnızca kaynak/hedef IP düzeyinde değil, port ve protokol bilgisiyle birlikte denetleyici kararlarıyla karşılaştırılabilmiştir. Bu nedenle run_05, tezde ana çalışma zamanı doğrulama deneyi olarak konumlandırılmalıdır.")
    md.append("")
    md.append("Buna karşılık `run_03_aligned_clean`, ilk başarılı hizalanmış çalışma zamanı doğrulaması olarak destekleyici canonical koşudur. `run_04_repeat_mixed_validation` ise port bilgisinin controller loglarında bulunmaması nedeniyle diagnostic/partial repetition olarak değerlendirilmiştir.")
    md.append("")
    md.append("## 3. Jüri Sorusu: run_04 neden ana sonuçlara dahil edilmedi?")
    md.append("")
    md.append("run_04 tamamen başarısız bir deney değildir; ancak akademik ana sonuç olarak kullanılabilecek kadar temiz değildir. Sorun model tahmininden ziyade, controller loglarında port bilgisinin bulunmaması nedeniyle flow-level exact matching kalitesinin sınırlanmasıdır. Bu nedenle run_04, sistem geliştirme sürecinde port-aware logging ihtiyacını ortaya koyan diagnostic bir koşu olarak raporlanmalıdır.")
    md.append("")
    md.append("Bu ayrım deneysel şeffaflığı artırır: Başarısız veya kısmi koşular gizlenmemekte, fakat ana performans iddiası yalnızca canonical koşular üzerinden kurulmaktadır.")
    md.append("")
    md.append("## 4. Jüri Sorusu: Flow-level eşleşme neden tüm satırlarda birebir değil?")
    md.append("")
    exact_true = summary.get("matched_controller_exact_true")
    exact_total = summary.get("matched_controller_exact_total")
    sec_true = summary.get("security_compatible_action_true")
    sec_total = summary.get("security_compatible_action_total")
    if exact_true is not None:
        md.append(f"Flow-level tabloda exact controller match `{exact_true}/{exact_total}` olarak görünmektedir. Security-compatible action sayısı ise `{sec_true}/{sec_total}` düzeyindedir.")
    else:
        md.append("Flow-level exact match değeri ilgili tabloda bulunamadı.")
    md.append("")
    md.append("Bu durum, model çıktısının hatalı olduğu anlamına doğrudan gelmez. Çünkü model PCAP tabanlı flow özellikleri üzerinden binary veya policy-level öneri üretirken, SDN denetleyicisi akışları zamanlama, polling aralığı, OpenFlow event görünürlüğü, TCP kontrol akışları ve loglama ayrıntılarına bağlı olarak gözlemler. Bu nedenle exact matching yanında security-compatible matching de raporlanmıştır.")
    md.append("")
    md.append("## 5. Jüri Sorusu: Yüksek ML başarımı gerçek zamanlı SDN başarımı anlamına gelir mi?")
    md.append("")
    md.append("Hayır, tek başına gelmez. Offline ML başarımı modelin veri kümesi üzerindeki sınıflandırma kapasitesini gösterir; fakat gerçek zamanlı SDN başarımı şu ek koşullara bağlıdır:")
    md.append("")
    md.append("- eğitim ve çalışma zamanı özelliklerinin aynı semantik yapıya sahip olması,")
    md.append("- feature order ve feature mapping uyumluluğu,")
    md.append("- denetleyici loglarının port/protokol düzeyinde yeterli ayrıntı içermesi,")
    md.append("- model kararının SDN politika aksiyonuna doğru çevrilmesi,")
    md.append("- drop, rate-limit ve quarantine gibi enforcement aksiyonlarının OpenFlow düzeyinde uygulanabilmesi.")
    md.append("")
    md.append("Bu tezdeki önemli katkı, offline model başarımını tek başına raporlamak yerine, model çıktısının SDN controller-side policy ve enforcement davranışıyla ilişkilendirilmesidir.")
    md.append("")
    md.append("## 6. Jüri Sorusu: Bu çalışma IDS mi, IPS mi?")
    md.append("")
    md.append("Çalışma yalnızca IDS olarak değerlendirilmemelidir. Sistem saldırı olasılığını ve policy kararını üretmekte, ardından SDN denetleyicisi üzerinden drop, quarantine_candidate ve rate_limit aksiyonları oluşturabilmektedir. Bu nedenle mimari, IDS bileşenini içeren fakat IPS davranışı da gösteren hibrit IDS/IPS prototipi olarak konumlandırılmalıdır.")
    md.append("")
    md.append("## 7. Güçlü Yönler")
    md.append("")
    md.append("- Offline model başarımı ile çalışma zamanı SDN doğrulaması birlikte ele alınmıştır.")
    md.append("- Canonical ve diagnostic deney koşulları ayrıştırılmıştır.")
    md.append("- Port-aware/protocol-aware flow matching yaklaşımı kullanılmıştır.")
    md.append("- Drop, quarantine ve rate-limit aksiyonları aynı deneysel çerçevede raporlanmıştır.")
    md.append("- Deneysel artifact dosyaları tablo, şekil ve kalite raporlarına dönüştürülmüştür.")
    md.append("")
    md.append("## 8. Sınırlılıklar")
    md.append("")
    md.append("- Deneyler kontrollü Mininet ortamında yürütülmüştür; fiziksel kampüs ağına genelleme için ek testler gerekir.")
    md.append("- Flow-level matching, controller loglarının ayrıntı düzeyine ve zamanlama uyumuna bağlıdır.")
    md.append("- Mevcut model seçilmiş Top-20 özelliklerle çalışmaktadır; daha geniş CIC-DDoS2019 alt kümeleriyle yeniden eğitim ileride yapılmalıdır.")
    md.append("- Controller overhead, CPU/memory kullanımı ve flow rule installation latency ölçümleri daha ayrıntılı bir deney setiyle genişletilebilir.")
    md.append("")
    md.append("## 9. Tez Metnine Eklenebilecek Kısa Savunma Paragrafı")
    md.append("")
    md.append("Bu çalışmada run_05 koşulunun ana deney olarak seçilmesinin nedeni, model çıktıları ile SDN denetleyicisi kararlarının port-aware ve protocol-aware biçimde karşılaştırılmasına olanak sağlamasıdır. run_04 koşulu ise sistem geliştirme sürecinde önemli bir diagnostic tekrar olarak korunmuş, ancak controller loglarında port bilgisinin bulunmaması nedeniyle ana sonuçların hesaplanmasında kullanılmamıştır. Bu ayrım, deneysel sonuçların yalnızca olumlu çıktılar üzerinden değil, gözlemlenebilirlik ve eşleştirme kalitesi açısından da şeffaf biçimde değerlendirilmesini sağlamaktadır.")
    md.append("")
    md.append("## 10. Önerilen Tez Kullanımı")
    md.append("")
    md.append("- Bölüm 4 sonunda çalışma zamanı doğrulama sonuçlarının yorumlanması kısmına kısa savunma paragrafı eklenebilir.")
    md.append("- Bölüm 5’te sınırlılıklar ve literatürle karşılaştırma altına run_04/run_05 ayrımı daha açık bağlanabilir.")
    md.append("- Savunma sunumunda run_03, run_04 ve run_05 için ayrı bir “canonical vs diagnostic” slaytı hazırlanabilir.")

    result = {
        "generated_at_utc": datetime.utcnow().isoformat(),
        "inputs": vars(args),
        "summary": summary,
    }

    Path(args.output_json).write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    Path(args.output_md).write_text("\n".join(md), encoding="utf-8")

    print("[INFO] MD:", args.output_md)
    print("[INFO] JSON:", args.output_json)
    print("[INFO] Summary:", summary)


if __name__ == "__main__":
    main()
