#!/usr/bin/env bash
set -euo pipefail

PCAP_INPUT="${1:-}"
OUTPUT_DIR="${2:-/data/output}"

if [[ -z "$PCAP_INPUT" ]]; then
  echo "Usage: docker run ... cicflowmeter <pcap_input> <output_dir>"
  exit 1
fi

mkdir -p "$OUTPUT_DIR"

echo "[INFO] PCAP input: $PCAP_INPUT"
echo "[INFO] Output dir: $OUTPUT_DIR"

echo "[INFO] Available jars:"
find /opt/CICFlowMeter -name "*.jar" -type f | sort

echo "[INFO] Candidate runnable jars:"
find /opt/CICFlowMeter -name "*.jar" -type f \
  | grep -v 'jnetpcap' \
  | grep -v 'gradle-wrapper' \
  | sort || true

JAR_PATH="$(
  find /opt/CICFlowMeter -name "*.jar" -type f \
    | grep -v 'jnetpcap' \
    | grep -v 'gradle-wrapper' \
    | head -1 || true
)"

if [[ -z "$JAR_PATH" ]]; then
  echo "[ERROR] Runnable CICFlowMeter jar not found."
  echo "[ERROR] Build may have failed."
  exit 1
fi

echo "[INFO] Using jar: $JAR_PATH"

echo "[INFO] Trying help output..."
java -jar "$JAR_PATH" --help || true

echo "[INFO] Trying PCAP conversion..."
java -jar "$JAR_PATH" "$PCAP_INPUT" "$OUTPUT_DIR" || true

echo "[INFO] Output files:"
find "$OUTPUT_DIR" -maxdepth 2 -type f -print