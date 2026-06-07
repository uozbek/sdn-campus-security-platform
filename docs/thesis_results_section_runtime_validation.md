# Runtime Validation of the Proposed SDN-Based IDS/IPS Prototype

## 1. Overview of the Runtime Validation Phase

This section presents the runtime validation results of the proposed SDN-based IDS/IPS prototype. The purpose of this phase is to move beyond offline machine learning evaluation and verify whether the trained detection model can be integrated with an SDN controller in a live experimental environment.

The validation experiment was conducted in a Mininet-based SDN testbed controlled by a Ryu controller. The runtime architecture included traffic generation, PCAP capture, selected-feature extraction, FastAPI-based model inference, controller-side policy decision-making, and OpenFlow-based mitigation. The active machine learning model used in this phase was the Final XGBoost Top-20 model, trained using a CIC-DDoS2019-compatible feature representation.

Unlike offline classification experiments, this runtime validation phase evaluates whether malicious traffic can be detected and whether the controller can translate this detection into practical enforcement actions such as rate-limiting, dropping, and quarantine forwarding.

## 2. Experimental Scenario

The runtime experiment used a mixed benign and malicious traffic scenario. Benign traffic was generated from hosts such as `10.10.10.2` and `10.10.10.3` toward the server host `10.10.40.14`. The malicious traffic was generated from `10.10.60.12` toward the same target server. The main malicious pattern was a high-volume UDP flow, while TCP control-like flows and benign UDP flows were also present in the captured traffic.

The canonical experiment selected for the main thesis reporting is:

`run_05_port_aware_repeat_validation`

This run was selected because it includes port-aware controller logs, protocol-aware runtime policy interpretation, and observed controller-side enforcement actions. Earlier runs were useful for debugging and validation, but `run_05` provides the cleanest flow-level comparison between runtime model decisions and controller-side policy actions.

## 3. Generated Experimental Artifacts

The outputs used in this section were generated under the following artifact directory:

`experiments/results/thesis_artifacts/run_05_port_aware_runtime_validation`

The directory contains thesis-ready tables, figures, and summary files. The most important files are:

- `thesis_artifacts_manifest.md`
- `thesis_artifacts_summary.json`
- `tables/table_canonical_runtime_validation_summary.csv`
- `tables/table_controller_action_distribution.csv`
- `tables/table_final_top20_prediction_distribution.csv`
- `tables/table_protocol_aware_final_policy_distribution.csv`
- `tables/table_enforcement_action_summary.csv`
- `tables/table_flow_level_model_controller_comparison.csv`
- `tables/table_protocol_aware_attack_probability_summary.csv`
- `figures/fig_controller_action_distribution.png`
- `figures/fig_final_top20_prediction_distribution.png`
- `figures/fig_protocol_aware_final_policy_distribution.png`
- `figures/fig_enforcement_action_summary.png`

These artifacts provide the basis for reporting both the runtime ML model behavior and the controller-side mitigation behavior.

## 4. Repeated Runtime Validation Results

Table 1 summarizes the canonical repeated runtime validation results. Two canonical runs were selected for thesis reporting: `run_03_aligned_clean` and `run_05_port_aware_repeat_validation`.

**Table 1. Canonical repeated runtime validation results**  
Source: `tables/table_canonical_runtime_validation_summary.csv`

In both canonical runs, the runtime pipeline generated nine Final Top-20 prediction records. The controller produced more than three thousand policy decision records per run, showing that the SDN controller continuously monitored flow statistics and applied the hybrid IDS/IPS policy logic during the experiment.

The key result is that both canonical runs produced five security-compatible flow-level matches between the runtime model output and controller-side behavior. In both runs, drop mitigation and quarantine-related evidence were observed. The second canonical run, `run_05_port_aware_repeat_validation`, additionally observed a rate-limit action, making it the strongest experimental run for thesis reporting.

The repeated validation results indicate that the proposed architecture is not limited to a single successful demonstration. Instead, the system shows consistent behavior across canonical runs, especially in terms of malicious UDP detection and controller-side mitigation.

## 5. Controller-Side Policy Action Distribution

**Table 2. Controller-side IDS/IPS policy action distribution**  
Source: `tables/table_controller_action_distribution.csv`

**Figure 1. Controller-side policy action distribution**  
Source: `figures/fig_controller_action_distribution.png`

The controller-side action distribution shows that most policy decisions were `allow`. This is expected because a large number of flow-stat records correspond to benign traffic, control flows, or zero-rate/low-rate states. However, the important observation is that the controller also generated security-relevant actions.

In `run_05_port_aware_repeat_validation`, the controller produced:

- 3179 `allow` decisions
- 22 `quarantine_candidate` decisions
- 1 `drop` decision
- 1 `rate_limit` decision

This distribution demonstrates that the controller did not operate as a passive monitoring component. Instead, it actively classified flow behavior and produced mitigation-oriented decisions when malicious UDP activity was detected.

## 6. Runtime Prediction Distribution of the Final XGBoost Top-20 Model

**Table 3. Runtime prediction distribution of the Final XGBoost Top-20 model**  
Source: `tables/table_final_top20_prediction_distribution.csv`

**Figure 2. Runtime BENIGN/ATTACK prediction distribution**  
Source: `figures/fig_final_top20_prediction_distribution.png`

The runtime prediction distribution shows that the Final XGBoost Top-20 model classified six flows as `BENIGN` and three flows as `ATTACK`.

This result is consistent with the mixed traffic design of the experiment. The benign class includes TCP control-like traffic and benign UDP traffic, while the attack class corresponds to malicious traffic generated from `10.10.60.12`. The presence of both benign and attack predictions in the same runtime capture supports the feasibility of applying the selected-feature model to live PCAP-derived flow records.

This is an important step beyond offline evaluation because the model was not only tested on static CSV data but also applied to features extracted from traffic captured during a live SDN experiment.

## 7. Protocol-Aware Final Policy Interpretation

**Table 4. Protocol-aware final policy distribution**  
Source: `tables/table_protocol_aware_final_policy_distribution.csv`

**Figure 3. Protocol-aware final policy action distribution**  
Source: `figures/fig_protocol_aware_final_policy_distribution.png`

The protocol-aware final policy layer was introduced to improve the interpretability of runtime model outputs. In the raw runtime prediction output, the model predicts whether a flow is benign or attack. However, for controller-side interpretation, this binary output is not always sufficient.

Some TCP flows may appear suspicious due to traffic context or source behavior, but they should not be treated in the same way as high-volume UDP attack flows. Therefore, the protocol-aware final policy separates the runtime outputs into more meaningful categories:

- `ALLOW_CONTROL_FLOW`
- `ALLOW`
- `DROP`
- `QUARANTINE_OBSERVED`

In `run_05`, the protocol-aware final policy produced:

- 6 `ALLOW_CONTROL_FLOW` entries
- 1 `ALLOW` entry
- 1 `DROP` entry
- 1 `QUARANTINE_OBSERVED` entry

This interpretation is important because it prevents TCP control-like traffic from being incorrectly interpreted as UDP flood traffic. It also distinguishes traffic observed after quarantine redirection from ordinary victim-directed traffic.

## 8. Enforcement Action Summary

**Table 5. SDN controller enforcement action summary**  
Source: `tables/table_enforcement_action_summary.csv`

**Figure 4. SDN controller enforcement action summary**  
Source: `figures/fig_enforcement_action_summary.png`

The enforcement summary provides evidence that the SDN controller translated detection decisions into concrete mitigation actions. In the canonical port-aware run, the following enforcement records were observed:

- 7 drop mitigation records
- 7 quarantine-related records
- 1 rate-limit record

The drop records indicate that OpenFlow drop rules were installed for the detected malicious UDP traffic. The quarantine records show that repeated high-confidence attack behavior triggered quarantine-related forwarding. The rate-limit record shows that the controller was also capable of applying a softer mitigation action before or alongside stronger enforcement.

This confirms that the proposed system performs runtime intrusion prevention, not merely intrusion detection.

## 9. Flow-Level Model-Controller Comparison

**Table 6. Flow-level model-controller comparison**  
Source: `tables/table_flow_level_model_controller_comparison.csv`

The flow-level comparison is one of the most important results of this validation phase. It compares the protocol-aware final model decisions with the controller-side policy logs using source IP, destination IP, source port, destination port, and transport protocol.

The malicious UDP flow from `10.10.60.12` to `10.10.40.14` is the key flow in this experiment. It was classified as `ATTACK` by the runtime model and mapped to a `DROP` final action in the protocol-aware policy output. On the controller side, the same flow was associated with `quarantine_candidate`, and the comparison also confirmed matching evidence for drop mitigation, quarantine, and rate-limit behavior.

This result is particularly important because it shows that the runtime model output and controller-side mitigation behavior are security-compatible, even when the exact action labels are not identical. In a practical IDS/IPS system, exact equality between model output and controller action is not always expected because the controller has a richer action space. For example, a model may recommend `DROP`, while the controller may escalate a repeated high-confidence attack to quarantine.

The quarantine-observed flow toward `10.10.99.16` was interpreted as a post-mitigation observation. Therefore, it should not be evaluated as a normal source-to-victim flow. This distinction strengthens the methodological validity of the analysis.

## 10. Attack Probability and Final Policy Mapping

**Table 7. Flow-level attack probability and protocol-aware final action summary**  
Source: `tables/table_protocol_aware_attack_probability_summary.csv`

The attack probability summary shows how the Final XGBoost Top-20 model scored each runtime flow. Benign flows had low attack probabilities and were mapped to `ALLOW` or `ALLOW_CONTROL_FLOW`. In contrast, the malicious UDP flow received a high attack probability and was mapped to `DROP`.

The post-quarantine flow toward `10.10.99.16` also received a high attack probability, but it was labeled as `QUARANTINE_OBSERVED`. This is a meaningful distinction because traffic observed toward the quarantine host reflects the mitigation process rather than a normal attack flow toward the original victim.

This result demonstrates the value of combining ML inference with protocol-aware and context-aware post-processing.

## 11. Overall Interpretation

The runtime validation results show that the proposed SDN-based IDS/IPS prototype can preserve benign traffic, detect malicious UDP traffic, and apply controller-side mitigation actions. The system successfully connects the following stages:

1. Mixed traffic generation in a Mininet-based SDN environment
2. PCAP capture from live traffic
3. CICFlowMeter-compatible selected-feature extraction
4. Final XGBoost Top-20 runtime inference
5. Protocol-aware final policy interpretation
6. Ryu controller-side policy decision-making
7. OpenFlow-based mitigation through rate-limit, drop, and quarantine actions

The most important contribution of this phase is that it validates the end-to-end runtime behavior of the proposed architecture. The results are stronger than offline-only classification results because they demonstrate that the ML model can be embedded into an SDN controller workflow and used to support real mitigation decisions.

## 12. Thesis-Relevant Contribution

This experiment contributes to the thesis in three ways.

First, it demonstrates that a selected-feature ML model trained in an offline setting can be used in a runtime SDN pipeline. The Final XGBoost Top-20 model was successfully applied to PCAP-derived flow features and produced meaningful BENIGN/ATTACK predictions.

Second, it shows that controller-side policy logic can enrich binary ML predictions with network-aware interpretation. The protocol-aware policy layer distinguishes TCP control-like flows, benign UDP flows, malicious UDP flows, and quarantine-observed flows.

Third, it provides evidence that the proposed IDS/IPS architecture can apply active mitigation. The observed rate-limit, drop, and quarantine logs demonstrate that the system operates as a prevention-oriented SDN security prototype rather than a passive detector.

## 13. Limitations

Although the runtime validation results are promising, several limitations should be noted.

First, the experiments were performed in a controlled Mininet environment. While this allows repeatable and observable experimentation, future work should evaluate the system under more diverse and longer-running traffic conditions.

Second, flow-level matching between PCAP-derived runtime model outputs and controller-side logs depends on timing, flow-stat polling intervals, and the availability of transport-port information in controller logs. Earlier diagnostic runs showed that missing port information can prevent exact model-controller matching.

Third, exact action matching is not always the best evaluation criterion. The controller has a richer action space than the binary ML model. Therefore, security-compatible matching is more appropriate than strict equality between model action and controller action.

Fourth, the current model was trained with a selected Top-20 feature subset. Although this improves runtime feasibility, future experiments should evaluate whether training with a larger and more representative subset of CIC-DDoS2019 improves robustness and generalization.

## 14. Conclusion

The canonical port-aware runtime validation experiment provides end-to-end evidence that the proposed SDN-based hybrid IDS/IPS prototype can operate in a live SDN testbed. The system preserved benign/control traffic, detected malicious UDP behavior, and applied mitigation through rate-limit, drop, and quarantine mechanisms.

These results support the central claim of the study: machine learning-based DDoS detection can be integrated with SDN controller-side policy enforcement to provide runtime intrusion detection and prevention in a campus-like SDN environment.

