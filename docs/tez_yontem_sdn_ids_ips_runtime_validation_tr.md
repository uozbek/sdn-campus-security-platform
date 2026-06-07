# Yöntem: SDN Tabanlı Makine Öğrenmesi Destekli IDS/IPS Mimarisi

## 1. Yöntem Bölümüne Genel Bakış

Bu bölümde, kampüs ağı benzeri bir yazılım tanımlı ağ ortamında DDoS saldırılarının makine öğrenmesi destekli olarak tespit edilmesi ve SDN denetleyicisi üzerinden önlenmesi için geliştirilen prototip mimari açıklanmaktadır. Önerilen yaklaşım, yalnızca çevrimdışı sınıflandırma başarısını ölçen klasik makine öğrenmesi deneylerinden farklı olarak, model çıktılarının çalışma zamanı ağ denetimi ve önleme kararlarıyla nasıl ilişkilendirilebileceğini göstermeyi amaçlamaktadır.

Bu amaç doğrultusunda çalışma üç temel katman üzerine kurulmuştur. İlk katman, Mininet ve Open vSwitch kullanılarak oluşturulan SDN deney ortamıdır. İkinci katman, Ryu tabanlı SDN denetleyicisi ve bu denetleyici içinde çalışan IDS/IPS politika mantığıdır. Üçüncü katman ise CIC-DDoS2019 veri kümesiyle uyumlu seçilmiş özellikler üzerinde eğitilen makine öğrenmesi modeli ve bu modeli çalışma zamanında sorgulayan FastAPI tabanlı tahmin servisidir.

Önerilen mimaride ağ trafiği yalnızca gözlemlenmemekte, aynı zamanda zararlı davranış tespit edildiğinde rate-limit, drop ve quarantine gibi önleme aksiyonlarına dönüştürülmektedir. Bu yönüyle çalışma, SDN tabanlı bir intrusion detection sisteminden ziyade, tespit ve önleme işlevlerini birlikte ele alan hibrit bir IDS/IPS prototipi olarak konumlandırılmıştır.

## 2. Önerilen Mimari

Önerilen sistem mimarisi dört ana bileşenden oluşmaktadır:

1. SDN veri düzlemi
2. SDN kontrol düzlemi
3. Makine öğrenmesi tabanlı tespit servisi
4. Politika ve önleme mekanizması

Veri düzleminde Mininet üzerinde oluşturulan sanal hostlar ve Open vSwitch anahtarları yer almaktadır. Bu katman, kampüs ağı benzeri bir yapının deneysel olarak modellenmesini sağlar. Kontrol düzleminde Ryu denetleyicisi çalışmakta ve OpenFlow aracılığıyla anahtarlarla haberleşmektedir. Makine öğrenmesi katmanında Final XGBoost Top-20 modeli FastAPI üzerinden erişilebilir hale getirilmiştir. Politika katmanı ise model çıktıları, akış istatistikleri ve yerel sezgisel kuralları birleştirerek nihai aksiyonu belirlemektedir.

Bu mimari içinde trafik akışı genel olarak şu sırayla işlenmektedir:

- Mininet hostları arasında benign ve malicious trafik üretilir.
- Open vSwitch anahtarları akışları Ryu denetleyicisine bildirir.
- Denetleyici flow statistics bilgilerini düzenli olarak toplar.
- Trafik ayrıca PCAP olarak yakalanır.
- PCAP dosyasından CICFlowMeter uyumlu seçilmiş özellikler çıkarılır.
- Final XGBoost Top-20 modeli bu özellikler üzerinde tahmin üretir.
- Runtime model çıktıları protocol-aware final policy katmanında yorumlanır.
- Denetleyici tarafında allow, monitor, rate-limit, drop veya quarantine gibi aksiyonlar uygulanır.
- Tüm kararlar CSV, JSON ve Markdown raporları olarak kaydedilir.

Bu yapı sayesinde hem model tarafındaki tespit başarısı hem de denetleyici tarafındaki önleme davranışı birlikte incelenebilmektedir.

## 3. SDN Deney Ortamı

Deney ortamı Mininet kullanılarak oluşturulmuştur. Mininet, SDN tabanlı ağ deneylerinin kontrollü ve tekrarlanabilir şekilde yürütülmesini sağladığı için tercih edilmiştir. Deneylerde Open vSwitch anahtarları OpenFlow 1.3 protokolü ile Ryu denetleyicisine bağlanmıştır.

Bu çalışma kapsamında kullanılan topoloji, kampüs ağı mantığını temsil edecek şekilde tasarlanmıştır. Topolojide farklı alt ağlara ait benign istemciler, saldırgan hostlar, hedef sunucu ve quarantine hostu bulunmaktadır. Örnek IP grupları aşağıdaki şekilde yapılandırılmıştır:

- Benign istemci hostları: `10.10.10.0/24`
- Hedef sunucu: `10.10.40.14`
- Saldırgan host: `10.10.60.12`
- Quarantine hostu: `10.10.99.16`

Bu yapı, zararsız istemci trafiği ile zararlı saldırı trafiğinin aynı deney ortamında üretilebilmesini sağlamaktadır. Ayrıca quarantine hostunun ayrı bir ağ segmentinde konumlandırılması, saldırgan trafiğin tespit sonrasında izole edilmesini deneysel olarak incelemeye olanak tanımaktadır.

## 4. Ryu Tabanlı SDN Denetleyicisi

Kontrol düzleminde Ryu tabanlı özel bir SDN denetleyicisi geliştirilmiştir. Denetleyicinin görevi yalnızca paket yönlendirme yapmak değildir. Denetleyici aynı zamanda akış istatistiklerini toplamakta, model veya sezgisel kurallardan gelen güvenlik sinyallerini değerlendirmekte ve nihai politika aksiyonunu üretmektedir.

Denetleyici tarafında aşağıdaki temel işlevler uygulanmıştır:

- OpenFlow 1.3 tabanlı anahtar bağlantılarının yönetilmesi
- IPv4 akışlarının izlenmesi
- TCP/UDP kaynak ve hedef port bilgilerinin çıkarılması
- Flow statistics kayıtlarının periyodik olarak toplanması
- Paket oranı ve byte oranı gibi runtime metriklerin hesaplanması
- Makine öğrenmesi API servisinden tahmin alınması
- API ulaşılamadığında veya model çıktısı belirsiz olduğunda yerel sezgisel karar mantığının kullanılması
- Allow, monitor, rate-limit, drop ve quarantine_candidate kararlarının üretilmesi
- OpenFlow kuralı veya meter kurulumu ile önleme aksiyonlarının uygulanması
- Deneysel analiz için logların CSV formatında saklanması

Bu yapı, denetleyiciyi yalnızca merkezi bir yönlendirme bileşeni olmaktan çıkarıp, güvenlik odaklı bir karar ve aksiyon motoruna dönüştürmektedir.

## 5. Makine Öğrenmesi Modeli

Bu çalışmada aktif runtime model olarak Final XGBoost Top-20 modeli kullanılmıştır. Model, CIC-DDoS2019 veri kümesiyle uyumlu özellik temsili üzerinde eğitilmiştir. Özellik seçimi sonucunda çalışma zamanı uygulanabilirliğini artırmak amacıyla 20 özelliklik daha hafif bir özellik alt kümesi tercih edilmiştir.

Bu yaklaşımın iki temel nedeni vardır. Birincisi, SDN denetleyicisiyle entegre edilecek bir modelin düşük gecikme ile çalışması gerekmektedir. Çok yüksek boyutlu özellik vektörleri runtime çıkarım süresini ve entegrasyon karmaşıklığını artırabilir. İkincisi, seçilmiş özelliklerle çalışan daha hafif bir model, deneysel prototip aşamasında daha kolay izlenebilir ve açıklanabilir sonuçlar üretmektedir.

Modelin çalışma zamanı pipeline’ında kullanılan genel akış şu şekildedir:

- PCAP dosyasından flow-level kayıtlar çıkarılır.
- Çıkarılan akış kayıtları aktif modelin beklediği `feature_order.json` sırasına göre düzenlenir.
- Eksik ve fazla özellikler kontrol edilir.
- Her akış FastAPI tabanlı tahmin servisine gönderilir.
- Model `BENIGN` veya `ATTACK` tahmini üretir.
- Model ayrıca saldırı olasılığı ve önerilen aksiyon bilgisini döndürür.
- Bu çıktı protocol-aware final policy katmanına aktarılır.

Bu yöntem, çevrimdışı eğitilen modelin çalışma zamanı SDN deney ortamına entegre edilmesini sağlamaktadır.

## 6. Runtime Feature Extraction Pipeline

Çalışma zamanı doğrulamasında kullanılan en kritik adımlardan biri PCAP tabanlı özellik çıkarımıdır. Deney sırasında üretilen trafik PCAP olarak kaydedilmiş, daha sonra bu PCAP dosyasından Final XGBoost Top-20 modelinin beklediği seçilmiş özellikler çıkarılmıştır.

Bu amaçla geliştirilen runtime pipeline aşağıdaki alt adımlardan oluşmaktadır:

1. PCAP dosyasının okunması
2. IP, TCP ve UDP paketlerinin ayrıştırılması
3. Akışların kaynak IP, hedef IP, kaynak port, hedef port ve protokol bilgisine göre gruplanması
4. CICFlowMeter uyumlu istatistiksel özelliklerin hesaplanması
5. Seçilmiş Top-20 özellik sırasının doğrulanması
6. Aktif model API’sine tahmin isteği gönderilmesi
7. Tahmin sonuçlarının CSV ve JSON olarak kaydedilmesi
8. Deney raporunun Markdown formatında üretilmesi

Bu pipeline sayesinde canlı deney ortamından elde edilen ham trafik, makine öğrenmesi modelinin kullanabileceği yapılandırılmış akış özelliklerine dönüştürülmüştür.

## 7. Protocol-Aware Final Policy Katmanı

Runtime model çıktısı tek başına yeterli değildir; çünkü model yalnızca akışın benign veya attack olma durumunu tahmin eder. Ancak SDN denetleyicisi tarafında alınacak aksiyon, taşıma protokolü ve akış bağlamına göre farklılaşmalıdır.

Bu nedenle protocol-aware final policy katmanı geliştirilmiştir. Bu katman model tahminlerini PCAP içinden çıkarılan protokol bilgisiyle birlikte yorumlar. Özellikle TCP kontrol benzeri akışlar, UDP saldırı akışları ve quarantine sonrası gözlenen akışlar birbirinden ayrıştırılır.

Final policy katmanında kullanılan temel yorumlama mantığı şu şekildedir:

- TCP kontrol veya kontrol benzeri akışlar `ALLOW_CONTROL_FLOW` olarak işaretlenir.
- Zararsız UDP akışları `ALLOW` olarak değerlendirilir.
- Yüksek olasılıklı zararlı UDP akışları `DROP` olarak yorumlanır.
- Quarantine hostuna yönelen post-mitigation akışlar `QUARANTINE_OBSERVED` olarak etiketlenir.

Bu ayrım, deneysel sonuçların daha doğru yorumlanmasını sağlamaktadır. Özellikle saldırgan hosttan çıkan TCP kontrol akışlarının doğrudan UDP flood saldırısı gibi değerlendirilmesini engellemektedir.

## 8. Hibrit Politika Karar Mekanizması

Denetleyici tarafında kullanılan karar mekanizması yalnızca makine öğrenmesi modeline dayanmamaktadır. Bunun yerine model çıktısı, akış istatistikleri ve yerel sezgisel kurallar birlikte değerlendirilmiştir. Bu nedenle yaklaşım hibrit bir IDS/IPS politikası olarak adlandırılabilir.

Politika karar mekanizması genel olarak şu sinyalleri kullanmaktadır:

- Model tahmini
- Model güven skoru
- Paket oranı
- Byte oranı
- Kaynak IP risk sayacı
- Tekrarlanan yüksek güvenli saldırı davranışı
- Protokol ve port bilgisi
- API erişilebilirliği

Bu sinyaller sonucunda denetleyici aşağıdaki aksiyonlardan birini üretebilir:

- `allow`
- `monitor`
- `rate_limit`
- `drop`
- `quarantine_candidate`

Bu aksiyon uzayı, binary model çıktısından daha zengindir. Bu nedenle deneysel değerlendirmede yalnızca exact action matching değil, security-compatible matching yaklaşımı da kullanılmıştır.

## 9. Önleme Mekanizmaları

Önerilen sistemde üç temel önleme mekanizması uygulanmıştır:

### 9.1 Rate-Limit

Rate-limit mekanizması, zararlı olma ihtimali yüksek fakat doğrudan drop gerektirmeyen akışların bant genişliğini sınırlamak için kullanılmıştır. Bu mekanizma OpenFlow meter yapısı üzerinden uygulanmıştır. Rate-limit, daha yumuşak bir önleme aksiyonu olarak değerlendirilmiştir.

### 9.2 Drop

Drop mekanizması, yüksek güvenle zararlı olarak değerlendirilen akışlar için uygulanmıştır. Denetleyici, ilgili akışa karşı OpenFlow drop kuralı kurarak trafiğin veri düzleminde engellenmesini sağlar. Deneylerde UDP saldırı akışı için drop mitigation kayıtları gözlenmiştir.

### 9.3 Quarantine

Quarantine mekanizması, tekrarlanan yüksek güvenli saldırı davranışı gösteren kaynakların izole edilmesi amacıyla kullanılmıştır. Bu durumda trafik, normal hedef yerine quarantine hostuna yönlendirilir veya quarantine ile ilişkili aksiyonlar üretilir. Deney ortamında quarantine hostu `10.10.99.16` olarak yapılandırılmıştır.

Bu üç mekanizma, önerilen mimarinin yalnızca saldırı tespiti değil, aynı zamanda saldırı önleme fonksiyonuna sahip olduğunu göstermektedir.

## 10. Loglama ve Deneysel İzlenebilirlik

Deneysel sonuçların analiz edilebilmesi için sistemin farklı bileşenleri tarafından çeşitli log dosyaları üretilmiştir. Bu loglar hem hata ayıklama hem de tezde kullanılacak deneysel tabloların oluşturulması için kullanılmıştır.

Başlıca log dosyaları şunlardır:

- `policy_decisions.csv`
- `predictions.csv`
- `flow_stats.csv`
- `mitigation_log.csv`
- `rate_limit_log.csv`
- `quarantine_log.csv`
- `mitigation_latency.csv`

`policy_decisions.csv`, denetleyici tarafından üretilen nihai politika kararlarını içermektedir. `predictions.csv`, model veya hibrit karar mekanizmasına ilişkin tahmin kayıtlarını tutmaktadır. `flow_stats.csv`, OpenFlow anahtarlarından toplanan akış istatistiklerini içermektedir. `mitigation_log.csv`, `rate_limit_log.csv` ve `quarantine_log.csv` ise uygulanan önleme aksiyonlarını ayrı ayrı belgelemektedir.

Bu yapı, deneysel sürecin yeniden izlenebilirliğini artırmakta ve sonuçların yalnızca görsel gözleme değil, dosya tabanlı kanıtlara dayanmasını sağlamaktadır.

## 11. Model-Controller Karşılaştırma Yöntemi

Runtime model çıktıları ile denetleyici taraflı kararların karşılaştırılması için port-aware ve protocol-aware bir karşılaştırma yöntemi kullanılmıştır. Karşılaştırmada temel akış anahtarı şu alanlardan oluşmaktadır:

- Kaynak IP
- Hedef IP
- Kaynak port
- Hedef port
- IP protokolü

Bu yaklaşım, aynı kaynak ve hedef IP çiftleri arasında farklı TCP/UDP akışlarının ayrıştırılmasını sağlamaktadır. Özellikle iperf3 gibi araçlarla üretilen trafiklerde aynı hedef port kullanılsa bile kaynak portlar farklı olabildiğinden, port-aware eşleştirme deneysel doğruluk açısından önemlidir.

Karşılaştırmada iki farklı uyumluluk düzeyi dikkate alınmıştır:

1. Exact controller flow-key match
2. Security-compatible action match

Exact match, model çıktısı ve denetleyici loglarının aynı flow key üzerinde buluşup buluşmadığını gösterir. Security-compatible match ise aksiyon adları birebir aynı olmasa bile güvenlik açısından uyumlu bir davranışın oluşup oluşmadığını değerlendirir.

Bu ayrım önemlidir; çünkü model `DROP` önerirken, denetleyici aynı akışı tekrarlanan saldırı davranışı nedeniyle `quarantine_candidate` olarak değerlendirebilir. Bu durumda aksiyon adları farklı olsa da güvenlik amacı açısından uyumludur.

## 12. Deneylerin Sınıflandırılması

Tekrarlı runtime deneyleri üç sınıfta değerlendirilmiştir:

### 12.1 Canonical Runs

Canonical run’lar, tezde ana deneysel bulgu olarak kullanılabilecek koşulardır. Bu koşullarda model çıktıları, protokol bilgisi, port bilgisi ve controller logları uyumlu şekilde değerlendirilebilmiştir.

Bu kapsamda iki canonical koşu belirlenmiştir:

- `run_03_aligned_clean`
- `run_05_port_aware_repeat_validation`

Ana tez raporlaması için özellikle `run_05_port_aware_repeat_validation` seçilmiştir.

### 12.2 Supporting Runs

`run_03_aligned_clean`, ilk başarılı runtime validation koşusu olarak destekleyici deney konumundadır. Bu koşu, sistemin uçtan uca çalıştığını göstermesi açısından önemlidir.

### 12.3 Diagnostic Runs

`run_04_repeat_mixed_validation`, port bilgisinin controller loglarında eksik olması nedeniyle diagnostic veya partial repetition olarak sınıflandırılmıştır. Bu koşu ana performans sonucu olarak kullanılmamış, ancak geliştirme sürecinde port-aware logging ihtiyacını göstermesi açısından değerli kabul edilmiştir.

## 13. Tezde Kullanılan Ana Deney Paketi

Ana tez raporlaması için kullanılan artifact paketi aşağıdaki dizinde tutulmaktadır:

`experiments/results/thesis_artifacts/run_05_port_aware_runtime_validation`

Bu dizin altında tezde kullanılacak tablolar, şekiller, manifest dosyaları ve özetler yer almaktadır. Ana metin için kullanılacak Türkçe sonuç bölümü ise şu dosyada hazırlanmıştır:

`docs/tez_runtime_validation_bolumu_tr.md`

Yöntem bölümü ile sonuç bölümü birlikte değerlendirildiğinde, çalışma hem sistem tasarımını hem de deneysel doğrulama çıktısını bütünlüklü olarak sunmaktadır.

## 14. Yöntemin Genel Değerlendirmesi

Önerilen yöntem, makine öğrenmesi tabanlı DDoS tespitini SDN denetleyicisi ile bütünleştirerek çalışma zamanı önleme davranışına dönüştürmektedir. Bu yaklaşımda model, doğrudan veri düzlemine müdahale etmez; bunun yerine SDN denetleyicisine güvenlik sinyali sağlar. Denetleyici ise bu sinyali ağ bağlamı, protokol bilgisi ve yerel politika mantığı ile birlikte değerlendirerek uygulanabilir aksiyona dönüştürür.

Bu yönüyle önerilen yöntem, klasik offline IDS değerlendirmelerinden ayrılmaktadır. Çalışmada yalnızca modelin sınıflandırma başarısı değil, model çıktısının SDN ortamında kullanılabilirliği, akış bazlı yorumlanabilirliği ve OpenFlow tabanlı önleme aksiyonlarına dönüştürülebilirliği incelenmiştir.

Sonuç olarak yöntem, kampüs benzeri SDN ortamlarında makine öğrenmesi destekli DDoS tespit ve önleme sistemlerinin prototiplenmesi için uygulanabilir bir çerçeve sunmaktadır.

