
---

## Aşama 15.4 — Mixed Benign and Malicious Runtime Traffic Experiment

Bu aşamada, geliştirilen SDN tabanlı IDS/IPS prototipi karma benign ve zararlı trafik altında test edilmiştir. Amaç, yalnızca offline model başarısını değil, aynı zamanda runtime SDN ortamında tespit, karar üretimi ve önleme mekanizmalarının birlikte çalıştığını göstermektir.

### Yapılanlar

- Mininet/Ryu tabanlı kampüs SDN test ortamı kullanıldı.
- Benign TCP/UDP trafik ile zararlı yüksek hacimli UDP trafik aynı deney içinde üretildi.
- Trafik `tcpdump` ile PCAP olarak yakalandı.
- PCAP dosyası Final XGBoost Top-20 runtime pipeline üzerinden işlendi.
- PCAP içinden seçilmiş 20 özellik çıkarıldı.
- Aktif model `final_xgboost_top20` ile flow bazlı tahmin yapıldı.
- Ryu controller tarafındaki `policy_decisions.csv`, `mitigation_log.csv`, `rate_limit_log.csv` ve `quarantine_log.csv` çıktıları toplandı.
- Final ML pipeline kararları ile controller policy kararları port-aware ve protocol-aware olarak karşılaştırıldı.
- Deney özeti ve raporu üretildi:
  - `mixed_traffic_experiment_report.md`
  - `mixed_traffic_experiment_summary.json`

### Öne çıkan sonuçlar

- Final runtime pipeline 7 flow çıkardı.
- Bu flowların 4 tanesi benign, 3 tanesi attack olarak sınıflandırıldı.
- Benign/control akışlar `ALLOW` veya `ALLOW_CONTROL_FLOW` olarak yorumlandı.
- Zararlı UDP akış `DROP` olarak işaretlendi.
- Controller tarafında saldırı davranışı için `rate_limit`, `drop` ve `quarantine_candidate` aksiyonları üretildi.
- Protocol-aware karşılaştırmada 5 exact controller flow-key match elde edildi.
- Security-compatible action count değeri 5 olarak raporlandı.
- Zararlı UDP akış için drop, quarantine ve rate-limit loglarıyla eşleşme sağlandı.

### Tez açısından önemi

Bu aşama, önerilen mimarinin yalnızca offline CIC-DDoS2019 modeliyle sınıflandırma yapan bir yapı olmadığını; aynı zamanda canlı SDN test ortamında karma trafik altında IDS/IPS davranışı gösterebildiğini ortaya koymuştur.

Bu deney, doktora tezinin yöntem ve deneysel doğrulama bölümlerinde şu iddiayı destekler:

> Önerilen SDN tabanlı hibrit IDS/IPS mimarisi, benign trafiği korurken yüksek hacimli UDP tabanlı zararlı trafiği tespit edebilmekte ve controller seviyesinde rate-limit, drop ve quarantine aksiyonlarıyla güvenlik açısından uyumlu önleme davranışı üretebilmektedir.

### Üretilen dosyalar

- `experiments/results/mixed_traffic_experiments/20260515_134819_mixed_benign_malicious_replay_v1/mixed_traffic_experiment_report.md`
- `experiments/results/mixed_traffic_experiments/20260515_134819_mixed_benign_malicious_replay_v1/mixed_traffic_experiment_summary.json`
- `experiments/results/mixed_traffic_experiments/20260515_134819_mixed_benign_malicious_replay_v1/runtime_pipeline/20260515_105336_mixed_benign_malicious_live_final_top20/runtime_pipeline_report.md`
- `experiments/results/mixed_traffic_experiments/20260515_134819_mixed_benign_malicious_replay_v1/comparison/port_aware_protocol_aware_v2/final_top20_vs_port_aware_controller_report.md`

### Durum

Tamamlandı.


---

## Aşama 15.5-B — Protocol-Aware Final Policy Builder

Bu aşamada, Final XGBoost Top-20 runtime pipeline çıktılarının controller logları ile daha doğru karşılaştırılabilmesi için protocol-aware final policy üretimi kalıcı bir araca dönüştürülmüştür.

### Yapılanlar

- `ml-service/tools/build_protocol_aware_final_policy.py` aracı oluşturuldu.
- Araç, `final_top20_runtime_predictions.csv` dosyasını ve aynı deneyde yakalanan PCAP dosyasını birlikte kullanmaktadır.
- PCAP içinden TCP/UDP protokol bilgisi `tcpdump` üzerinden çıkarılmaktadır.
- Flow bazında `ip_proto` ve `proto_packet_count` alanları üretilmektedir.
- TCP tabanlı iperf3 control/control-like akışlar `ALLOW_CONTROL_FLOW` olarak yorumlanmaktadır.
- UDP saldırı akışları model çıktısına göre `DROP` olarak korunmaktadır.
- Quarantine IP yönüne giden akışlar `QUARANTINE_OBSERVED` olarak ayrıştırılmaktadır.
- Bu çıktı, port-aware ve protocol-aware controller karşılaştırmasına girdi olarak kullanılabilir hale getirilmiştir.
- `prepare_traffic_scenario_run.py` script’i güncellenerek scenario runner komut zincirine protocol-aware policy üretimi eklenmiştir.

### Üretilen / Güncellenen Dosyalar

- `ml-service/tools/build_protocol_aware_final_policy.py`
- `ml-service/tools/prepare_traffic_scenario_run.py`
- `final_top20_policy_decisions_protocol_aware.csv`
- `final_top20_policy_decisions_protocol_aware.summary.json`

### Tez Açısından Önemi

Bu adım, PCAP tabanlı model çıktıları ile SDN controller tarafından üretilen policy ve enforcement logları arasındaki karşılaştırmanın daha metodolojik yapılmasını sağlar. Özellikle TCP control flow, UDP attack flow ve quarantine sonrası gözlenen akışların ayrıştırılması, deneysel doğrulama sonuçlarının tezde daha savunulabilir şekilde yorumlanmasına katkı sağlar.

### Durum

Tamamlandı.


---

## Aşama 15.5-C — Scenario Manifest and Reproducibility Checklist

Bu aşamada, mixed benign/malicious runtime deneylerinin tekrar üretilebilir ve akademik olarak izlenebilir hale getirilmesi için deney manifestosu ve reproducibility checklist üretimi eklendi.

### Yapılanlar

- `ml-service/tools/generate_experiment_manifest.py` aracı oluşturuldu.
- Her deney klasörü için `experiment_manifest.json` ve `experiment_manifest.md` çıktıları üretilebilir hale getirildi.
- Manifest içinde deney klasörü, runtime pipeline klasörü, comparison klasörü, senaryo dosyası, controller dosyası ve kullanılan model bilgileri kayıt altına alındı.
- PCAP, controller logları, final runtime prediction çıktıları, protocol-aware final policy çıktısı, comparison raporu ve mixed traffic raporu tek bir manifest dosyasında ilişkilendirildi.
- Row count değerleri, temel comparison metrikleri ve reproducibility checklist otomatik üretildi.
- Scenario runner komut zincirine manifest üretimi eklenmesi planlandı / uygulandı.

### Üretilen Dosyalar

- `ml-service/tools/generate_experiment_manifest.py`
- `experiment_manifest.json`
- `experiment_manifest.md`

### Tez Açısından Önemi

Bu aşama, deneylerin yalnızca sonuç üretmesini değil, aynı zamanda aynı koşullar altında tekrar çalıştırılabilir ve savunulabilir olmasını sağlar. Tez savunmasında "Bu deney nasıl üretildi?", "Hangi model kullanıldı?", "Hangi PCAP ve loglar karşılaştırıldı?", "Controller hangi modda çalıştı?" gibi sorulara doğrudan yanıt verir.

### Durum

Tamamlandı.


---

## Aşama 15.5-D — Multi-Run Mixed Traffic Experiment Aggregation

Bu aşamada, mixed benign/malicious runtime deneylerinin birden fazla koşu üzerinden analiz edilebilmesi için aggregate raporlama altyapısı eklenmiştir.

### Yapılanlar

- `ml-service/tools/aggregate_mixed_traffic_runs.py` aracı oluşturuldu.
- Araç, `mixed_traffic_experiment_summary.json` dosyalarını deney klasörlerinden otomatik olarak toplar.
- Her koşu için controller policy, flow stats, prediction, mitigation, quarantine, rate-limit ve comparison metriklerini tek tabloya indirger.
- Çoklu koşular için ortalama, standart sapma, minimum, maksimum ve toplam değerler hesaplanır.
- CSV, JSON ve Markdown formatlarında aggregate rapor üretir.
- Bu yapı, aynı senaryonun 3 veya 5 kez tekrar edilmesiyle tezde daha güçlü istatistiksel değerlendirme yapılmasına imkân sağlar.

### Üretilen Dosyalar

- `ml-service/tools/aggregate_mixed_traffic_runs.py`
- `experiments/results/mixed_traffic_experiments/aggregate_reports/mixed_traffic_multi_run_summary_*.csv`
- `experiments/results/mixed_traffic_experiments/aggregate_reports/mixed_traffic_multi_run_summary_*.json`
- `experiments/results/mixed_traffic_experiments/aggregate_reports/mixed_traffic_multi_run_report_*.md`

### Tez Açısından Önemi

Bu aşama, sistemin yalnızca tek bir deney koşusunda değil, tekrarlandığında da benzer güvenlik davranışları üretip üretmediğini değerlendirmek için gereklidir. Böylece benign trafik koruma, saldırı tespiti, rate-limit, drop ve quarantine enforcement mekanizmaları çoklu koşular üzerinden raporlanabilir.

### Durum

Tamamlandı / İlk tek koşu ile test edilecek.

