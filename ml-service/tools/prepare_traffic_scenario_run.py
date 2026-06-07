#!/usr/bin/env python3
import argparse
import json
from datetime import datetime
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None


def load_yaml(path: Path):
    if yaml is None:
        raise ImportError(
            "PyYAML is not installed. Install it with: pip install pyyaml"
        )

    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def sh_quote(value):
    value = str(value)
    return "'" + value.replace("'", "'\"'\"'") + "'"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", required=True, help="Path to YAML scenario file")
    args = parser.parse_args()

    scenario_path = Path(args.scenario)
    if not scenario_path.exists():
        raise FileNotFoundError(f"Scenario file not found: {scenario_path}")

    scenario = load_yaml(scenario_path)

    name = scenario.get("name", scenario_path.stem)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    output_root = Path(scenario.get("paths", {}).get("output_root", "experiments/results/mixed_traffic_experiments"))

    exp_dir = output_root / f"{timestamp}_{name}"
    logs_dir = exp_dir / "logs"
    pcaps_dir = exp_dir / "pcaps"
    runtime_dir = exp_dir / "runtime_pipeline"
    comparison_dir = exp_dir / "comparison" / "port_aware_protocol_aware_v2"

    for p in [exp_dir, logs_dir, pcaps_dir, runtime_dir, comparison_dir]:
        p.mkdir(parents=True, exist_ok=True)

    capture = scenario.get("capture", {})
    capture_interface = capture.get("interface", "any")
    capture_filter = capture.get("filter", "")
    pcap_name = capture.get("output_name", "scenario_capture.pcap")
    pcap_path = pcaps_dir / pcap_name

    server = scenario.get("server", {})
    server_host = server.get("host", "h14")
    server_ip = server.get("ip", "10.10.40.14")
    iperf3_port = int(server.get("iperf3_port", 5201))

    traffic = scenario.get("traffic", {})
    benign = traffic.get("benign", []) or []
    malicious = traffic.get("malicious", []) or []

    metadata = {
        "scenario_file": str(scenario_path),
        "scenario_name": name,
        "created_at_utc": datetime.utcnow().isoformat(),
        "experiment_dir": str(exp_dir),
        "logs_dir": str(logs_dir),
        "pcaps_dir": str(pcaps_dir),
        "runtime_dir": str(runtime_dir),
        "comparison_dir": str(comparison_dir),
        "pcap_path": str(pcap_path),
        "scenario": scenario,
    }

    metadata_path = exp_dir / "scenario_run_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")

    commands = []

    commands.append("#!/usr/bin/env bash")
    commands.append("set -euo pipefail")
    commands.append("")
    commands.append("# Generated scenario run commands")
    commands.append(f"export EXP_DIR={sh_quote(exp_dir)}")
    commands.append(f"export PCAP_PATH={sh_quote(pcap_path)}")
    commands.append(f"export FINAL_RUN_ROOT={sh_quote(runtime_dir)}")
    commands.append(f"export COMPARE_DIR={sh_quote(comparison_dir)}")
    commands.append("")
    commands.append("echo \"EXP_DIR=$EXP_DIR\"")
    commands.append("echo \"PCAP_PATH=$PCAP_PATH\"")
    commands.append("mkdir -p \"$EXP_DIR/logs\" \"$EXP_DIR/pcaps\" \"$FINAL_RUN_ROOT\" \"$COMPARE_DIR\"")
    commands.append("")

    commands.append("# 1) Start Ryu controller in another terminal")
    commands.append("# export CONTROLLER_DECISION_MODE=hybrid")
    commands.append("# ryu-manager controller/campus_l3_ids_controller_v13_decision_modes.py 2>&1 | tee logs/controller_scenario_debug.log")
    commands.append("")

    commands.append("# 2) Start Mininet in another terminal")
    commands.append("# sudo mn --custom topology/campus_topology_v1.py \\")
    commands.append("#   --topo campus_v1 \\")
    commands.append("#   --controller=remote,ip=127.0.0.1,port=6653 \\")
    commands.append("#   --switch ovsk,protocols=OpenFlow13 \\")
    commands.append("#   --link tc")
    commands.append("")

    commands.append("# 3) Start packet capture in host shell")
    commands.append("# Important: run from project root or use absolute paths.")
    commands.append(f"sudo tcpdump -i {capture_interface} -w \"$PCAP_PATH\" {sh_quote(capture_filter)}")
    commands.append("")

    commands.append("# 4) In Mininet CLI, start iperf3 server")
    commands.append(f"# {server_host} iperf3 -s -p {iperf3_port} &")
    commands.append("")

    commands.append("# 5) In Mininet CLI, generate benign traffic")
    for item in benign:
        src = item.get("src")
        dst_ip = server_ip
        duration = item.get("duration", 20)
        typ = item.get("type", "")
        name_i = item.get("name", "benign_flow")

        if typ == "iperf3_tcp":
            parallel = item.get("parallel", 1)
            commands.append(f"# {name_i}")
            commands.append(f"# {src} iperf3 -c {dst_ip} -p {iperf3_port} -t {duration} -P {parallel} &")

        elif typ == "iperf3_udp":
            bandwidth = item.get("bandwidth", "1M")
            commands.append(f"# {name_i}")
            commands.append(f"# {src} iperf3 -u -c {dst_ip} -p {iperf3_port} -b {bandwidth} -t {duration} &")

    commands.append("")
    commands.append("# 6) In Mininet CLI, generate malicious traffic")
    for item in malicious:
        src = item.get("src")
        dst_ip = server_ip
        duration = item.get("duration", 30)
        typ = item.get("type", "")
        name_i = item.get("name", "malicious_flow")

        if typ == "iperf3_udp":
            bandwidth = item.get("bandwidth", "80M")
            commands.append(f"# {name_i}")
            commands.append(f"# {src} iperf3 -u -c {dst_ip} -p {iperf3_port} -b {bandwidth} -t {duration} &")

        elif typ == "iperf3_tcp":
            parallel = item.get("parallel", 1)
            commands.append(f"# {name_i}")
            commands.append(f"# {src} iperf3 -c {dst_ip} -p {iperf3_port} -t {duration} -P {parallel} &")

    commands.append("")
    commands.append("# 7) After traffic ends, stop tcpdump manually with Ctrl+C, then collect controller logs")
    commands.append("cp logs/policy_decisions.csv \"$EXP_DIR/logs/\" 2>/dev/null || true")
    commands.append("cp logs/predictions.csv \"$EXP_DIR/logs/\" 2>/dev/null || true")
    commands.append("cp logs/flow_stats.csv \"$EXP_DIR/logs/\" 2>/dev/null || true")
    commands.append("cp logs/mitigation_log.csv \"$EXP_DIR/logs/\" 2>/dev/null || true")
    commands.append("cp logs/mitigation_latency.csv \"$EXP_DIR/logs/\" 2>/dev/null || true")
    commands.append("cp logs/quarantine_log.csv \"$EXP_DIR/logs/\" 2>/dev/null || true")
    commands.append("cp logs/rate_limit_log.csv \"$EXP_DIR/logs/\" 2>/dev/null || true")
    commands.append("cp logs/controller_scenario_debug.log \"$EXP_DIR/logs/\" 2>/dev/null || true")
    commands.append("")

    commands.append("# 8) Run Final Top-20 runtime pipeline")
    commands.append("python ml-service/tools/run_final_top20_runtime_pipeline.py \\")
    commands.append("  --pcap \"$PCAP_PATH\" \\")
    commands.append(f"  --run-name {sh_quote(name + '_final_top20')} \\")
    commands.append("  --output-root \"$FINAL_RUN_ROOT\"")
    commands.append("")
    commands.append("export FINAL_RUN_DIR=$(ls -td \"$FINAL_RUN_ROOT\"/* | head -1)")
    commands.append("echo \"FINAL_RUN_DIR=$FINAL_RUN_DIR\"")
    commands.append("")

    commands.append("# 9) Build protocol-aware final policy file")
    commands.append("python ml-service/tools/build_protocol_aware_final_policy.py \\")
    commands.append("  --predictions \"$FINAL_RUN_DIR/final_top20_runtime_predictions.csv\" \\")
    commands.append("  --pcap \"$PCAP_PATH\" \\")
    commands.append("  --output \"$FINAL_RUN_DIR/final_top20_policy_decisions_protocol_aware.csv\"")
    commands.append("")

    commands.append("# 10) Compare Final Top-20 decisions with controller logs")
    commands.append("python ml-service/tools/compare_final_top20_with_port_aware_controller_policy.py \\")
    commands.append("  --final-policy \"$FINAL_RUN_DIR/final_top20_policy_decisions_protocol_aware.csv\" \\")
    commands.append("  --controller-policy \"$EXP_DIR/logs/policy_decisions.csv\" \\")
    commands.append("  --mitigation-log \"$EXP_DIR/logs/mitigation_log.csv\" \\")
    commands.append("  --quarantine-log \"$EXP_DIR/logs/quarantine_log.csv\" \\")
    commands.append("  --rate-limit-log \"$EXP_DIR/logs/rate_limit_log.csv\" \\")
    commands.append("  --output-dir \"$COMPARE_DIR\"")
    commands.append("")

    commands.append("# 11) Generate mixed traffic experiment report")
    commands.append("python ml-service/tools/generate_mixed_traffic_experiment_report.py \\")
    commands.append("  --exp-dir \"$EXP_DIR\" \\")
    commands.append("  --final-run-dir \"$FINAL_RUN_DIR\" \\")
    commands.append("  --compare-dir \"$COMPARE_DIR\"")
    commands.append("")
    commands.append("# 12) Generate experiment manifest and reproducibility checklist")
    commands.append("python ml-service/tools/generate_experiment_manifest.py \\")
    commands.append("  --exp-dir \"$EXP_DIR\" \\")
    commands.append("  --final-run-dir \"$FINAL_RUN_DIR\" \\")
    commands.append("  --compare-dir \"$COMPARE_DIR\" \\")
    commands.append("  --scenario \"$SCENARIO_FILE\" \\")
    commands.append("  --controller \"controller/campus_l3_ids_controller_v13_decision_modes.py\"")
    commands.append("")
    commands.append("echo \"Scenario run prepared/completed.\"")
    commands.append("echo \"EXP_DIR=$EXP_DIR\"")

    commands_path = exp_dir / "run_commands.sh"
    commands_path.write_text("\n".join(commands) + "\n", encoding="utf-8")
    commands_path.chmod(0o755)

    readme = []
    readme.append(f"# Scenario Run — {name}")
    readme.append("")
    readme.append(f"- Created at UTC: `{metadata['created_at_utc']}`")
    readme.append(f"- Scenario file: `{scenario_path}`")
    readme.append(f"- Experiment directory: `{exp_dir}`")
    readme.append(f"- PCAP path: `{pcap_path}`")
    readme.append("")
    readme.append("## How to use")
    readme.append("")
    readme.append("1. Start the Ryu controller in one terminal.")
    readme.append("2. Start Mininet in another terminal.")
    readme.append("3. Start tcpdump capture using the command in `run_commands.sh`.")
    readme.append("4. Run the Mininet traffic commands listed in `run_commands.sh`.")
    readme.append("5. Stop tcpdump after traffic generation.")
    readme.append("6. Run the analysis commands from `run_commands.sh`.")
    readme.append("")
    readme.append("This first scenario-runner version intentionally keeps Mininet commands manual,")
    readme.append("so each experiment remains controllable and debuggable.")

    readme_path = exp_dir / "README.md"
    readme_path.write_text("\n".join(readme) + "\n", encoding="utf-8")

    print("[INFO] Scenario prepared.")
    print("[INFO] EXP_DIR:", exp_dir)
    print("[INFO] Metadata:", metadata_path)
    print("[INFO] Commands:", commands_path)
    print("[INFO] README:", readme_path)


if __name__ == "__main__":
    main()
