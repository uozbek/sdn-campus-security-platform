#!/usr/bin/env python3
from pathlib import Path
import json
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory", default="docs/bolum_4_artifact_insert_inventory.json")
    parser.add_argument("--artifact-root", default="experiments/results/thesis_artifacts/run_05_port_aware_runtime_validation")
    parser.add_argument("--output-md", default="docs/bolum_4_artifact_inventory_check.md")
    args = parser.parse_args()

    inventory_path = Path(args.inventory)
    root = Path(args.artifact_root)
    out = Path(args.output_md)

    items = json.loads(inventory_path.read_text(encoding="utf-8"))

    lines = []
    lines.append("# Bölüm 4 Artifact Varlık Kontrolü")
    lines.append("")
    lines.append(f"- Inventory: `{inventory_path}`")
    lines.append(f"- Artifact root: `{root}`")
    lines.append("")
    lines.append("| Tür | Kaynak | Beklenen tam yol | Durum |")
    lines.append("|---|---|---|---|")

    missing = 0

    for item in items:
        rel = item["source_path"]
        full = root / rel
        status = "ok" if full.exists() else "missing"
        if status == "missing":
            missing += 1
        lines.append(f"| {item['kind']} | `{rel}` | `{full}` | {status} |")

    lines.append("")
    lines.append(f"- Total: `{len(items)}`")
    lines.append(f"- Missing: `{missing}`")

    out.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("[INFO] Written:", out)
    print("[INFO] Total:", len(items))
    print("[INFO] Missing:", missing)

if __name__ == "__main__":
    main()
