#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="/root/sdn-campus-security-platform"
PCAP_DIR="$PROJECT_ROOT/experiments/pcaps"

IFACE="${1:-s6-eth2}"
NAME="${2:-runtime_capture}"

mkdir -p "$PCAP_DIR"

OUT="$PCAP_DIR/${NAME}_$(date -u +%Y%m%d_%H%M%S).pcap"

echo "[INFO] Capturing interface: $IFACE"
echo "[INFO] Output: $OUT"
echo "[INFO] Press CTRL+C to stop."

sudo tcpdump -i "$IFACE" -w "$OUT"
