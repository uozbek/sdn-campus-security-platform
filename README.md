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
