# Bölüm 3. Literatür Taraması ve İlgili Çalışmalar

## 3.1. Bölüme Genel Bakış

Bu bölümde, yazılım tanımlı ağlarda DDoS saldırılarının tespiti ve önlenmesine yönelik literatürde yer alan çalışmalar incelenmektedir. Literatür taraması, bu tez çalışmasının hangi akademik boşluğa odaklandığını göstermek ve önerilen yaklaşımı mevcut çalışmalarla karşılaştırmak amacıyla hazırlanmıştır.

Bu bölümde çalışmalar altı ana eksen üzerinden ele alınmaktadır:

- SDN tabanlı DDoS tespit çalışmaları
- Makine öğrenmesi tabanlı IDS/IPS yaklaşımları
- Derin öğrenme tabanlı yaklaşımlar
- Özellik seçimi ve hafif model tasarımları
- SDN denetleyicisiyle bütünleşik önleme mekanizmaları
- Runtime validation, Mininet/Ryu/OpenFlow tabanlı deneysel çalışmalar

Bu sınıflandırma, tezde geliştirilen sistemin yalnızca çevrimdışı bir sınıflandırma modeli olmadığını, aynı zamanda SDN denetleyicisiyle bütünleşen çalışma zamanı IDS/IPS prototipi olduğunu göstermek için kullanılmaktadır.

## 3.2. Literatür Tarama Stratejisi

Literatür taraması yapılırken aşağıdaki veri tabanları ve kaynaklar kullanılabilir:

- Web of Science
- Scopus
- IEEE Xplore
- ACM Digital Library
- SpringerLink
- ScienceDirect
- MDPI
- Nature Scientific Reports
- arXiv
- Google Scholar

Arama sürecinde aşağıdaki anahtar kelime grupları kullanılmalıdır:

| Arama Grubu | Örnek Anahtar Kelimeler |
|---|---|
| SDN ve DDoS | software-defined networking, SDN, DDoS detection, DDoS mitigation |
| Makine öğrenmesi | machine learning, ensemble learning, XGBoost, Random Forest, LightGBM |
| Derin öğrenme | deep learning, LSTM, CNN, DNN, autoencoder |
| SDN denetleyicisi | Ryu controller, OpenFlow, Mininet, Open vSwitch |
| Önleme aksiyonları | mitigation, rate limiting, drop rule, quarantine, flow rule installation |
| Veri kümeleri | CIC-DDoS2019, InSDN, CICIDS, SDN dataset |
| Çalışma zamanı doğrulama | runtime validation, real-time detection, online inference, controller overhead |

Örnek arama sorguları:

- “SDN DDoS detection machine learning”
- “software defined networking DDoS mitigation OpenFlow”
- “Ryu controller DDoS detection machine learning”
- “Mininet SDN DDoS attack detection XGBoost”
- “CIC-DDoS2019 SDN DDoS detection”
- “real-time DDoS detection SDN controller machine learning”
- “SDN IDS IPS rate limit drop quarantine”

## 3.3. Dahil Etme ve Hariç Tutma Ölçütleri

Literatür taramasında çalışmaların seçimi için dahil etme ve hariç tutma ölçütleri belirlenmelidir.

### Dahil Etme Ölçütleri

- SDN ortamında DDoS veya DoS saldırı tespiti yapan çalışmalar.
- Makine öğrenmesi veya derin öğrenme tabanlı saldırı tespiti içeren çalışmalar.
- Mininet, Ryu, OpenFlow veya benzeri SDN deney ortamları kullanan çalışmalar.
- Saldırı tespitine ek olarak önleme veya mitigation mekanizması sunan çalışmalar.
- Veri kümesi, özellik çıkarımı ve model değerlendirme metriklerini açıkça raporlayan çalışmalar.
- 2020 ve sonrası yayımlanan güncel çalışmalar.
- Sistematik derleme, survey veya kapsamlı karşılaştırma sunan çalışmalar.

### Hariç Tutma Ölçütleri

- SDN bağlamı içermeyen genel DDoS tespit çalışmaları.
- Yalnızca teorik öneri sunup deneysel doğrulama yapmayan çalışmalar.
- Veri kümesi, model veya metrik bilgisi yeterince açık olmayan çalışmalar.
- Sadece imza tabanlı klasik IDS yaklaşımı kullanan ve ML/DL içermeyen çalışmalar.
- Gerçek zamanlı veya çalışma zamanı kullanım bağlamı hiç tartışılmayan çalışmalar.

## 3.4. Literatür Sınıflandırma Matrisi

Aşağıdaki tablo, incelenen çalışmaların sistematik olarak karşılaştırılması için kullanılacaktır. Bu tablo, Web of Science, Scopus veya Google Scholar üzerinden seçilecek makalelerle doldurulmalıdır.

| No | Yazar/Yıl | Amaç | SDN Ortamı | Veri Kümesi | Yöntem/Model | Özellik Seçimi | Önleme Aksiyonu | Runtime Test | Güçlü Yön | Sınırlılık |
|---:|---|---|---|---|---|---|---|---|---|---|
| 1 | Kaynak-1 | SDN’de DDoS tespiti | Mininet/OpenFlow | Belirtilecek | ML/DL | Var/Yok | Var/Yok | Var/Yok | Belirtilecek | Belirtilecek |
| 2 | Kaynak-2 | SDN’de mitigation | Ryu/Mininet | Belirtilecek | Belirtilecek | Var/Yok | Drop/Rate-limit | Var/Yok | Belirtilecek | Belirtilecek |
| 3 | Kaynak-3 | Veri kümesi karşılaştırması | SDN/Genel | CIC-DDoS2019/InSDN | Belirtilecek | Var/Yok | Yok | Yok | Belirtilecek | Belirtilecek |
| 4 | Kaynak-4 | Real-time IDS | SDN controller | Belirtilecek | Belirtilecek | Var/Yok | Var | Var | Belirtilecek | Belirtilecek |
| 5 | Kaynak-5 | DL tabanlı tespit | SDN | Belirtilecek | LSTM/CNN/DNN | Var/Yok | Yok/Var | Var/Yok | Belirtilecek | Belirtilecek |

## 3.5. SDN Tabanlı DDoS Tespit Çalışmaları

SDN tabanlı DDoS tespit çalışmaları, geleneksel ağ güvenliği yaklaşımlarından farklı olarak merkezi denetleyicinin sağladığı ağ görünürlüğünden yararlanır. Bu çalışmalarda genellikle OpenFlow anahtarlarından elde edilen flow statistics verileri, port istatistikleri veya paket düzeyi gözlemler kullanılarak saldırı davranışı tespit edilmeye çalışılır.

Literatürdeki birçok çalışma, SDN denetleyicisinin trafik akışlarını izleyerek DDoS saldırılarını erken aşamada tespit edebileceğini göstermektedir. Bununla birlikte, yalnızca tespit yapmak yeterli değildir. SDN ortamında tespit edilen saldırıların denetleyici tarafından ağ kurallarına dönüştürülmesi ve veri düzleminde uygulanması gerekir.

Bu tez çalışması, bu noktada literatürdeki tespit odaklı çalışmalardan ayrılmaktadır. Önerilen prototip yalnızca saldırı tahmini üretmemekte, aynı zamanda denetleyici tarafında rate-limit, drop ve quarantine aksiyonlarını da üretebilmektedir.

## 3.6. Makine Öğrenmesi Tabanlı Yaklaşımlar

Makine öğrenmesi tabanlı yaklaşımlar, DDoS tespitinde yaygın olarak kullanılan yöntemler arasındadır. Random Forest, Support Vector Machine, Decision Tree, XGBoost, LightGBM ve benzeri algoritmalar ağ trafiğinden çıkarılan sayısal özellikler üzerinden benign ve attack sınıflarını ayırt etmeye çalışır.

Bu çalışmaların güçlü yönü, tabular ağ trafiği verilerinde yüksek sınıflandırma başarısı sağlayabilmeleridir. Özellikle ensemble tabanlı yöntemler, farklı özellik kombinasyonlarını değerlendirerek güçlü karar sınırları oluşturabilir.

Bununla birlikte, bu çalışmaların önemli bir sınırlılığı çoğu zaman çevrimdışı veri kümesi değerlendirmesine odaklanmalarıdır. Modelin gerçek zamanlı SDN denetleyicisiyle nasıl bütünleşeceği, inference gecikmesi, feature extraction maliyeti, controller overhead ve OpenFlow kural üretimi gibi konular her çalışmada ayrıntılı olarak ele alınmamaktadır.

Bu tez çalışmasında Final XGBoost Top-20 modeli kullanılmış ve model çıktısı runtime PCAP feature extraction pipeline üzerinden çalışma zamanı deneyine dahil edilmiştir.

## 3.7. Derin Öğrenme Tabanlı Yaklaşımlar

Derin öğrenme tabanlı yaklaşımlar, DDoS tespitinde özellikle karmaşık trafik örüntülerini öğrenebilme potansiyeli nedeniyle ilgi görmektedir. LSTM, CNN, DNN, autoencoder ve hibrit derin öğrenme modelleri bu alanda sık kullanılan yöntemler arasındadır.

Derin öğrenme modelleri büyük veri kümeleri üzerinde yüksek başarı sağlayabilse de, SDN çalışma zamanı ortamında bazı zorluklar oluşturabilir. Model boyutu, inference gecikmesi, eğitim maliyeti, açıklanabilirlik ve denetleyiciye getireceği ek yük bu zorluklardan bazılarıdır.

Bu tez çalışması, çalışma zamanı uygulanabilirliği nedeniyle daha hafif bir seçilmiş özellik seti ve XGBoost tabanlı model kullanmayı tercih etmiştir. Bu tercih, yüksek doğruluk ile denetleyiciye entegre edilebilirlik arasında pratik bir denge kurmayı amaçlamaktadır.

## 3.8. Özellik Seçimi ve Hafif Model Tasarımları

DDoS tespitinde kullanılan veri kümeleri genellikle çok sayıda trafik özelliği içerir. Ancak bu özelliklerin tamamının çalışma zamanı ortamında çıkarılması yüksek işlem maliyetine neden olabilir. Bu nedenle özellik seçimi, SDN tabanlı runtime IDS/IPS sistemleri için önemli bir araştırma konusudur.

Özellik seçimi sayesinde model daha az sayıda girdiyle çalışabilir, inference süresi azalabilir ve runtime feature extraction süreci daha uygulanabilir hale gelebilir. Bununla birlikte, özellik sayısını azaltmak bazı bilgi kayıplarına yol açabilir. Bu nedenle seçilen özelliklerin saldırı ayrımı açısından yeterli temsil gücüne sahip olması gerekir.

Bu tez çalışmasında Final Top-20 özellik seti kullanılmıştır. Bu yaklaşım, CICFlowMeter uyumlu seçilmiş özelliklerin runtime PCAP verisinden çıkarılmasına ve aktif modele gönderilmesine olanak sağlamıştır.

## 3.9. SDN Denetleyicisiyle Bütünleşik Önleme Çalışmaları

SDN tabanlı güvenlik çalışmalarının önemli bir kısmı saldırı tespitine odaklanırken, bazı çalışmalar tespit edilen saldırılara karşı mitigation mekanizmaları da sunmaktadır. Bu mekanizmalar arasında drop rule installation, rate limiting, blacklisting, rerouting ve quarantine benzeri yaklaşımlar yer alabilir.

Önleme mekanizmasının etkili olabilmesi için tespit kararının doğru akışla eşleştirilmesi gerekir. Kaynak IP, hedef IP, protokol, kaynak port ve hedef port bilgileri bu eşleştirmede kritik öneme sahiptir. Aksi halde benign trafik yanlışlıkla engellenebilir veya saldırı trafiği doğru şekilde hedeflenemeyebilir.

Bu tez çalışması, port-aware ve protocol-aware eşleştirmenin önemini deneysel olarak göstermektedir. Özellikle run_05_port_aware_repeat_validation koşusunda model çıktıları ile controller logları aynı akış bağlamında karşılaştırılmıştır.

## 3.10. Mininet, Ryu ve OpenFlow Tabanlı Deneysel Çalışmalar

Mininet ve Ryu, SDN güvenliği araştırmalarında sık kullanılan deneysel araçlardır. Mininet, kontrollü ve tekrarlanabilir ağ topolojileri oluşturmak için kullanılırken, Ryu denetleyicisi OpenFlow tabanlı güvenlik uygulamaları geliştirmek için uygun bir platform sunar.

Literatürde Mininet/Ryu tabanlı birçok çalışma DDoS saldırılarını simüle etmekte ve saldırı tespit algoritmalarını değerlendirmektedir. Ancak bu çalışmaların bir kısmı yalnızca belirli bir saldırı türüne veya yalnızca tespit performansına odaklanmaktadır.

Bu tez çalışması, Mininet/Ryu ortamında karma benign/malicious trafik üretmiş, PCAP yakalamış, runtime feature extraction gerçekleştirmiş, model inference üretmiş ve controller-side enforcement loglarını karşılaştırmıştır. Bu yönüyle deneysel zincir daha uçtan uca bir doğrulama sunmaktadır.

## 3.11. Literatürdeki Boşluklar

İncelenen çalışmalar genel olarak değerlendirildiğinde aşağıdaki araştırma boşlukları öne çıkmaktadır:

- Birçok çalışma çevrimdışı veri kümesi başarısına odaklanmakta, çalışma zamanı SDN entegrasyonunu sınırlı ele almaktadır.
- Model çıktısının SDN denetleyicisi üzerinde hangi güvenlik aksiyonuna dönüştürüleceği her zaman açık değildir.
- Port-aware ve protocol-aware flow-level eşleştirme çoğu çalışmada yeterince vurgulanmamaktadır.
- Rate-limit, drop ve quarantine aksiyonlarının birlikte ele alındığı uçtan uca prototipler sınırlıdır.
- Controller overhead, inference latency ve flow-stat polling maliyeti genellikle ayrıntılı incelenmemektedir.
- Deneysel artifact üretimi ve yeniden izlenebilirlik her çalışmada yeterince sistematik değildir.

Bu tez çalışması, bu boşlukların bir bölümüne yanıt vermeyi hedeflemektedir.

## 3.12. Bu Tez Çalışmasının Literatürdeki Konumu

Bu tez çalışması, SDN tabanlı DDoS tespiti ve önleme literatüründe makine öğrenmesi modelini çalışma zamanı SDN denetleyicisiyle bütünleştiren bir prototip olarak konumlanmaktadır. Çalışmanın temel farkı, yalnızca model doğruluğunu raporlamak yerine modelin runtime trafik analizinde nasıl kullanılabileceğini ve controller-side enforcement aksiyonlarına nasıl dönüştürülebileceğini göstermesidir.

Önerilen sistemde Final XGBoost Top-20 modeli, FastAPI inference servisi, PCAP tabanlı runtime feature extraction, Ryu tabanlı controller policy engine ve OpenFlow tabanlı enforcement mekanizmaları birlikte çalışmaktadır. Ayrıca port-aware ve protocol-aware final policy yaklaşımıyla model-controller karşılaştırması daha güvenilir hale getirilmiştir.

Bu yönüyle çalışma, offline classification odaklı literatür ile aktif SDN tabanlı IPS prototipleri arasında bir köprü kurmaktadır.

## 3.13. Bölüm Özeti

Bu bölümde SDN tabanlı DDoS tespiti ve önleme literatürü sınıflandırılmış, makine öğrenmesi ve derin öğrenme tabanlı yaklaşımlar değerlendirilmiş, özellik seçimi, Mininet/Ryu tabanlı deneyler ve controller-side mitigation çalışmaları tartışılmıştır.

Literatür değerlendirmesi, bu tez çalışmasının ana katkısının çalışma zamanı SDN IDS/IPS entegrasyonu olduğunu göstermektedir. Bir sonraki bölümde, bu katkıyı gerçekleştirmek için geliştirilen yöntem, deneysel prototip, runtime validation pipeline ve elde edilen sonuçlar ayrıntılı olarak sunulacaktır.
