#!/usr/bin/env python3
"""
Compare final Top-20 runtime ML pipeline decisions with port-aware controller logs.

Inputs:
- final_top20_policy_decisions.csv
- controller policy_decisions.csv
- controller mitigation_log.csv
- controller quarantine_log.csv
- controller rate_limit_log.csv

Matching key:
src_ip, dst_ip, src_port, dst_port, ip_proto

The script also supports relaxed matching by ignoring ip_proto when one side lacks it.
"""

import argparse
import json
from datetime import datetime
from pathlib import Path

import pandas as pd


def read_csv(path: Path) -> pd.DataFrame:
    if path is None or not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame()
    return pd.read_csv(path)


def normalize_int_value(value, default=0):
    try:
        if pd.isna(value):
            return default
        if value == "":
            return default
        return int(float(value))
    except Exception:
        return default


def normalize_str_value(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


def build_flow_key(src, dst, src_port, dst_port, proto):
    return (
        f"{normalize_str_value(src)}|"
        f"{normalize_str_value(dst)}|"
        f"{normalize_int_value(src_port)}|"
        f"{normalize_int_value(dst_port)}|"
        f"{normalize_int_value(proto)}"
    )


def build_ip_port_key(src, dst, src_port, dst_port):
    return (
        f"{normalize_str_value(src)}|"
        f"{normalize_str_value(dst)}|"
        f"{normalize_int_value(src_port)}|"
        f"{normalize_int_value(dst_port)}"
    )


def prepare_final_df(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    out = df.copy()

    rename_map = {
        "src_ip_final": "src_ip",
        "dst_ip_final": "dst_ip",
        "source_ip": "src_ip",
        "destination_ip": "dst_ip",
        "source_port": "src_port",
        "destination_port": "dst_port",
        "policy_final_action_final": "policy_final_action",
    }

    for old, new in rename_map.items():
        if old in out.columns and new not in out.columns:
            out[new] = out[old]

    if "ip_proto" not in out.columns:
        if "protocol" in out.columns:
            out["ip_proto"] = out["protocol"]
        else:
            # Runtime final_top20_policy_decisions may not include protocol.
            out["ip_proto"] = 0

    required = ["src_ip", "dst_ip", "src_port", "dst_port", "ip_proto"]
    for col in required:
        if col not in out.columns:
            out[col] = 0 if "port" in col or col == "ip_proto" else ""

    out["flow_key"] = out.apply(
        lambda r: build_flow_key(
            r["src_ip"], r["dst_ip"], r["src_port"], r["dst_port"], r["ip_proto"]
        ),
        axis=1,
    )
    out["ip_port_key"] = out.apply(
        lambda r: build_ip_port_key(
            r["src_ip"], r["dst_ip"], r["src_port"], r["dst_port"]
        ),
        axis=1,
    )

    return out


def prepare_controller_policy_df(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    out = df.copy()

    rename_map = {
        "ipv4_src": "src_ip",
        "ipv4_dst": "dst_ip",
    }

    for old, new in rename_map.items():
        if old in out.columns and new not in out.columns:
            out[new] = out[old]

    required = ["src_ip", "dst_ip", "src_port", "dst_port", "ip_proto"]
    for col in required:
        if col not in out.columns:
            out[col] = 0 if "port" in col or col == "ip_proto" else ""

    out["flow_key"] = out.apply(
        lambda r: build_flow_key(
            r["src_ip"], r["dst_ip"], r["src_port"], r["dst_port"], r["ip_proto"]
        ),
        axis=1,
    )
    out["ip_port_key"] = out.apply(
        lambda r: build_ip_port_key(
            r["src_ip"], r["dst_ip"], r["src_port"], r["dst_port"]
        ),
        axis=1,
    )

    return out


def prepare_action_log_df(df: pd.DataFrame, log_type: str) -> pd.DataFrame:
    if df.empty:
        return df

    out = df.copy()

    if log_type == "quarantine":
        if "original_dst_ip" in out.columns and "dst_ip" not in out.columns:
            out["dst_ip"] = out["original_dst_ip"]

    required = ["src_ip", "dst_ip", "src_port", "dst_port", "ip_proto"]
    for col in required:
        if col not in out.columns:
            out[col] = 0 if "port" in col or col == "ip_proto" else ""

    out["flow_key"] = out.apply(
        lambda r: build_flow_key(
            r["src_ip"], r["dst_ip"], r["src_port"], r["dst_port"], r["ip_proto"]
        ),
        axis=1,
    )
    out["ip_port_key"] = out.apply(
        lambda r: build_ip_port_key(
            r["src_ip"], r["dst_ip"], r["src_port"], r["dst_port"]
        ),
        axis=1,
    )

    return out


def action_severity(action) -> int:
    """
    Higher value means stronger/more security-relevant action.
    Used when multiple controller policy rows exist for the same flow.
    """
    a = str(action).strip().lower()

    order = {
        "allow": 0,
        "monitor": 1,
        "rate_limit": 2,
        "drop": 3,
        "quarantine_candidate": 4,
        "quarantine": 4,
    }

    return order.get(a, 0)


def index_best_action(df: pd.DataFrame, key_col: str) -> dict:
    """
    Build an index by key, keeping the strongest observed policy action.

    FlowStats logs may contain early zero-rate allow rows for a flow and later
    attack/drop/quarantine rows for the same flow. For comparison with the final
    runtime pipeline, the strongest observed controller action is more meaningful
    than the first observed row.
    """
    if df.empty or key_col not in df.columns:
        return {}

    result = {}

    for _, row in df.iterrows():
        key = row[key_col]
        row_dict = row.to_dict()

        current = result.get(key)
        if current is None:
            result[key] = row_dict
            continue

        current_action = current.get("policy_final_action", current.get("recommended_action", ""))
        candidate_action = row_dict.get("policy_final_action", row_dict.get("recommended_action", ""))

        if action_severity(candidate_action) > action_severity(current_action):
            result[key] = row_dict

    return result


def counts(df: pd.DataFrame, column: str) -> dict:
    if df.empty or column not in df.columns:
        return {}
    return {str(k): int(v) for k, v in df[column].value_counts(dropna=False).to_dict().items()}

def security_compatible(final_action, controller_action) -> bool:
    """
    Security-aware action compatibility.

    Exact string equality is too strict because controller policy can escalate
    a final DROP recommendation into quarantine_candidate after repeated
    high-confidence observations.
    """
    f = str(final_action).strip().lower()
    c = str(controller_action).strip().lower()

    if f in {"drop"} and c in {"drop", "quarantine_candidate", "quarantine"}:
        return True

    if f in {"allow", "allow_control_flow"} and c in {"allow"}:
        return True

    if f in {"monitor"} and c in {"monitor", "rate_limit", "drop", "quarantine_candidate", "quarantine"}:
        return True

    if f in {"rate_limit"} and c in {"rate_limit", "drop", "quarantine_candidate", "quarantine"}:
        return True

    return f == c


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--final-policy", required=True)
    parser.add_argument("--controller-policy", required=True)
    parser.add_argument("--mitigation-log", default=None)
    parser.add_argument("--quarantine-log", default=None)
    parser.add_argument("--rate-limit-log", default=None)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    final_policy_path = Path(args.final_policy)
    controller_policy_path = Path(args.controller_policy)
    mitigation_path = Path(args.mitigation_log) if args.mitigation_log else None
    quarantine_path = Path(args.quarantine_log) if args.quarantine_log else None
    rate_limit_path = Path(args.rate_limit_log) if args.rate_limit_log else None
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    final_df = prepare_final_df(read_csv(final_policy_path))
    controller_df = prepare_controller_policy_df(read_csv(controller_policy_path))
    mitigation_df = prepare_action_log_df(read_csv(mitigation_path), "mitigation")
    quarantine_df = prepare_action_log_df(read_csv(quarantine_path), "quarantine")
    rate_limit_df = prepare_action_log_df(read_csv(rate_limit_path), "rate_limit")

    controller_by_flow = index_best_action(controller_df, "flow_key")
    controller_by_ip_port = index_best_action(controller_df, "ip_port_key")

    mitigation_by_flow = index_best_action(mitigation_df, "flow_key")
    mitigation_by_ip_port = index_best_action(mitigation_df, "ip_port_key")

    quarantine_by_flow = index_best_action(quarantine_df, "flow_key")
    quarantine_by_ip_port = index_best_action(quarantine_df, "ip_port_key")

    rate_limit_by_flow = index_best_action(rate_limit_df, "flow_key")
    rate_limit_by_ip_port = index_best_action(rate_limit_df, "ip_port_key")

    rows = []

    for _, r in final_df.iterrows():
        flow_key = r["flow_key"]
        ip_port_key = r["ip_port_key"]

        exact_controller = controller_by_flow.get(flow_key)
        relaxed_controller = controller_by_ip_port.get(ip_port_key)

        matched_controller = exact_controller or relaxed_controller

        mitigation_match = mitigation_by_flow.get(flow_key) or mitigation_by_ip_port.get(ip_port_key)
        quarantine_match = quarantine_by_flow.get(flow_key) or quarantine_by_ip_port.get(ip_port_key)
        rate_limit_match = rate_limit_by_flow.get(flow_key) or rate_limit_by_ip_port.get(ip_port_key)

        final_action = r.get("policy_final_action", r.get("recommended_action", ""))
        final_prediction = r.get("prediction", r.get("prediction_final", ""))
        final_prob = r.get("attack_probability", r.get("attack_probability_final", ""))

        controller_action = ""
        controller_prediction = ""
        controller_confidence = ""

        if matched_controller:
            controller_action = matched_controller.get("policy_final_action", "")
            controller_prediction = matched_controller.get("ml_prediction", "")
            controller_confidence = matched_controller.get("ml_confidence", "")

        rows.append({
            "src_ip": r.get("src_ip", ""),
            "dst_ip": r.get("dst_ip", ""),
            "src_port": normalize_int_value(r.get("src_port", 0)),
            "dst_port": normalize_int_value(r.get("dst_port", 0)),
            "ip_proto": normalize_int_value(r.get("ip_proto", 0)),
            "flow_key": flow_key,
            "ip_port_key": ip_port_key,
            "final_prediction": final_prediction,
            "final_attack_probability": final_prob,
            "final_action": final_action,
            "matched_controller_exact": exact_controller is not None,
            "matched_controller_ip_port": matched_controller is not None,
            "controller_action": controller_action,
            "controller_prediction": controller_prediction,
            "controller_confidence": controller_confidence,
            "action_match": (
                str(final_action).strip().lower()
                == str(controller_action).strip().lower()
                if controller_action != ""
                else False
            ),
            "security_compatible_action": (
                security_compatible(final_action, controller_action)
                if controller_action != ""
                else False
            ),
            "matched_mitigation_drop": mitigation_match is not None,
            "matched_quarantine": quarantine_match is not None,
            "matched_rate_limit": rate_limit_match is not None,
        })

    comparison_df = pd.DataFrame(rows)

    comparison_csv = output_dir / "final_top20_vs_port_aware_controller_comparison.csv"
    summary_json = output_dir / "final_top20_vs_port_aware_controller_summary.json"
    report_md = output_dir / "final_top20_vs_port_aware_controller_report.md"

    comparison_df.to_csv(comparison_csv, index=False)

    summary = {
        "generated_at_utc": datetime.utcnow().isoformat(),
        "inputs": {
            "final_policy": str(final_policy_path),
            "controller_policy": str(controller_policy_path),
            "mitigation_log": str(mitigation_path) if mitigation_path else "",
            "quarantine_log": str(quarantine_path) if quarantine_path else "",
            "rate_limit_log": str(rate_limit_path) if rate_limit_path else "",
        },
        "row_counts": {
            "final_policy": int(len(final_df)),
            "controller_policy": int(len(controller_df)),
            "mitigation_log": int(len(mitigation_df)),
            "quarantine_log": int(len(quarantine_df)),
            "rate_limit_log": int(len(rate_limit_df)),
            "comparison": int(len(comparison_df)),
        },
        "final_action_counts": counts(final_df, "policy_final_action"),
        "controller_action_counts": counts(controller_df, "policy_final_action"),
        "mitigation_action_counts": counts(mitigation_df, "policy_final_action"),
        "quarantine_action_counts": counts(quarantine_df, "policy_final_action"),
        "rate_limit_action_counts": counts(rate_limit_df, "policy_final_action"),
        "matched_controller_exact_count": int(comparison_df["matched_controller_exact"].sum()) if not comparison_df.empty else 0,
        "matched_controller_ip_port_count": int(comparison_df["matched_controller_ip_port"].sum()) if not comparison_df.empty else 0,
        "action_match_count": int(comparison_df["action_match"].sum()) if not comparison_df.empty else 0,
        "security_compatible_action_count": int(comparison_df["security_compatible_action"].sum()) if not comparison_df.empty else 0,
        "matched_mitigation_drop_count": int(comparison_df["matched_mitigation_drop"].sum()) if not comparison_df.empty else 0,
        "matched_quarantine_count": int(comparison_df["matched_quarantine"].sum()) if not comparison_df.empty else 0,
        "matched_rate_limit_count": int(comparison_df["matched_rate_limit"].sum()) if not comparison_df.empty else 0,
    }

    summary_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = []
    lines.append("# Final Top-20 vs Port-Aware Controller Policy Comparison")
    lines.append("")
    lines.append(f"- Generated at UTC: `{summary['generated_at_utc']}`")
    lines.append("")
    lines.append("## Inputs")
    lines.append("")
    for k, v in summary["inputs"].items():
        lines.append(f"- {k}: `{v}`")
    lines.append("")
    lines.append("## Row Counts")
    lines.append("")
    for k, v in summary["row_counts"].items():
        lines.append(f"- {k}: `{v}`")
    lines.append("")
    lines.append("## Match Summary")
    lines.append("")
    lines.append(f"- Exact controller flow-key matches: `{summary['matched_controller_exact_count']}`")
    lines.append(f"- Relaxed IP-port controller matches: `{summary['matched_controller_ip_port_count']}`")
    lines.append(f"- Action matches: `{summary['action_match_count']}`")
    lines.append(f"- Security-compatible action matches: `{summary['security_compatible_action_count']}`")
    lines.append(f"- Matched DROP mitigation logs: `{summary['matched_mitigation_drop_count']}`")
    lines.append(f"- Matched quarantine logs: `{summary['matched_quarantine_count']}`")
    lines.append(f"- Matched rate-limit logs: `{summary['matched_rate_limit_count']}`")
    lines.append("")
    lines.append("## Action Distributions")
    lines.append("")
    lines.append(f"- Final actions: `{summary['final_action_counts']}`")
    lines.append(f"- Controller actions: `{summary['controller_action_counts']}`")
    lines.append(f"- Mitigation actions: `{summary['mitigation_action_counts']}`")
    lines.append(f"- Quarantine actions: `{summary['quarantine_action_counts']}`")
    lines.append(f"- Rate-limit actions: `{summary['rate_limit_action_counts']}`")
    lines.append("")
    lines.append("## Flow-Level Comparison")
    lines.append("")
    if comparison_df.empty:
        lines.append("_No comparison rows._")
    else:
        lines.append("| Flow Key | Final Action | Controller Action | Exact Match | IP-Port Match | Security-Compatible | DROP | Quarantine | Rate-limit |")
        lines.append("|---|---|---|---:|---:|---:|---:|---:|---:|")
        for _, row in comparison_df.iterrows():
            lines.append(
                f"| `{row['flow_key']}` "
                f"| `{row['final_action']}` "
                f"| `{row['controller_action']}` "
                f"| `{row['matched_controller_exact']}` "
                f"| `{row['matched_controller_ip_port']}` "
                f"| `{row['security_compatible_action']}` "
                f"| `{row['matched_mitigation_drop']}` "
                f"| `{row['matched_quarantine']}` "
                f"| `{row['matched_rate_limit']}` |"
            )
    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append(
        "This comparison uses a port-aware flow key. Exact matching requires "
        "`src_ip`, `dst_ip`, `src_port`, `dst_port`, and `ip_proto` to align. "
        "Relaxed matching uses IP and ports only, which is useful when the final "
        "runtime pipeline output does not include protocol."
    )

    report_md.write_text("\n".join(lines), encoding="utf-8")

    print("[INFO] Comparison completed.")
    print(f"[INFO] Comparison CSV: {comparison_csv}")
    print(f"[INFO] Summary JSON   : {summary_json}")
    print(f"[INFO] Report MD      : {report_md}")
    print()
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

