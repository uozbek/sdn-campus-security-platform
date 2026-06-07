# Runtime Validation Results and Discussion

## Results

The proposed SDN-based IDS/IPS prototype was evaluated in a mixed benign/malicious runtime scenario using a Mininet-based testbed and a Ryu SDN controller. The active detection model was the Final XGBoost Top-20 model, which was queried through a FastAPI-based inference service using PCAP-derived CICFlowMeter-compatible selected features.

The main canonical run used for reporting was `run_05_port_aware_repeat_validation`. This run was selected because it included port-aware controller logs, protocol-aware final policy interpretation, and observable enforcement actions.

The runtime prediction output contained nine flow-level records. The Final XGBoost Top-20 model classified six flows as `BENIGN` and three flows as `ATTACK`. The protocol-aware final policy layer further interpreted these outputs as six `ALLOW_CONTROL_FLOW`, one `ALLOW`, one `DROP`, and one `QUARANTINE_OBSERVED` decision.

Controller-side logs showed 3203 policy decisions in total. The action distribution consisted of 3179 `allow`, 22 `quarantine_candidate`, one `drop`, and one `rate_limit` decision. Enforcement logs also confirmed seven drop mitigation records, seven quarantine records, and one rate-limit record.

The flow-level model-controller comparison showed five exact controller flow-key matches and five security-compatible matches. The malicious UDP flow from `10.10.60.12` to `10.10.40.14` was classified as `ATTACK` by the runtime model and mapped to `DROP` by the protocol-aware final policy. On the controller side, the same flow was associated with quarantine behavior, and matching drop, quarantine, and rate-limit evidence was observed.

## Discussion

The results indicate that the proposed architecture can move beyond offline classification and operate as a runtime SDN security mechanism. The system was able to extract selected flow features from live PCAP data, submit them to the active ML model, interpret the prediction output in a protocol-aware manner, and associate malicious traffic with controller-side enforcement actions.

The distinction between exact action matching and security-compatible matching is important. The ML model produces binary detection-oriented outputs, whereas the controller has a richer action space including allow, rate-limit, drop, and quarantine. Therefore, a model-side `DROP` decision and a controller-side `quarantine_candidate` decision should not necessarily be interpreted as disagreement. In this context, they represent compatible mitigation behavior against the same malicious UDP flow.

The protocol-aware final policy layer also improved interpretability. TCP control-like flows were separated from UDP attack flows, and post-mitigation traffic toward the quarantine host was labeled as `QUARANTINE_OBSERVED`. This prevented the runtime analysis from confusing controller-induced quarantine traffic with ordinary victim-directed attack traffic.

Overall, the experiment supports the feasibility of integrating a selected-feature ML model with SDN controller-side prevention logic. The observed rate-limit, drop, and quarantine actions demonstrate that the prototype functions as an IDS/IPS mechanism rather than an offline-only detector.

However, the experiment was conducted in a controlled Mininet environment. Future work should repeat the validation under more diverse traffic patterns, longer experiment durations, and larger CIC-DDoS2019-derived training subsets. In addition, controller-side timing, flow-stat polling intervals, and transport-port visibility should be further standardized to improve flow-level model-controller alignment.

