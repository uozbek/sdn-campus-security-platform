# Bölüm 4 Tablo ve Şekil Yerleştirme Haritası

Bu dosya, `docs/bolum_4_yontem_ve_runtime_dogrulama_tr.md` dosyasını Word veya Google Docs ortamına aktarırken hangi tablo/şeklin nereye yerleştirileceğini göstermek için hazırlanmıştır.

## Ana Bölüm Dosyası

`docs/bolum_4_yontem_ve_runtime_dogrulama_tr.md`

## Artifact Dizini

`experiments/results/thesis_artifacts/run_05_port_aware_runtime_validation`

---

## Tablo Yerleştirme Haritası

| No | Tezdeki Başlık | Kaynak Dosya | Yerleştirilecek Bölüm |
|---|---|---|---|
| Tablo 1 | Canonical tekrarlı çalışma zamanı doğrulama sonuçları | `tables/table_canonical_runtime_validation_summary.csv` | 4. Tekrarlı Çalışma Zamanı Doğrulama Sonuçları |
| Tablo 2 | Denetleyici taraflı IDS/IPS politika aksiyon dağılımı | `tables/table_controller_action_distribution.csv` | 5. Denetleyici Taraflı Politika Aksiyon Dağılımı |
| Tablo 3 | Final XGBoost Top-20 modelinin runtime tahmin dağılımı | `tables/table_final_top20_prediction_distribution.csv` | 6. Runtime Tahmin Dağılımı |
| Tablo 4 | Protocol-aware final policy dağılımı | `tables/table_protocol_aware_final_policy_distribution.csv` | 7. Protocol-Aware Final Policy Yorumu |
| Tablo 5 | SDN denetleyicisi önleme aksiyon özeti | `tables/table_enforcement_action_summary.csv` | 8. SDN Denetleyicisi Önleme Aksiyonları |
| Tablo 6 | Flow-level model-controller karşılaştırması | `tables/table_flow_level_model_controller_comparison.csv` | 9. Flow-Level Model ve Denetleyici Karşılaştırması |
| Tablo 7 | Flow-level saldırı olasılığı ve protocol-aware final action özeti | `tables/table_protocol_aware_attack_probability_summary.csv` | 10. Saldırı Olasılığı ve Final Policy Eşlemesi |

---

## Şekil Yerleştirme Haritası

| No | Tezdeki Başlık | Kaynak Dosya | Yerleştirilecek Bölüm |
|---|---|---|---|
| Şekil 1 | Denetleyici taraflı politika aksiyon dağılımı | `figures/fig_controller_action_distribution.png` | 5. Denetleyici Taraflı Politika Aksiyon Dağılımı |
| Şekil 2 | Runtime BENIGN/ATTACK tahmin dağılımı | `figures/fig_final_top20_prediction_distribution.png` | 6. Runtime Tahmin Dağılımı |
| Şekil 3 | Protocol-aware final policy aksiyon dağılımı | `figures/fig_protocol_aware_final_policy_distribution.png` | 7. Protocol-Aware Final Policy Yorumu |
| Şekil 4 | SDN denetleyicisi önleme aksiyon özeti | `figures/fig_enforcement_action_summary.png` | 8. SDN Denetleyicisi Önleme Aksiyonları |

---

## Word’e Aktarırken Önerilen Sıra

1. Önce `docs/bolum_4_yontem_ve_runtime_dogrulama_tr.md` dosyasını Word’e aktar.
2. Markdown içindeki `[TABLO EKLEME NOKTASI]` ve `[ŞEKİL EKLEME NOKTASI]` işaretlerini bul.
3. İlgili CSV dosyasını tablo olarak Word’e ekle.
4. İlgili PNG dosyasını şekil olarak Word’e ekle.
5. Tablo ve şekil başlıklarını Word’ün caption sistemiyle yeniden numaralandır.
6. Son kontrolde Tablo 1–7 ve Şekil 1–4 sırasının bozulmadığından emin ol.

---

## Ana Sonuç Cümlesi

Bölüm 4’te kullanılacak ana sonuç cümlesi:

> Bu bölümde sunulan deneysel bulgular, önerilen SDN tabanlı makine öğrenmesi destekli IDS/IPS prototipinin canlı Mininet/Ryu ortamında zararsız trafiği koruyabildiğini, zararlı UDP trafiğini yüksek saldırı olasılığı ile tespit edebildiğini ve controller tarafında rate-limit, drop ve quarantine gibi önleme aksiyonlarına dönüştürebildiğini göstermektedir.

