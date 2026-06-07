#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path


def file_size(path: Path) -> str:
    if not path.exists():
        return "missing"
    n = path.stat().st_size
    if n < 1024:
        return f"{n} B"
    if n < 1024 ** 2:
        return f"{n / 1024:.1f} KB"
    return f"{n / 1024 ** 2:.1f} MB"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source-dir",
        default="docs/literature_review/source_files",
        help="Directory containing uploaded source files.",
    )
    parser.add_argument(
        "--output-md",
        default="docs/literature_review/literature_source_inventory.md",
    )
    parser.add_argument(
        "--output-json",
        default="docs/literature_review/literature_source_inventory.json",
    )
    args = parser.parse_args()

    source_dir = Path(args.source_dir)

    sources = [
        {
            "file": "SDN-ML-Security_Referans.bib",
            "type": "BibTeX reference library",
            "thesis_use": "Bölüm 3 literatür taraması için toplu bibliyografik kaynak havuzu.",
            "citation_policy": "Bu dosyadaki makaleler tek tek doğrulandıktan sonra tezde kaynak olarak kullanılmalıdır.",
        },
        {
            "file": "tez1.pdf",
            "type": "External PhD dissertation",
            "thesis_use": "SDN/OpenFlow arka planı, tez organizasyonu, kampüs ölçekli OpenSec güvenlik çerçevesi ve şekil/tablo düzeni için örnek çalışma.",
            "citation_policy": "İlgili fikirler doğrudan kullanılırsa kaynakçada ayrı tez kaydı olarak gösterilmelidir.",
        },
        {
            "file": "Manuscript.docx",
            "type": "Unpublished internal manuscript",
            "thesis_use": "Metaheuristic feature selection + ensemble ML tabanlı IDS modelinin yöntemsel arka planı ve bu tezdeki runtime SDN entegrasyonunun ön çalışması.",
            "citation_policy": "Yayınlanmadan dış kaynak gibi gösterilmemelidir; tez içinde 'önceki/yayın aşamasındaki çalışma' olarak dikkatli kullanılmalıdır.",
        },
    ]

    inventory = []
    for item in sources:
        path = source_dir / item["file"]
        record = dict(item)
        record["path"] = str(path)
        record["exists"] = path.exists()
        record["size"] = file_size(path)
        inventory.append(record)

    output_json = Path(args.output_json)
    output_md = Path(args.output_md)

    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(
        json.dumps(
            {
                "generated_at_utc": datetime.utcnow().isoformat(),
                "source_dir": str(source_dir),
                "sources": inventory,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    lines = []
    lines.append("# Literature Source Inventory")
    lines.append("")
    lines.append(f"- Generated at UTC: `{datetime.utcnow().isoformat()}`")
    lines.append(f"- Source directory: `{source_dir}`")
    lines.append("")
    lines.append("| File | Type | Exists | Size | Thesis Use | Citation Policy |")
    lines.append("|---|---|---|---:|---|---|")

    for r in inventory:
        lines.append(
            f"| `{r['file']}` | {r['type']} | {r['exists']} | {r['size']} | {r['thesis_use']} | {r['citation_policy']} |"
        )

    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append("- BibTeX kayıtları otomatik olarak literatür takip tablosuna aktarılabilir; ancak her kayıt daha sonra manuel olarak doğrulanmalıdır.")
    lines.append("- `tez1.pdf`, tez yapısı ve SDN/OpenFlow/OpenSec tartışması için yararlıdır; doğrudan metin aktarımı yapılmamalı, fikirler yeniden yazılmalı ve kaynak gösterilmelidir.")
    lines.append("- `Manuscript.docx`, henüz yayınlanmadığı için dış literatür gibi değil, çalışmanın önceki/ilişkili araştırma hattı olarak kullanılmalıdır.")
    lines.append("")

    output_md.write_text("\n".join(lines), encoding="utf-8")

    print("[INFO] Written:", output_md)
    print("[INFO] Written:", output_json)


if __name__ == "__main__":
    main()
