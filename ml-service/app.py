import csv
import json
import os
import time
import ipaddress
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "logs"
MODELS_DIR = BASE_DIR / "models"
ACTIVE_MODEL_DIR = Path(os.getenv("ACTIVE_MODEL_DIR", str(MODELS_DIR / "active")))
INFERENCE_LOG_FILE = LOG_DIR / "inference_log.csv"

MODEL_FILE = "model.pkl"
SCALER_FILE = "scaler.pkl"
FEATURE_ORDER_FILE = "feature_order.json"
LABEL_MAPPING_FILE = "label_mapping.json"
METADATA_FILE = "model_metadata.json"

class FlowFeatures(BaseModel):
    datapath_id: int
    ipv4_src: str
    ipv4_dst: str
    ip_proto: Optional[int] = None
    duration_sec: float = 0.0
    packet_count: float = 0.0
    byte_count: float = 0.0
    packet_rate: float = 0.0
    byte_rate: float = 0.0

app = FastAPI(
    title="SDN Campus ML Inference API",
    description="Real model inference service with heuristic fallback for SDN IDS/IPS prototype.",
    version="2.0.0"
)

MODEL: Optional[Any] = None
SCALER: Optional[Any] = None
FEATURE_ORDER: List[str] = []
LABEL_MAPPING: Dict[str, str] = {}
MODEL_METADATA: Dict[str, Any] = {}
MODEL_STATUS: str = "not_loaded"
MODEL_ERROR: str = ""

def ensure_log_dir() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)

def init_inference_log() -> None:
    ensure_log_dir()
    with open(INFERENCE_LOG_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "timestamp", "datapath_id", "ipv4_src", "ipv4_dst", "ip_proto",
            "duration_sec", "packet_count", "byte_count", "packet_rate", "byte_rate",
            "prediction", "confidence", "recommended_action", "model_id", "model_name",
            "model_status", "inference_latency_ms"
        ])

def ip_to_segment_id(ip_value: str) -> int:
    try:
        ip = ipaddress.ip_address(ip_value)
        subnets = {
            "10.10.10.0/24": 10, "10.10.20.0/24": 20, "10.10.30.0/24": 30,
            "10.10.40.0/24": 40, "10.10.50.0/24": 50, "10.10.60.0/24": 60,
            "10.10.70.0/24": 70, "10.10.99.0/24": 99,
        }
        for subnet, segment_id in subnets.items():
            if ip in ipaddress.ip_network(subnet):
                return segment_id
    except Exception:
        return 0
    return 0

def build_feature_dict(flow: FlowFeatures) -> Dict[str, float]:
    src_segment_id = ip_to_segment_id(flow.ipv4_src)
    dst_segment_id = ip_to_segment_id(flow.ipv4_dst)
    return {
        "datapath_id": float(flow.datapath_id),
        "ip_proto": float(flow.ip_proto or 0),
        "duration_sec": float(flow.duration_sec or 0.0),
        "packet_count": float(flow.packet_count or 0.0),
        "byte_count": float(flow.byte_count or 0.0),
        "packet_rate": float(flow.packet_rate or 0.0),
        "byte_rate": float(flow.byte_rate or 0.0),
        "src_segment_id": float(src_segment_id),
        "dst_segment_id": float(dst_segment_id),
        "is_same_segment": 1.0 if src_segment_id == dst_segment_id else 0.0,
        "is_server_dst": 1.0 if dst_segment_id == 40 else 0.0,
        "is_attacker_lab_src": 1.0 if src_segment_id == 60 else 0.0,
        "is_udp": 1.0 if flow.ip_proto == 17 else 0.0,
        "is_tcp": 1.0 if flow.ip_proto == 6 else 0.0,
        "is_icmp": 1.0 if flow.ip_proto == 1 else 0.0,
    }

def make_vector(flow: FlowFeatures) -> np.ndarray:
    feature_dict = build_feature_dict(flow)
    return np.asarray([float(feature_dict.get(name, 0.0)) for name in FEATURE_ORDER], dtype=float).reshape(1, -1)

def normalize_prediction(raw_prediction: Any) -> str:
    key = str(raw_prediction)
    if key in LABEL_MAPPING:
        return LABEL_MAPPING[key]
    if isinstance(raw_prediction, str):
        return raw_prediction
    try:
        class_id = int(raw_prediction)
        if class_id == 0:
            return "benign"
        if class_id == 1:
            return "suspicious"
        if class_id == 2:
            return "ddos_suspected"
    except Exception:
        pass
    return "unknown"

def recommended_action_from_prediction(prediction: str, confidence: float) -> str:
    if prediction in {"ddos", "ddos_suspected", "attack", "malicious"}:
        return "drop"
    if prediction in {"suspicious", "anomaly", "anomaly_observed"}:
        return "rate_limit"
    if confidence >= 0.95:
        return "drop"
    if confidence >= 0.85:
        return "rate_limit"
    if confidence >= 0.70:
        return "monitor"
    return "allow"

def heuristic_baseline_predict(flow: FlowFeatures) -> Dict[str, Any]:
    packet_rate = float(flow.packet_rate or 0.0)
    byte_rate = float(flow.byte_rate or 0.0)
    if packet_rate >= 5000 or byte_rate >= 10_000_000:
        prediction, confidence, recommended_action = "ddos_suspected", 0.95, "drop"
    elif packet_rate >= 800 or byte_rate >= 1_000_000:
        prediction, confidence, recommended_action = "suspicious", 0.85, "rate_limit"
    elif packet_rate >= 100 or byte_rate >= 300_000:
        prediction, confidence, recommended_action = "anomaly_observed", 0.72, "monitor"
    else:
        prediction, confidence, recommended_action = "benign", 0.60, "allow"
    return {
        "prediction": prediction,
        "confidence": confidence,
        "recommended_action": recommended_action,
        "model_id": "M000",
        "model_name": "heuristic_baseline",
        "model_status": "fallback"
    }

def real_model_predict(flow: FlowFeatures) -> Dict[str, Any]:
    vector = make_vector(flow)
    if SCALER is not None:
        vector = SCALER.transform(vector)
    raw_prediction = MODEL.predict(vector)[0]
    prediction = normalize_prediction(raw_prediction)
    confidence = 0.80
    if hasattr(MODEL, "predict_proba"):
        probabilities = MODEL.predict_proba(vector)[0]
        confidence = float(np.max(probabilities))
    recommended_action = recommended_action_from_prediction(prediction, confidence)
    return {
        "prediction": prediction,
        "confidence": confidence,
        "recommended_action": recommended_action,
        "model_id": MODEL_METADATA.get("model_id", "M001"),
        "model_name": MODEL_METADATA.get("model_name", "real_ml_model"),
        "model_status": "loaded"
    }

def append_inference_log(flow: FlowFeatures, result: Dict[str, Any], inference_latency_ms: float) -> None:
    ensure_log_dir()
    with open(INFERENCE_LOG_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.utcnow().isoformat(), flow.datapath_id, flow.ipv4_src, flow.ipv4_dst,
            flow.ip_proto if flow.ip_proto is not None else "", flow.duration_sec, flow.packet_count,
            flow.byte_count, flow.packet_rate, flow.byte_rate, result.get("prediction", ""),
            result.get("confidence", ""), result.get("recommended_action", ""), result.get("model_id", ""),
            result.get("model_name", ""), result.get("model_status", ""), inference_latency_ms
        ])

def load_json_file(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_model_artifacts() -> None:
    global MODEL, SCALER, FEATURE_ORDER, LABEL_MAPPING, MODEL_METADATA, MODEL_STATUS, MODEL_ERROR
    MODEL_STATUS = "not_loaded"
    MODEL_ERROR = ""
    model_path = ACTIVE_MODEL_DIR / MODEL_FILE
    scaler_path = ACTIVE_MODEL_DIR / SCALER_FILE
    feature_order_path = ACTIVE_MODEL_DIR / FEATURE_ORDER_FILE
    label_mapping_path = ACTIVE_MODEL_DIR / LABEL_MAPPING_FILE
    metadata_path = ACTIVE_MODEL_DIR / METADATA_FILE
    try:
        if not model_path.exists():
            MODEL_STATUS = "fallback"
            MODEL_ERROR = f"model file not found: {model_path}"
            return
        if not feature_order_path.exists():
            MODEL_STATUS = "fallback"
            MODEL_ERROR = f"feature_order.json not found: {feature_order_path}"
            return
        MODEL = joblib.load(model_path)
        SCALER = joblib.load(scaler_path) if scaler_path.exists() else None
        FEATURE_ORDER = load_json_file(feature_order_path, [])
        LABEL_MAPPING = load_json_file(label_mapping_path, {})
        MODEL_METADATA = load_json_file(metadata_path, {})
        if not FEATURE_ORDER:
            MODEL_STATUS = "fallback"
            MODEL_ERROR = "feature_order.json is empty"
            return
        MODEL_STATUS = "loaded"
        MODEL_ERROR = ""
    except Exception as exc:
        MODEL = None
        SCALER = None
        FEATURE_ORDER = []
        LABEL_MAPPING = {}
        MODEL_METADATA = {}
        MODEL_STATUS = "fallback"
        MODEL_ERROR = str(exc)

@app.on_event("startup")
def startup_event() -> None:
    init_inference_log()
    load_model_artifacts()

@app.get("/")
def root() -> Dict[str, Any]:
    return {
        "service": "SDN Campus ML Inference API",
        "version": "2.0.0",
        "model_status": MODEL_STATUS,
        "model_error": MODEL_ERROR,
        "active_model_dir": str(ACTIVE_MODEL_DIR)
    }

@app.get("/health")
def health() -> Dict[str, Any]:
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "model_status": MODEL_STATUS,
        "model_error": MODEL_ERROR,
        "active_model_dir": str(ACTIVE_MODEL_DIR)
    }

@app.get("/model-info")
def model_info() -> Dict[str, Any]:
    return {
        "model_status": MODEL_STATUS,
        "model_error": MODEL_ERROR,
        "active_model_dir": str(ACTIVE_MODEL_DIR),
        "model_metadata": MODEL_METADATA,
        "feature_order": FEATURE_ORDER,
        "label_mapping": LABEL_MAPPING
    }

@app.post("/reload-model")
def reload_model() -> Dict[str, Any]:
    load_model_artifacts()
    return {
        "status": "reloaded",
        "model_status": MODEL_STATUS,
        "model_error": MODEL_ERROR,
        "active_model_dir": str(ACTIVE_MODEL_DIR)
    }
def normalize_protocol(ip_proto: int) -> str:
    if ip_proto == 1:
        return "icmp"
    if ip_proto == 6:
        return "tcp"
    if ip_proto == 17:
        return "udp"
    return "other"


def runtime_heuristic_decision(packet_rate: float, byte_rate: float, ip_proto: int) -> dict:
    """
    SDN controller runtime feature set'i için tutarlı heuristic karar üretir.

    Bu endpoint CIC-DDoS2019 modelini kullanmaz.
    Controller'ın ürettiği runtime feature set'i:
    - packet_rate
    - byte_rate
    - ip_proto
    - packet_count
    - byte_count

    PSO-LightGBM modeli ise /predict-cicddos endpoint'inde kullanılır.
    """

    packet_rate = float(packet_rate or 0.0)
    byte_rate = float(byte_rate or 0.0)
    ip_proto = int(ip_proto or 0)

    proto_name = normalize_protocol(ip_proto)

    # Akış artık aktif değilse veya eski flow stat kalıntısı ise
    if packet_rate <= 0.0 and byte_rate <= 0.0:
        return {
            "prediction": "benign",
            "prediction_value": 0,
            "confidence": 0.05,
            "recommended_action": "allow",
            "reason": "zero_rate_flow_stats_ignored",
            "risk_level": "none",
            "protocol": proto_name,
        }

    # UDP yüksek hacimli trafik: saldırı benzeri davranış
    if ip_proto == 17:
        if packet_rate >= 2000 or byte_rate >= 3_000_000:
            return {
                "prediction": "attack",
                "prediction_value": 1,
                "confidence": 0.98,
                "recommended_action": "drop",
                "reason": "very_high_udp_rate",
                "risk_level": "high",
                "protocol": proto_name,
            }

        if packet_rate >= 800 or byte_rate >= 1_000_000:
            return {
                "prediction": "attack",
                "prediction_value": 1,
                "confidence": 0.92,
                "recommended_action": "rate_limit",
                "reason": "high_udp_rate",
                "risk_level": "medium",
                "protocol": proto_name,
            }

        if packet_rate >= 300 or byte_rate >= 500_000:
            return {
                "prediction": "suspicious",
                "prediction_value": 1,
                "confidence": 0.75,
                "recommended_action": "monitor",
                "reason": "moderate_udp_rate",
                "risk_level": "low",
                "protocol": proto_name,
            }

    # TCP yüksek ama daha temkinli davranalım.
    # Normal iperf TCP testlerinin yanlışlıkla drop olmasını istemiyoruz.
    if ip_proto == 6:
        if packet_rate >= 5000 or byte_rate >= 20_000_000:
            return {
                "prediction": "suspicious",
                "prediction_value": 1,
                "confidence": 0.80,
                "recommended_action": "monitor",
                "reason": "high_tcp_rate_monitor_only",
                "risk_level": "low",
                "protocol": proto_name,
            }

    # ICMP flood benzeri durum
    if ip_proto == 1:
        if packet_rate >= 1000:
            return {
                "prediction": "attack",
                "prediction_value": 1,
                "confidence": 0.90,
                "recommended_action": "rate_limit",
                "reason": "high_icmp_rate",
                "risk_level": "medium",
                "protocol": proto_name,
            }

    return {
        "prediction": "benign",
        "prediction_value": 0,
        "confidence": 0.10,
        "recommended_action": "allow",
        "reason": "runtime_features_below_threshold",
        "risk_level": "none",
        "protocol": proto_name,
    }

@app.post("/predict")
def predict(request: FlowFeatures) -> Dict[str, Any]:
    """
    SDN controller runtime prediction endpoint.

    Bu endpoint CIC-DDoS2019 PSO-LightGBM modelini kullanmaz.
    Controller runtime flow statistics için heuristic karar üretir.

    /predict-cicddos endpoint'i offline CIC-DDoS2019 selected ML modeli içindir.
    """

    start_time = time.perf_counter()

    packet_rate = float(getattr(request, "packet_rate", 0.0) or 0.0)
    byte_rate = float(getattr(request, "byte_rate", 0.0) or 0.0)
    ip_proto = int(getattr(request, "ip_proto", 0) or 0)

    decision = runtime_heuristic_decision(
        packet_rate=packet_rate,
        byte_rate=byte_rate,
        ip_proto=ip_proto,
    )

    inference_latency_ms = (time.perf_counter() - start_time) * 1000.0

    response = {
        "model_mode": "runtime_heuristic",
        "model_status": "loaded",
        "model_name": "runtime_heuristic_v1",
        "datapath_id": getattr(request, "datapath_id", None),
        "ipv4_src": getattr(request, "ipv4_src", ""),
        "ipv4_dst": getattr(request, "ipv4_dst", ""),
        "ip_proto": ip_proto,
        "packet_rate": packet_rate,
        "byte_rate": byte_rate,
        "prediction": decision["prediction"],
        "prediction_value": decision["prediction_value"],
        "confidence": decision["confidence"],
        "recommended_action": decision["recommended_action"],
        "reason": decision["reason"],
        "risk_level": decision["risk_level"],
        "protocol": decision["protocol"],
        "inference_latency_ms": inference_latency_ms,
    }

    return response
# -------------------------------------------------------------------
# CIC-DDoS2019 Active Model Test Endpoint
# -------------------------------------------------------------------
# Bu endpoint, Ryu controller'dan gelen runtime feature formatını bozmaz.
# /predict endpoint'i controller için kalır.
# /predict-cicddos endpoint'i ise CIC-DDoS2019 feature_order.json ile
# active modele doğrudan test isteği göndermek için kullanılır.


class CICDDoSPredictRequest(BaseModel):
    features: Dict[str, Any]


def _load_cicddos_active_artifacts():
    base_dir = Path(__file__).resolve().parent
    active_dir = base_dir / "models" / "active"

    model_path = active_dir / "model.pkl"
    feature_order_path = active_dir / "feature_order.json"
    label_mapping_path = active_dir / "label_mapping.json"
    metadata_path = active_dir / "model_metadata.json"

    if not model_path.exists():
        raise FileNotFoundError(f"Active model not found: {model_path}")

    if not feature_order_path.exists():
        raise FileNotFoundError(f"Feature order not found: {feature_order_path}")

    model = joblib.load(model_path)

    with feature_order_path.open("r", encoding="utf-8") as f:
        feature_order = json.load(f)

    if label_mapping_path.exists():
        with label_mapping_path.open("r", encoding="utf-8") as f:
            label_mapping = json.load(f)
    else:
        label_mapping = {"BENIGN": 0, "ATTACK": 1}

    if metadata_path.exists():
        with metadata_path.open("r", encoding="utf-8") as f:
            metadata = json.load(f)
    else:
        metadata = {}

    return model, feature_order, label_mapping, metadata


def _action_from_attack_probability(prob: float) -> str:
    if prob >= 0.95:
        return "DROP"
    if prob >= 0.85:
        return "QUARANTINE"
    if prob >= 0.75:
        return "RATE_LIMIT"
    if prob >= 0.55:
        return "ALERT"
    return "ALLOW"


def append_cicddos_inference_log(result: Dict[str, Any]) -> None:
    base_dir = Path(__file__).resolve().parent
    log_dir = base_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_path = log_dir / "cicddos_inference_log.csv"

    fieldnames = [
        "timestamp",
        "model_mode",
        "model_status",
        "model_name",
        "prediction",
        "prediction_value",
        "attack_probability",
        "recommended_action",
        "feature_count",
        "missing_feature_count",
        "extra_feature_count",
        "inference_latency_ms",
    ]

    row = {
        "timestamp": datetime.utcnow().isoformat(),
        "model_mode": result.get("model_mode", ""),
        "model_status": result.get("model_status", ""),
        "model_name": result.get("model_name", ""),
        "prediction": result.get("prediction", ""),
        "prediction_value": result.get("prediction_value", ""),
        "attack_probability": result.get("attack_probability", ""),
        "recommended_action": result.get("recommended_action", ""),
        "feature_count": result.get("feature_count", ""),
        "missing_feature_count": len(result.get("missing_features", [])),
        "extra_feature_count": len(result.get("extra_features", [])),
        "inference_latency_ms": result.get("inference_latency_ms", ""),
    }

    file_exists = log_path.exists()

    with log_path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        writer.writerow(row)

@app.post("/predict-cicddos")
def predict_cicddos(request: CICDDoSPredictRequest):
    start_time = time.perf_counter()

    model, feature_order, label_mapping, metadata = _load_cicddos_active_artifacts()

    row = {}

    missing_features = []
    extra_features = []

    input_features = request.features

    for feature in feature_order:
        if feature in input_features:
            row[feature] = input_features[feature]
        else:
            row[feature] = 0.0
            missing_features.append(feature)

    for feature in input_features.keys():
        if feature not in feature_order:
            extra_features.append(feature)

    X = pd.DataFrame([row], columns=feature_order)

    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(X)[0]
        attack_probability = float(proba[1])
    else:
        pred = int(model.predict(X)[0])
        attack_probability = 1.0 if pred == 1 else 0.0

    prediction_value = int(model.predict(X)[0])

    inverse_label_mapping = {int(v): k for k, v in label_mapping.items()}
    prediction_label = inverse_label_mapping.get(prediction_value, str(prediction_value))

    inference_latency_ms = (time.perf_counter() - start_time) * 1000.0

    result = {
        "model_mode": "ml_cicddos2019",
        "model_status": "loaded",
        "model_name": metadata.get("model_name", "unknown"),
        "prediction": prediction_label,
        "prediction_value": prediction_value,
        "attack_probability": attack_probability,
        "recommended_action": _action_from_attack_probability(attack_probability),
        "feature_count": len(feature_order),
        "missing_features": missing_features,
        "extra_features": extra_features,
        "inference_latency_ms": inference_latency_ms,
    }

    append_cicddos_inference_log(result)
    return result
