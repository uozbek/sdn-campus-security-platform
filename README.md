# SDN Campus Security Platform

This project implements a research-oriented SDN-based IDS/IPS testbed for campus networks.

## Main Components

- Mininet-based campus network topology
- Ryu/OpenFlow-based SDN controller
- Flow statistics collection
- ML/DL-based inference service
- Policy engine for detection decisions
- Mitigation mechanisms:
  - monitor
  - rate-limit
  - drop
  - quarantine
- Experiment runner and metrics collection

## Initial Development Phases

1. Project skeleton and configuration
2. Campus topology implementation
3. Modular Ryu controller
4. Flow statistics collection
5. ML inference API
6. Controller-to-ML integration
7. Policy engine
8. Mitigation mechanisms
9. Experiment scenarios
10. Evaluation and reporting

## Safety Notice

All traffic generation and attack simulation must be performed only inside an isolated Mininet laboratory environment.
Do not run attack traffic against real networks, public IP addresses, or institutional infrastructure.
