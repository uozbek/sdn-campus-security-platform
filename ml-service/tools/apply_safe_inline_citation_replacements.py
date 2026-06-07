#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

import pandas as pd


CHAPTER_FILES = [
    "docs/bolum_1_giris_tr.md",
    "docs/bolum_2_kavramsal_kuramsal_arka_plan_tr.md",
    "docs/bolum_3_literatur_taramasi_ve_ilgili_calismalar_tr.md",
    "docs/bolum_4_yontem_ve_runtime_dogrulama_tr.md",
    "docs/bolum_5_tartisma_sinirliliklar_gelecek_calismalar_tr.md",
    "docs/bolum_6_sonuc_ve_oneriler_tr.md",
]


def main() -> None:
    override = pd.read_csv("docs/inline_citation_manual_override.csv").fillna("")

    replacements = {}
    for _, row in override.iterrows():
        if row.get("final_action") == "replace" and row.get("final_inline_citation"):
            marker = str(row["marker"]).strip()
            citation = str(row["final_inline_citation"]).strip()
            replacements[f"[{marker}]"] = citation

    print("[INFO] Replacements:")
    for k, v in replacements.items():
        print(f"  {k} -> {v}")

    if not replacements:
        print("[INFO] No replacements to apply.")
        return

    for f in CHAPTER_FILES:
        p = Path(f)
        if not p.exists():
            continue

        text = p.read_text(encoding="utf-8")
        original = text

        for old, new in replacements.items():
            text = text.replace(old, new)

        if text != original:
            backup = p.with_suffix(p.suffix + ".bak_safe_citation_replace")
            backup.write_text(original, encoding="utf-8")
            p.write_text(text, encoding="utf-8")
            print("[INFO] Updated:", p)
            print("[INFO] Backup :", backup)

    print("[INFO] Done.")


if __name__ == "__main__":
    main()
