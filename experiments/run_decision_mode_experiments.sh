#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="/root/sdn-campus-security-platform"
SCENARIO_FILE="$PROJECT_ROOT/experiments/scenarios/decision_mode_runtime_scenario.mn"
CONTROLLER_FILE="$PROJECT_ROOT/controller/campus_l3_ids_controller_v13_decision_modes.py"
TOPO_FILE="$PROJECT_ROOT/topology/campus_topology_v1.py"
RESULT_BASE="$PROJECT_ROOT/experiments/results/decision_modes"

MODES=("heuristic_only" "ml_only" "hybrid")

cd "$PROJECT_ROOT"

mkdir -p "$RESULT_BASE"

echo "[INFO] Checking FastAPI health..."
if ! curl -s http://127.0.0.1:8000/health >/dev/null; then
  echo "[ERROR] FastAPI is not reachable at http://127.0.0.1:8000/health"
  echo "Start it first:"
  echo "cd $PROJECT_ROOT/ml-service && source ../venv/bin/activate && uvicorn app:app --host 127.0.0.1 --port 8000"
  exit 1
fi

for MODE in "${MODES[@]}"; do
  echo
  echo "============================================================"
  echo "[INFO] Running decision mode: $MODE"
  echo "============================================================"

  MODE_DIR="$RESULT_BASE/$MODE"
  mkdir -p "$MODE_DIR"

  echo "[INFO] Cleaning Mininet, controller and logs..."
  sudo mn -c >/dev/null 2>&1 || true
  sudo pkill -f ryu-manager || true
  sleep 2

  rm -f logs/flow_stats.csv
  rm -f logs/predictions.csv
  rm -f logs/policy_decisions.csv
  rm -f logs/mitigation_log.csv
  rm -f logs/rate_limit_log.csv
  rm -f logs/quarantine_log.csv
  rm -f logs/mitigation_latency.csv

  echo "[INFO] Starting Ryu controller in mode=$MODE..."
  source "$PROJECT_ROOT/venv/bin/activate"

  CONTROLLER_DECISION_MODE="$MODE" \
  ryu-manager "$CONTROLLER_FILE" \
    > "$MODE_DIR/controller_stdout.log" \
    2> "$MODE_DIR/controller_stderr.log" &

  RYU_PID=$!

  echo "[INFO] Ryu PID=$RYU_PID"
  echo "[INFO] Waiting for controller startup..."
  sleep 8

  echo "[INFO] Starting Mininet scenario..."
  sudo mn --custom "$TOPO_FILE" \
    --topo campus_v1 \
    --controller=remote,ip=127.0.0.1,port=6653 \
    --switch ovsk,protocols=OpenFlow13 \
    --link tc \
    < "$SCENARIO_FILE" \
    > "$MODE_DIR/mininet_stdout.log" \
    2> "$MODE_DIR/mininet_stderr.log" || true

  echo "[INFO] Mininet scenario finished."

  echo "[INFO] Stopping controller..."
  sudo kill "$RYU_PID" >/dev/null 2>&1 || true
  sleep 2
  sudo pkill -f ryu-manager || true

  echo "[INFO] Copying logs..."
  cp logs/flow_stats.csv "$MODE_DIR/" 2>/dev/null || true
  cp logs/predictions.csv "$MODE_DIR/" 2>/dev/null || true
  cp logs/policy_decisions.csv "$MODE_DIR/" 2>/dev/null || true
  cp logs/mitigation_log.csv "$MODE_DIR/" 2>/dev/null || true
  cp logs/rate_limit_log.csv "$MODE_DIR/" 2>/dev/null || true
  cp logs/quarantine_log.csv "$MODE_DIR/" 2>/dev/null || true
  cp logs/mitigation_latency.csv "$MODE_DIR/" 2>/dev/null || true

  cat > "$MODE_DIR/run_metadata.txt" << EOF
mode=$MODE
scenario_file=$SCENARIO_FILE
controller_file=$CONTROLLER_FILE
topology_file=$TOPO_FILE
tcp_normal=h1->h14 iperf3 tcp 1M 20s
udp_attack=h12->h14 iperf3 udp 30M 60s
post_wait=20s
stats_interval=5s
run_finished_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
EOF

  echo "[INFO] Saved results to $MODE_DIR"

  echo "[INFO] Quick policy summary for $MODE:"
  python - << PY
import pandas as pd
from pathlib import Path

mode_dir = Path("$MODE_DIR")
p = mode_dir / "policy_decisions.csv"

if not p.exists():
    print("policy_decisions.csv not found")
else:
    df = pd.read_csv(p)
    print("Rows:", len(df))
    print(df["policy_final_action"].value_counts(dropna=False))

    if "decision_mode" in df.columns:
        print("Decision mode:")
        print(df["decision_mode"].value_counts(dropna=False))

    bad = df[
        (df["ml_prediction"].astype(str).str.lower() == "benign")
        & (df["policy_final_action"].isin(["drop", "rate_limit", "quarantine_candidate"]))
    ]
    print("Benign but mitigated rows:", len(bad))
PY

done

echo
echo "[INFO] All decision mode experiments completed."
echo "[INFO] Run comparison:"
echo "python experiments/results/decision_modes/compare_decision_modes.py"