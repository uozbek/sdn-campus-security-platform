# Runtime Validation Table/Figure Checklist

Bu checklist, runtime validation sonuçlarını tez dosyasına aktarırken kullanılacak tablo ve şekilleri takip etmek için hazırlanmıştır.

## Tables to Insert

- [ ] Table 1 — Canonical repeated runtime validation results  
  Source: `experiments/results/thesis_artifacts/run_05_port_aware_runtime_validation/tables/table_canonical_runtime_validation_summary.csv`

- [ ] Table 2 — Controller-side IDS/IPS policy action distribution  
  Source: `experiments/results/thesis_artifacts/run_05_port_aware_runtime_validation/tables/table_controller_action_distribution.csv`

- [ ] Table 3 — Runtime prediction distribution of the Final XGBoost Top-20 model  
  Source: `experiments/results/thesis_artifacts/run_05_port_aware_runtime_validation/tables/table_final_top20_prediction_distribution.csv`

- [ ] Table 4 — Protocol-aware final policy distribution  
  Source: `experiments/results/thesis_artifacts/run_05_port_aware_runtime_validation/tables/table_protocol_aware_final_policy_distribution.csv`

- [ ] Table 5 — SDN controller enforcement action summary  
  Source: `experiments/results/thesis_artifacts/run_05_port_aware_runtime_validation/tables/table_enforcement_action_summary.csv`

- [ ] Table 6 — Flow-level model-controller comparison  
  Source: `experiments/results/thesis_artifacts/run_05_port_aware_runtime_validation/tables/table_flow_level_model_controller_comparison.csv`

- [ ] Table 7 — Flow-level attack probability and protocol-aware final action summary  
  Source: `experiments/results/thesis_artifacts/run_05_port_aware_runtime_validation/tables/table_protocol_aware_attack_probability_summary.csv`

## Figures to Insert

- [ ] Figure 1 — Controller-side policy action distribution  
  Source: `experiments/results/thesis_artifacts/run_05_port_aware_runtime_validation/figures/fig_controller_action_distribution.png`

- [ ] Figure 2 — Runtime BENIGN/ATTACK prediction distribution  
  Source: `experiments/results/thesis_artifacts/run_05_port_aware_runtime_validation/figures/fig_final_top20_prediction_distribution.png`

- [ ] Figure 3 — Protocol-aware final policy action distribution  
  Source: `experiments/results/thesis_artifacts/run_05_port_aware_runtime_validation/figures/fig_protocol_aware_final_policy_distribution.png`

- [ ] Figure 4 — SDN controller enforcement action summary  
  Source: `experiments/results/thesis_artifacts/run_05_port_aware_runtime_validation/figures/fig_enforcement_action_summary.png`

## Text Sections to Insert

- [ ] Overview of the runtime validation phase
- [ ] Experimental scenario
- [ ] Generated experimental artifacts
- [ ] Repeated runtime validation results
- [ ] Controller-side policy action distribution
- [ ] Runtime prediction distribution
- [ ] Protocol-aware final policy interpretation
- [ ] Enforcement action summary
- [ ] Flow-level model-controller comparison
- [ ] Attack probability and final policy mapping
- [ ] Overall interpretation
- [ ] Thesis-relevant contribution
- [ ] Limitations
- [ ] Conclusion

## Notes

- Ana deney olarak `run_05_port_aware_repeat_validation` kullanılmalıdır.
- `run_03_aligned_clean` destekleyici repeated validation olarak sunulabilir.
- `run_04_repeat_mixed_validation` port eksikliği nedeniyle diagnostic/partial run olarak açıklanmalıdır.
- Rate-limit, drop ve quarantine aynı canonical run içinde `run_05` ile gözlenmiştir.
- Flow-level exact matching yerine security-compatible matching yorumlanmalıdır.

