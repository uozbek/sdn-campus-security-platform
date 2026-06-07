# Bölüm 4. Yöntem ve Çalışma Zamanı Doğrulama

Bu bölümde, önerilen SDN tabanlı makine öğrenmesi destekli IDS/IPS mimarisinin tasarımı, deneysel prototip yapısı, çalışma zamanı doğrulama süreci ve elde edilen bulgular bütünlüklü bir çerçevede sunulmaktadır. Çalışmanın temel amacı, DDoS saldırı tespitinin yalnızca çevrimdışı veri kümesi üzerinde yapılan bir sınıflandırma problemi olarak ele alınmasının ötesine geçmek ve eğitilmiş model çıktılarının çalışma zamanında SDN denetleyicisi tarafından nasıl kullanılabileceğini göstermektir.

Bu nedenle bölüm iki ana eksen üzerine kurulmuştur. İlk eksende, Mininet/Open vSwitch tabanlı deney ortamı, Ryu denetleyicisi, FastAPI üzerinden sunulan makine öğrenmesi modeli, runtime feature extraction pipeline, protocol-aware final policy katmanı ve rate-limit/drop/quarantine önleme mekanizmaları yöntemsel olarak açıklanmaktadır. İkinci eksende ise geliştirilen prototipin karma normal ve zararlı trafik senaryosu altında nasıl davrandığı deneysel olarak değerlendirilmektedir.

Bölümde sunulan deneysel doğrulama, önerilen mimarinin uçtan uca çalışabilirliğini göstermeyi hedeflemektedir. Bu kapsamda trafik üretimi, PCAP yakalama, seçilmiş özellik çıkarımı, Final XGBoost Top-20 modeliyle tahmin üretimi, denetleyici taraflı politika kararı ve OpenFlow tabanlı önleme aksiyonları aynı deney zinciri içinde ele alınmıştır. Böylece önerilen yaklaşımın yalnızca saldırıyı sınıflandırabilen bir model değil, SDN kontrol düzlemine entegre edilebilen aktif bir IDS/IPS prototipi olduğu gösterilmeye çalışılmıştır.

Bölümün sonunda, elde edilen sonuçların tez açısından katkısı ve yöntemin sınırlılıkları tartışılmaktadır. Bu tartışma, sonraki bölümlerde yapılacak genel değerlendirme ve gelecek çalışma önerileri için temel oluşturmaktadır.

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

- Mininet hostları arasında normal ve zararlı trafik üretilir.
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

## 4.4. Ryu Tabanlı SDN Denetleyicisi

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

## 4.5. Makine Öğrenmesi Modeli

Bu çalışmada aktif runtime model olarak Final XGBoost Top-20 modeli kullanılmıştır. Model, CIC-DDoS2019 veri kümesiyle uyumlu özellik temsili üzerinde eğitilmiştir. Özellik seçimi sonucunda çalışma zamanı uygulanabilirliğini artırmak amacıyla 20 özelliklik daha hafif bir özellik alt kümesi tercih edilmiştir.

Bu yaklaşımın iki temel nedeni vardır. Birincisi, SDN denetleyicisiyle entegre edilecek bir modelin düşük gecikme ile çalışması gerekmektedir. Çok yüksek boyutlu özellik vektörleri runtime çıkarım süresini ve entegrasyon karmaşıklığını artırabilir. İkincisi, seçilmiş özelliklerle çalışan daha hafif bir model, deneysel prototip aşamasında daha kolay izlenebilir ve açıklanabilir sonuçlar üretmektedir.

Modelin çalışma zamanı pipeline’ında kullanılan genel akış şu şekildedir:

- PCAP dosyasından flow-level kayıtlar çıkarılır.
- Çıkarılan akış kayıtları aktif modelin beklediği `feature_order.json` sırasına göre düzenlenir.
- Karşılanmayan ve fazladan özellikler kontrol edilir.
- Her akış FastAPI tabanlı tahmin servisine gönderilir.
- Model `BENIGN` veya `ATTACK` tahmini üretir.
- Model ayrıca saldırı olasılığı ve önerilen aksiyon bilgisini döndürür.
- Bu çıktı protocol-aware final policy katmanına aktarılır.

Bu yöntem, çevrimdışı eğitilen modelin çalışma zamanı SDN deney ortamına entegre edilmesini sağlamaktadır.

## 4.6. Runtime Feature Extraction Pipeline

Çalışma zamanı doğrulamasında kullanılan en kritik adımlardan biri PCAP tabanlı özellik çıkarımıdır. Deney sırasında üretilen trafik PCAP olarak kaydedilmiş, ardından bu PCAP dosyasından Final XGBoost Top-20 modelinin beklediği seçilmiş özellikler çıkarılmıştır.

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

## 4.7. Protocol-Aware Final Policy Katmanı

Runtime model çıktısı tek başına yeterli değildir; çünkü model yalnızca akışın normal ya da saldırı niteliği taşıyıp taşımadığını tahmin eder. Ancak SDN denetleyicisi tarafında alınacak aksiyon, taşıma protokolü ve akış bağlamına göre farklılaşmalıdır.

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

Bu çalışmada model girdisi, çalışma zamanı akışından çıkarılan seçilmiş özelliklerden oluşan bir vektör olarak ele alınmıştır:

$$
\mathbf{x}_t = [f_1, f_2, \ldots, f_n]
$$

Burada \(\mathbf{x}_t\), \(t\) anında değerlendirilen akışa ait özellik vektörünü; \(f_i\) ise modelin beklediği seçilmiş akış özelliklerini göstermektedir. Makine öğrenmesi modeli bu vektör üzerinden saldırı olasılığını üretmektedir:

$$
p_t = P(y_t = \mathrm{attack} \mid \mathbf{x}_t)
$$

Denetleyici tarafındaki nihai aksiyon ise yalnızca bu olasılığa değil, protokol, port, trafik oranı ve önceki davranış geçmişi gibi çalışma zamanı bağlamına da bağlıdır. Bu ilişki aşağıdaki politika fonksiyonu ile özetlenebilir:

$$
a_t = \pi(p_t, proto_t, port_t, r_t, h_t)
$$

Burada \(a_t\) denetleyicinin uyguladığı aksiyonu, \(proto_t\) protokol bilgisini, \(port_t\) port bilgisini, \(r_t\) paket veya byte oranına dayalı trafik sinyalini, \(h_t\) ise kaynak akışın önceki davranış geçmişini ifade etmektedir. Bu kapsamda aksiyon uzayı aşağıdaki gibi tanımlanmıştır:

$$
a_t \in \{\mathrm{allow}, \mathrm{monitor}, \mathrm{rate\mbox{-}limit}, \mathrm{drop}, \mathrm{quarantine}\}
$$

Bu aksiyon uzayı, ikili model çıktısından daha zengin bir karar alanı sunmaktadır. Bu nedenle deneysel değerlendirmede yalnızca exact action matching değil, security-compatible matching yaklaşımı da kullanılmıştır.

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

`run_04_repeat_mixed_validation`, port bilgisinin controller loglarında bulunmaması nedeniyle diagnostic veya partial repetition olarak sınıflandırılmıştır. Bu koşu ana performans sonucu olarak kullanılmamış, ancak geliştirme sürecinde port-aware logging ihtiyacını göstermesi açısından değerli kabul edilmiştir.

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



---

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

## 4.8. Tekrarlı Çalışma Zamanı Doğrulama Sonuçları


> **[TABLO EKLEME NOKTASI — Tablo 4.4.1]**  
> Dosya: `experiments/results/thesis_artifacts/run_05_port_aware_runtime_validation/tables/table_canonical_runtime_validation_summary.csv`  
> Başlık: Canonical tekrarlı çalışma zamanı doğrulama sonuçları

**Tablo 4.4.1. Canonical tekrarlı çalışma zamanı doğrulama sonuçları**  
Kaynak: `tables/table_canonical_runtime_validation_summary.csv`

Tablo 4.4.1, tez raporlamasında kullanılmak üzere seçilen canonical çalışma zamanı doğrulama koşularını özetlemektedir. Bu kapsamda `run_03_aligned_clean` ve `run_05_port_aware_repeat_validation` koşuları canonical doğrulama koşuları olarak değerlendirilmiştir.

Her iki canonical koşuda da runtime pipeline dokuz adet Final Top-20 model tahmin kaydı üretmiştir. Denetleyici tarafında ise her koşuda üç binden fazla politika kararı kaydedilmiştir. Bu durum, Ryu tabanlı SDN denetleyicisinin deney süresince akış istatistiklerini sürekli izlediğini ve hibrit IDS/IPS politika mantığını aktif şekilde uyguladığını göstermektedir.

En önemli bulgu, her iki canonical koşuda da runtime model çıktısı ile denetleyici taraflı davranış arasında beş adet security-compatible flow-level eşleşme elde edilmiş olmasıdır. Ayrıca her iki koşuda da drop mitigation ve quarantine ile ilişkili kayıtlar gözlenmiştir. `run_05_port_aware_repeat_validation` koşusunda buna ek olarak rate-limit aksiyonu da gözlenmiştir. Bu nedenle `run_05`, tezde ana deney olarak sunulabilecek en güçlü çalışma zamanı doğrulama koşusudur.

## 5. Denetleyici Taraflı Politika Aksiyon Dağılımı


> **[TABLO EKLEME NOKTASI — Tablo 4.4.2]**  
> Dosya: `experiments/results/thesis_artifacts/run_05_port_aware_runtime_validation/tables/table_controller_action_distribution.csv`  
> Başlık: Denetleyici taraflı IDS/IPS politika aksiyon dağılımı

**Tablo 4.4.2. Denetleyici taraflı IDS/IPS politika aksiyon dağılımı**  
Kaynak: `tables/table_controller_action_distribution.csv`


> **[ŞEKİL EKLEME NOKTASI — Şekil 4.4.1]**  
> Dosya: `experiments/results/thesis_artifacts/run_05_port_aware_runtime_validation/figures/fig_controller_action_distribution.png`  
> Başlık: Denetleyici taraflı politika aksiyon dağılımı

**Şekil 4.4.1. Denetleyici taraflı politika aksiyon dağılımı**  
Kaynak: `figures/fig_controller_action_distribution.png`

Denetleyici taraflı aksiyon dağılımı incelendiğinde, politika kararlarının büyük kısmının `allow` olduğu görülmektedir. Bu beklenen bir sonuçtur; çünkü deney ortamında çok sayıda zararsız trafik, TCP kontrol akışı ve düşük oranlı ya da sıfır oranlı akış durumu bulunmaktadır.

Bununla birlikte, sistemin yalnızca izin verme davranışı göstermediği de açıktır. `run_05_port_aware_repeat_validation` koşusunda denetleyici aşağıdaki kararları üretmiştir:

- 3179 adet `allow`
- 22 adet `quarantine_candidate`
- 1 adet `drop`
- 1 adet `rate_limit`

Bu dağılım, denetleyicinin pasif bir gözlemci olarak çalışmadığını, zararlı UDP davranışı ortaya çıktığında önleme yönelimli kararlar üretebildiğini göstermektedir.

## 6. Final XGBoost Top-20 Modelinin Runtime Tahmin Dağılımı


> **[TABLO EKLEME NOKTASI — Tablo 4.4.3]**  
> Dosya: `experiments/results/thesis_artifacts/run_05_port_aware_runtime_validation/tables/table_final_top20_prediction_distribution.csv`  
> Başlık: Final XGBoost Top-20 modelinin runtime tahmin dağılımı

**Tablo 4.4.3. Final XGBoost Top-20 modelinin runtime tahmin dağılımı**  
Kaynak: `tables/table_final_top20_prediction_distribution.csv`


> **[ŞEKİL EKLEME NOKTASI — Şekil 4.4.2]**  
> Dosya: `experiments/results/thesis_artifacts/run_05_port_aware_runtime_validation/figures/fig_final_top20_prediction_distribution.png`  
> Başlık: Runtime BENIGN/ATTACK tahmin dağılımı

**Şekil 4.4.2. Runtime BENIGN/ATTACK tahmin dağılımı**  
Kaynak: `figures/fig_final_top20_prediction_distribution.png`

Runtime tahmin dağılımı, Final XGBoost Top-20 modelinin altı akışı `BENIGN`, üç akışı ise `ATTACK` olarak sınıflandırdığını göstermektedir.

Bu dağılım karma trafik senaryosu ile uyumludur. Zararsız sınıf TCP kontrol benzeri akışları ve zararsız UDP trafiğini içerirken, saldırı sınıfı `10.10.60.12` adresli saldırgan hosttan gelen zararlı UDP davranışını temsil etmektedir. Aynı PCAP yakalaması içinden hem benign hem de attack sınıflarının üretilmesi, seçilmiş özellik tabanlı modelin canlı trafik verisinden çıkarılan akış kayıtlarına uygulanabilir olduğunu göstermektedir.

Bu sonuç, modelin yalnızca statik CSV veri kümeleri üzerinde değil, canlı SDN deney ortamından elde edilen PCAP tabanlı özellikler üzerinde de çalışabildiğini ortaya koymaktadır.

## 7. Protocol-Aware Final Policy Yorumu


> **[TABLO EKLEME NOKTASI — Tablo 4.4]**  
> Dosya: `experiments/results/thesis_artifacts/run_05_port_aware_runtime_validation/tables/table_protocol_aware_final_policy_distribution.csv`  
> Başlık: Protocol-aware final policy dağılımı

**Tablo 4.4.4. Protocol-aware final policy dağılımı**  
Kaynak: `tables/table_protocol_aware_final_policy_distribution.csv`


> **[ŞEKİL EKLEME NOKTASI — Şekil 4.4.3]**  
> Dosya: `experiments/results/thesis_artifacts/run_05_port_aware_runtime_validation/figures/fig_protocol_aware_final_policy_distribution.png`  
> Başlık: Protocol-aware final policy aksiyon dağılımı

**Şekil 4.4.3. Protocol-aware final policy aksiyon dağılımı**  
Kaynak: `figures/fig_protocol_aware_final_policy_distribution.png`

Runtime model çıktısı temel olarak ikili bir sınıflandırma sunmaktadır: normal ya da saldırı. Ancak SDN denetleyicisi tarafında bu çıktıların doğrudan kullanılması her zaman yeterli değildir. Özellikle TCP kontrol benzeri akışların, trafik bağlamı nedeniyle yüksek saldırı olasılığı alması mümkündür. Buna rağmen bu akışların yüksek hacimli UDP flood akışlarıyla aynı şekilde ele alınması doğru olmayacaktır.

Bu nedenle protocol-aware final policy katmanı geliştirilmiştir. Bu katman model çıktısını taşıma protokolü ve akış bağlamı ile birlikte yorumlamaktadır. `run_05` koşusunda aşağıdaki final policy sınıfları üretilmiştir:

- 6 adet `ALLOW_CONTROL_FLOW`
- 1 adet `ALLOW`
- 1 adet `DROP`
- 1 adet `QUARANTINE_OBSERVED`

Bu ayrım, TCP kontrol benzeri akışların yanlışlıkla UDP flood saldırısı gibi değerlendirilmesini engellemekte ve quarantine hostuna yönelen trafiğin normal hedefe yönelen saldırı trafiğinden ayrı yorumlanmasını sağlamaktadır.

## 8. SDN Denetleyicisi Önleme Aksiyonları


> **[TABLO EKLEME NOKTASI — Tablo 4.5]**  
> Dosya: `experiments/results/thesis_artifacts/run_05_port_aware_runtime_validation/tables/table_enforcement_action_summary.csv`  
> Başlık: SDN denetleyicisi önleme aksiyon özeti

**Tablo 4.4.5. SDN denetleyicisi önleme aksiyon özeti**  
Kaynak: `tables/table_enforcement_action_summary.csv`


> **[ŞEKİL EKLEME NOKTASI — Şekil 4.4]**  
> Dosya: `experiments/results/thesis_artifacts/run_05_port_aware_runtime_validation/figures/fig_enforcement_action_summary.png`  
> Başlık: SDN denetleyicisi önleme aksiyon özeti

**Şekil 4.4.4. SDN denetleyicisi önleme aksiyon özeti**  
Kaynak: `figures/fig_enforcement_action_summary.png`

Önleme aksiyonları özeti, denetleyicinin tespit kararlarını veri düzleminde uygulanabilir aksiyonlara dönüştürdüğünü göstermektedir. Canonical port-aware koşuda aşağıdaki önleme kayıtları gözlenmiştir:

- 7 adet drop mitigation kaydı
- 7 adet quarantine-related kayıt
- 1 adet rate-limit kaydı

Drop kayıtları, tespit edilen zararlı UDP akışı için OpenFlow drop kurallarının kurulduğunu göstermektedir. Quarantine kayıtları, tekrarlanan yüksek güvenli saldırı davranışının quarantine forwarding ile sonuçlandığını göstermektedir. Rate-limit kaydı ise denetleyicinin yalnızca sert önleme aksiyonları değil, daha yumuşak bir sınırlama aksiyonu da uygulayabildiğini göstermektedir.

Bu bulgu, önerilen sistemin yalnızca saldırı tespiti yapan pasif bir IDS değil, aynı zamanda çalışma zamanında önleme aksiyonları üretebilen bir SDN tabanlı IDS/IPS prototipi olduğunu desteklemektedir.

## 9. Flow-Level Model ve Denetleyici Karşılaştırması


> **[TABLO EKLEME NOKTASI — Tablo 4.6]**  
> Dosya: `experiments/results/thesis_artifacts/run_05_port_aware_runtime_validation/tables/table_flow_level_model_controller_comparison.csv`  
> Başlık: Flow-level model-controller karşılaştırması

**Tablo 4.4.6. Flow-level model-controller karşılaştırması**  
Kaynak: `tables/table_flow_level_model_controller_comparison.csv`

Flow-level karşılaştırma bu doğrulama aşamasının en kritik çıktılarından biridir. Bu tablo, runtime model çıktıları ile denetleyici taraflı politika kayıtlarını kaynak IP, hedef IP, kaynak port, hedef port ve taşıma protokolü düzeyinde karşılaştırmaktadır.

Deneydeki temel zararlı akış, `10.10.60.12` adresinden `10.10.40.14` adresine giden UDP akışıdır. Bu akış runtime model tarafından `ATTACK` olarak sınıflandırılmış ve protocol-aware final policy çıktısında `DROP` olarak yorumlanmıştır. Denetleyici tarafında ise aynı akış `quarantine_candidate` aksiyonu ile ilişkilendirilmiştir. Ayrıca aynı akış için drop, quarantine ve rate-limit kayıtlarının da eşleştiği görülmektedir.

Bu durum exact action matching yerine security-compatible matching yaklaşımının neden daha anlamlı olduğunu göstermektedir. Çünkü binary model çıktısı `DROP` önerirken, denetleyici tekrarlanan yüksek güvenli saldırı davranışı nedeniyle aksiyonu quarantine seviyesine yükseltebilir. Dolayısıyla controller aksiyonunun model aksiyonu ile birebir aynı olması beklenmemelidir; önemli olan güvenlik açısından uyumlu bir önleme davranışının ortaya çıkmasıdır.

Quarantine hostu olan `10.10.99.16` adresine yönelen akış ise post-mitigation observation olarak yorumlanmıştır. Bu akış normal bir kaynak-hedef saldırı akışı gibi değerlendirilmemeli, denetleyici tarafından uygulanan quarantine mekanizmasının sonucu olarak ele alınmalıdır.

## 10. Saldırı Olasılığı ve Final Policy Eşlemesi


> **[TABLO EKLEME NOKTASI — Tablo 4.7]**  
> Dosya: `experiments/results/thesis_artifacts/run_05_port_aware_runtime_validation/tables/table_protocol_aware_attack_probability_summary.csv`  
> Başlık: Flow-level saldırı olasılığı ve protocol-aware final action özeti

**Tablo 4.4.7. Flow-level saldırı olasılığı ve protocol-aware final action özeti**  
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

İkinci olarak, PCAP tabanlı runtime model çıktıları ile denetleyici logları arasındaki flow-level eşleştirme zamanlama, flow-stat polling aralığı ve port bilgilerinin denetleyici loglarında bulunmasına bağlıdır. Önceki diagnostic koşul olan `run_04_repeat_mixed_validation`, port bilgisinin yer almadığı durumlarda exact matching’in zayıfladığını göstermiştir.

Üçüncü olarak, exact action matching tek başına yeterli bir ölçüt değildir. Çünkü makine öğrenmesi modeli binary bir çıktı üretirken, SDN denetleyicisi rate-limit, drop ve quarantine gibi daha zengin bir aksiyon uzayına sahiptir. Bu nedenle security-compatible matching daha anlamlı bir değerlendirme yaklaşımıdır.

Son olarak, mevcut model seçilmiş Top-20 özellik alt kümesiyle eğitilmiştir. Bu yaklaşım çalışma zamanı uygulanabilirliği açısından avantaj sağlasa da daha büyük ve temsili CIC-DDoS2019 alt kümeleri üzerinde yeniden eğitim yapılması modelin genellenebilirliğini artırabilir.

## 14. Sonuç

Canonical port-aware runtime validation deneyi, önerilen SDN tabanlı hibrit IDS/IPS prototipinin canlı bir SDN test ortamında çalışabildiğini göstermektedir. Sistem zararsız ve kontrol trafiğini korumuş, zararlı UDP davranışını yüksek saldırı olasılığı ile tespit etmiş ve denetleyici tarafında rate-limit, drop ve quarantine aksiyonları üretmiştir.

Bu sonuçlar, çalışmanın temel iddiasını desteklemektedir: makine öğrenmesi tabanlı DDoS tespiti, SDN denetleyicisiyle bütünleştirilerek kampüs benzeri yazılım tanımlı ağ ortamlarında çalışma zamanı saldırı tespit ve önleme mekanizmasına dönüştürülebilir.

---

## Bölüm 4 Genel Kapanış Değerlendirmesi

Bu bölümde geliştirilen SDN tabanlı makine öğrenmesi destekli IDS/IPS prototipinin hem yöntemsel tasarımı hem de çalışma zamanı doğrulama sonuçları sunulmuştur. İlk olarak sistem mimarisi, deney ortamı, Ryu tabanlı denetleyici, FastAPI üzerinden çalışan Final XGBoost Top-20 modeli, runtime feature extraction pipeline ve protocol-aware final policy katmanı açıklanmıştır. Ardından bu bileşenlerin karma normal ve zararlı trafik senaryosu altında nasıl çalıştığı deneysel olarak incelenmiştir.

Elde edilen bulgular, önerilen sistemin benign ve kontrol trafiğini koruyabildiğini, zararlı UDP davranışını yüksek saldırı olasılığı ile tespit edebildiğini ve bu tespiti SDN denetleyicisi üzerinde rate-limit, drop ve quarantine gibi önleme aksiyonlarına dönüştürebildiğini göstermektedir. Özellikle port-aware ve protocol-aware karşılaştırma yaklaşımı, model çıktısı ile denetleyici davranışının daha doğru ilişkilendirilmesini sağlamıştır.

Bu bölümdeki sonuçlar, çalışmanın ana iddiasını desteklemektedir: makine öğrenmesi tabanlı DDoS tespiti, SDN kontrol düzlemiyle bütünleştirildiğinde yalnızca pasif bir sınıflandırma çıktısı üretmekle kalmaz; aynı zamanda ağ davranışına müdahale edebilen aktif bir güvenlik mekanizmasına dönüşebilir. Bununla birlikte deneylerin kontrollü Mininet ortamında yürütülmüş olması, daha çeşitli trafik profilleri ve daha uzun süreli testler ile desteklenmesi gereken bir sınırlılık olarak değerlendirilmelidir.

Sonraki bölümde, bu deneysel bulgular daha geniş bir akademik bağlamda tartışılacak; önerilen mimarinin güçlü yönleri, sınırlılıkları, literatürdeki benzer yaklaşımlardan farkları ve gelecekte yapılabilecek geliştirmeler değerlendirilecektir.

## Deneysel Koşuların Canonical ve Diagnostic Olarak Ayrılması

Bu çalışmada `run_05_port_aware_repeat_validation` koşulunun ana deney olarak seçilmesinin nedeni, model çıktıları ile SDN denetleyicisi kararlarının port-aware ve protocol-aware biçimde karşılaştırılmasına olanak sağlamasıdır. `run_03_aligned_clean` ilk başarılı hizalanmış çalışma zamanı doğrulaması olarak destekleyici canonical koşu olarak korunmuştur. `run_04_repeat_mixed_validation` ise sistem geliştirme sürecinde önemli bir diagnostic tekrar olarak değerlendirilmiş, ancak controller loglarında port bilgisinin bulunmaması nedeniyle ana sonuçların hesaplanmasında kullanılmamıştır. Bu ayrım, deneysel sonuçların yalnızca olumlu çıktılar üzerinden değil, gözlemlenebilirlik ve eşleştirme kalitesi açısından da şeffaf biçimde değerlendirilmesini sağlamaktadır.
