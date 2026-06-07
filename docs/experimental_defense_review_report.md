# Deneysel Sonuçlar İçin Savunma/Jüri Perspektifi Değerlendirme Raporu

- Generated at UTC: `2026-05-20T18:47:57.958511`
- Canonical aggregate CSV: `experiments/results/mixed_traffic_experiments/canonical_runtime_validation_runs/aggregate_reports/mixed_traffic_multi_run_summary_20260519_193527.csv`
- Flow comparison CSV: `experiments/results/thesis_artifacts/run_05_port_aware_runtime_validation/tables/table_flow_level_model_controller_comparison.csv`

## 1. Deneysel Kanıtın Özeti

- Canonical run sayısı: `2`
- Flow-level karşılaştırma satırı: `9`
- Runtime prediction satırı: `9`
- Controller action satırı: `4`
- Enforcement summary satırı: `3`

Bu deneysel yapı, yalnızca offline makine öğrenmesi başarımını değil, model çıktılarının SDN denetleyicisi tarafında politika kararlarına ve önleme aksiyonlarına bağlanıp bağlanamadığını değerlendirmektedir.

## 2. Jüri Sorusu: Neden run_05 ana deney olarak seçildi?

`run_05_port_aware_repeat_validation`, port-aware ve protocol-aware eşleştirme için en güçlü canonical koşudur. Bu koşuda model çıktıları yalnızca kaynak/hedef IP düzeyinde değil, port ve protokol bilgisiyle birlikte denetleyici kararlarıyla karşılaştırılabilmiştir. Bu nedenle run_05, tezde ana çalışma zamanı doğrulama deneyi olarak konumlandırılmalıdır.

Buna karşılık `run_03_aligned_clean`, ilk başarılı hizalanmış çalışma zamanı doğrulaması olarak destekleyici canonical koşudur. `run_04_repeat_mixed_validation` ise port bilgisinin controller loglarında bulunmaması nedeniyle diagnostic/partial repetition olarak değerlendirilmiştir.

## 3. Jüri Sorusu: run_04 neden ana sonuçlara dahil edilmedi?

run_04 tamamen başarısız bir deney değildir; ancak akademik ana sonuç olarak kullanılabilecek kadar temiz değildir. Sorun model tahmininden ziyade, controller loglarında port bilgisinin bulunmaması nedeniyle flow-level exact matching kalitesinin sınırlanmasıdır. Bu nedenle run_04, sistem geliştirme sürecinde port-aware logging ihtiyacını ortaya koyan diagnostic bir koşu olarak raporlanmalıdır.

Bu ayrım deneysel şeffaflığı artırır: Başarısız veya kısmi koşular gizlenmemekte, fakat ana performans iddiası yalnızca canonical koşular üzerinden kurulmaktadır.

## 4. Jüri Sorusu: Flow-level eşleşme neden tüm satırlarda birebir değil?

Flow-level tabloda exact controller match `5/9` olarak görünmektedir. Security-compatible action sayısı ise `5/9` düzeyindedir.

Bu durum, model çıktısının hatalı olduğu anlamına doğrudan gelmez. Çünkü model PCAP tabanlı flow özellikleri üzerinden binary veya policy-level öneri üretirken, SDN denetleyicisi akışları zamanlama, polling aralığı, OpenFlow event görünürlüğü, TCP kontrol akışları ve loglama ayrıntılarına bağlı olarak gözlemler. Bu nedenle exact matching yanında security-compatible matching de raporlanmıştır.

## 5. Jüri Sorusu: Yüksek ML başarımı gerçek zamanlı SDN başarımı anlamına gelir mi?

Hayır, tek başına gelmez. Offline ML başarımı modelin veri kümesi üzerindeki sınıflandırma kapasitesini gösterir; fakat gerçek zamanlı SDN başarımı şu ek koşullara bağlıdır:

- eğitim ve çalışma zamanı özelliklerinin aynı semantik yapıya sahip olması,
- feature order ve feature mapping uyumluluğu,
- denetleyici loglarının port/protokol düzeyinde yeterli ayrıntı içermesi,
- model kararının SDN politika aksiyonuna doğru çevrilmesi,
- drop, rate-limit ve quarantine gibi enforcement aksiyonlarının OpenFlow düzeyinde uygulanabilmesi.

Bu tezdeki önemli katkı, offline model başarımını tek başına raporlamak yerine, model çıktısının SDN controller-side policy ve enforcement davranışıyla ilişkilendirilmesidir.

## 6. Jüri Sorusu: Bu çalışma IDS mi, IPS mi?

Çalışma yalnızca IDS olarak değerlendirilmemelidir. Sistem saldırı olasılığını ve policy kararını üretmekte, ardından SDN denetleyicisi üzerinden drop, quarantine_candidate ve rate_limit aksiyonları oluşturabilmektedir. Bu nedenle mimari, IDS bileşenini içeren fakat IPS davranışı da gösteren hibrit IDS/IPS prototipi olarak konumlandırılmalıdır.

## 7. Güçlü Yönler

- Offline model başarımı ile çalışma zamanı SDN doğrulaması birlikte ele alınmıştır.
- Canonical ve diagnostic deney koşulları ayrıştırılmıştır.
- Port-aware/protocol-aware flow matching yaklaşımı kullanılmıştır.
- Drop, quarantine ve rate-limit aksiyonları aynı deneysel çerçevede raporlanmıştır.
- Deneysel artifact dosyaları tablo, şekil ve kalite raporlarına dönüştürülmüştür.

## 8. Sınırlılıklar

- Deneyler kontrollü Mininet ortamında yürütülmüştür; fiziksel kampüs ağına genelleme için ek testler gerekir.
- Flow-level matching, controller loglarının ayrıntı düzeyine ve zamanlama uyumuna bağlıdır.
- Mevcut model seçilmiş Top-20 özelliklerle çalışmaktadır; daha geniş CIC-DDoS2019 alt kümeleriyle yeniden eğitim ileride yapılmalıdır.
- Controller overhead, CPU/memory kullanımı ve flow rule installation latency ölçümleri daha ayrıntılı bir deney setiyle genişletilebilir.

## 9. Tez Metnine Eklenebilecek Kısa Savunma Paragrafı

Bu çalışmada run_05 koşulunun ana deney olarak seçilmesinin nedeni, model çıktıları ile SDN denetleyicisi kararlarının port-aware ve protocol-aware biçimde karşılaştırılmasına olanak sağlamasıdır. run_04 koşulu ise sistem geliştirme sürecinde önemli bir diagnostic tekrar olarak korunmuş, ancak controller loglarında port bilgisinin bulunmaması nedeniyle ana sonuçların hesaplanmasında kullanılmamıştır. Bu ayrım, deneysel sonuçların yalnızca olumlu çıktılar üzerinden değil, gözlemlenebilirlik ve eşleştirme kalitesi açısından da şeffaf biçimde değerlendirilmesini sağlamaktadır.

## 10. Önerilen Tez Kullanımı

- Bölüm 4 sonunda çalışma zamanı doğrulama sonuçlarının yorumlanması kısmına kısa savunma paragrafı eklenebilir.
- Bölüm 5’te sınırlılıklar ve literatürle karşılaştırma altına run_04/run_05 ayrımı daha açık bağlanabilir.
- Savunma sunumunda run_03, run_04 ve run_05 için ayrı bir “canonical vs diagnostic” slaytı hazırlanabilir.