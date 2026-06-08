# Repository Analysis: Architecture, Quality, and Feature Roadmap

## 1. Purpose

This document summarizes the repository-level architecture, code quality observations, and future feature roadmap for the SDN Campus Security Platform. It is based on the external GitArch analysis report and adapted to match the thesis terminology and current repository state.

## 2. Architecture Summary

The platform is organized as a research-oriented SDN IDS/IPS testbed. It combines a Mininet/Open vSwitch campus-like topology, a Ryu SDN controller, a FastAPI-based machine learning service, runtime feature extraction tools, and OpenFlow-based mitigation actions.

The main control loop is as follows:

1. Mininet/Open vSwitch produces traffic in a segmented campus-like topology.
2. The Ryu controller collects flow statistics and receives packet-in events.
3. Flow-level information is sent to the FastAPI ML service.
4. The ML service returns prediction and confidence information.
5. The controller combines model output with protocol, port, traffic-rate, and risk-history context.
6. The controller produces allow, monitor, rate-limit, drop, or quarantine-related decisions.
7. OpenFlow rules or meters are used to apply selected mitigation behavior.

See `docs/figures/architecture_high_level.mmd`.

## 3. Machine Learning and Metaheuristic Feature Selection

The model development pipeline includes dataset cleaning, feature reduction, feature-selection experiments, candidate model training, and final model export. Metaheuristic feature-selection methods such as PSO, HHO, GWO, and DFO are part of the experimental candidate feature-selection stage.

These methods were used to explore feature subsets and compare candidate model behavior. However, the active runtime path is based on the final exported model selected according to model performance, feature compatibility, and SDN runtime integration requirements. In the current thesis prototype, the Final XGBoost Top-20 path is emphasized because it provides a compact, runtime-compatible feature representation and can be integrated with the FastAPI inference service and Ryu controller workflow.

See `docs/figures/ml_training_pipeline.mmd`.

## 4. Runtime IDS/IPS Lifecycle

The runtime IDS/IPS lifecycle connects flow statistics, ML inference, policy interpretation, and OpenFlow enforcement. The controller does not blindly apply model outputs. Instead, it evaluates model confidence together with network context and local policy rules.

The resulting action space includes:

- allow
- monitor
- rate-limit
- drop
- quarantine_candidate

See `docs/figures/runtime_ids_ips_lifecycle.mmd`.

## 5. Code Quality Findings

The external analysis report identified the following improvement areas:

1. More robust FastAPI error handling for malformed IP addresses and unavailable model files.
2. Centralized feature sanitization to avoid training/runtime feature drift.
3. More flexible configuration-driven paths for models, logs, and metadata.
4. Asynchronous or background logging to avoid blocking the inference path.
5. Stronger input validation using Pydantic types such as `IPvAnyAddress`.
6. More memory-efficient large dataset loading and preprocessing.

These points should be treated as future engineering improvements. They do not invalidate the research prototype but help define the next stage toward a more reliable and scalable implementation.

See `docs/figures/quality_improvement_roadmap.mmd`.

## 6. Future Feature Roadmap

The following improvements are recommended for future work:

- asynchronous controller-to-ML-service inference calls;
- confidence-based mitigation thresholds;
- configurable dry-run or observe-only mitigation mode;
- automated traffic generation using YAML scenarios;
- flow feature aggregation cache;
- model versioning and hot-swapping;
- false-positive feedback loop for future retraining;
- larger topology and distributed-controller experiments.

These items are aligned with the long-term goal of improving runtime scalability, reproducibility, and operational safety of the SDN IDS/IPS prototype.
