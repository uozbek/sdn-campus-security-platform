#!/usr/bin/env python3

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

ACTIVE_FEATURE_ORDER = PROJECT_ROOT / "ml-service" / "models" / "active" / "feature_order.json"
OUTPUT_REPORT = PROJECT_ROOT / "ml-service" / "experiments" / "reports" / "feature_schema_compatibility_report.json"

# Şu an roadmap/controller tarafında kullandığımız SDN runtime feature set'i.
# İleride controller dosyasından otomatik çıkarılabilir; şimdilik açık ve kontrollü tutuyoruz.
SDN_RUNTIME_FEATURES = [
    "ip_proto",
    "duration_sec",
    "packet_count",
    "byte_count",
    "packet_rate",
    "byte_rate",
    "src_segment_id",
    "dst_segment_id",
    "is_same_segment",
    "is_server_dst",
    "is_attacker_lab_src",
    "is_udp",
    "is_tcp",
    "is_icmp",
]

# Bazı kavramsal eşleşmeler. Bunlar birebir aynı şey değildir;
# sadece adapter tasarımı için ipucu sağlar.
POSSIBLE_SEMANTIC_MAPPING = {
    "Protocol": "ip_proto",
    "Flow_Duration": "duration_sec",
    "Total_Fwd_Packets": "packet_count",
    "Total_Length_of_Fwd_Packets": "byte_count",
    "Flow_Packets_s": "packet_rate",
    "Flow_Bytes_s": "byte_rate",
}


def main():
    if not ACTIVE_FEATURE_ORDER.exists():
        raise FileNotFoundError(f"Active feature_order.json bulunamadı: {ACTIVE_FEATURE_ORDER}")

    with ACTIVE_FEATURE_ORDER.open("r", encoding="utf-8") as f:
        active_features = json.load(f)

    active_set = set(active_features)
    sdn_set = set(SDN_RUNTIME_FEATURES)

    exact_common = sorted(active_set & sdn_set)
    active_only = [f for f in active_features if f not in sdn_set]
    sdn_only = [f for f in SDN_RUNTIME_FEATURES if f not in active_set]

    semantic_matches = []
    for cic_feature, sdn_feature in POSSIBLE_SEMANTIC_MAPPING.items():
        semantic_matches.append({
            "cicddos_feature": cic_feature,
            "sdn_runtime_feature": sdn_feature,
            "cicddos_feature_exists": cic_feature in active_set,
            "sdn_runtime_feature_exists": sdn_feature in sdn_set,
            "warning": "Semantic match only; units/time windows may differ."
        })

    direct_compatibility = len(active_only) == 0

    recommendation = {
        "direct_controller_integration": direct_compatibility,
        "recommended_strategy": None,
        "notes": []
    }

    if direct_compatibility:
        recommendation["recommended_strategy"] = "direct_use"
        recommendation["notes"].append(
            "Active model feature set is directly compatible with SDN runtime features."
        )
    else:
        recommendation["recommended_strategy"] = "dual_model_or_adapter"
        recommendation["notes"].extend([
            "CIC-DDoS2019 model should be kept as offline/reference IDS model.",
            "For controller runtime, either train a second SDN-runtime model using controller-produced features or implement a feature adapter with carefully validated semantics.",
            "Directly filling missing CIC-DDoS2019 features with zero is not recommended for production decisions.",
            "Use /predict-cicddos for offline model testing and /predict for controller runtime inference."
        ])

    report = {
        "active_model_feature_count": len(active_features),
        "sdn_runtime_feature_count": len(SDN_RUNTIME_FEATURES),
        "exact_common_features_count": len(exact_common),
        "exact_common_features": exact_common,
        "active_model_only_features_count": len(active_only),
        "active_model_only_features": active_only,
        "sdn_runtime_only_features_count": len(sdn_only),
        "sdn_runtime_only_features": sdn_only,
        "possible_semantic_mapping": semantic_matches,
        "recommendation": recommendation,
    }

    OUTPUT_REPORT.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_REPORT.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print("[INFO] Active model feature count:", len(active_features))
    print("[INFO] SDN runtime feature count:", len(SDN_RUNTIME_FEATURES))
    print("[INFO] Exact common feature count:", len(exact_common))
    print("[INFO] Direct compatibility:", direct_compatibility)
    print("[INFO] Recommendation:", recommendation["recommended_strategy"])
    print("[INFO] Report written:", OUTPUT_REPORT)


if __name__ == "__main__":
    main()
