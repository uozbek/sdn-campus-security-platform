# Bölüm Açılış/Kapanış Paragrafı İnceleme Raporu

## bolum_1_giris_tr.md

- Paragraph count: `42`

### İlk 3 paragraf

> # Bölüm 1. Giriş

> ## 1.1. Araştırmanın Arka Planı

> Bilgisayar ağları, günümüzde üniversitelerden kamu kurumlarına, veri merkezlerinden çevrimiçi eğitim platformlarına kadar çok farklı ölçeklerde kritik hizmetlerin yürütülmesini sağlayan temel altyapılardan biri haline gelmiştir. Ağ servislerinin kesintisiz çalışması, yalnızca teknik bir gereklilik değil, aynı zamanda kurumsal süreklilik, veri güvenliği ve hizmet kalitesi açısından da kritik bir ihtiyaçtır. Bu nedenle ağ güvenliği, özellikle geniş ölçekli ve çok kullanıcılı ortamlarda giderek daha önemli bir araştırma alanı haline gelmektedir.

### Son 3 paragraf

> Dördüncü bölümde önerilen yöntem, geliştirilen SDN tabanlı IDS/IPS prototipi, makine öğrenmesi modeli, runtime validation deneyleri, tablo ve şekiller sunulmaktadır.

> Beşinci bölümde deneysel bulgular tartışılmakta, çalışmanın güçlü yönleri, sınırlılıkları ve gelecek çalışma önerileri değerlendirilmektedir.

> Son bölümde ise çalışmanın genel sonuçları özetlenmekte ve araştırmanın SDN tabanlı ağ güvenliği alanına katkıları değerlendirilmektedir.

## bolum_2_kavramsal_kuramsal_arka_plan_tr.md

- Paragraph count: `70`

### İlk 3 paragraf

> # Bölüm 2. Kavramsal ve Kuramsal Arka Plan

> ## 2.1. Bölüme Genel Bakış

> Bu bölümde, tez çalışmasının dayandığı temel kavramlar ve kuramsal altyapı açıklanmaktadır. Çalışmanın ana ekseni yazılım tanımlı ağlar, DDoS saldırıları, makine öğrenmesi tabanlı saldırı tespiti ve SDN tabanlı aktif önleme mekanizmalarıdır. Bu nedenle bölüm, önerilen yöntemin anlaşılabilmesi için gerekli teknik arka planı sistematik biçimde sunmayı amaçlamaktadır.

### Son 3 paragraf

> ## 2.17. Bölüm Özeti

> Bu bölümde, tez çalışmasının dayandığı temel kavramsal ve kuramsal arka plan sunulmuştur. Geleneksel ağ mimarilerinin sınırlılıkları, SDN mimarisinin programlanabilir yapısı, OpenFlow protokolü, Ryu denetleyicisi, Mininet/Open vSwitch deney ortamı, DDoS saldırıları, IDS/IPS kavramları, makine öğrenmesi tabanlı saldırı tespiti ve SDN tabanlı önleme aksiyonları açıklanmıştır.

> Bu arka plan, sonraki bölümlerde sunulacak literatür değerlendirmesi, yöntem tasarımı ve runtime validation deneylerinin anlaşılması için temel oluşturmaktadır. Bir sonraki bölümde, SDN tabanlı DDoS tespiti ve önleme alanındaki mevcut akademik çalışmalar incelenecek ve bu tez çalışmasının literatürdeki yeri tartışılacaktır.

## bolum_3_literatur_taramasi_ve_ilgili_calismalar_tr.md

- Paragraph count: `58`

### İlk 3 paragraf

> # Bölüm 3. Literatür Taraması ve İlgili Çalışmalar

> _Bu taslak literatür sentez tablosundan otomatik olarak desteklenmiştir. Üretim zamanı: `2026-05-20T08:56:37.371051`_

> ## 3.1. Bölüme Genel Bakış

### Son 3 paragraf

> Çalışmanın ayırt edici yönü, model çıktılarının port-aware ve protocol-aware biçimde controller loglarıyla karşılaştırılmasıdır. Bu sayede aynı kaynak-hedef IP çifti üzerindeki benign TCP, benign UDP, malicious UDP ve quarantine-observed akışlar birbirinden ayrılabilmektedir. Canonical run_05 deneyinde rate-limit, drop ve quarantine aksiyonlarının gözlenmesi, önerilen sistemin pasif IDS yerine aktif SDN tabanlı IDS/IPS prototipi olarak konumlandırılabileceğini göstermektedir.

> ## 3.11. Bölüm Özeti

> Bu bölümde SDN tabanlı DDoS tespiti ve önleme literatürü, ML/DL yaklaşımları, özellik seçimi, runtime/controller entegrasyonu, mitigation/prevention ve veri kümesi kullanımı açısından değerlendirilmiştir. Literatür sentezi, bu tez çalışmasının temel katkısının makine öğrenmesi tabanlı tespiti çalışma zamanı SDN denetleyici aksiyonlarına bağlayan port-aware/protocol-aware aktif IDS/IPS zinciri olduğunu göstermektedir.

## bolum_4_yontem_ve_runtime_dogrulama_tr.md

- Paragraph count: `192`

### İlk 3 paragraf

> # Bölüm 4. Yöntem ve Çalışma Zamanı Doğrulama

> Bu bölümde, önerilen SDN tabanlı makine öğrenmesi destekli IDS/IPS mimarisinin tasarımı, deneysel prototip yapısı, çalışma zamanı doğrulama süreci ve elde edilen bulgular bütünlüklü bir çerçevede sunulmaktadır. Çalışmanın temel amacı, DDoS saldırı tespitinin yalnızca çevrimdışı veri kümesi üzerinde yapılan bir sınıflandırma problemi olarak ele alınmasının ötesine geçmek ve eğitilmiş model çıktılarının çalışma zamanında SDN denetleyicisi tarafından nasıl kullanılabileceğini göstermektir.

> Bu nedenle bölüm iki ana eksen üzerine kurulmuştur. İlk eksende, Mininet/Open vSwitch tabanlı deney ortamı, Ryu denetleyicisi, FastAPI üzerinden sunulan makine öğrenmesi modeli, runtime feature extraction pipeline, protocol-aware final policy katmanı ve rate-limit/drop/quarantine önleme mekanizmaları yöntemsel olarak açıklanmaktadır. İkinci eksende ise geliştirilen prototipin karma benign/malicious trafik senaryosu altında nasıl davrandığı deneysel olarak değerlendirilmektedir.

### Son 3 paragraf

> Elde edilen bulgular, önerilen sistemin benign ve kontrol trafiğini koruyabildiğini, zararlı UDP davranışını yüksek saldırı olasılığı ile tespit edebildiğini ve bu tespiti SDN denetleyicisi üzerinde rate-limit, drop ve quarantine gibi önleme aksiyonlarına dönüştürebildiğini göstermektedir. Özellikle port-aware ve protocol-aware karşılaştırma yaklaşımı, model çıktısı ile denetleyici davranışının daha doğru ilişkilendirilmesini sağlamıştır.

> Bu bölümdeki sonuçlar, çalışmanın ana iddiasını desteklemektedir: makine öğrenmesi tabanlı DDoS tespiti, SDN kontrol düzlemiyle bütünleştirildiğinde yalnızca pasif bir sınıflandırma çıktısı üretmekle kalmaz; aynı zamanda ağ davranışına müdahale edebilen aktif bir güvenlik mekanizmasına dönüşebilir. Bununla birlikte deneylerin kontrollü Mininet ortamında yürütülmüş olması, daha çeşitli trafik profilleri ve daha uzun süreli testler ile desteklenmesi gereken bir sınırlılık olarak değerlendirilmelidir.

> Sonraki bölümde, bu deneysel bulgular daha geniş bir akademik bağlamda tartışılacak; önerilen mimarinin güçlü yönleri, sınırlılıkları, literatürdeki benzer yaklaşımlardan farkları ve gelecekte yapılabilecek geliştirmeler değerlendirilecektir.

## bolum_5_tartisma_sinirliliklar_gelecek_calismalar_tr.md

- Paragraph count: `47`

### İlk 3 paragraf

> # Bölüm 5. Tartışma, Sınırlılıklar ve Gelecek Çalışmalar

> ## 5.1. Bölüme Genel Bakış

> Bu bölümde, önceki bölümde sunulan SDN tabanlı makine öğrenmesi destekli IDS/IPS prototipinin deneysel bulguları daha geniş bir akademik bağlamda tartışılmaktadır. Bölüm 4’te önerilen mimarinin canlı Mininet/Ryu ortamında benign trafiği koruyabildiği, zararlı UDP trafiğini tespit edebildiği ve rate-limit, drop ve quarantine gibi önleme aksiyonlarına dönüştürebildiği gösterilmiştir. Bu bölümde ise söz konusu bulguların ne anlama geldiği, çalışmanın güçlü yönleri, sınırlılıkları ve gelecekte hangi araştırma yönleriyle geliştirilebileceği ele alınmaktadır.

### Son 3 paragraf

> **Tablo 5.x. Bu tez çalışmasının mevcut literatürle sonuç ve işlevsellik açısından karşılaştırılması**

> | Çalışma                                                                              | Model/Yöntem                                     | Veri kümesi                                             | Raporlanan metrikler                                                                               | Runtime test   | Controller-side mitigation         | Rate-limit/Drop/Quarantine              | Port/Protocol-aware analiz   | Güçlü yön                                                                  | Sınırlılık                                                                     | |:-------------------------------------------------------------------------------------|:-------------------------------------------------|:--------------------------------------------------------|:---------------------------------------------------------------------------------------------------|:---------------|:

> Bu tablo, önerilen yöntemin iki yönlü katkısını göstermektedir. İlk katkı, seçilmiş özellikler kullanan Final XGBoost Top-20 modelinin çalışma zamanı senaryosuna taşınmasıdır. İkinci katkı ise model çıktılarının SDN denetleyicisi üzerinde rate-limit, drop ve quarantine gibi uygulanabilir aksiyonlara dönüştürülmesidir. Bu yönüyle çalışma, yalnızca offline başarı metriklerine değil, SDN tabanlı aktif savunma davranışına da odaklanmaktadır.

## bolum_6_sonuc_ve_oneriler_tr.md

- Paragraph count: `43`

### İlk 3 paragraf

> # Bölüm 6. Sonuç ve Öneriler

> ## 6.1. Bölüme Genel Bakış

> Bu bölümde, tez çalışmasının genel sonuçları, elde edilen temel bulgular, çalışmanın akademik ve pratik katkıları, sınırlılıkları ve gelecekte yapılabilecek geliştirmeler özetlenmektedir. Önceki bölümlerde yazılım tanımlı ağlar, DDoS saldırıları, makine öğrenmesi tabanlı saldırı tespiti, SDN tabanlı önleme mekanizmaları ve geliştirilen runtime IDS/IPS prototipi ayrıntılı olarak ele alınmıştır.

### Son 3 paragraf

> Bu tez çalışması, SDN tabanlı kampüs ağı benzeri bir ortamda makine öğrenmesi destekli DDoS tespiti ve aktif önleme mekanizmalarının birlikte çalışabileceğini göstermiştir. Geliştirilen prototip, Final XGBoost Top-20 modeli, runtime PCAP feature extraction, FastAPI inference servisi, Ryu denetleyicisi ve OpenFlow tabanlı enforcement mekanizmalarını aynı deneysel zincir içinde birleştirmiştir.

> Canonical deneyler sonucunda benign trafiğin korunduğu, malicious UDP trafiğin tespit edildiği ve rate-limit, drop ve quarantine aksiyonlarının uygulanabildiği görülmüştür. Bu sonuç, önerilen yaklaşımın yalnızca çevrimdışı bir saldırı tespit modeli değil, çalışma zamanı SDN tabanlı aktif IDS/IPS prototipi olarak değerlendirilebileceğini göstermektedir.

> Sonuç olarak bu çalışma, SDN tabanlı ağ güvenliği alanında makine öğrenmesi destekli tespit ile programlanabilir ağ önleme mekanizmaları arasında uygulanabilir bir bütünleşme yaklaşımı sunmaktadır. Daha geniş veri kümeleri, daha fazla deney tekrarı, controller overhead analizi ve gerçek testbed çalışmalarıyla bu yaklaşımın daha da güçlendirilmesi mümkündür.
