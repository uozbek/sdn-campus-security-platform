#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from datetime import datetime
from pathlib import Path


SECTION_PATTERNS = [
    ("Tez Bölümlerinin Sunuş Sırası", r"TEZ BÖLÜMLERİNİN SUNUŞ SIRASI"),
    ("Genel Biçimsel Kurallar", r"GENEL BİÇİMSEL KURALLAR"),
    ("Kâğıt ve Çoğaltma Sistemi", r"Kâğıt ve Çoğaltma Sistemi"),
    ("Sayfa Düzeni", r"Sayfa Düzeni"),
    ("Yazım Şekli", r"Yazım şekli"),
    ("Kenar Boşlukları", r"Kenar boşlukları"),
    ("Yazı Karakteri", r"Yazı Karakteri"),
    ("Satır Aralıkları ve Paragraf Düzeni", r"Satır Aralıkları ve Paragraf Düzeni"),
    ("Bölüm Başlıkları", r"Bölüm Başlıkları"),
    ("Tablolar ve Şekiller", r"Tablo|Şekil"),
    ("Kaynak Gösterme", r"Kaynak"),
    ("Ekler", r"Ekler"),
    ("Özgeçmiş", r"Özgeçmiş"),
]


def clean_line(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def find_windows(lines: list[str], pattern: str, window: int = 35) -> list[str]:
    out = []
    rx = re.compile(pattern, re.IGNORECASE)
    seen = set()

    for i, line in enumerate(lines):
        if rx.search(line):
            start = max(0, i)
            end = min(len(lines), i + window)
            block = "\n".join(lines[start:end]).strip()
            if block not in seen:
                seen.add(block)
                out.append(block)

    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--guide-txt",
        default="docs/thesis_template_sources/fbe_lisansustu_tez_yazim_kilavuzu.txt",
    )
    parser.add_argument(
        "--template-docx",
        default="docs/thesis_template_sources/tez_hazirlama_sablonu.docx",
    )
    parser.add_argument(
        "--output-md",
        default="docs/tez_format_kontrol_kriterleri.md",
    )
    args = parser.parse_args()

    guide = Path(args.guide_txt)
    if not guide.exists():
        raise SystemExit(f"[ERROR] Guide TXT not found: {guide}")

    text = guide.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()

    md = []
    md.append("# SAÜ FBE Tez Format Kontrol Kriterleri")
    md.append("")
    md.append(f"- Generated at UTC: `{datetime.utcnow().isoformat()}`")
    md.append(f"- Kılavuz TXT: `{args.guide_txt}`")
    md.append(f"- Şablon DOCX: `{args.template_docx}`")
    md.append("")
    md.append("Bu dosya, Sakarya Üniversitesi Fen Bilimleri Enstitüsü Lisansüstü Tez Yazım Kılavuzu ve Tez Hazırlama Şablonu esas alınarak hazırlanacak otomatik/yarı otomatik kontrol kriterlerini tanımlar.")
    md.append("")
    md.append("## 1. Kılavuzdan Çıkarılan Ana Bölümler")
    md.append("")

    for title, pattern in SECTION_PATTERNS:
        blocks = find_windows(lines, pattern, window=28)
        md.append(f"### 1.{SECTION_PATTERNS.index((title, pattern)) + 1}. {title}")
        md.append("")
        if not blocks:
            md.append("_Bu başlık için otomatik metin bloğu bulunamadı; manuel kontrol gerekir._")
            md.append("")
            continue

        for b in blocks[:2]:
            cleaned = "\n".join(clean_line(x) for x in b.splitlines() if clean_line(x))
            md.append("```text")
            md.append(cleaned[:3000])
            md.append("```")
            md.append("")

    md.append("## 2. Otomatik Kontrole Dönüştürülecek Kurallar")
    md.append("")
    md.append("| Kontrol Alanı | Otomatik Kontrol Durumu | Not |")
    md.append("|---|---|---|")
    md.append("| Ön bölüm sırası | yapılacak | Dış kapak, iç kapak, onay/beyan, özet, abstract, içindekiler vb. |")
    md.append("| Ana bölüm sırası | kısmen var | Bölüm 1–6 ve kaynakça kontrol edilecek |")
    md.append("| Sayfa boyutu | yapılacak | DOCX section ayarlarından kontrol edilecek |")
    md.append("| Kenar boşlukları | yapılacak | DOCX section margin değerleri kontrol edilecek |")
    md.append("| Yazı tipi/punto | yapılacak | Normal stil ve paragraf run kontrolleri eklenecek |")
    md.append("| Satır aralığı | yapılacak | ParagraphFormat line_spacing kontrolü eklenecek |")
    md.append("| Tablo sayısı ve tablo başlıkları | kısmen var | Tablo nesne sayısı var; başlık konumu eklenecek |")
    md.append("| Şekil sayısı ve şekil başlıkları | kısmen var | Inline shape sayısı var; başlık konumu eklenecek |")
    md.append("| Kaynakça varlığı | yapılacak | Kaynakça başlığı ve referans kayıtları kontrol edilecek |")
    md.append("| Ekler/Özgeçmiş | yapılacak | Nihai tez paketinde kontrol edilecek |")
    md.append("")
    md.append("## 3. Mevcut Tez Yapısı İçin Öncelikli Düzeltme Alanları")
    md.append("")
    md.append("- Tez ön bölümleri şablona göre yeniden düzenlenmeli.")
    md.append("- Tablo ve şekil başlıkları kılavuzdaki konum ve adlandırma kurallarına göre standartlaştırılmalı.")
    md.append("- Kaynakça taslağı APA7 veya kılavuzun belirttiği kaynak gösterme kurallarına göre biçimlendirilmeli.")
    md.append("- DOCX üretim araçları şablondaki stilleri mümkün olduğunca kullanacak şekilde geliştirilmeli.")
    md.append("- Kalite kontrol aracı biçimsel kuralları ayrıca raporlamalı.")
    md.append("")

    out = Path(args.output_md)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(md), encoding="utf-8")

    print("[INFO] Written:", out)


if __name__ == "__main__":
    main()
