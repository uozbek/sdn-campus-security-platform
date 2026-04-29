#!/bin/bash

set -e

echo "[*] Checking SDN Campus Security Platform project structure..."

REQUIRED_DIRS=(
  "infrastructure"
  "topology"
  "controller"
  "controller/modules"
  "ml-service"
  "ml-service/models"
  "feature-extraction"
  "traffic-generator"
  "mitigation"
  "monitoring"
  "experiments/scenarios"
  "experiments/results"
  "datasets/raw"
  "datasets/processed"
  "notebooks"
  "reports"
  "docs"
  "logs"
)

REQUIRED_FILES=(
  "config.yaml"
  "README.md"
  "requirements.txt"
  ".gitignore"
  "ml-service/models/model_registry.csv"
  "experiments/scenarios/e01_normal_traffic.yaml"
  "experiments/scenarios/e02_udp_flood_lab.yaml"
)

for dir in "${REQUIRED_DIRS[@]}"; do
  if [ -d "$dir" ]; then
    echo "[OK] Directory exists: $dir"
  else
    echo "[ERROR] Missing directory: $dir"
    exit 1
  fi
done

for file in "${REQUIRED_FILES[@]}"; do
  if [ -f "$file" ]; then
    echo "[OK] File exists: $file"
  else
    echo "[ERROR] Missing file: $file"
    exit 1
  fi
done

echo "[*] Project structure check completed successfully."
