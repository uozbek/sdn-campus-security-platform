# Bölüm 1. Giriş

## 1.1. Araştırmanın Arka Planı

Bilgisayar ağları, günümüzde üniversitelerden kamu kurumlarına, veri merkezlerinden çevrimiçi eğitim platformlarına kadar çok farklı ölçeklerde kritik hizmetlerin yürütülmesini sağlayan temel altyapılardan biri haline gelmiştir. Ağ servislerinin kesintisiz çalışması, yalnızca teknik bir gereklilik değil, aynı zamanda kurumsal süreklilik, veri güvenliği ve hizmet kalitesi açısından da kritik bir ihtiyaçtır. Bu nedenle ağ güvenliği, özellikle geniş ölçekli ve çok kullanıcılı ortamlarda giderek daha önemli bir araştırma alanı haline gelmektedir.

Bu bağlamda Dağıtık Hizmet Engelleme saldırıları, yani DDoS saldırıları, ağ servislerinin erişilebilirliğini hedef alan en yaygın ve etkili tehditlerden biridir. DDoS saldırılarında saldırganlar, hedef sisteme çok sayıda istek veya yüksek hacimli trafik göndererek ağ kaynaklarını, sunucu kapasitesini veya uygulama servislerini tüketmeye çalışır. Bu tür saldırılar, özellikle kampüs ağları gibi çok sayıda kullanıcı, sunucu, alt ağ ve servis barındıran yapılarda ciddi hizmet kesintilerine yol açabilir.

Geleneksel ağ güvenliği çözümleri çoğunlukla sabit kurallara, imza tabanlı tespit mekanizmalarına veya merkezi güvenlik cihazlarına dayanmaktadır. Bu yaklaşımlar belirli saldırı türlerinde etkili olabilse de, değişken trafik örüntülerinin bulunduğu büyük ölçekli ağlarda yeterli esnekliği sağlayamayabilir. Ayrıca saldırıların hacmi, süresi, protokol türü ve davranış biçimi değiştikçe sabit kuralların güncel tutulması zorlaşmaktadır. Bu nedenle daha dinamik, uyarlanabilir ve ağ davranışını çalışma zamanında analiz edebilen yöntemlere ihtiyaç duyulmaktadır.

## 1.2. Yazılım Tanımlı Ağlar ve Güvenlik Potansiyeli

Yazılım Tanımlı Ağlar, ağ kontrol düzlemi ile veri düzlemini birbirinden ayırarak ağ yönetimini daha merkezi, programlanabilir ve esnek hale getiren bir yaklaşımdır. SDN mimarisinde anahtarlar veri iletiminden sorumluyken, yönlendirme ve politika kararları merkezi bir denetleyici tarafından verilir. Bu yapı, ağ davranışının yazılım aracılığıyla dinamik olarak yönetilmesine olanak tanır.

SDN’in programlanabilir yapısı, ağ güvenliği açısından önemli fırsatlar sunmaktadır. Denetleyici, ağ genelinden akış istatistiklerini toplayabilir, şüpheli trafik örüntülerini gözlemleyebilir ve gerektiğinde OpenFlow kuralları aracılığıyla belirli akışlara müdahale edebilir. Bu müdahaleler arasında trafiğin sınırlandırılması, tamamen engellenmesi veya karantina ağına yönlendirilmesi yer alabilir.

Bununla birlikte SDN tabanlı güvenlik yaklaşımlarının etkili olabilmesi için yalnızca merkezi kontrol yeterli değildir. Denetleyicinin hangi trafiğin normal, hangisinin zararlı olduğuna karar verebilmesi gerekir. Bu noktada makine öğrenmesi ve derin öğrenme yöntemleri, ağ trafiğinden çıkarılan özellikler üzerinden saldırı davranışlarını tespit etmek için güçlü bir araç olarak öne çıkmaktadır.

## 1.3. Makine Öğrenmesi Tabanlı DDoS Tespiti

Makine öğrenmesi tabanlı saldırı tespiti, ağ trafiğinden elde edilen istatistiksel ve davranışsal özelliklerin sınıflandırma modelleriyle analiz edilmesine dayanır. Bu modeller, geçmiş veri kümeleri üzerinde eğitilerek benign ve malicious trafik örüntülerini ayırt etmeyi öğrenir. DDoS tespiti alanında karar ağaçları, Random Forest, XGBoost, LightGBM, destek vektör makineleri ve derin öğrenme tabanlı modeller yaygın olarak kullanılmaktadır.

Ancak literatürdeki birçok çalışma, model başarısını çoğunlukla çevrimdışı veri kümesi üzerinde raporlanan sınıflandırma metrikleriyle değerlendirmektedir. Doğruluk, precision, recall ve F1-score gibi metrikler modelin ayırt edici gücünü göstermek açısından önemlidir; fakat modelin gerçek veya gerçekçi bir ağ ortamında nasıl kullanılacağını tek başına açıklamaz. Özellikle SDN gibi çalışma zamanında karar verilmesi gereken ortamlarda, model çıktısının denetleyici davranışına nasıl dönüştürüleceği ayrıca ele alınmalıdır.

Bu tez çalışması, tam olarak bu boşluğa odaklanmaktadır. Amaç yalnızca DDoS saldırılarını yüksek başarıyla sınıflandıran bir model geliştirmek değil, aynı zamanda bu modelin SDN denetleyicisiyle bütünleştirilerek aktif bir IDS/IPS mekanizmasına dönüştürülebileceğini göstermektir.

## 1.4. Problem Tanımı

Kampüs ağları, çok sayıda kullanıcı, sunucu, servis ve alt ağdan oluşan karmaşık yapılardır. Bu ağlarda benign trafik ile saldırı trafiği çoğu zaman aynı hedef servise, aynı portlara veya benzer zaman aralıklarında yönelebilir. Bu durum, yalnızca IP düzeyinde veya yalnızca trafik hacmine dayalı kararlar verilmesini zorlaştırır.

Bu tez kapsamında ele alınan temel problem şudur:

Makine öğrenmesi tabanlı DDoS tespit modeli, SDN tabanlı kampüs ağı benzeri bir ortamda çalışma zamanı trafik analiziyle bütünleştirilerek benign trafiği koruyan, zararlı trafiği tespit eden ve uygun önleme aksiyonlarını uygulayan aktif bir IDS/IPS prototipine dönüştürülebilir mi?

Bu problem üç alt soruya ayrılabilir:

1. SDN denetleyicisi, çalışma zamanı akış istatistikleri ve PCAP tabanlı özellik çıkarımı ile makine öğrenmesi modelini birlikte kullanabilir mi?
2. Eğitilmiş makine öğrenmesi modeli, karma benign/malicious trafik senaryosunda zararlı UDP davranışını ayırt edebilir mi?
3. Model çıktısı, SDN denetleyicisi üzerinde rate-limit, drop ve quarantine gibi aktif önleme aksiyonlarına güvenilir biçimde dönüştürülebilir mi?

## 1.5. Araştırmanın Amacı

Bu tez çalışmasının temel amacı, SDN tabanlı kampüs ağı benzeri bir ortamda DDoS saldırılarının makine öğrenmesi destekli olarak tespit edilmesi ve tespit edilen saldırı trafiğine karşı aktif önleme aksiyonlarının uygulanmasıdır.

Bu amaç doğrultusunda çalışmada aşağıdaki hedefler benimsenmiştir:

- Mininet ve Open vSwitch kullanılarak kampüs ağı benzeri bir SDN test ortamı oluşturmak.
- Ryu tabanlı bir SDN denetleyicisi geliştirerek akış istatistiklerini toplamak ve güvenlik politikalarını uygulamak.
- CIC-DDoS2019 ailesiyle uyumlu seçilmiş özellikler üzerinden çalışan bir makine öğrenmesi modeli kullanmak.
- Final XGBoost Top-20 modelini FastAPI tabanlı bir inference servisi olarak çalışma zamanı sistemine entegre etmek.
- Runtime PCAP tabanlı feature extraction pipeline geliştirmek.
- Model çıktısını protocol-aware ve port-aware policy katmanı üzerinden yorumlamak.
- Rate-limit, drop ve quarantine mekanizmalarıyla aktif önleme davranışı üretmek.
- Karma benign/malicious trafik senaryolarında sistemin uçtan uca çalışabilirliğini deneysel olarak doğrulamak.

## 1.6. Araştırmanın Katkıları

Bu çalışmanın temel katkıları aşağıdaki şekilde özetlenebilir:

Birinci katkı, makine öğrenmesi tabanlı DDoS tespitinin SDN çalışma zamanı ortamına entegre edilmesidir. Model yalnızca çevrimdışı sınıflandırma başarısı açısından değil, canlı Mininet/Ryu test ortamında kullanılabilirliği açısından da değerlendirilmiştir.

İkinci katkı, runtime feature extraction, FastAPI model servisi, Ryu denetleyicisi ve OpenFlow tabanlı enforcement mekanizmalarının aynı prototip zincirinde birleştirilmesidir. Bu yapı, offline ML modeli ile online SDN kontrol davranışı arasında uygulanabilir bir köprü kurmaktadır.

Üçüncü katkı, port-aware ve protocol-aware değerlendirme yaklaşımının deneysel sürece dahil edilmesidir. Bu yaklaşım, aynı IP çifti arasında bulunan TCP kontrol trafiği, benign UDP trafiği, malicious UDP trafiği ve quarantine-observed trafik ayrımının daha doğru yapılmasını sağlamıştır.

Dördüncü katkı, rate-limit, drop ve quarantine aksiyonlarının aynı SDN tabanlı IDS/IPS prototipi içinde ele alınmasıdır. Bu sayede sistem yalnızca saldırıyı tespit eden pasif bir IDS olarak değil, saldırıya müdahale edebilen aktif bir IPS prototipi olarak değerlendirilmiştir.

Beşinci katkı, deneysel çıktıların tez yazımı için sistematik olarak paketlenmesidir. Policy decision logları, prediction kayıtları, flow statistics dosyaları, mitigation/quarantine/rate-limit logları, comparison raporları, canonical aggregate raporları, tablo ve şekil artifact’leri düzenli biçimde üretilmiştir.

##

Bu katkılar birlikte değerlendirildiğinde, tez çalışması dört temel eksende konumlandırılmaktadır. Birinci eksen, makine öğrenmesi modelinin yalnızca çevrimdışı veri kümesi üzerinde değerlendirilmesi yerine SDN çalışma zamanı ortamına entegre edilmesidir. İkinci eksen, model çıktıları ile denetleyici kararlarının port-aware ve protocol-aware biçimde ilişkilendirilmesidir. Üçüncü eksen, saldırı tespitinin drop, rate-limit ve quarantine_candidate gibi aktif önleme aksiyonlarına dönüştürülerek IDS ve IPS işlevlerinin aynı prototip zincirinde ele alınmasıdır. Dördüncü eksen ise deneysel çıktıların tablo, şekil, log, artifact ve kalite kontrol raporları üzerinden yeniden üretilebilir bir tez raporlama yapısına dönüştürülmesidir. Bu nedenle çalışma, yalnızca yüksek sınıflandırma başarımı raporlayan bir model çalışması olarak değil, SDN tabanlı DDoS tespit ve önleme sistemlerinin çalışma zamanı uygulanabilirliğini gösteren uçtan uca bir deneysel prototip olarak değerlendirilmelidir.

1.7. Deneysel Yaklaşımın Özeti

Çalışmada geliştirilen prototip, Mininet üzerinde oluşturulan kampüs ağı benzeri bir topoloji, Open vSwitch anahtarları, Ryu denetleyicisi, FastAPI tabanlı makine öğrenmesi servisi ve PCAP tabanlı runtime feature extraction pipeline bileşenlerinden oluşmaktadır.

Deneysel süreçte benign TCP/UDP trafik ve zararlı yüksek hacimli UDP trafik aynı hedef sunucuya yönlendirilmiştir. Trafik PCAP olarak yakalanmış, seçilmiş Top-20 özellikler çıkarılmış ve Final XGBoost modeliyle runtime tahminler üretilmiştir. Denetleyici tarafında ise flow statistics verileri değerlendirilmiş ve hibrit politika mantığıyla güvenlik kararları oluşturulmuştur.

Canonical deneyler içinde `run_05_port_aware_repeat_validation` ana deney olarak seçilmiştir. Bu koşuda controller logları, mitigation logları, quarantine logları ve rate-limit logları port bilgisiyle birlikte kaydedilmiş; model-controller karşılaştırması port-aware ve protocol-aware olarak yapılmıştır. Sonuçlar, benign trafiğin korunduğunu, malicious UDP trafiğin tespit edildiğini ve rate-limit, drop ve quarantine mekanizmalarının gözlemlendiğini göstermektedir.

## 1.8. Tezin Organizasyonu

Bu tez çalışması aşağıdaki bölümlerden oluşmaktadır.

Birinci bölümde araştırmanın arka planı, problem tanımı, amaçları, katkıları ve genel deneysel yaklaşımı sunulmaktadır.

İkinci bölümde SDN mimarisi, DDoS saldırıları, makine öğrenmesi tabanlı saldırı tespiti ve SDN güvenliği konularına ilişkin kavramsal ve kuramsal arka plan verilmektedir.

Üçüncü bölümde literatürdeki SDN tabanlı DDoS tespiti ve önleme çalışmaları incelenmekte, mevcut yaklaşımlar karşılaştırılmakta ve bu tezin konumlandırması yapılmaktadır.

Dördüncü bölümde önerilen yöntem, geliştirilen SDN tabanlı IDS/IPS prototipi, makine öğrenmesi modeli, runtime validation deneyleri, tablo ve şekiller sunulmaktadır.

Beşinci bölümde deneysel bulgular tartışılmakta, çalışmanın güçlü yönleri, sınırlılıkları ve gelecek çalışma önerileri değerlendirilmektedir.

Son bölümde ise çalışmanın genel sonuçları özetlenmekte ve araştırmanın SDN tabanlı ağ güvenliği alanına katkıları değerlendirilmektedir.
