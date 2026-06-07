#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path


CHAPTER_FILES = [
    "docs/bolum_1_giris_tr.md",
    "docs/bolum_2_kavramsal_kuramsal_arka_plan_tr.md",
    "docs/bolum_3_literatur_taramasi_ve_ilgili_calismalar_tr.md",
    "docs/bolum_4_yontem_ve_runtime_dogrulama_tr.md",
    "docs/bolum_5_tartisma_sinirliliklar_gelecek_calismalar_tr.md",
    "docs/bolum_6_sonuc_ve_oneriler_tr.md",
]


ACADEMIC_SIGNAL_TERMS = [
    "bu tez",
    "bu çalışma",
    "önerilen",
    "katkı",
    "literatür",
    "deney",
    "bulgu",
    "sonuç",
    "sınırlılık",
    "gelecek çalışma",
    "yöntem",
    "model",
    "doğrulama",
    "runtime",
    "çalışma zamanı",
]

THESIS_DOMAIN_TERMS = [
    "sdn",
    "yazılım tanımlı ağ",
    "ddos",
    "ids",
    "ips",
    "makine öğrenmesi",
    "derin öğrenme",
    "ryu",
    "mininet",
    "openflow",
    "cic-ddos2019",
    "cicddos2019",
    "feature selection",
    "özellik seçimi",
    "rate-limit",
    "drop",
    "quarantine",
    "karantina",
]

WEAK_SIGNAL_PATTERNS = [
    r"\bTODO\b",
    r"\bXXX\b",
    r"eksik",
    r"buraya",
    r"daha sonra",
    r"kontrol edilecek",
    r"TODO_",
]


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def count_refs(text: str) -> int:
    patterns = [
        r"\[BIB\d{3}\]",
        r"\[LR\d{3}\]",
        r"\[MAN\d{3}\]",
        r"\([A-ZÇĞİÖŞÜa-zçğıöşü\-]+ et al\.,?\s*\d{4}\)",
        r"\([A-ZÇĞİÖŞÜa-zçğıöşü\-]+ vd\.,?\s*\d{4}\)",
    ]
    return sum(len(re.findall(p, text)) for p in patterns)


def count_headings(text: str) -> int:
    return len(re.findall(r"^#{1,6}\s+", text, flags=re.MULTILINE))


def count_tables(text: str) -> int:
    return len(re.findall(r"^\|.*\|$", text, flags=re.MULTILINE))


def count_caption_mentions(text: str) -> dict:
    return {
        "tablo": len(re.findall(r"\bTablo\s+\d+", text, flags=re.IGNORECASE)),
        "sekil": len(re.findall(r"\bŞekil\s+\d+", text, flags=re.IGNORECASE)),
    }


def term_hits(text: str, terms: list[str]) -> list[str]:
    low = text.lower()
    return [t for t in terms if t.lower() in low]


def weak_hits(text: str) -> list[str]:
    hits = []
    for p in WEAK_SIGNAL_PATTERNS:
        if re.search(p, text, flags=re.IGNORECASE):
            hits.append(p)
    return hits


def paragraph_count(text: str) -> int:
    parts = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    return len(parts)


def word_count(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text, flags=re.UNICODE))


def score_chapter(metrics: dict) -> tuple[str, list[str]]:
    issues = []

    if metrics["word_count"] < 800:
        issues.append("word_count_low")
    if metrics["heading_count"] < 3:
        issues.append("heading_count_low")
    if metrics["domain_signal_count"] < 4:
        issues.append("domain_signal_low")
    if metrics["academic_signal_count"] < 4:
        issues.append("academic_signal_low")
    if metrics["weak_hit_count"] > 0:
        issues.append("weak_placeholder_or_todo_signal")
    if metrics["reference_count"] == 0 and metrics["chapter_no"] in [2, 3, 5]:
        issues.append("expected_references_missing")

    status = "ok" if not issues else "check"
    return status, issues


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-md",
        default="docs/chapter_academic_quality_report.md",
    )
    parser.add_argument(
        "--output-json",
        default="docs/chapter_academic_quality_report.json",
    )
    args = parser.parse_args()

    rows = []

    for idx, f in enumerate(CHAPTER_FILES, start=1):
        path = Path(f)
        text = read_text(path)

        academic_hits = term_hits(text, ACADEMIC_SIGNAL_TERMS)
        domain_hits = term_hits(text, THESIS_DOMAIN_TERMS)
        wh = weak_hits(text)
        caps = count_caption_mentions(text)

        metrics = {
            "chapter_no": idx,
            "file": f,
            "exists": path.exists(),
            "size_kb": round(path.stat().st_size / 1024, 1) if path.exists() else 0,
            "word_count": word_count(text),
            "paragraph_count": paragraph_count(text),
            "heading_count": count_headings(text),
            "markdown_table_line_count": count_tables(text),
            "reference_count": count_refs(text),
            "table_caption_mentions": caps["tablo"],
            "figure_caption_mentions": caps["sekil"],
            "academic_signal_count": len(academic_hits),
            "domain_signal_count": len(domain_hits),
            "weak_hit_count": len(wh),
            "academic_hits": academic_hits,
            "domain_hits": domain_hits,
            "weak_hits": wh,
        }

        status, issues = score_chapter(metrics)
        metrics["status"] = status
        metrics["issues"] = issues
        rows.append(metrics)

    result = {
        "generated_at_utc": datetime.utcnow().isoformat(),
        "chapters": rows,
        "summary": {
            "chapter_count": len(rows),
            "ok": sum(1 for r in rows if r["status"] == "ok"),
            "check": sum(1 for r in rows if r["status"] != "ok"),
        },
    }

    out_json = Path(args.output_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    md = []
    md.append("# Bölüm Bazlı Akademik İçerik Kalite Kontrol Raporu")
    md.append("")
    md.append(f"- Generated at UTC: `{result['generated_at_utc']}`")
    md.append(f"- Chapter count: `{result['summary']['chapter_count']}`")
    md.append(f"- OK: `{result['summary']['ok']}`")
    md.append(f"- Check: `{result['summary']['check']}`")
    md.append("")
    md.append("## 1. Bölüm Özeti")
    md.append("")
    md.append("| Bölüm | Dosya | Kelime | Başlık | Referans | Tablo Atfı | Şekil Atfı | Akademik Sinyal | Alan Sinyali | Durum | Sorunlar |")
    md.append("|---:|---|---:|---:|---:|---:|---:|---:|---:|---|---|")

    for r in rows:
        md.append(
            f"| {r['chapter_no']} | `{r['file']}` | {r['word_count']} | {r['heading_count']} | "
            f"{r['reference_count']} | {r['table_caption_mentions']} | {r['figure_caption_mentions']} | "
            f"{r['academic_signal_count']} | {r['domain_signal_count']} | {r['status']} | {', '.join(r['issues'])} |"
        )

    md.append("")
    md.append("## 2. Bölüm Bazlı Detaylar")
    md.append("")

    for r in rows:
        md.append(f"### Bölüm {r['chapter_no']}")
        md.append("")
        md.append(f"- Dosya: `{r['file']}`")
        md.append(f"- Durum: `{r['status']}`")
        md.append(f"- Sorunlar: `{r['issues']}`")
        md.append(f"- Akademik sinyal terimleri: `{', '.join(r['academic_hits'])}`")
        md.append(f"- Alan sinyal terimleri: `{', '.join(r['domain_hits'])}`")
        md.append(f"- Zayıf/TODO sinyalleri: `{', '.join(r['weak_hits']) if r['weak_hits'] else 'yok'}`")
        md.append("")

    md.append("## 3. Yorum")
    md.append("")
    md.append("Bu rapor otomatik bir ön kontroldür. Bölümlerin akademik bütünlüğü için nihai karar manuel okuma ile verilmelidir. Özellikle Bölüm 2, 3 ve 5 için atıf yoğunluğu; Bölüm 4 için deneysel yöntem-sonuç tutarlılığı; Bölüm 6 için katkı ve gelecek çalışma bağlantısı ayrıca gözden geçirilmelidir.")

    out_md = Path(args.output_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(md), encoding="utf-8")

    print("[INFO] MD:", out_md)
    print("[INFO] JSON:", out_json)
    print("[INFO] Summary:", result["summary"])


if __name__ == "__main__":
    main()
