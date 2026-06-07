# Bölüm 6. Sonuç ve Öneriler

## 6.1. Bölüme Genel Bakış

Bu bölümde, tez çalışmasının genel sonuçları, elde edilen temel bulgular, çalışmanın akademik ve pratik katkıları, sınırlılıkları ve gelecekte yapılabilecek geliştirmeler özetlenmektedir. Önceki bölümlerde yazılım tanımlı ağlar, DDoS saldırıları, makine öğrenmesi tabanlı saldırı tespiti, SDN tabanlı önleme mekanizmaları ve geliştirilen runtime IDS/IPS prototipi ayrıntılı olarak ele alınmıştır.

Bu tez çalışmasının temel amacı, makine öğrenmesi tabanlı DDoS tespit modelinin SDN denetleyicisiyle bütünleştirilerek çalışma zamanında aktif önleme aksiyonları üretebilen bir IDS/IPS prototipine dönüştürülüp dönüştürülemeyeceğini araştırmaktır. Bu amaç doğrultusunda Mininet, Open vSwitch, Ryu denetleyicisi, FastAPI tabanlı model servisi ve PCAP tabanlı runtime feature extraction pipeline bileşenlerinden oluşan deneysel bir sistem geliştirilmiştir.

## 6.2. Çalışmanın Genel Özeti

Tez kapsamında öncelikle SDN tabanlı kampüs ağı benzeri bir deney ortamı oluşturulmuştur. Bu ortamda Open vSwitch anahtarları veri düzlemini, Ryu denetleyicisi ise kontrol düzlemini temsil etmiştir. Deney ortamı, benign TCP/UDP trafik ile malicious UDP trafik senaryolarının birlikte çalıştırılabileceği şekilde yapılandırılmıştır.

Makine öğrenmesi tarafında, CIC-DDoS2019 veri kümesi ailesiyle uyumlu seçilmiş özellikler üzerinden çalışan Final XGBoost Top-20 modeli kullanılmıştır. Model, FastAPI tabanlı servis aracılığıyla çalışma zamanı pipeline’ına entegre edilmiştir. PCAP dosyalarından seçilmiş Top-20 özellikler çıkarılmış, aktif modelin beklediği feature order ile şema uyumluluğu kontrol edilmiş ve runtime tahminler üretilmiştir.

Denetleyici tarafında ise flow statistics verileri, model çıktıları ve yerel sezgisel kurallar hibrit politika mantığıyla değerlendirilmiştir. Bu değerlendirme sonucunda allow, monitor, rate-limit, drop ve quarantine_candidate gibi politika kararları üretilmiştir. Zararlı UDP akışları için OpenFlow tabanlı drop, rate-limit ve quarantine mekanizmaları uygulanmıştır.

## 6.3. Elde Edilen Temel Bulgular

Çalışmanın en önemli bulgusu, makine öğrenmesi tabanlı DDoS tespit modelinin SDN denetleyicisiyle bütünleştirilerek çalışma zamanı ortamında aktif güvenlik kararlarına dönüştürülebilmesidir. Bu bulgu, modelin yalnızca çevrimdışı sınıflandırma başarısı açısından değil, gerçekçi bir SDN kontrol zinciri içinde kullanılabilirliği açısından da anlamlı olduğunu göstermektedir.

Canonical runtime validation deneylerinde benign/control akışların korunabildiği, malicious UDP akışların yüksek saldırı olasılığı ile tespit edilebildiği ve bu tespitlerin controller-side enforcement aksiyonlarına dönüştürülebildiği gözlenmiştir. Özellikle run_05_port_aware_repeat_validation koşusu, port-aware ve protocol-aware doğrulama açısından en güçlü deney koşusu olarak değerlendirilmiştir.

Bu koşuda controller policy distribution, final model prediction distribution, protocol-aware final policy distribution, enforcement action summary ve flow-level model-controller comparison çıktıları üretilmiştir. Deney sonucunda rate-limit, drop ve quarantine aksiyonlarının gözlenmesi, önerilen sistemin yalnızca pasif bir IDS değil, aktif bir IPS prototipi olarak da çalışabildiğini göstermektedir.

## 6.4. Araştırma Sorularına Yanıtlar

Bu tez çalışmasının başlangıcında üç temel araştırma sorusu belirlenmiştir.

Birinci araştırma sorusu, SDN denetleyicisinin çalışma zamanı akış istatistikleri ve PCAP tabanlı özellik çıkarımı ile makine öğrenmesi modelini birlikte kullanıp kullanamayacağıdır. Geliştirilen prototip, bu soruya olumlu yanıt vermektedir. Ryu denetleyicisi flow statistics verilerini toplamış, PCAP tabanlı pipeline seçilmiş özellikleri çıkarmış ve FastAPI üzerinden çalışan model inference servisiyle birlikte çalışmıştır.

İkinci araştırma sorusu, eğitilmiş makine öğrenmesi modelinin karma benign/malicious trafik senaryosunda zararlı UDP davranışını ayırt edip edemeyeceğidir. Runtime prediction sonuçları, benign akışların BENIGN, zararlı UDP akışların ise ATTACK olarak sınıflandırılabildiğini göstermiştir. Bu sonuç, modelin runtime veriyle de anlamlı tahminler üretebildiğini göstermektedir.

Üçüncü araştırma sorusu, model çıktısının SDN denetleyicisi üzerinde rate-limit, drop ve quarantine gibi aktif önleme aksiyonlarına dönüştürülüp dönüştürülemeyeceğidir. Run_05 deneyinde bu üç aksiyonun da gözlenmesi, model çıktısı ve controller-side policy engine birlikteliğinin aktif IPS davranışı üretebildiğini göstermektedir.

## 6.5. Çalışmanın Akademik Katkıları

Bu tez çalışmasının akademik katkıları birkaç başlık altında özetlenebilir.

İlk katkı, DDoS tespitini yalnızca çevrimdışı sınıflandırma problemi olarak ele almaması, bunu SDN çalışma zamanı ortamına taşımasıdır. Bu yönüyle çalışma, offline ML modeli ile online SDN enforcement davranışı arasında bir köprü kurmaktadır.

İkinci katkı, port-aware ve protocol-aware değerlendirme yaklaşımının deneysel sürece dahil edilmesidir. Aynı kaynak ve hedef IP çifti arasında benign TCP, benign UDP, malicious UDP ve quarantine-observed akışların bulunabileceği gösterilmiş; bu nedenle doğru değerlendirme için port ve protokol bilgisinin zorunlu olduğu ortaya konmuştur.

Üçüncü katkı, rate-limit, drop ve quarantine aksiyonlarının aynı prototip içinde birlikte ele alınmasıdır. Bu yaklaşım, saldırıya karşı tek seviyeli bir müdahale yerine kademeli ve bağlama duyarlı bir savunma mantığı sunmaktadır.

Dördüncü katkı, deneysel artifact üretiminin sistematik hale getirilmesidir. Policy decision logları, prediction dosyaları, flow statistics, mitigation logları, quarantine logları, rate-limit logları, protocol-aware comparison raporları, canonical aggregate raporları, tablo ve şekil çıktıları tez yazımına doğrudan aktarılabilecek şekilde paketlenmiştir.

## 6.6. Pratik Katkılar

Çalışmanın pratik katkısı, SDN tabanlı bir ağda makine öğrenmesi destekli saldırı tespit ve önleme mekanizmasının nasıl prototipleneceğini göstermesidir. Mininet, Open vSwitch, Ryu ve FastAPI gibi açık kaynaklı araçlarla uçtan uca çalışan bir güvenlik zinciri kurulmuştur.

Bu yapı, kampüs ağları gibi çok kullanıcılı ortamlarda uygulanabilecek dinamik güvenlik politikalarının tasarımı için bir referans mimari sağlayabilir. Gerçek üretim ortamına geçmeden önce saldırı senaryolarının kontrollü biçimde denenmesi, politika eşiklerinin ayarlanması ve model-controller bütünleşmesinin doğrulanması açısından bu prototip yararlı bir başlangıç noktasıdır.

Ayrıca çalışma, deneysel süreçte karşılaşılabilecek pratik sorunları da ortaya koymuştur. PCAP boyutu, tcpdump filtreleme, port bilgisinin controller loglarına eklenmesi, FastAPI servisinin erişilebilirliği, feature schema uyumluluğu ve flow-level comparison gibi konular, runtime IDS/IPS geliştirme sürecinde dikkat edilmesi gereken pratik başlıklardır.

## 6.7. Sınırlılıkların Özeti

Çalışmanın bazı sınırlılıkları bulunmaktadır. İlk sınırlılık, deneylerin Mininet tabanlı kontrollü bir ortamda gerçekleştirilmiş olmasıdır. Mininet tekrarlanabilirlik açısından güçlü bir araçtır; ancak gerçek kampüs ağlarındaki fiziksel cihaz performansı, kullanıcı davranış çeşitliliği ve uzun süreli trafik dinamikleri bu ortamda tam olarak temsil edilemez.

İkinci sınırlılık, kullanılan modelin seçilmiş Top-20 özellik setiyle çalışmasıdır. Bu yaklaşım runtime uygulanabilirlik açısından avantaj sağlasa da daha geniş veri kümeleri ve daha farklı saldırı türleriyle yeniden değerlendirilmelidir.

Üçüncü sınırlılık, deney tekrar sayısının henüz sınırlı olmasıdır. Canonical run_03 ve run_05 sonuçları güçlü bir doğrulama sunmakla birlikte, daha yüksek istatistiksel güven için farklı trafik oranları, farklı saldırı tipleri ve daha fazla tekrar gereklidir.

Dördüncü sınırlılık, controller overhead ve ölçeklenebilirlik analizlerinin henüz tam kapsamlı yapılmamış olmasıdır. Denetleyici CPU/RAM kullanımı, flow-stat polling yükü, inference latency, API round-trip süresi ve OpenFlow kural sayısı ileride daha ayrıntılı ölçülmelidir.

## 6.8. Gelecek Çalışmalar İçin Öneriler

Gelecek çalışmalarda ilk olarak daha geniş ve temsil edici veri kümeleriyle model yeniden eğitilmelidir. CIC-DDoS2019 veri kümesinin daha büyük alt kümeleri, InSDN gibi SDN odaklı veri kümeleri veya gerçek kampüs ağı trafiğinden anonimleştirilmiş veriler kullanılabilir.

İkinci olarak, saldırı senaryoları çeşitlendirilmelidir. UDP flood dışındaki TCP SYN flood, HTTP flood, DNS amplification, düşük yoğunluklu stealth DDoS ve çok kaynaklı botnet benzeri trafik senaryoları test ortamına eklenebilir.

Üçüncü olarak, controller overhead ayrıntılı biçimde analiz edilmelidir. Bu analizde flow statistics toplama sıklığı, model inference gecikmesi, API round-trip süresi, OpenFlow kural kurulum gecikmesi ve denetleyici üzerindeki işlem yükü birlikte değerlendirilmelidir.

Dördüncü olarak, hibrit politika motoru daha uyarlanabilir hale getirilebilir. Sabit eşik değerleri yerine reinforcement learning veya adaptive thresholding yaklaşımları kullanılarak rate-limit, drop ve quarantine kararlarının ağ durumuna göre dinamik ayarlanması sağlanabilir.

Beşinci olarak, sistem daha büyük topolojilerde ve daha uzun süreli deneylerle test edilmelidir. Çok katmanlı kampüs topolojileri, daha fazla host, daha fazla servis ve eş zamanlı birden fazla saldırgan senaryosu sisteme eklenmelidir.

Altıncı olarak, gerçek fiziksel testbed veya yarı-gerçekçi sanallaştırılmış kampüs ağı ortamında doğrulama yapılmalıdır. Bu sayede Mininet ortamında elde edilen sonuçların gerçek ağlara aktarılabilirliği daha güvenilir biçimde değerlendirilebilir.

## 6.9. Sonuç

Bu tez çalışması, SDN tabanlı kampüs ağı benzeri bir ortamda makine öğrenmesi destekli DDoS tespiti ve aktif önleme mekanizmalarının birlikte çalışabileceğini göstermiştir. Geliştirilen prototip, Final XGBoost Top-20 modeli, runtime PCAP feature extraction, FastAPI inference servisi, Ryu denetleyicisi ve OpenFlow tabanlı enforcement mekanizmalarını aynı deneysel zincir içinde birleştirmiştir.

Canonical deneyler sonucunda benign trafiğin korunduğu, malicious UDP trafiğin tespit edildiği ve rate-limit, drop ve quarantine aksiyonlarının uygulanabildiği görülmüştür. Bu sonuç, önerilen yaklaşımın yalnızca çevrimdışı bir saldırı tespit modeli değil, çalışma zamanı SDN tabanlı aktif IDS/IPS prototipi olarak değerlendirilebileceğini göstermektedir.

Sonuç olarak bu çalışma, SDN tabanlı ağ güvenliği alanında makine öğrenmesi destekli tespit ile programlanabilir ağ önleme mekanizmaları arasında uygulanabilir bir bütünleşme yaklaşımı sunmaktadır. Daha geniş veri kümeleri, daha fazla deney tekrarı, controller overhead analizi ve gerçek testbed çalışmalarıyla bu yaklaşımın daha da güçlendirilmesi mümkündür.

## Tezin Akademik Katkısının Sonuç Açısından Değerlendirilmesi

Bu tez çalışması, yazılım tanımlı kampüs ağlarında DDoS saldırılarının makine öğrenmesi destekli olarak tespit edilmesi ve tespit sonucunun SDN denetleyicisi üzerinden aktif önleme aksiyonlarına dönüştürülmesi problemini ele almıştır. Elde edilen sonuçlar, önerilen mimarinin yalnızca çevrimdışı sınıflandırma başarımı üretmediğini; aynı zamanda çalışma zamanı trafik gözlemi, model tahmini, politika kararı ve OpenFlow tabanlı enforcement adımlarını birlikte çalıştırabildiğini göstermektedir.

Çalışmanın akademik katkısı dört noktada özetlenebilir. Birincisi, makine öğrenmesi modelinin SDN çalışma zamanı ortamına entegre edilmesi ve model çıktısının denetleyici tarafındaki karar mekanizmasına bağlanmasıdır. İkincisi, port-aware ve protocol-aware doğrulama yaklaşımıyla model çıktıları ile controller-side policy kararları arasında daha izlenebilir bir eşleştirme kurulmasıdır. Üçüncüsü, IDS işlevinin drop, rate-limit ve quarantine_candidate gibi IPS aksiyonlarıyla aynı prototip içinde değerlendirilmesidir. Dördüncüsü ise deneysel çıktıların tablo, şekil, kalite kontrol raporu ve artifact dosyalarıyla yeniden üretilebilir bir tez raporlama zincirine dönüştürülmesidir.

Bu yönleriyle çalışma, literatürde sık görülen yalnızca offline metrik raporlamasına dayalı DDoS tespit çalışmalarından ayrılmaktadır. Bulgular, yüksek sınıflandırma başarımının tek başına yeterli olmadığını; modelin SDN denetleyicisiyle nasıl bütünleştirildiğinin, hangi akışla eşleştiğinin ve hangi önleme aksiyonuna dönüştüğünün de deneysel olarak belgelenmesi gerektiğini göstermektedir. Bu nedenle tez, SDN tabanlı DDoS tespit ve önleme çalışmalarında model başarımı ile çalışma zamanı uygulanabilirliği arasındaki boşluğu azaltmaya yönelik yöntemsel ve deneysel bir katkı sunmaktadır.
