# SDN Campus Security Platform

## Project Overview

This project is a research-oriented SDN security platform for designing and validating machine-learning-assisted IDS/IPS mechanisms in a simulated campus network environment. It uses Mininet and Open vSwitch to emulate campus-like network topologies, the Ryu SDN controller to collect flow statistics and apply OpenFlow-based policies, and a FastAPI-based machine learning service to provide runtime traffic classification signals.

The platform focuses on evaluating how offline-trained DDoS detection models can be integrated into an SDN control plane and transformed into policy decisions such as allow, monitor, rate-limit, drop, and quarantine. It enables controlled experimentation with benign and malicious traffic scenarios without affecting production infrastructure.

The current prototype is intended for academic research on SDN-based DDoS detection and prevention, runtime feature extraction, controller-side policy enforcement, and reproducible IDS/IPS validation workflows.

## Core Components

- **Mininet / Open vSwitch testbed:** Emulates a campus-like SDN topology with benign clients, attacker hosts, target services, and quarantine-related network segments.
- **Ryu SDN controller:** Collects flow statistics, maintains policy logic, and applies OpenFlow-based mitigation actions.
- **Machine learning service:** Exposes the active detection model through a FastAPI inference API.
- **Runtime feature extraction pipeline:** Converts captured traffic into model-compatible flow-level features.
- **Policy and mitigation layer:** Translates model signals and network context into allow, monitor, rate-limit, drop, or quarantine decisions.
- **Experiment and reporting tools:** Produce repeatable runtime validation outputs, logs, tables, and thesis-ready artifacts.

## Research Context

The project supports doctoral research on software-defined campus network security, with a focus on DDoS detection and prevention using machine learning-assisted IDS/IPS mechanisms. The main research direction is not limited to offline model accuracy; instead, it evaluates whether trained models can be operationalized inside an SDN control loop and connected to practical mitigation behavior.

## Repository Scope

This repository contains source code, controller applications, topology definitions, experiment scripts, utility tools, and thesis-related markdown documentation. Large datasets, binary model artifacts, PCAP files, generated DOCX/PDF documents, and runtime logs are intentionally excluded from version control.

## Code Overview

This repository contains a research testbed for an SDN-based Intrusion Detection and Prevention System (IDS/IPS) designed for campus-like network environments. It integrates Mininet and Open vSwitch for network emulation, the Ryu SDN controller for programmable traffic management, and a FastAPI-based machine learning service for runtime traffic classification and policy support.

### Core Infrastructure and Configuration

- `config.yaml`: Central configuration file for network segments, SDN controller parameters, ML service endpoints, and IDS/IPS policy thresholds.
- `requirements.txt`: Python dependencies for the SDN controller, FastAPI service, machine learning pipeline, experiment tools, and thesis-support utilities.
- `README.md`: High-level description of the platform, repository scope, and development context.

### SDN Controller (`controller/`)

The controller module follows an incremental development path from basic L3 routing toward ML-assisted IDS/IPS behavior.

- `campus_l3_controller_v1.py` and `campus_l3_controller_v2.py`: Early L3-aware routing controllers with ARP handling, virtual gateway behavior, and static host mapping.
- `campus_l3_ids_controller_v3.py` to later versions: Progressive integration of flow statistics collection, ML API calls, policy decisions, and mitigation actions such as drop, rate-limit, and quarantine-related handling.
- Decision-mode controller variants: Support experimentation with heuristic-only, ML-only, and hybrid decision logic where available.
- Observe-only controller generation utilities: Support baseline or controller-overhead experiments where detection and logging are enabled but mitigation actions are disabled.

### Machine Learning Service (`ml-service/`)

- `app.py`: Main FastAPI application that exposes model inference endpoints to the SDN controller and supports fallback behavior where applicable.
- `app_heuristic_fallback.py`: Simplified heuristic-oriented service variant used for testing and fallback scenarios.
- `training/`: Model development and evaluation pipeline, including dataset cleaning, feature reduction, feature selection experiments, candidate model training, and export of the active runtime model.
- Feature schema tools: Utilities such as schema compatibility checks help ensure that runtime-extracted flow features match the feature order expected by the active model.

### Topology and Experiments

- `topology/campus_topology_v1.py`: Mininet topology definition for a campus-like SDN environment with multiple logical network segments.
- `experiments/`: Scripts and scenario definitions for controlled traffic generation, runtime validation, and IDS/IPS policy testing.
- `traffic-generator/`: Command templates and helper notes for producing normal and attack-like traffic patterns during experiments.

### Documentation and Thesis Support (`docs/`)

The `docs/` directory contains thesis chapter drafts, architecture notes, API contracts, quality-control reports, citation/reference audit outputs, and thesis-support documentation. The thesis-related material supports a PhD study on machine-learning-assisted DDoS detection and prevention in software-defined campus networks.

Large datasets, binary model artifacts, PCAP captures, generated DOCX/PDF files, and runtime logs are intentionally excluded from version control.

## Repository Structure

The repository is organized around five main concerns: SDN control, machine learning inference, experiment execution, monitoring, and thesis-oriented research documentation.

### Applications

- `apps/literature_relevance/`: Streamlit-based literature relevance analysis tools used to evaluate thesis-related papers, extract abstracts/full-text signals, summarize findings, and support reference screening workflows.

### SDN Controller

- `controller/`: Contains the evolution of the Ryu-based SDN controller implementation.
  - `campus_l3_controller_v1.py` and `campus_l3_controller_v2.py` provide the early L3 routing and ARP-handling foundation.
  - `campus_l3_ids_controller_v3.py` to `campus_l3_ids_controller_v13_decision_modes.py` progressively introduce flow monitoring, ML service integration, policy decision logic, mitigation behavior, runtime metrics, and decision-mode experimentation.
  - `campus_l3_ids_controller_v10_observe_only.py` supports observe-only experiments where detection and logging are active but mitigation actions are disabled.

### Machine Learning Service

- `ml-service/`: Provides the FastAPI-based model service, training scripts, model metadata, and thesis-support utilities.
  - `app.py` is the main runtime inference API used by the SDN controller.
  - `app_heuristic_fallback.py` provides a simplified heuristic fallback service for testing and fallback scenarios.
  - `training/` contains the model development pipeline, including dataset preparation, cleaning, feature reduction, feature selection experiments, candidate model training, model comparison, and final XGBoost Top-20 export.
  - `models/active/` stores lightweight metadata required by the active runtime model, such as feature order, label mapping, and model metadata. Large binary model files are intentionally excluded from version control.
  - `tools/` contains experiment reporting, runtime validation, citation auditing, thesis DOCX assembly, reference processing, and quality-control utilities.

### Topology, Experiments, and Traffic Generation

- `topology/`: Defines the Mininet-based campus network topology.
- `experiments/`: Contains scenario definitions and scripts for controlled runtime validation experiments.
- `traffic-generator/`: Provides command templates for generating normal traffic and high-rate TCP/UDP traffic during experiments.
- `monitoring/`: Contains scripts for controller resource monitoring, runtime metric reporting, and LaTeX/TikZ-ready reporting outputs.

### Documentation and Thesis Support

- `docs/`: Contains thesis chapter drafts, architecture notes, API contracts, runtime validation reports, citation/reference audits, SAÜ FBE formatting checks, and thesis quality-control outputs.
- `roadmap.md`: Tracks the development roadmap and major implementation stages of the SDN Campus Security Platform.
- `config.yaml`: Central configuration for network segments, controller settings, ML service endpoints, and IDS/IPS policy thresholds.
- `requirements.txt`: Python dependencies required for the controller, ML service, training scripts, monitoring tools, and document utilities.

Large datasets, PCAP files, generated DOCX/PDF documents, binary model artifacts, runtime logs, and temporary backup files are excluded from version control to keep the repository lightweight and reproducible.

## Architecture and Quality Report

A repository-level architecture, code quality, and future feature roadmap is available in:

- [`docs/repo_analysis_architecture_quality_features.md`](docs/repo_analysis_architecture_quality_features.md)

Mermaid diagrams are available under:

- [`docs/figures/architecture_high_level.mmd`](docs/figures/architecture_high_level.mmd)
- [`docs/figures/ml_training_pipeline.mmd`](docs/figures/ml_training_pipeline.mmd)
- [`docs/figures/runtime_ids_ips_lifecycle.mmd`](docs/figures/runtime_ids_ips_lifecycle.mmd)
- [`docs/figures/data_preprocessing_pipeline.mmd`](docs/figures/data_preprocessing_pipeline.mmd)
- [`docs/figures/quality_improvement_roadmap.mmd`](docs/figures/quality_improvement_roadmap.mmd)
