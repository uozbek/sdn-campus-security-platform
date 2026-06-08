# Bölüm 2. Kavramsal ve Kuramsal Arka Plan

## 2.1. Bölüme Genel Bakış

Bu bölümde, tez çalışmasının dayandığı temel kavramlar ve kuramsal altyapı açıklanmaktadır. Çalışmanın ana ekseni yazılım tanımlı ağlar, DDoS saldırıları, makine öğrenmesi tabanlı saldırı tespiti ve SDN tabanlı aktif önleme mekanizmalarıdır. Bu nedenle bölüm, önerilen yöntemin anlaşılabilmesi için gerekli teknik arka planı sistematik biçimde sunmayı amaçlamaktadır.

İlk olarak geleneksel ağ mimarileri ile yazılım tanımlı ağ mimarileri arasındaki farklar açıklanmaktadır. Ardından SDN’in kontrol düzlemi, veri düzlemi, OpenFlow protokolü ve Ryu denetleyicisi gibi bileşenleri ele alınmaktadır. Devamında DDoS saldırılarının temel özellikleri ve kampüs ağları üzerindeki etkileri incelenmektedir. Son olarak, makine öğrenmesi tabanlı saldırı tespiti, özellik çıkarımı, model değerlendirme metrikleri ve SDN ortamında IDS/IPS bütünleştirmesi tartışılmaktadır.

## 2.2. Geleneksel Ağ Mimarileri

Geleneksel ağ mimarilerinde yönlendirme, anahtarlama ve güvenlik kararları çoğunlukla dağıtık ağ cihazları üzerinde verilir. Her yönlendirici veya anahtar, kendi kontrol mantığına, yönlendirme tablolarına ve yerel yapılandırmasına sahiptir. Bu yapı, küçük ve orta ölçekli ağlarda yeterli olsa da büyük ölçekli ve dinamik ağlarda yönetim karmaşıklığını artırabilir.

Geleneksel yapılarda güvenlik politikalarının uygulanması genellikle güvenlik duvarları, saldırı tespit sistemleri, saldırı önleme sistemleri ve erişim kontrol listeleri üzerinden gerçekleştirilir. Ancak bu politikaların ağ genelinde tutarlı şekilde yönetilmesi her zaman kolay değildir. Özellikle kampüs ağları gibi çok sayıda alt ağ, kullanıcı grubu ve servis barındıran ortamlarda manuel yapılandırma hataları, politika tutarsızlıkları ve gecikmiş müdahale önemli sorunlar oluşturabilir.

Bu nedenle modern ağ güvenliği yaklaşımlarında daha merkezi, programlanabilir ve otomasyona açık mimarilere yönelim artmıştır. Yazılım tanımlı ağlar bu ihtiyaca yanıt veren önemli yaklaşımlardan biridir.

## 2.3. Yazılım Tanımlı Ağlar

Yazılım Tanımlı Ağlar, ağın kontrol düzlemi ile veri düzlemini birbirinden ayıran bir mimari yaklaşımdır. Veri düzlemi, paketlerin iletilmesinden sorumlu anahtar ve yönlendiricilerden oluşurken, kontrol düzlemi ağın genel davranışını belirleyen karar mekanizmasını temsil eder. SDN’de bu karar mekanizması merkezi veya mantıksal olarak merkezi bir denetleyici tarafından yönetilir.

Bu ayrım, ağ yönetimini daha esnek hale getirir. Ağ yöneticileri, belirli cihazları tek tek yapılandırmak yerine denetleyici üzerinde çalışan uygulamalar aracılığıyla ağ genelinde politika tanımlayabilir. Böylece yönlendirme, erişim kontrolü, trafik mühendisliği ve güvenlik politikaları daha dinamik biçimde uygulanabilir.

SDN mimarisinin temel avantajları şunlardır:

- Merkezi ağ görünürlüğü sağlaması.
- Programlanabilir kontrol düzlemi sunması.
- Trafik akışlarına dinamik müdahale imkânı vermesi.
- Güvenlik politikalarının ağ genelinde tutarlı uygulanmasını kolaylaştırması.
- Deneysel ağ araştırmaları için esnek bir prototipleme ortamı sağlaması.

Bu özellikler, SDN’i DDoS tespiti ve önleme çalışmaları için uygun bir araştırma zemini haline getirmektedir.

## 2.4. SDN Mimarisi: Kontrol Düzlemi ve Veri Düzlemi

SDN mimarisinde veri düzlemi, paketleri ileten ağ cihazlarından oluşur. Bu cihazlar genellikle OpenFlow uyumlu anahtarlar olarak yapılandırılır. Veri düzlemindeki anahtarlar, hangi paketin hangi porta iletileceğine ilişkin kararları flow table adı verilen kurallara göre uygular.

Kontrol düzlemi ise ağın genel davranışını belirleyen denetleyiciden oluşur. Denetleyici, anahtarların flow table yapılarını güncelleyebilir, ağ topolojisini izleyebilir, akış istatistiklerini toplayabilir ve gerektiğinde yeni kurallar yükleyebilir. Bu yapı, güvenlik uygulamaları açısından oldukça önemlidir. Çünkü denetleyici, şüpheli bir akışı tespit ettiğinde ilgili akış için drop, rate-limit veya yönlendirme gibi müdahaleler uygulayabilir.

Bu tez çalışmasında Ryu denetleyicisi, kontrol düzleminin temel bileşeni olarak kullanılmıştır. Open vSwitch anahtarları ise veri düzlemini temsil etmektedir. Denetleyici ve anahtarlar arasındaki iletişim OpenFlow protokolü üzerinden gerçekleştirilmiştir.

## 2.5. OpenFlow Protokolü

OpenFlow, SDN mimarilerinde kontrol düzlemi ile veri düzlemi arasında iletişim sağlayan temel protokollerden biridir. OpenFlow sayesinde denetleyici, anahtarların flow table yapılarını okuyabilir, güncelleyebilir ve belirli trafik akışlarına ilişkin kurallar yükleyebilir.

Bir OpenFlow kuralı genellikle eşleşme alanları, öncelik değeri, sayaçlar ve aksiyonlardan oluşur. Eşleşme alanları kaynak IP, hedef IP, protokol, kaynak port, hedef port gibi değerleri içerebilir. Aksiyonlar ise paketi belirli bir porta iletme, düşürme, denetleyiciye gönderme veya meter üzerinden sınırlama gibi davranışları ifade eder.

Bu tez kapsamında OpenFlow kuralları, saldırı olarak değerlendirilen akışlara müdahale etmek için kullanılmıştır. Drop aksiyonu ile zararlı akışların engellenmesi, rate-limit için meter yapılarının kullanılması ve quarantine davranışı için yönlendirme kurallarının uygulanması bu kapsamda değerlendirilmiştir.

## 2.6. Ryu Denetleyicisi

Ryu, Python tabanlı açık kaynaklı bir SDN denetleyici platformudur. Araştırma ve prototipleme çalışmalarında yaygın olarak tercih edilmesinin temel nedenleri arasında Python ile geliştirilebilir olması, OpenFlow desteği sunması ve deneysel uygulamalar için esnek bir yapı sağlaması yer almaktadır.

Bu çalışmada Ryu denetleyicisi, yalnızca geleneksel L3 yönlendirme görevlerini yerine getiren bir bileşen olarak değil, aynı zamanda IDS/IPS karar mekanizmasının merkezinde yer alan bir güvenlik denetleyicisi olarak kullanılmıştır. Denetleyici, akış istatistikleri verilerini toplayarak trafik davranışını izlemiş, makine öğrenmesi modelinden veya hibrit karar mantığından gelen sonuçları değerlendirmiş ve uygun önleme aksiyonlarını üretmiştir.

Ryu tabanlı denetleyici mimarisi, deneysel SDN güvenliği çalışmalarında hızlı prototipleme açısından önemli bir avantaj sağlamaktadır. Bununla birlikte gerçek üretim ortamlarında denetleyici dayanıklılığı, ölçeklenebilirlik, hata toleransı ve performans gibi konular ayrıca ele alınmalıdır.

## 2.7. Mininet ve Open vSwitch

Mininet, SDN araştırmalarında yaygın olarak kullanılan bir ağ emülasyon ortamıdır. Tek bir fiziksel veya sanal makine üzerinde host, switch, controller ve link bileşenleriyle gerçekçi ağ topolojileri oluşturulmasına olanak tanır. Mininet’in en önemli avantajlarından biri, tekrarlanabilir deney ortamları sağlamasıdır.

Open vSwitch ise yazılımsal bir sanal anahtar çözümüdür ve OpenFlow desteğiyle SDN deneylerinde sıkça kullanılmaktadır. Bu tez çalışmasında Open vSwitch anahtarları, kampüs ağı benzeri topolojinin veri düzlemini oluşturmak için kullanılmıştır.

Mininet ve Open vSwitch birleşimi, gerçek kampüs ağına geçmeden önce önerilen güvenlik mimarisinin kontrollü bir ortamda test edilmesini sağlamıştır. Ancak bu ortamın fiziksel ağ cihazlarının tüm performans özelliklerini temsil etmediği de dikkate alınmalıdır.

## 2.8. DDoS Saldırıları

Dağıtık Hizmet Engelleme saldırıları, hedef sistemin erişilebilirliğini bozmayı amaçlayan saldırılardır. Bu saldırılarda çok sayıda kaynak veya botnet bileşeni, hedef sisteme yoğun trafik göndererek bant genişliğini, işlemci kaynaklarını, bellek kapasitesini veya uygulama servislerini tüketmeye çalışır.

DDoS saldırıları genel olarak hacimsel saldırılar, protokol tabanlı saldırılar ve uygulama katmanı saldırıları şeklinde sınıflandırılabilir. Hacimsel saldırılar yüksek bant genişliği tüketmeye odaklanırken, protokol tabanlı saldırılar TCP/IP protokol yığınının zayıf noktalarını kullanabilir. Uygulama katmanı saldırıları ise HTTP gibi servisleri hedef alarak daha düşük hacimde fakat daha etkili davranışlar sergileyebilir.

Bu tez çalışmasında özellikle UDP tabanlı yüksek hacimli saldırı davranışı üzerinde durulmuştur. UDP flood türü saldırılar, bağlantısız yapısı nedeniyle yüksek miktarda paket üretimine uygun olduğundan DDoS senaryolarında sık görülen bir saldırı biçimidir.

## 2.9. Kampüs Ağlarında DDoS Tehdidi

Kampüs ağları, farklı kullanıcı gruplarını, akademik birimleri, idari servisleri, veri merkezlerini, çevrimiçi eğitim sistemlerini ve araştırma altyapılarını aynı ağ çatısı altında barındırabilir. Bu yapı, kampüs ağlarını hem hizmet çeşitliliği hem de güvenlik riski açısından karmaşık hale getirir.

Bir kampüs ağında DDoS saldırısı yalnızca tek bir sunucuyu değil, birçok bağlı hizmeti etkileyebilir. Örneğin öğrenme yönetim sistemleri, video konferans servisleri, kimlik doğrulama sistemleri, web portalları ve veritabanı servisleri bu tür saldırılardan dolaylı veya doğrudan etkilenebilir. Bu nedenle kampüs ağlarında DDoS tespiti ve önleme mekanizmalarının hızlı, doğru ve merkezi biçimde çalışması önemlidir.

SDN tabanlı yaklaşım, kampüs ağı genelinde merkezi görünürlük sağlayarak bu tür saldırılara karşı dinamik müdahale imkânı sunabilir. Bu tez çalışmasının kampüs ağı benzeri bir topolojiye odaklanmasının temel nedeni de budur.

## 2.10. IDS ve IPS Kavramları

Saldırı Tespit Sistemleri, ağ veya sistem davranışlarını izleyerek şüpheli ya da zararlı aktiviteleri tespit etmeyi amaçlayan güvenlik mekanizmalarıdır. IDS sistemleri genellikle pasif gözlem yapar ve tespit edilen olaylar hakkında alarm üretir.

Saldırı Önleme Sistemleri ise tespit edilen saldırılara karşı aktif müdahale gerçekleştiren yapılardır. IPS sistemleri zararlı trafiği engelleyebilir, bağlantıyı sonlandırabilir, trafiği sınırlayabilir veya şüpheli kaynakları izole edebilir.

Bu tez çalışması IDS ve IPS yaklaşımlarını birlikte ele almaktadır. Makine öğrenmesi modeli saldırı tespit işlevini yerine getirirken, SDN denetleyicisi rate-limit, drop ve quarantine mekanizmalarıyla saldırı önleme işlevini üstlenmektedir. Bu nedenle önerilen mimari hibrit bir IDS/IPS prototipi olarak değerlendirilmektedir.

## 2.11. Makine Öğrenmesi Tabanlı Saldırı Tespiti

Makine öğrenmesi tabanlı saldırı tespitinde, ağ trafiğinden çıkarılan sayısal özellikler sınıflandırma modellerine girdi olarak verilir. Model, bu özelliklere dayanarak trafiğin normal veya saldırı sınıfına ait olup olmadığını tahmin eder.

Bu alanda kullanılan modeller arasında karar ağaçları, Random Forest, XGBoost, LightGBM, destek vektör makineleri, yapay sinir ağları ve derin öğrenme tabanlı mimariler yer almaktadır. Ağaç tabanlı ensemble yöntemleri, tabular ağ trafiği verilerinde genellikle güçlü performans göstermektedir. Bu tez çalışmasında Final XGBoost Top-20 modeli çalışma zamanı tespit bileşeni olarak kullanılmıştır.

Makine öğrenmesi tabanlı tespit yaklaşımlarının başarısı, kullanılan veri kümesine, özelliklerin kalitesine, sınıf dengesine, modelin genellenebilirliğine ve çalışma zamanı koşullarına bağlıdır.

## 2.12. CIC-DDoS2019 Veri Kümesi ve CICFlowMeter Uyumlu Özellikler

DDoS tespiti çalışmalarında kullanılan veri kümeleri, modelin öğrenebileceği trafik örüntülerinin temelini oluşturur. CIC-DDoS2019, DDoS saldırı türlerini içeren yaygın kullanılan veri kümelerinden biridir. Bu veri kümesi, farklı saldırı davranışlarını ve normal trafik örneklerini içermesi nedeniyle akademik çalışmalarda sıkça tercih edilmektedir.

CICFlowMeter ise ağ trafiğinden flow tabanlı özellikler çıkarmak için kullanılan bir araçtır. Flow duration, packet length, byte rate, packet rate, header length, flag counts gibi birçok özellik bu tür araçlarla üretilebilir. Bu tez çalışmasında kullanılan çalışma zamanı özellik çıkarımı yaklaşımı, CICFlowMeter uyumlu seçilmiş özelliklerin çalışma zamanı PCAP verisinden çıkarılmasına dayanmıştır.

Özellik sayısının azaltılması, çalışma zamanı uygulanabilirlik açısından önemlidir. Bu nedenle Final Top-20 özellik seti kullanılarak daha hafif bir model çıkarım süreci hedeflenmiştir.

## 2.13. Model Değerlendirme Metrikleri

Makine öğrenmesi tabanlı saldırı tespitinde model performansı genellikle accuracy, precision, recall, F1-score, ROC-AUC gibi metriklerle değerlendirilir. Accuracy genel doğru sınıflandırma oranını gösterirken, precision modelin saldırı olarak etiketlediği örneklerin ne kadarının gerçekten saldırı olduğunu ifade eder. Recall, gerçek saldırıların ne kadarının tespit edilebildiğini gösterir. F1-score ise precision ve recall arasında dengeli bir ölçüt sunar.

Ancak SDN tabanlı çalışma zamanı güvenlik sistemlerinde bu metrikler tek başına yeterli değildir. Çünkü çalışma zamanı ortamında modelin tahmin üretmesi kadar, bu tahminin denetleyici tarafından nasıl yorumlandığı ve hangi ağ aksiyonuna dönüştüğü de önemlidir.

Bu nedenle bu tez çalışmasında model performansı yalnızca sınıflandırma metrikleriyle değil, denetleyici aksiyon distribution, akış düzeyinde model-controller comparison, mitigation log, quarantine log ve rate-limit log gibi çalışma zamanı göstergelerle de değerlendirilmiştir.

## 2.14. Çalışma Zamanı Özellik Çıkarımı

Runtime özellik çıkarımı, canlı veya yakalanmış ağ trafiğinden modelin beklediği özelliklerin çıkarılması sürecidir. Bu süreç, çevrimdışı veri kümesi üzerinde model eğitimi ile çalışma zamanı model kullanımı arasındaki en kritik bağlantılardan biridir.

Eğitim veri kümesindeki özellikler ile çalışma zamanı ortamda çıkarılan özelliklerin aynı anlamı taşıması gerekir. Aksi halde model, eğitim sırasında öğrendiği dağılımdan farklı bir veriyle karşılaşır ve hatalı tahminler üretebilir. Bu nedenle özellik sırası, özellik adları, karşılanmayan özelliklerin kontrolü ve fazladan özelliklerin ayrıştırılması önemlidir.

Bu tez çalışmasında çalışma zamanı PCAP dosyalarından Final Top-20 özellik seti çıkarılmış ve aktif modelin beklediği özellik sırası ile karşılaştırılmıştır. Böylece model çıkarım sürecinin şema uyumluluğu doğrulanmıştır.

## 2.15. SDN Tabanlı Önleme Aksiyonları

SDN ortamında saldırı tespitinden sonra uygulanabilecek birçok önleme aksiyonu bulunmaktadır. Bu çalışmada üç temel aksiyon üzerinde durulmuştur: rate-limit, drop ve quarantine.

Rate-limit, şüpheli trafiğin tamamen kesilmeden belirli bir bant genişliği veya paket oranı ile sınırlandırılmasıdır. Bu yaklaşım, yanlış pozitif durumlarında hizmetin tamamen kesilmesini önlemek açısından faydalı olabilir.

Drop, zararlı olduğu yüksek güvenle değerlendirilen akışların engellenmesini ifade eder. OpenFlow kuralları ile belirli kaynak IP, hedef IP, protokol ve port değerlerine sahip akışlar düşürülebilir.

Quarantine ise saldırgan veya yüksek riskli kaynakların izole edilmesi anlamına gelir. Bu çalışmada quarantine davranışı, tekrarlanan yüksek güvenli saldırı davranışının ardından trafiğin karantina hostuna yönlendirilmesi şeklinde ele alınmıştır.

## 2.16. Hibrit Politika Mantığı

Makine öğrenmesi modeli, ağ trafiğinin normal ya da saldırı niteliği taşıyıp taşımadığına ilişkin olasılıksal bir çıktı üretir. Ancak bu çıktının doğrudan ağ aksiyonuna dönüştürülmesi her zaman doğru olmayabilir. Çünkü ağ bağlamı, protokol türü, port bilgisi, akış yönü, paket oranı ve önceki davranış geçmişi de dikkate alınmalıdır.

Bu nedenle bu tez çalışmasında hibrit politika mantığı kullanılmıştır. Bu mantık, makine öğrenmesi çıktısını yerel sezgisel kurallar ve protokol/port farkındalığı ile birlikte değerlendirir. Örneğin düşük riskli veya trafik oranı anlamlı bir saldırı göstergesi taşımayan akışlar normal kabul edilirken, yüksek güvenli ve tekrarlanan UDP saldırı davranışları drop veya quarantine aksiyonlarına dönüştürülebilir.

Hibrit yaklaşım, yalnızca model çıktısına dayalı kararların neden olabileceği hatalı aksiyon riskini azaltmayı amaçlar. Aynı zamanda SDN denetleyicisinin kararlarını protokol, port ve trafik bağlamıyla ilişkilendirerek daha açıklanabilir hale getirir.

## 2.17. Kavramsal Çerçevenin Literatürle İlişkilendirilmesi

Bu bölümde verilen kavramsal çerçeve, yazılım tanımlı ağların temel mimarisi, makine öğrenmesi tabanlı saldırı tespiti, özellik seçimi ve veri kümesi güvenilirliği eksenlerinde ele alınmıştır. SDN mimarisinin kontrol düzlemi, veri düzlemi ve programlanabilir ağ yönetimi bakımından sağladığı olanaklar, genel SDN literatüründe ayrıntılı biçimde tartışılmıştır (Kreutz vd., 2015). Bu çerçeve, tez kapsamında kullanılan Ryu, OpenFlow ve Mininet tabanlı deney ortamının yalnızca teknik bir test düzeneği değil, aynı zamanda programlanabilir güvenlik politikalarının sınandığı bir araştırma ortamı olarak ele alınmasını desteklemektedir.

Makine öğrenmesi tabanlı IDS yaklaşımlarında model başarımı, kullanılan veri kümesinin niteliği, özellik uzayının temsil gücü ve seçilen öğrenme algoritmasının saldırı davranışını ne ölçüde ayırt edebildiğiyle yakından ilişkilidir. Öğrenme yöntemlerine ilişkin genel IDS literatürü, farklı algoritmaların ağ saldırısı tespitindeki güçlü ve sınırlı yönlerini ortaya koymaktadır (Aburomman ve Reaz, 2016). Özellik seçimi açısından ise filtre tabanlı yaklaşımlar, sürü zekâsı tabanlı optimizasyon yöntemleri ve hibrit seçim stratejileri özellikle yüksek boyutlu ağ trafiği verilerinde önem kazanmaktadır (Ambusaidi vd., 2016; Feng vd., 2018; Khaire ve Dhanalakshmi, 2022).

Bu tez çalışmasında özellik seçimi ve model sadeleştirme yalnızca sınıflandırma başarımını artırma amacıyla değil, çalışma zamanı uygulanabilirliği açısından da ele alınmaktadır. Bu nedenle parçacık sürü optimizasyonu, Harris Hawks optimizasyonu, Dragonfly algoritması, Grey Wolf optimizasyonu ve ensemble learning gibi yöntemsel arka plan kaynakları, önerilen modelleme sürecinin kuramsal temelini destekleyen tamamlayıcı kaynaklar olarak değerlendirilmiştir (Wang vd., 2018; Heidari vd., 2019; Meraihi vd., 2020; Alabool vd., 2021; Shami vd., 2022; Zhou, 2012). Bununla birlikte bu çalışmaların bir kısmı doğrudan SDN-DDoS alanına değil, yöntemsel arka plana katkı sağladığı için tez içinde sınırlı ve bağlama bağlı biçimde kullanılmaktadır.

Veri kümesi tarafında ise DDoS saldırı tespitinde kullanılan veri setlerinin temsil gücü, etiketleme kalitesi ve gerçek ağ davranışını yansıtma düzeyi önemlidir. CIC-DDoS2019 gibi veri kümeleri, DDoS saldırı türleri ve trafik çeşitliliği bakımından literatürde önemli bir referans noktasıdır (Sharafaldin vd., 2019). Buna karşılık ağ trafiği etiketleme süreçlerinin tek başına yeterli olmadığı, veri kümesi kalitesinin deneysel genellenebilirlik üzerinde doğrudan etkili olduğu da vurgulanmaktadır (Guerra-Manzanares vd., 2022). Bu nedenle bu tezde veri kümesi tabanlı çevrimdışı başarı ile SDN çalışma zamanı davranışı arasındaki fark ayrıca dikkate alınmaktadır.

## 2.18. Bölüm Özeti

Bu bölümde, tez çalışmasının dayandığı temel kavramsal ve kuramsal arka plan sunulmuştur. Geleneksel ağ mimarilerinin sınırlılıkları, SDN mimarisinin programlanabilir yapısı, OpenFlow protokolü, Ryu denetleyicisi, Mininet/Open vSwitch deney ortamı, DDoS saldırıları, IDS/IPS kavramları, makine öğrenmesi tabanlı saldırı tespiti, çalışma zamanı özellik çıkarımı, hibrit politika mantığı ve SDN tabanlı önleme aksiyonları açıklanmıştır.

Bu arka plan, sonraki bölümlerde sunulacak literatür değerlendirmesi, yöntem tasarımı ve çalışma zamanı doğrulaması deneylerinin anlaşılması için temel oluşturmaktadır. Bir sonraki bölümde, SDN tabanlı DDoS tespiti ve önleme alanındaki mevcut akademik çalışmalar incelenecek ve bu tez çalışmasının literatürdeki yeri tartışılacaktır.
