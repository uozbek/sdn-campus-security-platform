#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from datetime import datetime
import pandas as pd


def clean(s):
    return str(s or "").strip()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--plan-csv",
        default="docs/literature_review/zotero_clean/chapter_3_5_fulltext_revision_plan.csv",
    )
    parser.add_argument(
        "--output-md",
        default="docs/literature_review/zotero_clean/chapter_5_fulltext_discussion_revision.md",
    )
    parser.add_argument(
        "--output-csv",
        default="docs/literature_review/zotero_clean/chapter_5_fulltext_discussion_revision.csv",
    )
    args = parser.parse_args()

    plan_path = Path(args.plan_csv)
    if not plan_path.exists():
        raise SystemExit(f"[ERROR] Missing plan CSV: {plan_path}")

    df = pd.read_csv(plan_path).fillna("")

    b5 = df[df["chapter_5_discussion_use"].astype(str).str.strip().ne("")].copy()
    b5["priority_score_num"] = pd.to_numeric(b5["priority_score"], errors="coerce").fillna(0)
    b5 = b5.sort_values(["priority_score_num", "year"], ascending=[False, False])

    rows = []
    for _, r in b5.iterrows():
        use = clean(r.get("chapter_5_discussion_use", ""))
        title = clean(r.get("title", ""))
        key = clean(r.get("zotero_key", ""))
        year = clean(r.get("year", ""))
        score = clean(r.get("priority_score", ""))

        theme = []
        u = use.lower()
        if "mitigation" in u or "prevention" in u:
            theme.append("mitigation/prevention gap")
        if "runtime" in u or "latency" in u or "online" in u:
            theme.append("runtime validation gap")
        if "controller" in u or "testbed" in u:
            theme.append("controller/testbed integration")
        if "accuracy" in u or "fpr" in u or "far" in u or "yanlış pozitif" in u:
            theme.append("metric interpretation")
        if "veri seti" in u or "genellenebilirlik" in u:
            theme.append("dataset/generalizability")

        if not theme:
            theme.append("supporting discussion")

        rows.append({
            "zotero_key": key,
            "year": year,
            "priority_score": score,
            "discussion_theme": "; ".join(sorted(set(theme))),
            "chapter_5_discussion_use": use,
            "title": title,
            "suggested_use_sentence": (
                f"{key} kaynağı, Bölüm 5'te {', '.join(sorted(set(theme)))} "
                f"başlığı altında literatürle karşılaştırmalı tartışmayı güçlendirmek için kullanılabilir."
            ),
        })

    out = pd.DataFrame(rows)
    Path(args.output_csv).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.output_csv, index=False)

    theme_counts = {}
    for val in out["discussion_theme"]:
        for t in str(val).split("; "):
            if t:
                theme_counts[t] = theme_counts.get(t, 0) + 1

    md = []
    md.append("# Chapter 5 Full Text Discussion Revision")
    md.append("")
    md.append(f"- Generated at UTC: `{datetime.utcnow().isoformat()}`")
    md.append(f"- Input plan CSV: `{args.plan_csv}`")
    md.append(f"- Output CSV: `{args.output_csv}`")
    md.append(f"- Candidate count: `{len(out)}`")
    md.append("")
    md.append("## 1. Tema Dağılımı")
    md.append("")
    md.append("| Tema | Kaynak sayısı |")
    md.append("|---|---:|")
    for k, v in sorted(theme_counts.items()):
        md.append(f"| {k} | {v} |")

    md.append("")
    md.append("## 2. Bölüm 5 İçin Önerilen Revizyon Eksenleri")
    md.append("")
    md.append("### 2.1. Detection-only literatür ile mitigation/prevention odaklı çalışmaların ayrımı")
    md.append("")
    md.append(
        "Bölüm 5'te, literatürdeki çalışmaların önemli bir kısmının yüksek sınıflandırma başarımı "
        "raporlamasına rağmen tespit çıktısını ağ denetleyicisi üzerinde uygulanabilir bir önleme politikasına "
        "dönüştürme düzeyinin sınırlı kaldığı vurgulanmalıdır. Bu tez, model çıktısını OpenFlow tabanlı "
        "`drop`, `rate-limit` ve `quarantine` gibi aksiyonlara dönüştürerek detection-only çizgiden ayrılmaktadır."
    )
    md.append("")
    md.append("### 2.2. Offline sınıflandırma başarımı ile runtime SDN davranışı arasındaki boşluk")
    md.append("")
    md.append(
        "Full text sinyalleri, birçok çalışmada model başarımının accuracy, F1 veya AUC gibi metriklerle "
        "değerlendirildiğini; ancak controller-side gecikme, flow rule uygulama süresi, runtime inference "
        "ve ağ davranışı üzerindeki etkilerin daha sınırlı ele alındığını göstermektedir. Bölüm 5'te bu boşluk, "
        "tez çalışmasının temel motivasyonlarından biri olarak daha açık kurulmalıdır."
    )
    md.append("")
    md.append("### 2.3. Controller/testbed entegrasyonu ve pratik uygulanabilirlik")
    md.append("")
    md.append(
        "Ryu, Mininet, OpenFlow veya benzeri testbed sinyali taşıyan çalışmalar, tezdeki çalışma zamanı "
        "doğrulama yaklaşımıyla karşılaştırılmalıdır. Burada amaç, yalnızca SDN ortamı kullanan çalışmaları "
        "listelemek değil; bu çalışmaların IDS kararını gerçekten IPS aksiyonuna dönüştürüp dönüştürmediğini "
        "ve runtime ölçüm sağlayıp sağlamadığını tartışmaktır."
    )
    md.append("")
    md.append("### 2.4. Accuracy dışı metriklerin önemi")
    md.append("")
    md.append(
        "Bölüm 5'te accuracy merkezli değerlendirme yaklaşımının IDS/IPS bağlamında tek başına yeterli "
        "olmadığı vurgulanmalıdır. Yanlış pozitifler, SDN tabanlı önleme sistemlerinde yanlış akış engelleme, "
        "meşru kullanıcı trafiğinin kesilmesi veya gereksiz controller aksiyonu üretme gibi operasyonel "
        "sonuçlara yol açabileceği için FPR/FAR, F1 ve AUC gibi metriklerin birlikte değerlendirilmesi gerekir."
    )
    md.append("")
    md.append("### 2.5. Veri seti güncelliği ve genellenebilirlik")
    md.append("")
    md.append(
        "NSL-KDD bu tezde deneysel veri seti olarak kullanılmamalıdır. Bu veri seti yalnızca klasik IDS "
        "literatüründe tarihsel bir örnek olarak, gerekli görülürse çok kısa biçimde anılmalıdır. Tezin veri "
        "seti yönelimi CIC-DDoS2019 ve CICFlowMeter-style akış özellikleri üzerinde tutulmalıdır."
    )
    md.append("")
    md.append("## 3. Bölüm 5'e Eklenebilecek Taslak Paragraf")
    md.append("")
    md.append(
        "Literatürdeki SDN tabanlı DDoS tespit çalışmalarının önemli bir bölümü, sınıflandırma başarımını "
        "accuracy, F1-score, AUC veya yanlış pozitif oranı gibi metrikler üzerinden değerlendirmektedir. "
        "Bu değerlendirme yaklaşımı model karşılaştırması açısından yararlı olmakla birlikte, SDN tabanlı "
        "bir IDS/IPS sisteminin pratik değerini tek başına açıklamakta sınırlı kalmaktadır. Çünkü çalışma "
        "zamanı ortamında model çıktısının denetleyici politikalarına nasıl dönüştürüldüğü, OpenFlow kurallarının "
        "hangi gecikmeyle uygulandığı, yanlış pozitif kararların meşru trafiği nasıl etkileyebileceği ve sistemin "
        "drop, rate-limit veya quarantine gibi aksiyonları hangi koşullarda ürettiği ayrıca değerlendirilmelidir. "
        "Bu tez çalışması, çevrimdışı model başarımını Ryu denetleyici, FastAPI tabanlı çıkarım servisi ve "
        "OpenFlow tabanlı önleme aksiyonlarıyla ilişkilendirerek literatürdeki detection-only yaklaşımlardan "
        "ayrılmaktadır."
    )
    md.append("")
    md.append("## 4. Kaynak Bazlı Kullanım Planı")
    md.append("")
    md.append("| Key | Year | Score | Tema | Kullanım | Title |")
    md.append("|---|---:|---:|---|---|---|")
    for _, r in out.iterrows():
        title = clean(r["title"]).replace("|", "\\|")
        theme = clean(r["discussion_theme"]).replace("|", "\\|")
        use = clean(r["chapter_5_discussion_use"]).replace("|", "\\|")
        md.append(f"| {r['zotero_key']} | {r['year']} | {r['priority_score']} | {theme[:100]} | {use[:180]} | {title[:120]} |")

    md.append("")
    md.append("## 5. Uygulama Notu")
    md.append("")
    md.append(
        "Bu dosya doğrudan tez metnini değiştirmez. Önce Bölüm 5 metninde hangi alt başlığın güçlendirileceği "
        "seçilmeli, ardından yukarıdaki taslak paragraf tez bağlamına göre uyarlanarak eklenmelidir."
    )

    Path(args.output_md).write_text("\n".join(md), encoding="utf-8")

    print("[INFO] Candidate count:", len(out))
    print("[INFO] Theme counts:", theme_counts)
    print("[INFO] CSV:", args.output_csv)
    print("[INFO] MD:", args.output_md)


if __name__ == "__main__":
    main()
