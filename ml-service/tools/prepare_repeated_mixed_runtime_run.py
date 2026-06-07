#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path


def utc_stamp() -> str:
    return datetime.utcnow().strftime("%Y%m%d_%H%M%S")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Prepare a repeated mixed benign/malicious SDN runtime experiment run."
    )

    parser.add_argument(
        "--root-dir",
        default="experiments/results/mixed_traffic_experiments/repeated_mixed_runtime_20260516_130204",
        help="Root directory for repeated mixed runtime experiments.",
    )

    parser.add_argument(
        "--run-id",
        default="",
        help="Run id, e.g. run_04_repeat. If omitted, a timestamped run id is generated.",
    )

    parser.add_argument(
        "--scenario-name",
        default="mixed_benign_malicious_runtime_validation",
        help="Scenario name for metadata.",
    )

    args = parser.parse_args()

    root_dir = Path(args.root_dir)
    run_id = args.run_id.strip() or f"run_{utc_stamp()}_mixed_repeat"

    exp_dir = root_dir / run_id
    logs_dir = exp_dir / "logs"
    pcaps_dir = exp_dir / "pcaps"
    runtime_dir = exp_dir / "runtime_pipeline"
    comparison_dir = exp_dir / "comparison" / "port_aware_protocol_aware_api_ok"

    for directory in [logs_dir, pcaps_dir, runtime_dir, comparison_dir]:
        directory.mkdir(parents=True, exist_ok=True)

    pcap_path = pcaps_dir / "mixed_benign_malicious_live.pcap"
    filtered_pcap_path = pcaps_dir / "mixed_benign_malicious_live_5201_only.pcap"

    metadata = {
        "run_id": run_id,
        "scenario_name": args.scenario_name,
        "created_at_utc": datetime.utcnow().isoformat(),
        "exp_dir": str(exp_dir),
        "logs_dir": str(logs_dir),
        "pcaps_dir": str(pcaps_dir),
        "runtime_pipeline_dir": str(runtime_dir),
        "comparison_dir": str(comparison_dir),
        "pcap_path": str(pcap_path),
        "filtered_pcap_path": str(filtered_pcap_path),
        "status": "prepared",
        "notes": [
            "Start Ryu controller and ML API before running traffic.",
            "Capture PCAP during mixed benign/malicious traffic generation.",
            "Copy controller logs after the run.",
            "Run Final Top-20 runtime pipeline with active FastAPI model.",
            "Build protocol-aware final policy using the filtered PCAP.",
            "Compare final policy with controller policy logs.",
        ],
    }

    write_text(
        exp_dir / "run_metadata.json",
        json.dumps(metadata, indent=2, ensure_ascii=False),
    )

    commands = f"""#!/usr/bin/env bash
set -euo pipefail

cd /root/sdn-campus-security-platform
source venv/bin/activate

export EXP_DIR="{exp_dir}"
export PCAP_PATH="{pcap_path}"
export FILTERED_PCAP="{filtered_pcap_path}"
export COMPARE_DIR="{comparison_dir}"

echo "EXP_DIR=$EXP_DIR"
echo "PCAP_PATH=$PCAP_PATH"
echo "FILTERED_PCAP=$FILTERED_PCAP"
echo "COMPARE_DIR=$COMPARE_DIR"

mkdir -p "$EXP_DIR/logs" "$EXP_DIR/pcaps" "$EXP_DIR/runtime_pipeline" "$COMPARE_DIR"

# 1) Optional: clear old controller logs manually before a fresh run.
# rm -f logs/policy_decisions.csv logs/predictions.csv logs/flow_stats.csv
# rm -f logs/mitigation_log.csv logs/rate_limit_log.csv logs/quarantine_log.csv logs/mitigation_latency.csv

# 2) Start PCAP capture in another terminal.
# sudo tcpdump -i any -Z root -w "$PCAP_PATH" "host 10.10.40.14 or host 10.10.60.12 or host 10.10.10.1 or host 10.10.10.2 or host 10.10.10.3 or host 10.10.99.16"

# 3) Run mixed benign/malicious traffic generation manually from Mininet.

# 4) Copy controller logs after the run.
cp logs/policy_decisions.csv "$EXP_DIR/logs/" 2>/dev/null || true
cp logs/predictions.csv "$EXP_DIR/logs/" 2>/dev/null || true
cp logs/flow_stats.csv "$EXP_DIR/logs/" 2>/dev/null || true
cp logs/mitigation_log.csv "$EXP_DIR/logs/" 2>/dev/null || true
cp logs/rate_limit_log.csv "$EXP_DIR/logs/" 2>/dev/null || true
cp logs/quarantine_log.csv "$EXP_DIR/logs/" 2>/dev/null || true
cp logs/mitigation_latency.csv "$EXP_DIR/logs/" 2>/dev/null || true
cp logs/controller_*.log "$EXP_DIR/logs/" 2>/dev/null || true

# 5) Create smaller 5201-only PCAP for protocol-aware policy builder.
if [ -f "$PCAP_PATH" ]; then
  tcpdump -nn -r "$PCAP_PATH" -w "$FILTERED_PCAP" "port 5201"
else
  echo "[WARN] PCAP not found: $PCAP_PATH"
fi

# 6) Run Final Top-20 runtime pipeline.
python ml-service/tools/run_final_top20_runtime_pipeline.py \\
  --pcap "$PCAP_PATH" \\
  --run-name "mixed_benign_malicious_live_final_top20_{run_id}_api_ok" \\
  --output-root "$EXP_DIR/runtime_pipeline"

export FINAL_RUN_DIR=$(ls -td "$EXP_DIR"/runtime_pipeline/*api_ok | head -1)
echo "FINAL_RUN_DIR=$FINAL_RUN_DIR"

# 7) Build protocol-aware final policy.
python ml-service/tools/build_protocol_aware_final_policy.py \\
  --predictions "$FINAL_RUN_DIR/final_top20_runtime_predictions.csv" \\
  --pcap "$FILTERED_PCAP" \\
  --output "$FINAL_RUN_DIR/final_top20_policy_decisions_protocol_aware.csv"

# 8) Compare runtime final policy with controller logs.
python ml-service/tools/compare_final_top20_with_port_aware_controller_policy.py \\
  --final-policy "$FINAL_RUN_DIR/final_top20_policy_decisions_protocol_aware.csv" \\
  --controller-policy "$EXP_DIR/logs/policy_decisions.csv" \\
  --mitigation-log "$EXP_DIR/logs/mitigation_log.csv" \\
  --quarantine-log "$EXP_DIR/logs/quarantine_log.csv" \\
  --rate-limit-log "$EXP_DIR/logs/rate_limit_log.csv" \\
  --output-dir "$COMPARE_DIR"

# 9) Generate mixed traffic experiment report.
python ml-service/tools/generate_mixed_traffic_experiment_report.py \\
  --exp-dir "$EXP_DIR" \\
  --final-run-dir "$FINAL_RUN_DIR" \\
  --compare-dir "$COMPARE_DIR"

echo
echo "Generated files:"
ls -lh "$EXP_DIR"/mixed_traffic_experiment_* 2>/dev/null || true
ls -lh "$FINAL_RUN_DIR"/final_top20_policy_decisions_protocol_aware.csv 2>/dev/null || true
ls -lh "$COMPARE_DIR"/final_top20_vs_port_aware_controller_* 2>/dev/null || true
"""

    run_commands = exp_dir / "run_commands.sh"
    write_text(run_commands, commands)
    run_commands.chmod(0o755)

    readme = f"""# Repeated Mixed Runtime Experiment — {run_id}

This directory was prepared for a repeated mixed benign/malicious runtime validation experiment.

## Paths

- Experiment directory: {exp_dir}
- PCAP path: {pcap_path}
- Filtered PCAP path: {filtered_pcap_path}
- Logs directory: {logs_dir}
- Runtime pipeline directory: {runtime_dir}
- Comparison directory: {comparison_dir}

## Main Command File

bash {run_commands}

## Expected Successful Indicators

- benign traffic is mostly allowed
- malicious UDP traffic from 10.10.60.12 to 10.10.40.14 is detected
- at least one drop mitigation log is produced
- quarantine log is produced if repeated high-confidence attack is observed
- protocol-aware final policy contains DROP for UDP attack flow
- comparison report shows security-compatible final/controller behavior

## Recommended Manual Workflow

1. Start the ML FastAPI service.
2. Start the Ryu controller.
3. Start PCAP capture.
4. Generate benign and malicious traffic in Mininet.
5. Stop PCAP capture.
6. Copy controller logs into the experiment directory.
7. Run runtime Final Top-20 pipeline.
8. Build protocol-aware final policy.
9. Compare final model decisions with controller policy/enforcement logs.
10. Generate the mixed traffic experiment report.
"""

    write_text(exp_dir / "README.md", readme)

    print("[INFO] Prepared repeated mixed runtime run.")
    print(f"[INFO] Run ID      : {run_id}")
    print(f"[INFO] EXP_DIR     : {exp_dir}")
    print(f"[INFO] Metadata    : {exp_dir / 'run_metadata.json'}")
    print(f"[INFO] Commands    : {run_commands}")
    print(f"[INFO] README      : {exp_dir / 'README.md'}")


if __name__ == "__main__":
    main()