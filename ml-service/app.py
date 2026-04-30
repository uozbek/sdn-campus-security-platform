import os
import time
from datetime import datetime
from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field


# -------------------------------------------------------------------
# Path configuration
# -------------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, "ml-service", "logs")
INFERENCE_LOG_FILE = os.path.join(LOG_DIR, "inference_log.csv")


# -------------------------------------------------------------------
# FastAPI application
# -------------------------------------------------------------------

app = FastAPI(
    title="SDN Campus IDS/IPS ML Inference API",
    version="0.1.0",
    description="ML inference service for SDN-based campus IDS/IPS prototype."
)


# -------------------------------------------------------------------
# Request / response schemas
# -------------------------------------------------------------------

class FlowFeatures(BaseModel):
    datapath_id: int = Field(..., description="OpenFlow datapath/switch ID")
    ipv4_src: str = Field(..., description="Source IPv4 address")
    ipv4_dst: str = Field(..., description="Destination IPv4 address")
    ip_proto: Optional[int] = Field(None, description="IP protocol number: ICMP=1, TCP=6, UDP=17")
    duration_sec: float = Field(..., ge=0, description="Flow duration in seconds")
    packet_count: float = Field(..., ge=0, description="Total packet count")
    byte_count: float = Field(..., ge=0, description="Total byte count")
    packet_rate: float = Field(..., ge=0, description="Packets per second")
    byte_rate: float = Field(..., ge=0, description="Bytes per second")


class PredictionResponse(BaseModel):
    prediction: str
    confidence: float
    recommended_action: str
    model_id: str
    model_name: str
    inference_latency_ms: float
    timestamp: str


# -------------------------------------------------------------------
# Utility functions
# -------------------------------------------------------------------

def ensure_log_dir():
    os.makedirs(LOG_DIR, exist_ok=True)


def init_inference_log():
    ensure_log_dir()

    if not os.path.exists(INFERENCE_LOG_FILE):
        with open(INFERENCE_LOG_FILE, "w") as f:
            f.write(
                "timestamp,"
                "model_id,"
                "model_name,"
                "datapath_id,"
                "ipv4_src,"
                "ipv4_dst,"
                "ip_proto,"
                "duration_sec,"
                "packet_count,"
                "byte_count,"
                "packet_rate,"
                "byte_rate,"
                "prediction,"
                "confidence,"
                "recommended_action,"
                "inference_latency_ms\n"
            )


def append_inference_log(features: FlowFeatures, response: PredictionResponse):
    ensure_log_dir()

    with open(INFERENCE_LOG_FILE, "a") as f:
        f.write(
            f"{response.timestamp},"
            f"{response.model_id},"
            f"{response.model_name},"
            f"{features.datapath_id},"
            f"{features.ipv4_src},"
            f"{features.ipv4_dst},"
            f"{features.ip_proto if features.ip_proto is not None else ''},"
            f"{features.duration_sec},"
            f"{features.packet_count},"
            f"{features.byte_count},"
            f"{features.packet_rate},"
            f"{features.byte_rate},"
            f"{response.prediction},"
            f"{response.confidence},"
            f"{response.recommended_action},"
            f"{response.inference_latency_ms}\n"
        )


# -------------------------------------------------------------------
# Heuristic baseline model
# -------------------------------------------------------------------

def heuristic_baseline_predict(features: FlowFeatures):
    """
    Temporary baseline model for integration testing.

    This is NOT the final ML model.
    It provides deterministic allow/monitor/drop decisions based on
    simple packet_rate and byte_rate thresholds.

    Later, this function will be replaced by:
    - model_loader.py
    - scaler
    - feature_order.json
    - trained sklearn / PyTorch model
    """

    prediction = "benign"
    confidence = 0.60
    recommended_action = "allow"

    packet_rate = features.packet_rate
    byte_rate = features.byte_rate

    # Conservative thresholds for lab-only testing.
    # These values should be tuned after observing normal traffic baselines.
    if packet_rate >= 1000 or byte_rate >= 5_000_000:
        prediction = "ddos_suspected"
        confidence = 0.95
        recommended_action = "drop"

    elif packet_rate >= 300 or byte_rate >= 1_000_000:
        prediction = "suspicious"
        confidence = 0.85
        recommended_action = "rate_limit"

    elif packet_rate >= 100 or byte_rate >= 300_000:
        prediction = "anomaly_observed"
        confidence = 0.72
        recommended_action = "monitor"

    return prediction, confidence, recommended_action


# -------------------------------------------------------------------
# API lifecycle
# -------------------------------------------------------------------

@app.on_event("startup")
def startup_event():
    init_inference_log()


# -------------------------------------------------------------------
# API endpoints
# -------------------------------------------------------------------

@app.get("/")
def root():
    return {
        "service": "SDN Campus IDS/IPS ML Inference API",
        "status": "running",
        "version": "0.1.0",
        "model": "heuristic_baseline"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/predict", response_model=PredictionResponse)
def predict(features: FlowFeatures):
    start_time = time.perf_counter()

    prediction, confidence, recommended_action = heuristic_baseline_predict(features)

    end_time = time.perf_counter()
    inference_latency_ms = (end_time - start_time) * 1000

    response = PredictionResponse(
        prediction=prediction,
        confidence=confidence,
        recommended_action=recommended_action,
        model_id="M000",
        model_name="heuristic_baseline",
        inference_latency_ms=inference_latency_ms,
        timestamp=datetime.utcnow().isoformat()
    )

    append_inference_log(features, response)

    return response
