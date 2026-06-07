# Tez Bölüm Paketi README

Bu dosya, SDN tabanlı makine öğrenmesi destekli IDS/IPS doktora tez çalışması kapsamında üretilen yöntem, çalışma zamanı doğrulama, tartışma, tablo, şekil ve deney artifact dosyalarını indekslemek için hazırlanmıştır.

## 1. Ana Word Dosyaları

| Dosya | Açıklama | Kullanım |
|---|---|---|
| docs/bolum_4_yontem_ve_runtime_dogrulama_tr_with_artifacts.docx | Bölüm 4 yöntem ve çalışma zamanı doğrulama metni; belge sonunda Tablo 1–7 ve Şekil 1–4 eklenmiştir. | Tezde Bölüm 4 ana dosyası olarak kullanılabilir. |
| docs/bolum_5_tartisma_sinirliliklar_gelecek_calismalar_tr.docx | Bölüm 5 tartışma, sınırlılıklar ve gelecek çalışmalar metni. | Tezde Bölüm 5 ana dosyası olarak kullanılabilir. |

## 2. Markdown Kaynak Dosyaları

| Dosya | Açıklama |
|---|---|
| docs/bolum_4_yontem_ve_runtime_dogrulama_tr.md | Bölüm 4 için ana Markdown kaynak dosyası. |
| docs/bolum_5_tartisma_sinirliliklar_gelecek_calismalar_tr.md | Bölüm 5 için ana Markdown kaynak dosyası. |
| docs/bolum_4_tablo_sekil_insert_map.md | Bölüm 4 içinde hangi tablo/şeklin nereye yerleştirileceğini gösteren harita. |
| docs/thesis_runtime_validation_table_figure_checklist.md | Tezde kullanılacak tablo/şekil kontrol listesi. |
| docs/thesis_runtime_validation_package.md | Runtime validation deneylerinin tez/makale yazımı için paketlenmiş açıklaması. |

## 3. Ana Deney Dizini

Canonical ana deney:

experiments/results/mixed_traffic_experiments/repeated_mixed_runtime_20260516_130204/run_05_port_aware_repeat_validation

Bu deney, port-aware ve protocol-aware doğrulamanın en temiz şekilde yapıldığı ana runtime validation koşusudur.

## 4. Destekleyici Canonical Deney

Destekleyici başarılı koşu:

experiments/results/mixed_traffic_experiments/repeated_mixed_runtime_20260516_130204/run_03_aligned_clean

Bu koşu ilk başarılı aligned runtime validation deneyi olarak kullanılabilir.

## 5. Diagnostic Koşu

Diagnostic/partial repetition koşusu:

experiments/results/mixed_traffic_experiments/repeated_mixed_runtime_20260516_130204/run_04_repeat_mixed_validation

Bu koşu controller loglarında port bilgisi eksik olduğu için ana performans sonucu olarak değil, geliştirme sürecindeki bir diagnostic koşu olarak değerlendirilmelidir.

## 6. Tez Artifact Dizini

Tez için üretilen tablo ve şekiller:

experiments/results/thesis_artifacts/run_05_port_aware_runtime_validation

Alt dizinler:

experiments/results/thesis_artifacts/run_05_port_aware_runtime_validation/tables
experiments/results/thesis_artifacts/run_05_port_aware_runtime_validation/figures

## 7. Tezde Kullanılacak Tablolar

| No | Dosya | Açıklama |
|---|---|---|
| Tablo 1 | tables/table_canonical_runtime_validation_summary.csv | Canonical tekrarlı çalışma zamanı doğrulama sonuçları. |
| Tablo 2 | tables/table_controller_action_distribution.csv | Denetleyici taraflı IDS/IPS politika aksiyon dağılımı. |
| Tablo 3 | tables/table_final_top20_prediction_distribution.csv | Final XGBoost Top-20 modelinin runtime tahmin dağılımı. |
| Tablo 4 | tables/table_protocol_aware_final_policy_distribution.csv | Protocol-aware final policy dağılımı. |
| Tablo 5 | tables/table_enforcement_action_summary.csv | SDN denetleyicisi önleme aksiyon özeti. |
| Tablo 6 | tables/table_flow_level_model_controller_comparison.csv | Flow-level model-controller karşılaştırması. |
| Tablo 7 | tables/table_protocol_aware_attack_probability_summary.csv | Flow-level saldırı olasılığı ve protocol-aware final action özeti. |

## 8. Tezde Kullanılacak Şekiller

| No | Dosya | Açıklama |
|---|---|---|
| Şekil 1 | figures/fig_controller_action_distribution.png | Denetleyici taraflı politika aksiyon dağılımı. |
| Şekil 2 | figures/fig_final_top20_prediction_distribution.png | Runtime BENIGN/ATTACK tahmin dağılımı. |
| Şekil 3 | figures/fig_protocol_aware_final_policy_distribution.png | Protocol-aware final policy aksiyon dağılımı. |
| Şekil 4 | figures/fig_enforcement_action_summary.png | SDN denetleyicisi önleme aksiyon özeti. |

## 9. Ana Deney Raporları

Run 05 ana deney raporu:

experiments/results/mixed_traffic_experiments/repeated_mixed_runtime_20260516_130204/run_05_port_aware_repeat_validation/mixed_traffic_experiment_report.md

Run 05 özet JSON:

experiments/results/mixed_traffic_experiments/repeated_mixed_runtime_20260516_130204/run_05_port_aware_repeat_validation/mixed_traffic_experiment_summary.json

Run 05 model-controller karşılaştırma raporu:

experiments/results/mixed_traffic_experiments/repeated_mixed_runtime_20260516_130204/run_05_port_aware_repeat_validation/comparison/port_aware_protocol_aware_api_ok/final_top20_vs_port_aware_controller_report.md

## 10. Canonical Aggregate Raporu

Canonical aggregate dizini:

experiments/results/mixed_traffic_experiments/canonical_runtime_validation_runs/aggregate_reports

Bu rapor, run_03_aligned_clean ve run_05_port_aware_repeat_validation koşularını birlikte özetler.

## 11. Tezde Kullanılacak Ana Sonuç Cümlesi

Bu çalışmada geliştirilen SDN tabanlı makine öğrenmesi destekli IDS/IPS prototipi, canlı Mininet/Ryu ortamında benign trafiği koruyabilmiş, zararlı UDP trafiğini yüksek saldırı olasılığı ile tespit edebilmiş ve bu tespiti SDN denetleyicisi üzerinde rate-limit, drop ve quarantine gibi aktif önleme aksiyonlarına dönüştürebilmiştir.

## 12. Dikkat Edilecek Noktalar

- Ana sonuçlar için öncelikli olarak run_05_port_aware_repeat_validation kullanılmalıdır.
- run_03_aligned_clean, repeated validation desteği olarak kullanılabilir.
- run_04_repeat_mixed_validation, port bilgisi eksik olduğu için ana sonuç olarak sunulmamalıdır.
- Bölüm 4 Word dosyasında tablolar ve şekiller belge sonunda ek olarak yer almaktadır.
- Word’e son aktarımda tablolar ve şekiller istenirse metin içindeki ilgili başlıkların altına manuel taşınabilir.
- docs/roadmap.md, deneysel sürecin aşama aşama takibi için güncel tutulmalıdır.
