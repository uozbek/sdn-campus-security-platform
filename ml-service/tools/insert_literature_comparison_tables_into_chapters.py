#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path


def read_text(path: Path) -> str:
    if not path.exists():
        raise SystemExit(f"[ERROR] Missing file: {path}")
    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def backup_file(path: Path) -> Path:
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    backup = path.with_suffix(path.suffix + f".bak_lit_comparison_{ts}")
    backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    return backup


def append_before_section(text: str, section_marker: str, insertion: str) -> str:
    if insertion.strip() in text:
        return text

    idx = text.find(section_marker)
    if idx == -1:
        return text.rstrip() + "\n\n" + insertion.strip() + "\n"

    return text[:idx].rstrip() + "\n\n" + insertion.strip() + "\n\n" + text[idx:].lstrip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--chapter3-md",
        default="docs/bolum_3_literatur_taramasi_ve_ilgili_calismalar_tr.md",
    )
    parser.add_argument(
        "--chapter5-md",
        default="docs/bolum_5_tartisma_sinirliliklar_gelecek_calismalar_tr.md",
    )
    parser.add_argument(
        "--chapter3-table-md",
        default="docs/literature_review/synthesis/table_chapter3_methodological_comparison.md",
    )
    parser.add_argument(
        "--chapter5-table-md",
        default="docs/literature_review/synthesis/table_chapter5_result_functionality_comparison.md",
    )
    args = parser.parse_args()

    chapter3 = Path(args.chapter3_md)
    chapter5 = Path(args.chapter5_md)
    ch3_table = Path(args.chapter3_table_md)
    ch5_table = Path(args.chapter5_table_md)

    ch3_text = read_text(chapter3)
    ch5_text = read_text(chapter5)
    ch3_table_text = read_text(ch3_table)
    ch5_table_text = read_text(ch5_table)

    ch3_backup = backup_file(chapter3)
    ch5_backup = backup_file(chapter5)

    ch3_insertion = f"""## 3.x. Literatürdeki Çalışmalar ile Bu Tez Çalışmasının Yöntemsel Karşılaştırması

Literatür taramasında incelenen çalışmalar, SDN tabanlı DDoS tespiti, ML/DL tabanlı sınıflandırma, özellik seçimi, çalışma zamanı doğrulama ve aktif önleme mekanizmaları açısından karşılaştırılmıştır. Tablo 3.x, seçili çalışmalar ile bu tez çalışmasını yöntemsel bileşenler bakımından özetlemektedir. Tabloda görüldüğü üzere, mevcut çalışmaların önemli bir kısmı SDN bağlamında yüksek tespit başarısı raporlamakla birlikte, port/protocol-aware controller karşılaştırması ve rate-limit/drop/quarantine aksiyonlarının birlikte doğrulanması daha sınırlı kalmaktadır.

**Tablo 3.x. SDN tabanlı DDoS tespit ve önleme çalışmalarının yöntemsel karşılaştırması**

{ch3_table_text}

Bu karşılaştırma, tez çalışmasının literatürdeki konumunu daha açık hale getirmektedir. Önerilen çalışma, yalnızca makine öğrenmesi tabanlı bir sınıflandırma modeli önermekle kalmamakta; model çıktısını Ryu denetleyicisi, OpenFlow kuralları, port-aware/protocol-aware karar yorumlama ve aktif mitigation aksiyonlarıyla ilişkilendirmektedir.
"""

    ch5_insertion = f"""## 5.x. Mevcut Literatürle Sonuç ve İşlevsellik Açısından Karşılaştırma

Bu bölümde elde edilen runtime validation bulguları, literatürdeki seçili çalışmalarla işlevsel açıdan karşılaştırılmıştır. Tablo 5.x, önerilen sistemin yalnızca sınıflandırma başarısı açısından değil, aynı zamanda SDN denetleyicisiyle bütünleşik çalışma zamanı doğrulama ve aktif mitigation üretimi açısından da değerlendirildiğini göstermektedir. Literatürde birçok çalışma offline veya yarı gerçek zamanlı tespit başarısına odaklanırken, bu tez çalışması model çıktısını OpenFlow tabanlı rate-limit, drop ve quarantine aksiyonlarıyla ilişkilendirmektedir.

**Tablo 5.x. Bu tez çalışmasının mevcut literatürle sonuç ve işlevsellik açısından karşılaştırılması**

{ch5_table_text}

Bu tablo, önerilen yöntemin iki yönlü katkısını göstermektedir. İlk katkı, seçilmiş özellikler kullanan Final XGBoost Top-20 modelinin çalışma zamanı senaryosuna taşınmasıdır. İkinci katkı ise model çıktılarının SDN denetleyicisi üzerinde rate-limit, drop ve quarantine gibi uygulanabilir aksiyonlara dönüştürülmesidir. Bu yönüyle çalışma, yalnızca offline başarı metriklerine değil, SDN tabanlı aktif savunma davranışına da odaklanmaktadır.
"""

    # Bölüm 3'te boşluk/konumlandırma kısmından önce eklemek daha doğru.
    ch3_markers = [
        "## 3.9. Literatürdeki Boşluklar",
        "## 3.10. Bu Tez Çalışmasının Literatürdeki Konumu",
        "## 3.11. Bölüm Özeti",
    ]
    for marker in ch3_markers:
        if marker in ch3_text:
            ch3_text = append_before_section(ch3_text, marker, ch3_insertion)
            break
    else:
        ch3_text = ch3_text.rstrip() + "\n\n" + ch3_insertion.strip() + "\n"

    # Bölüm 5'te sonuç/tartışma kapanışından önce eklemek daha doğru.
    ch5_markers = [
        "## 5.",
        "# Bölüm 6",
    ]

    # Daha güvenli: Bölüm 5'in sonuna ekle; varsa tekrar ekleme.
    if ch5_insertion.strip() not in ch5_text:
        ch5_text = ch5_text.rstrip() + "\n\n" + ch5_insertion.strip() + "\n"

    write_text(chapter3, ch3_text)
    write_text(chapter5, ch5_text)

    print("[INFO] Chapter 3 updated:", chapter3)
    print("[INFO] Chapter 3 backup :", ch3_backup)
    print("[INFO] Chapter 5 updated:", chapter5)
    print("[INFO] Chapter 5 backup :", ch5_backup)


if __name__ == "__main__":
    main()
