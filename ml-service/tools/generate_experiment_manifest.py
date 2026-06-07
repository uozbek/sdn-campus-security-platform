#!/usr/bin/env python3
import argparse
import json
import platform
import subprocess
from datetime import datetime
from pathlib import Path

import pandas as pd


def safe_read_json(path):
    path = Path(path)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def safe_row_count(path):
    path = Path(path)
    if not path.exists():
        return None
    try:
        return int(len(pd.read_csv(path)))
    except Exception:
        return None


def file_info(path):
    path = Path(path)
    if not path.exists():
        return {
            "path": str(path),
            "exists": False,
            "size_bytes": None,
        }

    return {
        "path": str(path),
        "exists": True,
        "size_bytes": path.stat().st_size,
    }


def run_cmd(cmd):
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            check=False,
        )
        return result.stdout.strip()
    except Exception:
        return ""


def main():
    parser = argparse.ArgumentParser(
        description="Generate experiment manifest and reproducibility checklist for SDN IDS/IPS experiments."
    )
    parser.add_argument("--exp-dir", required=True)
    parser.add_argument("--final-run-dir", required=True)
    parser.add_argument("--compare-dir", required=True)
    parser.add_argument("--scenario", default="")
    parser.add_argument("--controller", default="controller/campus_l3_ids_controller_v13_decision_modes.py")
    parser.add_argument("--output-name", default="experiment_manifest")
    args = parser.parse_args()

    exp_dir = Path(args.exp_dir)
    final_run_dir = Path(args.final_run_dir)
    compare_dir = Path(args.compare_dir)

    if not exp_dir.exists():
        raise FileNotFoundError(f"Experiment directory not found: {exp_dir}")

    runtime_summary = safe_read_json(final_run_dir / "runtime_pipeline_summary.json")
    comparison_summary = safe_read_json(compare_dir / "final_top20_vs_port_aware_controller_summary.json")
    mixed_summary = safe_read_json(exp_dir / "mixed_traffic_experiment_summary.json")

    files = {
        "scenario": args.scenario,
        "pcap": exp_dir / "pcaps" / "mixed_benign_malicious_live.pcap",
        "controller": args.controller,
        "policy_decisions": exp_dir / "logs" / "policy_decisions.csv",
        "predictions": exp_dir / "logs" / "predictions.csv",
        "flow_stats": exp_dir / "logs" / "flow_stats.csv",
        "mitigation_log": exp_dir / "logs" / "mitigation_log.csv",
        "rate_limit_log": exp_dir / "logs" / "rate_limit_log.csv",
        "quarantine_log": exp_dir / "logs" / "quarantine_log.csv",
        "runtime_predictions": final_run_dir / "final_top20_runtime_predictions.csv",
        "protocol_aware_policy": final_run_dir / "final_top20_policy_decisions_protocol_aware_tool.csv",
        "runtime_report": final_run_dir / "runtime_pipeline_report.md",
        "comparison_report": compare_dir / "final_top20_vs_port_aware_controller_report.md",
        "comparison_summary": compare_dir / "final_top20_vs_port_aware_controller_summary.json",
        "mixed_report": exp_dir / "mixed_traffic_experiment_report.md",
        "mixed_summary": exp_dir / "mixed_traffic_experiment_summary.json",
    }

    row_counts = {
        "policy_decisions": safe_row_count(files["policy_decisions"]),
        "predictions": safe_row_count(files["predictions"]),
        "flow_stats": safe_row_count(files["flow_stats"]),
        "mitigation_log": safe_row_count(files["mitigation_log"]),
        "rate_limit_log": safe_row_count(files["rate_limit_log"]),
        "quarantine_log": safe_row_count(files["quarantine_log"]),
        "runtime_predictions": safe_row_count(files["runtime_predictions"]),
        "protocol_aware_policy": safe_row_count(files["protocol_aware_policy"]),
    }

    active_model_info = runtime_summary.get("active_model_info", {})
    model_metadata = active_model_info.get("model_metadata", {})

    manifest = {
        "generated_at_utc": datetime.utcnow().isoformat(),
        "experiment": {
            "exp_dir": str(exp_dir),
            "final_run_dir": str(final_run_dir),
            "compare_dir": str(compare_dir),
            "scenario": args.scenario,
            "controller": args.controller,
            "decision_mode": "hybrid",
            "environment": {
                "python_version": platform.python_version(),
                "platform": platform.platform(),
                "hostname": platform.node(),
            },
        },
        "model": {
            "model_status": active_model_info.get("model_status"),
            "model_name": model_metadata.get("model_name"),
            "algorithm": model_metadata.get("algorithm"),
            "dataset_family": model_metadata.get("dataset_family"),
            "feature_count": model_metadata.get("feature_count"),
            "feature_selection_method": model_metadata.get("feature_selection_method"),
            "input_schema": model_metadata.get("input_schema"),
            "threshold": model_metadata.get("threshold"),
            "holdout_metrics": model_metadata.get("holdout_metrics", {}),
        },
        "files": {k: file_info(v) if k != "scenario" else str(v) for k, v in files.items()},
        "row_counts": row_counts,
        "runtime_summary": {
            "prediction_summary": runtime_summary.get("prediction_summary", {}),
        },
        "comparison_summary": comparison_summary,
        "mixed_traffic_summary": {
            "action_counts": mixed_summary.get("action_counts", {}),
            "row_counts": mixed_summary.get("row_counts", {}),
        },
        "reproducibility_checklist": [
            {
                "step": 1,
                "item": "Activate project virtual environment",
                "command": "cd /root/sdn-campus-security-platform && source venv/bin/activate",
            },
            {
                "step": 2,
                "item": "Start ML FastAPI service and verify active model",
                "command": "curl http://127.0.0.1:8000/health && curl http://127.0.0.1:8000/model-info | python -m json.tool",
            },
            {
                "step": 3,
                "item": "Start Ryu controller in hybrid decision mode",
                "command": "CONTROLLER_DECISION_MODE=hybrid ryu-manager controller/campus_l3_ids_controller_v13_decision_modes.py",
            },
            {
                "step": 4,
                "item": "Start Mininet campus topology",
                "command": "sudo mn --custom topology/campus_topology_v1.py --topo campus_v1 --controller=remote,ip=127.0.0.1,port=6653 --switch ovsk,protocols=OpenFlow13 --link tc",
            },
            {
                "step": 5,
                "item": "Generate mixed benign and malicious traffic and capture PCAP",
                "command": "Use generated run_commands.sh inside the experiment directory.",
            },
            {
                "step": 6,
                "item": "Run Final Top-20 runtime pipeline on captured PCAP",
                "command": "python ml-service/tools/run_final_top20_runtime_pipeline.py --pcap <pcap> --run-name <name> --output-root <runtime_pipeline_dir>",
            },
            {
                "step": 7,
                "item": "Build protocol-aware final policy output",
                "command": "python ml-service/tools/build_protocol_aware_final_policy.py --predictions <final_predictions.csv> --pcap <pcap> --output <protocol_aware_policy.csv>",
            },
            {
                "step": 8,
                "item": "Compare final model policy with controller policy/enforcement logs",
                "command": "python ml-service/tools/compare_final_top20_with_port_aware_controller_policy.py --final-policy <policy.csv> --controller-policy <policy_decisions.csv> --mitigation-log <mitigation_log.csv> --quarantine-log <quarantine_log.csv> --rate-limit-log <rate_limit_log.csv> --output-dir <compare_dir>",
            },
            {
                "step": 9,
                "item": "Generate mixed traffic experiment report",
                "command": "python ml-service/tools/generate_mixed_traffic_experiment_report.py --exp-dir <exp_dir> --final-run-dir <final_run_dir> --compare-dir <compare_dir>",
            },
        ],
    }

    json_path = exp_dir / f"{args.output_name}.json"
    md_path = exp_dir / f"{args.output_name}.md"

    json_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    md = []
    md.append("# Experiment Manifest and Reproducibility Checklist")
    md.append("")
    md.append(f"- Generated at UTC: `{manifest['generated_at_utc']}`")
    md.append(f"- Experiment directory: `{exp_dir}`")
    md.append(f"- Final runtime pipeline directory: `{final_run_dir}`")
    md.append(f"- Comparison directory: `{compare_dir}`")
    md.append(f"- Scenario: `{args.scenario}`")
    md.append(f"- Controller: `{args.controller}`")
    md.append("")

    md.append("## 1. Model")
    md.append("")
    md.append(f"- Model status: `{manifest['model'].get('model_status')}`")
    md.append(f"- Model name: `{manifest['model'].get('model_name')}`")
    md.append(f"- Algorithm: `{manifest['model'].get('algorithm')}`")
    md.append(f"- Dataset family: `{manifest['model'].get('dataset_family')}`")
    md.append(f"- Feature count: `{manifest['model'].get('feature_count')}`")
    md.append(f"- Feature selection method: `{manifest['model'].get('feature_selection_method')}`")
    md.append(f"- Input schema: `{manifest['model'].get('input_schema')}`")
    md.append("")

    md.append("## 2. Key Files")
    md.append("")
    md.append("| Item | Exists | Size Bytes | Path |")
    md.append("|---|---:|---:|---|")
    for key, info in manifest["files"].items():
        if key == "scenario":
            md.append(f"| {key} |  |  | `{info}` |")
        else:
            md.append(f"| {key} | {info['exists']} | {info['size_bytes']} | `{info['path']}` |")
    md.append("")

    md.append("## 3. Row Counts")
    md.append("")
    md.append("| File | Rows |")
    md.append("|---|---:|")
    for key, value in row_counts.items():
        md.append(f"| {key} | {value} |")
    md.append("")

    md.append("## 4. Main Comparison Metrics")
    md.append("")
    selected_metrics = [
        "matched_controller_exact_count",
        "matched_controller_ip_port_count",
        "action_match_count",
        "security_compatible_action_count",
        "matched_mitigation_drop_count",
        "matched_quarantine_count",
        "matched_rate_limit_count",
    ]
    md.append("| Metric | Value |")
    md.append("|---|---:|")
    for key in selected_metrics:
        md.append(f"| {key} | {comparison_summary.get(key)} |")
    md.append("")

    md.append("## 5. Reproducibility Checklist")
    md.append("")
    for item in manifest["reproducibility_checklist"]:
        md.append(f"### Step {item['step']} — {item['item']}")
        md.append("")
        md.append("```bash")
        md.append(item["command"])
        md.append("```")
        md.append("")

    md.append("## 6. Thesis Method Note")
    md.append("")
    md.append(
        "This manifest records the concrete runtime artifacts used to validate the SDN-based IDS/IPS prototype. "
        "It links the captured traffic, selected-feature runtime inference output, controller-side policy decisions, "
        "and OpenFlow enforcement logs in a single reproducible experiment record."
    )
    md.append("")

    md_path.write_text("\n".join(md), encoding="utf-8")

    print("[INFO] Written:", json_path)
    print("[INFO] Written:", md_path)


if __name__ == "__main__":
    main()
