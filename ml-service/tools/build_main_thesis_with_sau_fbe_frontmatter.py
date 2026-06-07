#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


def run(cmd: list[str]) -> None:
    print("[RUN]", " ".join(cmd))
    subprocess.run(cmd, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build main thesis DOCX using generated SAÜ FBE frontmatter."
    )
    parser.add_argument(
        "--frontmatter",
        default="docs/sau_fbe_frontmatter_generated.docx",
    )
    parser.add_argument(
        "--output",
        default="docs/tez_ana_taslak_tr_sau_fbe.docx",
    )
    parser.add_argument(
        "--rules-json",
        default="docs/sau_fbe_format_rules.json",
    )
    parser.add_argument(
        "--metadata-quality-json",
        default="docs/thesis_metadata_quality_report.json",
    )
    parser.add_argument(
        "--allow-todo-metadata",
        action="store_true",
        help="Allow build even if thesis metadata quality report contains TODO/check fields.",
    )
    args = parser.parse_args()

    frontmatter = Path(args.frontmatter)
    output = Path(args.output)

    metadata_quality_path = Path(args.metadata_quality_json)
    if metadata_quality_path.exists() and not args.allow_todo_metadata:
        import json
        data = json.loads(metadata_quality_path.read_text(encoding="utf-8"))
        summary = data.get("summary", {})
        if summary.get("check", 0) > 0 or summary.get("todo_count", 0) > 0:
            raise SystemExit(
                "[ERROR] Metadata quality report contains TODO/check fields. "
                "Update docs/thesis_metadata.yaml or rerun with --allow-todo-metadata."
            )

    chapters = [
        frontmatter,
        Path("docs/bolum_1_giris_tr.docx"),
        Path("docs/bolum_2_kavramsal_kuramsal_arka_plan_tr.docx"),
        Path("docs/bolum_3_literatur_taramasi_ve_ilgili_calismalar_tr.docx"),
        Path("docs/bolum_4_yontem_ve_runtime_dogrulama_tr_with_artifacts.docx"),
        Path("docs/bolum_5_tartisma_sinirliliklar_gelecek_calismalar_tr.docx"),
        Path("docs/bolum_6_sonuc_ve_oneriler_tr.docx"),
        Path("docs/bolum_7_kaynakca_taslagi.docx"),
    ]

    missing = [str(p) for p in chapters if not p.exists()]
    if missing:
        raise SystemExit("[ERROR] Missing chapter/frontmatter files:\n" + "\n".join(missing))

    merge_cmd = [
        "python",
        "ml-service/tools/merge_thesis_chapters_docx.py",
        "--output",
        str(output),
    ]

    for ch in chapters:
        merge_cmd.extend(["--chapter", str(ch)])

    run(merge_cmd)

    run([
        "python",
        "ml-service/tools/apply_sau_fbe_docx_format.py",
        "--input",
        str(output),
        "--output",
        str(output),
        "--rules-json",
        args.rules_json,
        "--body-font",
        "Times New Roman",
        "--body-size",
        "12",
    ])

    print("[INFO] Written:", output)


if __name__ == "__main__":
    main()
