# Önerilen SDN Tabanlı IDS/IPS Prototipinin Çalışma Zamanı Doğrulaması

## 1. Çalışma Zamanı Doğrulama Aşamasına Genel Bakış

Bu bölümde, önerilen yazılım tanımlı ağ tabanlı saldırı tespit ve önleme prototipinin çalışma zamanı doğrulama sonuçları sunulmaktadır. Bu aşamadaki temel amaç, geliştirilen makine öğrenmesi modelinin yalnızca çevrimdışı veri kümeleri üzerinde başarılı olup olmadığını göstermek değil, aynı zamanda canlı bir SDN deney ortamında denetleyici ile bütünleşik şekilde çalışıp çalışmadığını doğrulamaktır.

Bu doğrulama süreci Mininet tabanlı bir SDN test ortamında ve Ryu denetleyicisi kullanılarak gerçekleştirilmiştir. Deney mimarisi; trafik üretimi, PCAP yakalama, seçilmiş özellik çıkarımı, FastAPI tabanlı model çıkarımı, denetleyici taraflı politika kararı ve OpenFlow tabanlı önleme mekanizmalarından oluşmaktadır. Bu aşamada kullanılan aktif makine öğrenmesi modeli, CIC-DDoS2019 veri kümesiyle uyumlu özellik temsili üzerinden eğitilen Final XGBoost Top-20 modelidir.

Çevrimdışı sınıflandırma deneylerinden farklı olarak bu aşama, model çıktısının gerçek zamanlı ağ davranışı içinde nasıl kullanılabileceğini ve bu çıktının SDN denetleyicisi tarafından rate-limit, drop ve quarantine gibi önleme aksiyonlarına nasıl dönüştürülebileceğini göstermektedir.

## 2. Deney Senaryosu

Çalışma zamanı doğrulama deneyinde zararsız ve zararlı trafiğin birlikte bulunduğu karma bir trafik senaryosu kullanılmıştır. Zararsız trafik, `10.10.10.2` ve `10.10.10.3` gibi istemci hostlardan `10.10.40.14` adresli sunucu hosta doğru üretilmiştir. Zararlı trafik ise `10.10.60.12` adresli saldırgan hosttan yine `10.10.40.14` adresli hedef sunucuya doğru oluşturulmuştur.

Deneydeki temel zararlı trafik deseni yüksek hacimli UDP akışıdır. Bununla birlikte, TCP kontrol benzeri akışlar ve zararsız UDP trafiği de yakalanan trafik içinde yer almaktadır. Bu durum, modelin yalnızca tek tip bir saldırı trafiği üzerinde değil, karma trafik koşullarında da değerlendirilmesine olanak sağlamıştır.

Ana tez raporlaması için seçilen canonical deney koşusu aşağıdaki gibidir:

`run_05_port_aware_repeat_validation`

Bu koşu, denetleyici loglarında kaynak port ve hedef port bilgilerinin bulunması, protocol-aware runtime policy yorumlamasının yapılabilmesi ve rate-limit, drop ve quarantine aksiyonlarının aynı deneyde gözlenmesi nedeniyle ana deney olarak seçilmiştir.

## 3. Deneysel Çıktılar ve Artifact Yapısı

Bu bölümde kullanılan tablo, şekil ve özet dosyaları aşağıdaki dizin altında üretilmiştir:

`experiments/results/thesis_artifacts/run_05_port_aware_runtime_validation`

Bu dizin tezde doğrudan kullanılabilecek tabloları, şekilleri ve özet dosyalarını içermektedir. Öne çıkan dosyalar şunlardır:

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

Bu yapı, deneysel sonuçların yalnızca terminal çıktısı olarak kalmamasını, tez ve makale yazımına aktarılabilecek izlenebilir bir sonuç paketine dönüşmesini sağlamaktadır.

## 4. Tekrarlı Çalışma Zamanı Doğrulama Sonuçları

**Tablo 1. Canonical tekrarlı çalışma zamanı doğrulama sonuçları**  
Kaynak: `tables/table_canonical_runtime_validation_summary.csv`

Tablo 1, tez raporlamasında kullanılmak üzere seçilen canonical çalışma zamanı doğrulama koşularını özetlemektedir. Bu kapsamda `run_03_aligned_clean` ve `run_05_port_aware_repeat_validation` koşuları canonical doğrulama koşuları olarak değerlendirilmiştir.

Her iki canonical koşuda da runtime pipeline dokuz adet Final Top-20 model tahmin kaydı üretmiştir. Denetleyici tarafında ise her koşuda üç binden fazla politika kararı kaydedilmiştir. Bu durum, Ryu tabanlı SDN denetleyicisinin deney süresince akış istatistiklerini sürekli izlediğini ve hibrit IDS/IPS politika mantığını aktif şekilde uyguladığını göstermektedir.

En önemli bulgu, her iki canonical koşuda da runtime model çıktısı ile denetleyici taraflı davranış arasında beş adet security-compatible flow-level eşleşme elde edilmiş olmasıdır. Ayrıca her iki koşuda da drop mitigation ve quarantine ile ilişkili kayıtlar gözlenmiştir. `run_05_port_aware_repeat_validation` koşusunda buna ek olarak rate-limit aksiyonu da gözlenmiştir. Bu nedenle `run_05`, tezde ana deney olarak sunulabilecek en güçlü çalışma zamanı doğrulama koşusudur.

## 5. Denetleyici Taraflı Politika Aksiyon Dağılımı

**Tablo 2. Denetleyici taraflı IDS/IPS politika aksiyon dağılımı**  
Kaynak: `tables/table_controller_action_distribution.csv`

**Şekil 1. Denetleyici taraflı politika aksiyon dağılımı**  
Kaynak: `figures/fig_controller_action_distribution.png`

Denetleyici taraflı aksiyon dağılımı incelendiğinde, politika kararlarının büyük kısmının `allow` olduğu görülmektedir. Bu beklenen bir sonuçtur; çünkü deney ortamında çok sayıda zararsız trafik, TCP kontrol akışı ve düşük oranlı ya da sıfır oranlı akış durumu bulunmaktadır.

Bununla birlikte, sistemin yalnızca izin verme davranışı göstermediği de açıktır. `run_05_port_aware_repeat_validation` koşusunda denetleyici aşağıdaki kararları üretmiştir:

- 3179 adet `allow`
- 22 adet `quarantine_candidate`
- 1 adet `drop`
- 1 adet `rate_limit`

Bu dağılım, denetleyicinin pasif bir gözlemci olarak çalışmadığını, zararlı UDP davranışı ortaya çıktığında önleme yönelimli kararlar üretebildiğini göstermektedir.

## 6. Final XGBoost Top-20 Modelinin Runtime Tahmin Dağılımı

**Tablo 3. Final XGBoost Top-20 modelinin runtime tahmin dağılımı**  
Kaynak: `tables/table_final_top20_prediction_distribution.csv`

**Şekil 2. Runtime BENIGN/ATTACK tahmin dağılımı**  
Kaynak: `figures/fig_final_top20_prediction_distribution.png`

Runtime tahmin dağılımı, Final XGBoost Top-20 modelinin altı akışı `BENIGN`, üç akışı ise `ATTACK` olarak sınıflandırdığını göstermektedir.

Bu dağılım karma trafik senaryosu ile uyumludur. Zararsız sınıf TCP kontrol benzeri akışları ve zararsız UDP trafiğini içerirken, saldırı sınıfı `10.10.60.12` adresli saldırgan hosttan gelen zararlı UDP davranışını temsil etmektedir. Aynı PCAP yakalaması içinden hem benign hem de attack sınıflarının üretilmesi, seçilmiş özellik tabanlı modelin canlı trafik verisinden çıkarılan akış kayıtlarına uygulanabilir olduğunu göstermektedir.

Bu sonuç, modelin yalnızca statik CSV veri kümeleri üzerinde değil, canlı SDN deney ortamından elde edilen PCAP tabanlı özellikler üzerinde de çalışabildiğini ortaya koymaktadır.

## 7. Protocol-Aware Final Policy Yorumu

**Tablo 4. Protocol-aware final policy dağılımı**  
Kaynak: `tables/table_protocol_aware_final_policy_distribution.csv`

**Şekil 3. Protocol-aware final policy aksiyon dağılımı**  
Kaynak: `figures/fig_protocol_aware_final_policy_distribution.png`

Runtime model çıktısı temel olarak binary bir sınıflandırma sunmaktadır: benign veya attack. Ancak SDN denetleyicisi tarafında bu çıktıların doğrudan kullanılması her zaman yeterli değildir. Özellikle TCP kontrol benzeri akışların, trafik bağlamı nedeniyle yüksek saldırı olasılığı alması mümkündür. Buna rağmen bu akışların yüksek hacimli UDP flood akışlarıyla aynı şekilde ele alınması doğru olmayacaktır.

Bu nedenle protocol-aware final policy katmanı geliştirilmiştir. Bu katman model çıktısını taşıma protokolü ve akış bağlamı ile birlikte yorumlamaktadır. `run_05` koşusunda aşağıdaki final policy sınıfları üretilmiştir:

- 6 adet `ALLOW_CONTROL_FLOW`
- 1 adet `ALLOW`
- 1 adet `DROP`
- 1 adet `QUARANTINE_OBSERVED`

Bu ayrım, TCP kontrol benzeri akışların yanlışlıkla UDP flood saldırısı gibi değerlendirilmesini engellemekte ve quarantine hostuna yönelen trafiğin normal hedefe yönelen saldırı trafiğinden ayrı yorumlanmasını sağlamaktadır.

## 8. SDN Denetleyicisi Önleme Aksiyonları

**Tablo 5. SDN denetleyicisi önleme aksiyon özeti**  
Kaynak: `tables/table_enforcement_action_summary.csv`

**Şekil 4. SDN denetleyicisi önleme aksiyon özeti**  
Kaynak: `figures/fig_enforcement_action_summary.png`

Önleme aksiyonları özeti, denetleyicinin tespit kararlarını veri düzleminde uygulanabilir aksiyonlara dönüştürdüğünü göstermektedir. Canonical port-aware koşuda aşağıdaki önleme kayıtları gözlenmiştir:

- 7 adet drop mitigation kaydı
- 7 adet quarantine-related kayıt
- 1 adet rate-limit kaydı

Drop kayıtları, tespit edilen zararlı UDP akışı için OpenFlow drop kurallarının kurulduğunu göstermektedir. Quarantine kayıtları, tekrarlanan yüksek güvenli saldırı davranışının quarantine forwarding ile sonuçlandığını göstermektedir. Rate-limit kaydı ise denetleyicinin yalnızca sert önleme aksiyonları değil, daha yumuşak bir sınırlama aksiyonu da uygulayabildiğini göstermektedir.

Bu bulgu, önerilen sistemin yalnızca saldırı tespiti yapan pasif bir IDS değil, aynı zamanda çalışma zamanında önleme aksiyonları üretebilen bir SDN tabanlı IDS/IPS prototipi olduğunu desteklemektedir.

## 9. Flow-Level Model ve Denetleyici Karşılaştırması

**Tablo 6. Flow-level model-controller karşılaştırması**  
Kaynak: `tables/table_flow_level_model_controller_comparison.csv`

Flow-level karşılaştırma bu doğrulama aşamasının en kritik çıktılarından biridir. Bu tablo, runtime model çıktıları ile denetleyici taraflı politika kayıtlarını kaynak IP, hedef IP, kaynak port, hedef port ve taşıma protokolü düzeyinde karşılaştırmaktadır.

Deneydeki temel zararlı akış, `10.10.60.12` adresinden `10.10.40.14` adresine giden UDP akışıdır. Bu akış runtime model tarafından `ATTACK` olarak sınıflandırılmış ve protocol-aware final policy çıktısında `DROP` olarak yorumlanmıştır. Denetleyici tarafında ise aynı akış `quarantine_candidate` aksiyonu ile ilişkilendirilmiştir. Ayrıca aynı akış için drop, quarantine ve rate-limit kayıtlarının da eşleştiği görülmektedir.

Bu durum exact action matching yerine security-compatible matching yaklaşımının neden daha anlamlı olduğunu göstermektedir. Çünkü binary model çıktısı `DROP` önerirken, denetleyici tekrarlanan yüksek güvenli saldırı davranışı nedeniyle aksiyonu quarantine seviyesine yükseltebilir. Dolayısıyla controller aksiyonunun model aksiyonu ile birebir aynı olması beklenmemelidir; önemli olan güvenlik açısından uyumlu bir önleme davranışının ortaya çıkmasıdır.

Quarantine hostu olan `10.10.99.16` adresine yönelen akış ise post-mitigation observation olarak yorumlanmıştır. Bu akış normal bir kaynak-hedef saldırı akışı gibi değerlendirilmemeli, denetleyici tarafından uygulanan quarantine mekanizmasının sonucu olarak ele alınmalıdır.

## 10. Saldırı Olasılığı ve Final Policy Eşlemesi

**Tablo 7. Flow-level saldırı olasılığı ve protocol-aware final action özeti**  
Kaynak: `tables/table_protocol_aware_attack_probability_summary.csv`

Saldırı olasılığı özeti, Final XGBoost Top-20 modelinin her runtime akış için ürettiği saldırı olasılıklarını göstermektedir. Zararsız akışlar düşük saldırı olasılıkları almış ve `ALLOW` ya da `ALLOW_CONTROL_FLOW` olarak yorumlanmıştır. Buna karşılık zararlı UDP akışı yüksek saldırı olasılığı almış ve `DROP` aksiyonuna eşlenmiştir.

Quarantine hostuna yönelen post-mitigation akış da yüksek saldırı olasılığı almıştır; ancak bu akış `QUARANTINE_OBSERVED` olarak etiketlenmiştir. Bu ayrım, quarantine yönlendirmesi sonucunda oluşan trafiğin normal hedefe giden saldırı trafiğiyle karıştırılmasını engellemektedir.

Bu sonuç, makine öğrenmesi çıktılarının protocol-aware ve context-aware bir yorumlama katmanı ile birlikte kullanılmasının çalışma zamanı SDN güvenliği açısından önemli olduğunu göstermektedir.

## 11. Genel Değerlendirme

Çalışma zamanı doğrulama sonuçları, önerilen SDN tabanlı IDS/IPS prototipinin zararsız trafiği koruyabildiğini, zararlı UDP trafiğini tespit edebildiğini ve denetleyici taraflı önleme aksiyonları uygulayabildiğini göstermektedir.

Başarılı doğrulama zinciri şu aşamalardan oluşmaktadır:

1. Mininet tabanlı SDN ortamında karma trafik üretimi
2. Canlı trafiğin PCAP olarak yakalanması
3. CICFlowMeter uyumlu seçilmiş özelliklerin çıkarılması
4. Final XGBoost Top-20 modelinden runtime tahmin alınması
5. Protocol-aware final policy yorumunun yapılması
6. Ryu denetleyicisi tarafında politika kararının üretilmesi
7. OpenFlow tabanlı rate-limit, drop ve quarantine aksiyonlarının uygulanması

Bu zincir, önerilen mimarinin yalnızca çevrimdışı model başarısına dayanmadığını, çalışma zamanı SDN ortamında uçtan uca çalışabildiğini göstermektedir.

## 12. Tez Açısından Katkı

Bu deneysel aşama teze üç temel katkı sağlamaktadır.

İlk olarak, çevrimdışı olarak eğitilmiş seçilmiş özellik tabanlı bir makine öğrenmesi modelinin çalışma zamanı SDN pipeline’ına entegre edilebildiği gösterilmiştir. Final XGBoost Top-20 modeli, PCAP üzerinden çıkarılan akış özellikleri üzerinde anlamlı benign/attack tahminleri üretmiştir.

İkinci olarak, binary model çıktılarının SDN denetleyicisi tarafında daha zengin ve ağ bağlamına duyarlı bir politika yorumuna dönüştürülebileceği gösterilmiştir. Protocol-aware final policy katmanı TCP kontrol akışlarını, zararsız UDP trafiğini, zararlı UDP trafiğini ve quarantine sonrası gözlenen trafiği ayrı ayrı yorumlamaktadır.

Üçüncü olarak, önerilen mimarinin aktif önleme aksiyonları üretebildiği gösterilmiştir. Rate-limit, drop ve quarantine kayıtları, sistemin pasif bir saldırı tespit mekanizmasından ziyade önleme odaklı bir SDN güvenlik prototipi olarak çalıştığını ortaya koymaktadır.

## 13. Sınırlılıklar

Bu sonuçlar güçlü bir çalışma zamanı doğrulama kanıtı sunsa da bazı sınırlılıklar dikkate alınmalıdır.

İlk olarak, deneyler kontrollü bir Mininet ortamında gerçekleştirilmiştir. Bu ortam tekrarlanabilirlik ve gözlemlenebilirlik açısından avantaj sağlasa da sistemin daha çeşitli trafik profilleri ve daha uzun süreli senaryolar altında da test edilmesi gerekmektedir.

İkinci olarak, PCAP tabanlı runtime model çıktıları ile denetleyici logları arasındaki flow-level eşleştirme zamanlama, flow-stat polling aralığı ve port bilgilerinin denetleyici loglarında bulunmasına bağlıdır. Önceki diagnostic koşul olan `run_04_repeat_mixed_validation`, port bilgisinin eksik olduğu durumlarda exact matching’in zayıfladığını göstermiştir.

Üçüncü olarak, exact action matching tek başına yeterli bir ölçüt değildir. Çünkü makine öğrenmesi modeli binary bir çıktı üretirken, SDN denetleyicisi rate-limit, drop ve quarantine gibi daha zengin bir aksiyon uzayına sahiptir. Bu nedenle security-compatible matching daha anlamlı bir değerlendirme yaklaşımıdır.

Son olarak, mevcut model seçilmiş Top-20 özellik alt kümesiyle eğitilmiştir. Bu yaklaşım çalışma zamanı uygulanabilirliği açısından avantaj sağlasa da daha büyük ve temsili CIC-DDoS2019 alt kümeleri üzerinde yeniden eğitim yapılması modelin genellenebilirliğini artırabilir.

## 14. Sonuç

Canonical port-aware runtime validation deneyi, önerilen SDN tabanlı hibrit IDS/IPS prototipinin canlı bir SDN test ortamında çalışabildiğini göstermektedir. Sistem zararsız ve kontrol trafiğini korumuş, zararlı UDP davranışını yüksek saldırı olasılığı ile tespit etmiş ve denetleyici tarafında rate-limit, drop ve quarantine aksiyonları üretmiştir.

Bu sonuçlar, çalışmanın temel iddiasını desteklemektedir: makine öğrenmesi tabanlı DDoS tespiti, SDN denetleyicisiyle bütünleştirilerek kampüs benzeri yazılım tanımlı ağ ortamlarında çalışma zamanı saldırı tespit ve önleme mekanizmasına dönüştürülebilir.

