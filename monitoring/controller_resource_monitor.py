#!/usr/bin/env python3
"""
Aşama 14.7 — Controller Resource Monitor

Bu script, çalışan ryu-manager process'ini bulur ve CPU/memory kullanımını
logs/controller_resource_usage.csv dosyasına yazar.

Kullanım:

python monitoring/controller_resource_monitor.py \
  --interval 1 \
  --output logs/controller_resource_usage.csv
"""

import argparse
import csv
import time
from datetime import datetime
from pathlib import Path

import psutil


def find_ryu_process():
    candidates = []

    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            name = proc.info.get("name") or ""
            cmdline = proc.info.get("cmdline") or []
            cmdline_str = " ".join(cmdline)

            if "ryu-manager" in name or "ryu-manager" in cmdline_str:
                candidates.append(proc)

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    if not candidates:
        return None

    # Birden fazla varsa en yeni/aktif olanı seçmek yerine ilkini alıyoruz.
    # İleride PID parametresi de eklenebilir.
    return candidates[0]


def ensure_header(output_path):
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_path.exists() and output_path.stat().st_size > 0:
        return

    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "timestamp",
            "pid",
            "process_name",
            "cpu_percent",
            "memory_rss_mb",
            "memory_vms_mb",
            "num_threads",
            "status",
        ])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--interval", type=float, default=1.0)
    parser.add_argument("--output", default="logs/controller_resource_usage.csv")
    args = parser.parse_args()

    output_path = Path(args.output)
    ensure_header(output_path)

    proc = find_ryu_process()

    if proc is None:
        print("[ERROR] ryu-manager process bulunamadı.")
        print("Önce controller'ı başlatın:")
        print("ryu-manager controller/campus_l3_ids_controller_v10_ml_ready.py")
        return

    print(f"[INFO] Monitoring ryu-manager PID={proc.pid}")
    print(f"[INFO] Output: {output_path}")

    # psutil cpu_percent ilk çağrıda 0 dönebilir; warm-up.
    proc.cpu_percent(interval=None)

    while True:
        try:
            cpu = proc.cpu_percent(interval=args.interval)
            mem = proc.memory_info()

            row = [
                datetime.utcnow().isoformat(),
                proc.pid,
                proc.name(),
                cpu,
                mem.rss / (1024 * 1024),
                mem.vms / (1024 * 1024),
                proc.num_threads(),
                proc.status(),
            ]

            with output_path.open("a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(row)

            print(
                f"[RESOURCE] cpu={cpu:.2f}% "
                f"rss={mem.rss / (1024 * 1024):.2f}MB "
                f"threads={proc.num_threads()}",
                flush=True,
            )

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            print("[ERROR] ryu-manager process artık erişilebilir değil.")
            break


if __name__ == "__main__":
    main()
