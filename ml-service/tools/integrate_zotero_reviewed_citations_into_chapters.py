#!/usr/bin/env python3
from pathlib import Path


def append_once(path: Path, marker: str, content: str) -> None:
    text = path.read_text(encoding="utf-8")
    if marker in text:
        print(f"[INFO] Already integrated: {path}")
        return
    path.write_text(text.rstrip() + "\n\n" + content.strip() + "\n", encoding="utf-8")
    print(f"[INFO] Updated: {path}")


b2 = Path("docs/bolum_2_kavramsal_kuramsal_arka_plan_tr.md")
b3 = Path("docs/bolum_3_literatur_taramasi_ve_ilgili_calismalar_tr.md")
b5 = Path("docs/bolum_5_tartisma_sinirliliklar_gelecek_calismalar_tr.md")


b2_content = """
## 2.x. Zotero Reviewed Kaynakça ile Kavramsal Çerçevenin Güçlendirilmesi

Bu tezde kullanılan kavramsal çerçeve, yazılım tanımlı ağların temel mimarisi, makine öğrenmesi tabanlı saldırı tespiti, özellik seçimi ve veri kümesi güvenilirliği eksenlerinde yeniden gözden geçirilmiştir. SDN mimarisinin kontrol düzlemi, veri düzlemi ve programlanabilir ağ yönetimi bakımından sağladığı olanaklar, genel SDN literatüründe ayrıntılı biçimde tartışılmıştır (Kreutz vd., 2015). Bu çerçeve, tez kapsamında kullanılan Ryu, OpenFlow ve Mininet tabanlı deney ortamının yalnızca teknik bir test düzeneği değil, aynı zamanda programlanabilir güvenlik politikalarının sınandığı bir araştırma ortamı olarak ele alınmasını desteklemektedir.

Makine öğrenmesi tabanlı IDS yaklaşımlarında model başarımı, kullanılan veri kümesinin niteliği, özellik uzayının temsil gücü ve seçilen öğrenme algoritmasının saldırı davranışını ne ölçüde ayırt edebildiğiyle yakından ilişkilidir. Öğrenme yöntemlerine ilişkin genel IDS literatürü, farklı algoritmaların ağ saldırısı tespitindeki güçlü ve sınırlı yönlerini ortaya koymaktadır (Aburomman ve Reaz, 2016). Özellik seçimi açısından ise filtre tabanlı yaklaşımlar, sürü zekâsı tabanlı optimizasyon yöntemleri ve hibrit seçim stratejileri özellikle yüksek boyutlu ağ trafiği verilerinde önem kazanmaktadır (Ambusaidi vd., 2016; Feng vd., 2018; Khaire ve Dhanalakshmi, 2022).

Bu tez çalışmasında özellik seçimi ve model sadeleştirme yalnızca sınıflandırma başarımını artırma amacıyla değil, çalışma zamanı uygulanabilirliği açısından da ele alınmaktadır. Bu nedenle parçacık sürü optimizasyonu, Harris Hawks optimizasyonu, Dragonfly algoritması, Grey Wolf optimizasyonu ve ensemble learning gibi yöntemsel arka plan kaynakları, önerilen modelleme sürecinin kuramsal temelini destekleyen tamamlayıcı kaynaklar olarak değerlendirilmiştir (Wang vd., 2018; Heidari vd., 2019; Meraihi vd., 2020; Alabool vd., 2021; Shami vd., 2022; Zhou, 2012). Bununla birlikte bu çalışmaların bir kısmı doğrudan SDN-DDoS alanına değil, yöntemsel arka plana katkı sağladığı için tez içinde sınırlı ve bağlama bağlı biçimde kullanılmaktadır.

Veri kümesi tarafında ise DDoS saldırı tespitinde kullanılan veri setlerinin temsil gücü, etiketleme kalitesi ve gerçek ağ davranışını yansıtma düzeyi kritik önemdedir. CIC-DDoS2019 gibi veri kümeleri, gerçekçi DDoS saldırı türleri ve trafik çeşitliliği bakımından literatürde önemli bir referans noktasıdır (Sharafaldin vd., 2019). Buna karşılık ağ trafiği etiketleme süreçlerinin tek başına yeterli olmadığı, veri kümesi kalitesinin deneysel genellenebilirlik üzerinde doğrudan etkili olduğu da vurgulanmaktadır (Guerra-Manzanares vd., 2022). Bu nedenle bu tezde veri kümesi tabanlı offline başarı ile SDN çalışma zamanı davranışı arasındaki fark ayrıca tartışılmaktadır.

<!-- ZOTERO_REVIEWED_CITATION_INTEGRATION_B2 -->
"""


b3_content = """
## 3.x. Zotero Reviewed Kaynakça ile Literatür Sentezinin Genişletilmesi

Reviewed Zotero kaynak havuzu üzerinden yapılan yeniden değerlendirme, SDN tabanlı DDoS tespiti literatürünün birkaç ana hatta kümelendiğini göstermektedir. İlk grup, SDN mimarisi üzerinde makine öğrenmesi veya derin öğrenme ile DDoS saldırılarının tespit edilmesine odaklanan çalışmalardan oluşmaktadır. Bu grupta SVM, derin sinir ağları, GRU, LSTM, ensemble modeller ve hibrit öğrenme yaklaşımları yaygın biçimde kullanılmaktadır (Tang vd., 2016; Ye vd., 2018; Doriguzzi-Corin vd., 2020; Ahuja vd., 2021; Rehman vd., 2021). Bu çalışmalar, model başarımı açısından önemli sonuçlar üretmekle birlikte, çoğu zaman saldırı tespitinin denetleyici tarafında uygulanabilir önleme davranışına nasıl dönüştürüldüğünü sınırlı biçimde ele almaktadır.

İkinci grup çalışmalar, SDN ortamında tespit ile birlikte önleme veya azaltma mekanizmasını da değerlendirmektedir. Bu çizgide OpenFlow tabanlı ağlarda DDoS tespiti, bant genişliği kontrolü, düşük oranlı DDoS saldırılarının belirlenmesi, IDS/IPS uyarı üretimi ve controller/testbed tabanlı doğrulama öne çıkmaktadır (Alsmadi ve AlEroud, 2017; Latah ve Toker, 2018; Lima Filho vd., 2019; Pérez-Díaz vd., 2020; Garba vd., 2024). Bu çalışmalar, tezde önerilen rate-limit, drop ve quarantine aksiyonlarının literatürdeki mitigation/prevention tartışmalarıyla ilişkilendirilmesine imkân vermektedir.

Üçüncü grup, özellik seçimi ve hibrit modelleme çalışmalarından oluşmaktadır. SDN-DDoS alanında özellik seçimi, yalnızca model doğruluğunu artırmak için değil, denetleyici ve inference servisi üzerinde daha düşük maliyetli çalışma zamanı kararları üretebilmek için de önemlidir. Bu kapsamda feature selection temelli SDN-DDoS çalışmaları ve bio-inspired/hybrid feature selection yaklaşımları literatürde önemli yer tutmaktadır (Polat vd., 2020; Mohammad vd., 2022; Bakro vd., 2024). Bu çalışmalar, tezde kullanılan seçilmiş özellik seti, model sadeleştirme ve runtime inference yaklaşımıyla yöntemsel olarak ilişkilidir.

Dördüncü grup, çalışma zamanı performansı, deneysel doğrulama ve test ortamı güvenilirliği üzerine yoğunlaşmaktadır. Özellikle çevrimiçi performans analizi, SDN controller davranışı, gerçek zamanlı veya near-real-time doğrulama ve Mininet/Ryu benzeri testbed kullanımları, offline sınıflandırma başarımı ile gerçek ağ davranışı arasındaki boşluğu tartışmak için önemlidir (Chouhan vd., 2023; Gonzalez ve Charfadine, 2023; Magnani vd., 2023). Bu tez çalışması, söz konusu boşluğu model servisi, Ryu denetleyicisi, PCAP tabanlı runtime feature extraction ve OpenFlow enforcement davranışını aynı prototip zincirinde bir araya getirerek ele almaktadır.

Son olarak, genel IDS ve anomaly detection literatürü, SDN-DDoS alanına doğrudan özgü olmasa da saldırı tespitinde yanlış pozitiflerin azaltılması, anomali tabanlı tespit zorlukları ve model çıktılarının yorumlanması açısından yararlı bir arka plan sunmaktadır (Garcia-Teodoro vd., 2009; Goeschel, 2016; Moore vd., 2023). Bu kaynaklar, tezde özellikle false positive riskleri, benign UDP trafiğinin korunması ve protocol-aware karar katmanının gerekçelendirilmesi açısından destekleyici niteliktedir.

<!-- ZOTERO_REVIEWED_CITATION_INTEGRATION_B3 -->
"""


b5_content = """
## 5.x. Zotero Reviewed Kaynakça Bağlamında Tartışmanın Genişletilmesi

Reviewed Zotero kaynak havuzu, bu tez çalışmasının literatürdeki konumunu üç temel açıdan güçlendirmektedir. Birincisi, mevcut SDN-DDoS çalışmalarının önemli bir bölümü yüksek sınıflandırma başarımı raporlamakta; ancak bu başarımın controller tarafında uygulanabilir, izlenebilir ve akış düzeyinde doğrulanabilir önleme davranışlarına dönüştürülmesi her çalışmada aynı ayrıntıda ele alınmamaktadır. Bu nedenle bu tezde model çıktısının rate-limit, drop ve quarantine gibi aksiyonlara dönüştürülmesi, yalnızca performans metriği değil, sistem davranışı açısından da tartışılmıştır (Alsmadi ve AlEroud, 2017; Pérez-Díaz vd., 2020; Garba vd., 2024).

İkinci olarak, çalışma zamanı doğrulama sonuçları değerlendirilirken veri kümesi kaynaklı sınırlılıklar dikkate alınmalıdır. CIC-DDoS2019 gibi veri kümeleri saldırı türleri açısından zengin bir temel sunsa da, eğitim veri kümesi ile runtime ortamda çıkarılan özelliklerin aynı anlamsal karşılığa sahip olması gerekir (Sharafaldin vd., 2019). Ağ trafiği etiketleme süreçlerinin karmaşıklığı ve veri kümelerinin gerçek ağ davranışını sınırlı temsil edebilme riski, modelin farklı kampüs ağı topolojilerine taşınabilirliği açısından dikkatli yorumlanmalıdır (Guerra-Manzanares vd., 2022; Khalid ve Aldabagh, 2024).

Üçüncü olarak, runtime ve near-real-time IDS yaklaşımları, yalnızca modelin doğru tahmin üretmesini değil, bu tahminin zamanında, açıklanabilir ve ağ politikasına dönüştürülebilir olmasını gerektirir. Çevrimiçi IDS performans analizi ve SDN controller tabanlı değerlendirme çalışmaları, bu noktada offline deneylerin tek başına yeterli olmadığını göstermektedir (Lima Filho vd., 2019; Magnani vd., 2023; Gonzalez ve Charfadine, 2023). Bu tezde canonical ve diagnostic run ayrımı yapılması, port-aware/protocol-aware kayıtların tutulması ve flow-level model-controller eşleştirmesi yapılması, söz konusu deneysel şeffaflık ihtiyacına verilen bir yanıt olarak değerlendirilebilir.

Bununla birlikte, bu tez çalışmasının bazı sınırlılıkları da bulunmaktadır. Deneysel doğrulama Mininet/Ryu tabanlı kontrollü bir ortamda yürütülmüştür; bu durum tekrar üretilebilirlik açısından avantaj sağlasa da gerçek kampüs ağlarındaki kullanıcı çeşitliliği, trafik yoğunluğu ve cihaz heterojenliğini bütünüyle temsil etmeyebilir. Ayrıca seçilmiş özellikler ve belirli saldırı türleri üzerinden elde edilen sonuçların, daha geniş saldırı aileleri ve farklı ağ ölçeklerinde yeniden sınanması gerekir. Gelecek çalışmalarda daha büyük CIC-DDoS2019 alt kümeleri, farklı veri setleri, daha kapsamlı runtime feature extraction senaryoları ve controller overhead ölçümleri birlikte ele alınmalıdır.

<!-- ZOTERO_REVIEWED_CITATION_INTEGRATION_B5 -->
"""


append_once(b2, "ZOTERO_REVIEWED_CITATION_INTEGRATION_B2", b2_content)
append_once(b3, "ZOTERO_REVIEWED_CITATION_INTEGRATION_B3", b3_content)
append_once(b5, "ZOTERO_REVIEWED_CITATION_INTEGRATION_B5", b5_content)
