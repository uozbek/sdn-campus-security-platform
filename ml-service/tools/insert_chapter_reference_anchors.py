#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


INSERTIONS = {
    "docs/bolum_2_kavramsal_kuramsal_arka_plan_tr.md": """
## Bölüm 2 Kaynak Bağlantısı

Bu bölümde verilen kavramsal çerçeve, makine öğrenmesi temelleri, destek vektör makineleri, özellik seçimi, IDS yaklaşımları ve DDoS tespitinde hibrit modelleme literatürüyle ilişkilidir. Bu bağlamda temel makine öğrenmesi ve SVM arka planı [BIB058] ve [BIB018] ile; IDS ve özellik seçimi bağlamı [BIB023], [BIB014] ve [BIB022] ile; SDN tabanlı DDoS savunma bakış açısı ise [BIB041] ile ilişkilendirilmiştir.
""",
    "docs/bolum_3_literatur_taramasi_ve_ilgili_calismalar_tr.md": """
## Bölüm 3 Kaynak Bağlantısı

Bu bölümdeki literatür sentezi, SDN tabanlı DDoS tespit ve önleme çalışmalarını, makine öğrenmesi/derin öğrenme tabanlı IDS yaklaşımlarını, özellik seçimi çalışmalarını ve Ryu/Mininet/OpenFlow tabanlı çalışma zamanı doğrulamalarını birlikte değerlendirmektedir. Sistematik ve kapsamlı SDN-DDoS literatür değerlendirmeleri [LR001], [LR005] ve [BIB041] ile; Ryu denetleyici tabanlı DDoS tespit mimarileri [BIB053] ile; hibrit özellik seçimi ve DDoS tespit yaklaşımları ise [BIB022], [BIB023] ve [BIB039] ile ilişkilendirilmiştir.
""",
    "docs/bolum_5_tartisma_sinirliliklar_gelecek_calismalar_tr.md": """
## Bölüm 5 Kaynak Bağlantısı

Bu bölümde tartışılan bulgular, mevcut literatürdeki offline sınıflandırma odaklı çalışmalar ile SDN denetleyicisi üzerinden aktif önleme davranışı üreten yaklaşımlar arasındaki farkı görünür kılmaktadır. DDoS savunma mekanizmaları ve SDN bağlamı [BIB041] ile; Ryu tabanlı tespit çerçeveleri [BIB053] ile; hibrit özellik seçimi ve DDoS tespit performansı [BIB022] ve [BIB023] ile; IDS yanlış pozitiflerinin azaltılması ise [BIB043] ile ilişkilendirilmiştir.
""",
}


def main() -> None:
    for file, insertion in INSERTIONS.items():
        p = Path(file)
        if not p.exists():
            print("[WARN] Missing:", p)
            continue

        text = p.read_text(encoding="utf-8")
        marker = insertion.strip().splitlines()[0].strip()

        if marker in text:
            print("[INFO] Already exists:", marker, "in", p)
            continue

        backup = p.with_suffix(p.suffix + ".bak_ref_anchors")
        backup.write_text(text, encoding="utf-8")

        p.write_text(text.rstrip() + "\n\n" + insertion.strip() + "\n", encoding="utf-8")
        print("[INFO] Updated:", p)
        print("[INFO] Backup :", backup)


if __name__ == "__main__":
    main()
