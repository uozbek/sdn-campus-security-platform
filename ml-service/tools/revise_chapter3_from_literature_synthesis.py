#!/usr/bin/env python3
from __future__ import annotations

import argparse
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


def has_any(row, terms) -> bool:
    blob = " ".join(clean(v).lower() for v in row.values)
    return any(t.lower() in blob for t in terms)


def pick_records(df: pd.DataFrame, terms: list[str], limit: int = 12) -> pd.DataFrame:
    if df.empty:
        return df

    mask = df.apply(lambda r: has_any(r, terms), axis=1)
    subset = df[mask].copy()

    if subset.empty:
        subset = df.copy()

    def rel_rank(x):
        x = clean(x)
        return {"High": 0, "Medium": 1, "Low": 2, "": 3}.get(x, 3)

    if "relevance_to_this_thesis" in subset.columns:
        subset["_rel_rank"] = subset["relevance_to_this_thesis"].apply(rel_rank)
    else:
        subset["_rel_rank"] = 3

    if "year" in subset.columns:
        subset["_year_int"] = pd.to_numeric(subset["year"], errors="coerce").fillna(0).astype(int)
    else:
        subset["_year_int"] = 0

    subset = subset.sort_values(by=["_rel_rank", "_year_int"], ascending=[True, False])
    return subset.head(limit).drop(columns=[c for c in ["_rel_rank", "_year_int"] if c in subset.columns])


def short_citation_list(df: pd.DataFrame) -> str:
    items = []
    for _, r in df.iterrows():
        rid = clean(r.get("id", ""))
        year = clean(r.get("year", ""))
        title = clean(r.get("title", ""))
        if not title:
            continue
        if len(title) > 90:
            title = title[:87] + "..."
        items.append(f"- `{rid}` ({year}) — {title}")
    return "\n".join(items) if items else "- Bu kategori için kaynak manuel olarak seçilmelidir."


def table_md(df: pd.DataFrame, limit: int = 10) -> str:
    cols = [
        "id", "year", "title", "dataset", "ml_dl_model",
        "real_time_or_offline", "mitigation_action",
        "relevance_to_this_thesis"
    ]
    cols = [c for c in cols if c in df.columns]
    tmp = df[cols].head(limit).copy()

    for c in tmp.columns:
        tmp[c] = tmp[c].astype(str).replace("nan", "")
        tmp[c] = tmp[c].apply(lambda x: x[:100] + "..." if len(x) > 100 else x)

    if tmp.empty:
        return "_No records._"
    return tmp.to_markdown(index=False)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--synthesis-csv",
        default="docs/literature_review/synthesis/chapter3_literature_synthesis_candidates.csv",
    )
    parser.add_argument(
        "--output-md",
        default="docs/bolum_3_literatur_taramasi_ve_ilgili_calismalar_tr_literature_supported.md",
    )
    parser.add_argument(
        "--summary-output",
        default="docs/literature_review/synthesis/chapter3_revision_source_summary.md",
    )
    args = parser.parse_args()

    synthesis_csv = Path(args.synthesis_csv)
    output_md = Path(args.output_md)
    summary_output = Path(args.summary_output)

    if not synthesis_csv.exists():
        raise SystemExit(f"[ERROR] Missing synthesis CSV: {synthesis_csv}")

    df = pd.read_csv(synthesis_csv).fillna("")

    sdn_ddos = pick_records(df, ["sdn", "software-defined", "software defined", "openflow", "ddos"], 15)
    ml_dl = pick_records(df, ["machine learning", "deep learning", "xgboost", "random forest", "svm", "lstm", "cnn", "ensemble"], 15)
    feature_selection = pick_records(df, ["feature selection", "metaheuristic", "pso", "gwo", "hho", "dfo", "pca"], 10)
    runtime = pick_records(df, ["runtime", "real-time", "real time", "controller", "ryu", "mininet", "openflow", "open vswitch", "ovs"], 12)
    mitigation = pick_records(df, ["mitigation", "prevention", "drop", "rate-limit", "rate limit", "quarantine", "reroute"], 12)
    datasets = pick_records(df, ["cic-ddos2019", "cicddos2019", "cicids", "insdn", "nsl-kdd", "unsw-nb15", "dataset"], 12)

    md = []
    md.append("# Bölüm 3. Literatür Taraması ve İlgili Çalışmalar")
    md.append("")
    md.append(f"_Bu taslak literatür sentez tablosundan otomatik olarak desteklenmiştir. Üretim zamanı: `{datetime.utcnow().isoformat()}`_")
    md.append("")
    md.append("## 3.1. Bölüme Genel Bakış")
    md.append("")
    md.append(
        "Bu bölümde, yazılım tanımlı ağlarda DDoS saldırılarının makine öğrenmesi ve derin öğrenme yöntemleriyle "
        "tespit edilmesi, SDN denetleyicisiyle bütünleşik önleme mekanizmaları ve çalışma zamanı doğrulama yaklaşımları "
        "incelenmektedir. Literatür taraması, bu tez çalışmasının yalnızca çevrimdışı bir sınıflandırma yaklaşımı değil, "
        "aynı zamanda SDN denetleyicisiyle bütünleşik aktif IDS/IPS prototipi olarak konumlandırılmasını destekleyecek "
        "şekilde yapılandırılmıştır."
    )
    md.append("")
    md.append(
        "Hazırlanan literatür havuzunda 67 aday kaynak yer almakta; bu kaynakların tamamı SDN, DDoS veya OpenFlow "
        "bağlamıyla ilişkili görünmektedir. Bunun yanında 42 çalışma ML/DL tabanlı yaklaşımlarla, 21 çalışma veri kümesi "
        "kullanımıyla, 9 çalışma runtime/controller/testbed bağlamıyla ve 8 çalışma mitigation/prevention bağlamıyla "
        "ilişkilendirilmiştir. Bu dağılım, literatürde tespit odaklı çalışmaların daha yoğun olduğunu; buna karşılık "
        "denetleyiciyle bütünleşik runtime enforcement çalışmalarının daha sınırlı kaldığını göstermektedir."
    )
    md.append("")
    md.append("## 3.2. Literatür Tarama ve Sınıflandırma Yaklaşımı")
    md.append("")
    md.append(
        "Literatür taramasında SDN tabanlı DDoS tespiti, makine öğrenmesi, derin öğrenme, özellik seçimi, Mininet/Ryu/OpenFlow "
        "tabanlı deneysel kurulumlar ve aktif mitigation mekanizmaları ana sınıflandırma eksenleri olarak belirlenmiştir. "
        "Kaynaklar; kullanılan veri kümesi, model türü, test ortamı, runtime/offline ayrımı ve önleme aksiyonu içerip "
        "içermemesi bakımından karşılaştırılmıştır."
    )
    md.append("")
    md.append("## 3.3. SDN Tabanlı DDoS Tespit Çalışmaları")
    md.append("")
    md.append(
        "SDN mimarisi, kontrol düzlemi ile veri düzlemini ayırdığı için ağ trafiğinin merkezi biçimde gözlemlenmesine ve "
        "programlanabilir güvenlik politikalarının uygulanmasına olanak sağlar. Bu nedenle DDoS saldırılarının tespiti "
        "için flow statistics, OpenFlow mesajları, port istatistikleri ve denetleyici gözlemleri literatürde sık kullanılan "
        "veri kaynaklarıdır. Literatür havuzundaki SDN/DDoS/OpenFlow odaklı çalışmalar, bu genel yaklaşımın farklı veri "
        "kümeleri, modeller ve testbed yapılarıyla uygulandığını göstermektedir."
    )
    md.append("")
    md.append("Bu alt başlık için öne çıkan kaynaklar:")
    md.append("")
    md.append(short_citation_list(sdn_ddos))
    md.append("")
    md.append("### Tablo 3.1. SDN/DDoS/OpenFlow Odaklı Seçilmiş Çalışmalar")
    md.append("")
    md.append(table_md(sdn_ddos, 10))
    md.append("")
    md.append("## 3.4. Makine Öğrenmesi ve Derin Öğrenme Tabanlı IDS Yaklaşımları")
    md.append("")
    md.append(
        "Makine öğrenmesi ve derin öğrenme tabanlı çalışmalar, ağ trafiğinden çıkarılan özellikler üzerinden benign ve saldırı "
        "akışlarını ayırt etmeyi hedefler. Literatürde Random Forest, SVM, Decision Tree, XGBoost, ensemble learning, LSTM, "
        "CNN ve autoencoder gibi modellerin farklı veri kümeleri üzerinde değerlendirildiği görülmektedir. Bu çalışmaların "
        "önemli bir bölümü yüksek sınıflandırma başarısı raporlamakla birlikte, modelin SDN denetleyicisiyle çalışma zamanı "
        "bütünleşmesi her zaman ayrıntılı olarak ele alınmamaktadır."
    )
    md.append("")
    md.append("Bu alt başlık için öne çıkan kaynaklar:")
    md.append("")
    md.append(short_citation_list(ml_dl))
    md.append("")
    md.append("### Tablo 3.2. ML/DL Tabanlı Seçilmiş IDS Çalışmaları")
    md.append("")
    md.append(table_md(ml_dl, 10))
    md.append("")
    md.append("## 3.5. Özellik Seçimi ve Hafif Model Tasarımları")
    md.append("")
    md.append(
        "SDN tabanlı runtime IDS/IPS sistemlerinde yalnızca model doğruluğu değil, özellik çıkarım maliyeti ve inference süresi de "
        "kritiktir. Bu nedenle özellik seçimi, modelin çalışma zamanı uygulanabilirliği açısından önemli bir konudur. "
        "Metaheuristic feature selection, top-k feature selection, PCA ve benzeri yaklaşımlar, modelin daha az sayıda özellik ile "
        "çalışmasını sağlayarak denetleyici ve model servisi üzerindeki yükü azaltabilir."
    )
    md.append("")
    md.append(
        "Bu tez çalışmasında kullanılan Final XGBoost Top-20 yaklaşımı da bu bağlama yerleşmektedir. Amaç, CIC-DDoS2019 uyumlu "
        "özellikler arasından daha az sayıda fakat ayırt edici özelliği kullanarak runtime pipeline içinde uygulanabilir bir "
        "model elde etmektir."
    )
    md.append("")
    md.append("Bu alt başlık için öne çıkan kaynaklar:")
    md.append("")
    md.append(short_citation_list(feature_selection))
    md.append("")
    md.append("### Tablo 3.3. Özellik Seçimi Odaklı Seçilmiş Çalışmalar")
    md.append("")
    md.append(table_md(feature_selection, 10))
    md.append("")
    md.append("## 3.6. Runtime, Controller ve Testbed Entegrasyonu")
    md.append("")
    md.append(
        "SDN güvenliği çalışmalarında Mininet, Ryu, OpenFlow ve Open vSwitch tabanlı deneysel ortamlar sık kullanılmaktadır. "
        "Bu araçlar, kontrollü saldırı senaryoları üretmek, flow-level istatistik toplamak ve denetleyici taraflı karar "
        "mekanizmalarını test etmek için uygundur. Buna rağmen literatürdeki birçok çalışmanın offline veri kümesi değerlendirmesi "
        "ile sınırlı kaldığı; model çıktısının gerçek zamanlı veya yarı gerçek zamanlı denetleyici aksiyonlarına nasıl bağlandığını "
        "ayrıntılı göstermediği görülmektedir."
    )
    md.append("")
    md.append("Bu alt başlık için öne çıkan kaynaklar:")
    md.append("")
    md.append(short_citation_list(runtime))
    md.append("")
    md.append("### Tablo 3.4. Runtime/Controller/Testbed Odaklı Seçilmiş Çalışmalar")
    md.append("")
    md.append(table_md(runtime, 10))
    md.append("")
    md.append("## 3.7. SDN Tabanlı Önleme ve Mitigation Yaklaşımları")
    md.append("")
    md.append(
        "DDoS tespitinin güvenlik açısından anlamlı hale gelebilmesi için tespit sonucunun ağ üzerinde uygulanabilir önleme "
        "aksiyonlarına dönüştürülmesi gerekir. Literatürde drop, rate-limit, reroute, quarantine veya blacklist gibi aksiyonlar "
        "farklı biçimlerde ele alınmaktadır. Ancak bu aksiyonların aynı çalışma zamanı prototipi içinde birlikte değerlendirilmesi "
        "ve model-controller uyumunun flow-level olarak gösterilmesi daha sınırlı bir araştırma alanıdır."
    )
    md.append("")
    md.append(
        "Bu tez çalışması bu noktada literatürdeki boşluğa odaklanmaktadır. Canonical runtime validation sürecinde rate-limit, "
        "drop ve quarantine aksiyonları aynı port-aware/protocol-aware deney zinciri içinde gözlemlenmiştir."
    )
    md.append("")
    md.append("Bu alt başlık için öne çıkan kaynaklar:")
    md.append("")
    md.append(short_citation_list(mitigation))
    md.append("")
    md.append("### Tablo 3.5. Mitigation/Prevention Odaklı Seçilmiş Çalışmalar")
    md.append("")
    md.append(table_md(mitigation, 10))
    md.append("")
    md.append("## 3.8. Veri Kümeleri ve Deneysel Değerlendirme")
    md.append("")
    md.append(
        "DDoS tespit çalışmalarında CIC-DDoS2019, CICIDS, InSDN, NSL-KDD, UNSW-NB15 ve özel oluşturulmuş veri kümeleri gibi "
        "farklı kaynaklar kullanılmaktadır. Veri kümesi seçimi, modelin saldırı tiplerini öğrenme kapasitesini ve çalışma zamanı "
        "ortamına aktarılabilirliğini doğrudan etkiler. SDN bağlamı içeren veri kümeleri, denetleyici ve flow-level güvenlik "
        "analizi açısından daha uygun olabilir; ancak klasik IDS veri kümeleri de model karşılaştırması için yaygın olarak kullanılmaktadır."
    )
    md.append("")
    md.append("Bu alt başlık için öne çıkan kaynaklar:")
    md.append("")
    md.append(short_citation_list(datasets))
    md.append("")
    md.append("### Tablo 3.6. Veri Kümesi Odaklı Seçilmiş Çalışmalar")
    md.append("")
    md.append(table_md(datasets, 10))
    md.append("")
    md.append("## 3.9. Literatürdeki Boşluklar")
    md.append("")
    md.append("Literatür sentezinden hareketle aşağıdaki boşluklar öne çıkmaktadır:")
    md.append("")
    md.append("- Çalışmaların önemli bir bölümü offline classification başarısına odaklanmakta, runtime SDN denetleyici entegrasyonunu sınırlı ele almaktadır.")
    md.append("- Model çıktısının OpenFlow tabanlı aksiyonlara nasıl dönüştürüldüğü her çalışmada açık değildir.")
    md.append("- Port-aware ve protocol-aware flow-level eşleştirme çoğu çalışmada ayrıntılı tartışılmamaktadır.")
    md.append("- Rate-limit, drop ve quarantine aksiyonlarının aynı prototip içinde birlikte değerlendirildiği çalışmalar sınırlıdır.")
    md.append("- Controller overhead, inference latency, flow-stat polling maliyeti ve OpenFlow kural kurulum gecikmesi çoğu çalışmada ikincil düzeyde kalmaktadır.")
    md.append("")
    md.append("## 3.10. Bu Tez Çalışmasının Literatürdeki Konumu")
    md.append("")
    md.append(
        "Bu tez çalışması, literatürdeki offline ML tabanlı DDoS tespit yaklaşımları ile SDN tabanlı aktif IPS yaklaşımları arasında "
        "bir köprü kurmaktadır. Önerilen sistem; Final XGBoost Top-20 modeli, FastAPI inference servisi, PCAP tabanlı runtime feature "
        "extraction, Ryu tabanlı policy engine ve OpenFlow tabanlı enforcement mekanizmalarını bir arada kullanmaktadır."
    )
    md.append("")
    md.append(
        "Çalışmanın ayırt edici yönü, model çıktılarının port-aware ve protocol-aware biçimde controller loglarıyla karşılaştırılmasıdır. "
        "Bu sayede aynı kaynak-hedef IP çifti üzerindeki benign TCP, benign UDP, malicious UDP ve quarantine-observed akışlar birbirinden "
        "ayrılabilmektedir. Canonical run_05 deneyinde rate-limit, drop ve quarantine aksiyonlarının gözlenmesi, önerilen sistemin pasif "
        "IDS yerine aktif SDN tabanlı IDS/IPS prototipi olarak konumlandırılabileceğini göstermektedir."
    )
    md.append("")
    md.append("## 3.11. Bölüm Özeti")
    md.append("")
    md.append(
        "Bu bölümde SDN tabanlı DDoS tespiti ve önleme literatürü, ML/DL yaklaşımları, özellik seçimi, runtime/controller entegrasyonu, "
        "mitigation/prevention ve veri kümesi kullanımı açısından değerlendirilmiştir. Literatür sentezi, bu tez çalışmasının temel "
        "katkısının makine öğrenmesi tabanlı tespiti çalışma zamanı SDN denetleyici aksiyonlarına bağlayan port-aware/protocol-aware "
        "aktif IDS/IPS zinciri olduğunu göstermektedir."
    )
    md.append("")

    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text("\n".join(md), encoding="utf-8")

    summary = []
    summary.append("# Chapter 3 Revision Source Summary")
    summary.append("")
    summary.append(f"- Generated at UTC: `{datetime.utcnow().isoformat()}`")
    summary.append(f"- Source synthesis CSV: `{synthesis_csv}`")
    summary.append("")
    summary.append("| Category | Selected Records |")
    summary.append("|---|---:|")
    summary.append(f"| SDN/DDoS/OpenFlow | {len(sdn_ddos)} |")
    summary.append(f"| ML/DL | {len(ml_dl)} |")
    summary.append(f"| Feature selection | {len(feature_selection)} |")
    summary.append(f"| Runtime/controller/testbed | {len(runtime)} |")
    summary.append(f"| Mitigation/prevention | {len(mitigation)} |")
    summary.append(f"| Dataset | {len(datasets)} |")
    summary.append("")
    summary.append("## Notes")
    summary.append("")
    summary.append("- Bu otomatik taslak, kaynakları kategori düzeyinde yerleştirir.")
    summary.append("- Nihai tez metninde her iddia için BibTeX kaynaklarından doğru atıf formatı eklenmelidir.")
    summary.append("- Full-text incelemesi yapılmadan kesin metrik/model iddiaları sert biçimde yazılmamalıdır.")
    summary.append("")

    summary_output.parent.mkdir(parents=True, exist_ok=True)
    summary_output.write_text("\n".join(summary), encoding="utf-8")

    print("[INFO] Written:", output_md)
    print("[INFO] Written:", summary_output)
    print("[INFO] Records:", len(df))


if __name__ == "__main__":
    main()
