# Thesis Runtime Validation Package

Bu dosya, SDN tabanlı IDS/IPS prototipinin runtime validation sonuçlarının tez/makale yazımında kullanılacak ana paketini tanımlar.

## 1. Main Results Text

Ana tez sonuç metni:

`docs/thesis_results_section_runtime_validation.md`

Bu dosya, tezde "Experimental Results", "Runtime Validation", "Evaluation of the Proposed SDN-Based IDS/IPS Prototype" veya benzeri bir bölüm altında doğrudan kullanılabilecek şekilde hazırlanmıştır.

## 2. Thesis Artifact Directory

Tezde kullanılacak tablo, şekil ve özet dosyaları aşağıdaki dizinde tutulmaktadır:

`experiments/results/thesis_artifacts/run_05_port_aware_runtime_validation`

## 3. Core Manifest Files

| File | Purpose |
|---|---|
| `experiments/results/thesis_artifacts/run_05_port_aware_runtime_validation/thesis_artifacts_manifest.md` | Üretilen tablo ve şekillerin listesi |
| `experiments/results/thesis_artifacts/run_05_port_aware_runtime_validation/thesis_artifacts_summary.json` | Makine tarafından okunabilir artifact özeti |
| `experiments/results/thesis_artifacts/run_05_port_aware_runtime_validation/thesis_table_figure_captions.md` | Tezde kullanılacak tablo/şekil başlıkları ve açıklamaları |

## 4. Recommended Main Tables

| Thesis Table | Artifact File | Usage |
|---|---|---|
| Table 1 | `experiments/results/thesis_artifacts/run_05_port_aware_runtime_validation/tables/table_canonical_runtime_validation_summary.csv` | Canonical repeated runtime validation summary |
| Table 2 | `experiments/results/thesis_artifacts/run_05_port_aware_runtime_validation/tables/table_controller_action_distribution.csv` | Controller-side policy action distribution |
| Table 3 | `experiments/results/thesis_artifacts/run_05_port_aware_runtime_validation/tables/table_final_top20_prediction_distribution.csv` | Final XGBoost Top-20 runtime prediction distribution |
| Table 4 | `experiments/results/thesis_artifacts/run_05_port_aware_runtime_validation/tables/table_protocol_aware_final_policy_distribution.csv` | Protocol-aware final policy distribution |
| Table 5 | `experiments/results/thesis_artifacts/run_05_port_aware_runtime_validation/tables/table_enforcement_action_summary.csv` | Rate-limit, drop and quarantine enforcement summary |
| Table 6 | `experiments/results/thesis_artifacts/run_05_port_aware_runtime_validation/tables/table_flow_level_model_controller_comparison.csv` | Flow-level model-controller comparison |
| Table 7 | `experiments/results/thesis_artifacts/run_05_port_aware_runtime_validation/tables/table_protocol_aware_attack_probability_summary.csv` | Attack probability and final policy mapping |

## 5. Recommended Main Figures

| Thesis Figure | Artifact File | Usage |
|---|---|---|
| Figure 1 | `experiments/results/thesis_artifacts/run_05_port_aware_runtime_validation/figures/fig_controller_action_distribution.png` | Controller policy action distribution |
| Figure 2 | `experiments/results/thesis_artifacts/run_05_port_aware_runtime_validation/figures/fig_final_top20_prediction_distribution.png` | Runtime BENIGN/ATTACK prediction distribution |
| Figure 3 | `experiments/results/thesis_artifacts/run_05_port_aware_runtime_validation/figures/fig_protocol_aware_final_policy_distribution.png` | Protocol-aware final policy distribution |
| Figure 4 | `experiments/results/thesis_artifacts/run_05_port_aware_runtime_validation/figures/fig_enforcement_action_summary.png` | Enforcement action summary |

## 6. Canonical Experiment

Ana tez deney koşusu:

`run_05_port_aware_repeat_validation`

Bu koşu, aşağıdaki nedenlerle ana canonical deney olarak kullanılmalıdır:

- Controller loglarında `src_port` ve `dst_port` alanları vardır.
- Protocol-aware final policy üretimi yapılmıştır.
- Flow-level model-controller eşleştirme port ve protokol düzeyinde yapılabilmiştir.
- Rate-limit, drop ve quarantine aksiyonları aynı deneyde gözlenmiştir.
- Runtime model çıktıları ile controller-side enforcement davranışları security-compatible olarak eşleşmiştir.

## 7. Supporting Experiment

Destekleyici canonical koşu:

`run_03_aligned_clean`

Bu koşu ilk başarılı runtime validation koşusu olarak kullanılabilir. Ancak ana tablo ve şekiller için `run_05` daha temizdir.

## 8. Diagnostic Experiment

Diagnostic / partial repetition koşusu:

`run_04_repeat_mixed_validation`

Bu koşuda controller loglarında port bilgisi eksik olduğu için flow-level exact matching zayıf kalmıştır. Bu nedenle ana performans sonucu olarak değil, geliştirme sürecindeki sınırlılık veya debugging örneği olarak değerlendirilebilir.

## 9. Recommended Thesis Placement

Bu paket aşağıdaki tez bölümlerinde kullanılabilir:

- Experimental Setup
- Runtime Validation Environment
- Evaluation Results
- Controller-Side Mitigation Results
- Discussion
- Limitations

## 10. Core Claim Supported by This Package

Bu artifact paketi şu temel iddiayı destekler:

> Offline olarak eğitilen seçilmiş özellik tabanlı bir makine öğrenmesi modeli, SDN controller mimarisiyle entegre edilerek canlı Mininet/Ryu ortamında zararlı UDP trafiğini tespit edebilir ve controller tarafında rate-limit, drop ve quarantine gibi önleme aksiyonlarına dönüştürülebilir.

