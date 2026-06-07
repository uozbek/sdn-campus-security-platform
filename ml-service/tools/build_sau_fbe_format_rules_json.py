#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from docx import Document


def cm(x) -> float:
    return round(float(x.cm), 2)


def style_info(doc: Document, style_name: str) -> dict:
    try:
        st = doc.styles[style_name]
        font = st.font
        return {
            "exists": True,
            "font_name": font.name,
            "font_size_pt": font.size.pt if font.size else None,
            "bold": font.bold,
            "italic": font.italic,
        }
    except Exception:
        return {"exists": False}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--template-docx",
        default="docs/thesis_template_sources/tez_hazirlama_sablonu.docx",
    )
    parser.add_argument(
        "--guide-txt",
        default="docs/thesis_template_sources/fbe_lisansustu_tez_yazim_kilavuzu.txt",
    )
    parser.add_argument(
        "--output-json",
        default="docs/sau_fbe_format_rules.json",
    )
    args = parser.parse_args()

    template = Path(args.template_docx)
    guide = Path(args.guide_txt)

    if not template.exists():
        raise SystemExit(f"[ERROR] Template DOCX not found: {template}")

    doc = Document(template)
    section = doc.sections[0]

    rules = {
        "generated_at_utc": datetime.utcnow().isoformat(),
        "source": {
            "template_docx": str(template),
            "guide_txt": str(guide),
            "guide_basis": "SAÜ FBE Lisansüstü Tez Yazım Kılavuzu, Ağustos 2022; kılavuzda yer almayan konularda APA7 dikkate alınır.",
        },
        "page": {
            "expected_size": "A4",
            "width_cm": cm(section.page_width),
            "height_cm": cm(section.page_height),
        },
        "margins": {
            "top_cm": cm(section.top_margin),
            "bottom_cm": cm(section.bottom_margin),
            "left_cm": cm(section.left_margin),
            "right_cm": cm(section.right_margin),
            "header_distance_cm": cm(section.header_distance),
            "footer_distance_cm": cm(section.footer_distance),
            "tolerance_cm": 0.15,
            "source_note": "Values read from official Tez Hazırlama Şablonu DOCX."
        },
        "styles": {
            "Normal": style_info(doc, "Normal"),
            "Heading 1": style_info(doc, "Heading 1"),
            "Heading 2": style_info(doc, "Heading 2"),
            "Heading 3": style_info(doc, "Heading 3"),
            "Başlık 1": style_info(doc, "Başlık 1"),
            "Başlık 2": style_info(doc, "Başlık 2"),
            "Başlık 3": style_info(doc, "Başlık 3"),
        },
        "required_frontmatter_order": [
            "Dış kapak",
            "İç kapak",
            "Onay sayfası",
            "İthaf sayfası",
            "Teşekkür",
            "İçindekiler",
            "Kısaltmalar",
            "Simgeler",
            "Tablo listesi",
            "Şekil listesi",
            "Özet",
            "Abstract",
        ],
        "required_main_order": [
            "Giriş",
            "Diğer bölümler",
            "Sonuç ve öneriler",
            "Kaynaklar",
            "Ekler",
            "Özgeçmiş",
        ],
        "caption_rules": {
            "table_caption": "Kılavuz 3.6 Tablo ve Şekiller bölümüne göre doğrulanacak.",
            "figure_caption": "Kılavuz 3.6 Tablo ve Şekiller bölümüne göre doğrulanacak."
        },
        "reference_rules": {
            "style": "APA7 basis according to guide preface",
            "note": "Kılavuzda yer almayan konularda APA kuralları dikkate alınır."
        }
    }

    out = Path(args.output_json)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rules, indent=2, ensure_ascii=False), encoding="utf-8")

    print("[INFO] Written:", out)
    print(json.dumps(rules, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
