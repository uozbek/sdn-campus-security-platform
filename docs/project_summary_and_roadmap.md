# SDN Campus Security Platform — Proje Özeti ve Yol Haritası

## 1. Projenin Genel Amacı

Bu prototipin amacı, kampüs ağına benzeyen bir SDN test ortamı üzerinde aşağıdaki işlevleri gerçekleştiren modüler bir IDS/IPS araştırma platformu geliştirmektir:

1. Segmentli kampüs ağı topolojisi kurmak.
2. SDN controller ile subnetler arası yönlendirme yapmak.
3. Flow istatistiklerini toplamak.
4. Bu istatistikleri ML inference servisine göndermek.
5. ML modelinden `allow`, `monitor`, `rate_limit`, `drop` önerisi almak.
6. Sonraki aşamalarda bu önerilere göre OpenFlow tabanlı önleme yapmak.

Çalışma şu anda sadece çalışan bir Mininet demosu olmaktan çıkarılıp, yayın/tez için genişletilebilir bir SDN tabanlı IDS/IPS araştırma platformu olacak şekilde ilerlemektedir.

---

## 2. Şu Ana Kadar Kurulan Ana Mimari

Mevcut mimari aşağıdaki gibidir:

```text
+-----------------------------+
|      ML Inference API       |
| FastAPI / heuristic model   |
| /predict endpoint           |
+--------------^--------------+
               |
               | HTTP POST /predict
               |
+--------------+--------------+
|       Ryu SDN Controller    |
| campus_l3_ids_controller_v4 |
| - L3 routing                |
| - Flow stats collection     |
| - ML API integration        |
| - predictions.csv logging   |
+--------------^--------------+
               |
               | OpenFlow 1.3
               |
+--------------+--------------+
|     Mininet Campus Network  |
| core / distribution / access|
| h1-h16 segmented hosts      |
+-----------------------------+
```

Henüz yapılmayan ana kısım:

```text
ML önerisine göre gerçek drop/rate-limit/quarantine uygulanması
```

Şu anda controller sadece ML API’den öneri almakta ve bu sonucu loglamaktadır.

---

## 3. Proje Dizin Yapısı

Şu ana kadar oluşturulan ana yapı şöyledir:

```text
~/sdn-campus-security-platform/
│
├── config.yaml
├── README.md
├── requirements.txt
├── .gitignore
│
├── topology/
│   └── campus_topology_v1.py
│
├── controller/
│   ├── campus_l3_controller_v1.py
│   ├── campus_l3_controller_v2.py
│   ├── campus_l3_ids_controller_v3.py
│   └── campus_l3_ids_controller_v4.py
│
├── ml-service/
│   ├── app.py
│   ├── logs/
│   │   ├── .gitkeep
│   │   └── inference_log.csv
│   └── models/
│       └── model_registry.csv
│
├── traffic-generator/
│   ├── normal_traffic_commands.txt
│   ├── udp_high_rate_commands.txt
│   └── tcp_high_rate_commands.txt
│
├── logs/
│   ├── .gitkeep
│   ├── flow_stats.csv
│   └── predictions.csv
│
├── experiments/
│   ├── scenarios/
│   │   ├── e01_normal_traffic.yaml
│   │   └── e02_udp_flood_lab.yaml
│   └── results/
│
├── datasets/
│   ├── raw/
│   └── processed/
│
├── monitoring/
├── reports/
├── notebooks/
├── docs/
├── infrastructure/
└── mitigation/
```

Not: `ml-service` klasör adı değiştirilmemiştir. Python import sorununu aşmak için API klasör içine girilerek çalıştırılmaktadır:

```bash
cd ml-service
uvicorn app:app --host 127.0.0.1 --port 8000
```

---

## 4. Aşama 1 — Profesyonel Proje İskeleti

İlk aşamada proje rastgele dosyalardan oluşan bir demo yerine, düzenli bir araştırma platformu olarak yapılandırılmıştır.

Yapılanlar:

```text
[✓] Ana proje klasörü oluşturuldu
[✓] Klasör yapısı hazırlandı
[✓] Python venv oluşturuldu
[✓] Ryu, FastAPI, uvicorn, pandas, numpy, scikit-learn, joblib, pyyaml, psutil kuruldu
[✓] requirements.txt üretildi
[✓] config.yaml oluşturuldu
[✓] README.md oluşturuldu
[✓] .gitignore oluşturuldu
[✓] model_registry.csv oluşturuldu
[✓] İlk deney YAML şablonları oluşturuldu
[✓] Git local repo başlatıldı
[✓] İlk commitler alındı
```

Bu aşamada Ryu/eventlet uyumsuzluğu için `eventlet==0.30.2` pinleme yaklaşımı kullanılmıştır.

---

## 5. Aşama 2 — Kampüs Topolojisi

Topoloji dosyası:

```text
topology/campus_topology_v1.py
```

Kurulan kampüs benzeri yapı:

```text
Core Layer:
  s1

Distribution Layer:
  s2, s3

Access Layer:
  s4, s5, s6, s7

Hosts:
  h1-h4    student
  h5-h7    academic
  h8-h9    administrative
  h10-h11  guest
  h12-h13  attacker_lab
  h14      server
  h15      monitoring
  h16      quarantine
```

IP planı:

```text
student         10.10.10.0/24
academic        10.10.20.0/24
administrative  10.10.30.0/24
server          10.10.40.0/24
guest           10.10.50.0/24
attacker_lab    10.10.60.0/24
monitoring      10.10.70.0/24
quarantine      10.10.99.0/24
```

Host gateway planı:

```text
student         10.10.10.254
academic        10.10.20.254
administrative  10.10.30.254
server          10.10.40.254
guest           10.10.50.254
attacker_lab    10.10.60.254
monitoring      10.10.70.254
quarantine      10.10.99.254
```

Virtual gateway MAC:

```text
00:00:00:00:fe:fe
```

Mininet `net` çıktısında doğrulanan port eşleşmeleri:

```text
h1  h1-eth0:s4-eth2
h2  h2-eth0:s4-eth3
h3  h3-eth0:s4-eth4
h4  h4-eth0:s4-eth5

h5  h5-eth0:s5-eth2
h6  h6-eth0:s5-eth3
h7  h7-eth0:s5-eth4
h8  h8-eth0:s5-eth5
h9  h9-eth0:s5-eth6
h10 h10-eth0:s5-eth7
h11 h11-eth0:s5-eth8

h12 h12-eth0:s6-eth2
h13 h13-eth0:s6-eth3
h14 h14-eth0:s6-eth4

h15 h15-eth0:s7-eth2
h16 h16-eth0:s7-eth3

s1-eth1 <-> s2-eth1
s1-eth2 <-> s3-eth1
s2-eth2 <-> s4-eth1
s2-eth3 <-> s5-eth1
s3-eth2 <-> s6-eth1
s3-eth3 <-> s7-eth1
```

---

## 6. Aşama 3 — L3-Aware Ryu Controller

Başlangıçta `simple_switch_13` ve L2 mantığıyla test yapılmıştır. Ancak farklı subnetler arası trafik için L3 routing gerektiğinden önce `campus_l3_controller_v1.py`, ardından daha kararlı olan aşağıdaki dosya geliştirilmiştir:

```text
controller/campus_l3_controller_v2.py
```

V2 controller özellikleri:

```text
[✓] OpenFlow 1.3
[✓] Virtual gateway ARP cevapları
[✓] Statik host IP → MAC eşleşmesi
[✓] Statik host IP → edge switch bilgisi
[✓] Statik switchler arası port haritası
[✓] L3 routed forwarding
[✓] Ethernet src/dst rewrite
[✓] OpenFlow flow rule installation
```

Başarılı test:

```bash
h1 ping -c 5 10.10.40.14
h14 ping -c 5 10.10.10.1
```

Sonuç:

```text
5 packets transmitted, 5 received, 0% packet loss
```

Bu aşama ile kampüs segmentleri arasında kontrollü SDN routing sağlanmıştır.

---

## 7. Aşama 4 — Flow Statistics Collection

Daha sonra V2 controller üzerine IDS hazırlık katmanı eklenmiştir:

```text
controller/campus_l3_ids_controller_v3.py
```

V3 controller özellikleri:

```text
[✓] V2’deki L3 routing korundu
[✓] Datapath registry eklendi
[✓] Monitor thread eklendi
[✓] Her 5 saniyede flow stats request gönderildi
[✓] EventOFPFlowStatsReply işlendi
[✓] logs/flow_stats.csv oluşturuldu
[✓] packet_count, byte_count, duration_sec alındı
[✓] packet_rate, byte_rate hesaplandı
```

`flow_stats.csv` formatı:

```csv
timestamp,datapath_id,priority,ipv4_src,ipv4_dst,ip_proto,duration_sec,packet_count,byte_count,packet_rate,byte_rate
```

Başarılı gözlem:

```text
10.10.10.1 → 10.10.40.14
10.10.40.14 → 10.10.10.1
```

Bu akışlar farklı switchlerde loglanmıştır:

```text
s4, s2, s1, s3, s6
```

Bu aşamada `ip_proto` boş gelmektedir. Bunun sebebi flow match’in şu anda sadece `ipv4_src` ve `ipv4_dst` üzerinden kurulmasıdır.

---

## 8. Aşama 5 — ML Inference API v1

Ayrı çalışan ML servisi hazırlanmıştır:

```text
ml-service/app.py
```

Teknik yapı:

```text
FastAPI
uvicorn
/predict endpoint
/health endpoint
heuristic_baseline model
inference_log.csv
```

API çalıştırma:

```bash
cd ~/sdn-campus-security-platform
source venv/bin/activate

cd ml-service
uvicorn app:app --host 127.0.0.1 --port 8000
```

Endpointler:

```text
GET  /
GET  /health
POST /predict
```

İlk model gerçek ML modeli değildir; geçici deterministic baseline olarak tasarlanmıştır:

```text
packet_rate >= 1000 veya byte_rate >= 5_000_000
    → ddos_suspected / drop

packet_rate >= 300 veya byte_rate >= 1_000_000
    → suspicious / rate_limit

packet_rate >= 100 veya byte_rate >= 300_000
    → anomaly_observed / monitor

aksi halde
    → benign / allow
```

ML API response formatı:

```json
{
  "prediction": "benign",
  "confidence": 0.6,
  "recommended_action": "allow",
  "model_id": "M000",
  "model_name": "heuristic_baseline",
  "inference_latency_ms": 0.0,
  "timestamp": "..."
}
```

Inference log dosyası:

```text
ml-service/logs/inference_log.csv
```

---

## 9. Aşama 6 — Controller → ML API Entegrasyonu

Bu aşamada V4 controller’a geçilmiştir:

```text
controller/campus_l3_ids_controller_v4.py
```

V4 controller’ın amacı:

```text
[✓] V3 gibi L3 routing yapmak
[✓] Flow stats toplamaya devam etmek
[✓] Her flow kaydı için ML API’ye /predict isteği göndermek
[✓] ML API sonucunu logs/predictions.csv içine yazmak
[✓] Controller logunda ML prediction satırı göstermek
```

İlk başta `requests` kullanılmıştır; fakat Ryu/eventlet ortamında şu hata çıkmıştır:

```text
RecursionError: maximum recursion depth exceeded
requests → urllib3 → ssl zinciri
```

Bu nedenle controller tarafında `requests` yerine standart Python kütüphaneleriyle devam edilmiştir:

```python
import json
import http.client
```

ML API sabitleri:

```python
ML_API_HOST = "127.0.0.1"
ML_API_PORT = 8000
ML_API_PATH = "/predict"
ML_API_TIMEOUT = 1.5
```

V4 controller’da fail-open davranışı vardır:

```text
ML API çalışmazsa:
prediction = api_unreachable
recommended_action = allow
```

Bu önemlidir; çünkü prototip aşamasında ML servis hatası yüzünden trafiğin kesilmesi istenmemektedir.

`predictions.csv` formatı:

```csv
timestamp,datapath_id,ipv4_src,ipv4_dst,ip_proto,duration_sec,packet_count,byte_count,packet_rate,byte_rate,prediction,confidence,recommended_action,model_id,model_name,inference_latency_ms,controller_ml_roundtrip_ms,api_status
```

Bu aşamanın başarı kriteri:

```text
api_status=ok
prediction=benign/suspicious/ddos_suspected
recommended_action=allow/monitor/rate_limit/drop
```

---

## 10. Aşama 7 — Kontrollü Trafik Senaryoları

Bu aşamada henüz gerçek önleme yapılmamıştır. Amaç, farklı trafik türleri altında ML API’nin ne önerdiğini gözlemlemektir.

Trafik senaryo dosyaları:

```text
traffic-generator/normal_traffic_commands.txt
traffic-generator/udp_high_rate_commands.txt
traffic-generator/tcp_high_rate_commands.txt
```

Normal trafik:

```text
h14 iperf3 -s &

h1 ping -c 10 10.10.40.14
h2 ping -c 10 10.10.40.14
h3 ping -c 10 10.10.40.14

h1 iperf3 -c 10.10.40.14 -t 20 -b 1M
h2 iperf3 -c 10.10.40.14 -t 20 -b 2M
h3 iperf3 -c 10.10.40.14 -t 20 -b 1M
```

Kontrollü UDP yüksek hacimli trafik:

```text
h14 iperf3 -s &
h12 iperf3 -u -c 10.10.40.14 -b 20M -t 30
```

Kontrollü TCP yüksek hacimli trafik:

```text
h14 iperf3 -s &
h12 iperf3 -c 10.10.40.14 -t 30 -b 20M
```

Burada:

```text
h12 = attacker_lab segmenti
h14 = server segmenti
```

Beklenen log davranışı:

```text
Normal trafik:
  benign / allow
  bazen anomaly_observed / monitor

Yüksek hacimli trafik:
  suspicious / rate_limit
  veya ddos_suspected / drop
```

Not: Şu anda `drop` ve `rate_limit` sadece öneridir. Controller henüz gerçek OpenFlow mitigation uygulamamaktadır.

---

## 11. Mevcut Sistemin Güçlü Tarafları

Şu ana kadar kurulan yapı tez/prototip açısından sağlam bir temel sağlamaktadır:

```text
[✓] Segmentli kampüs topolojisi var
[✓] SDN controller üzerinden L3 routing var
[✓] OpenFlow flow rule kurulumu çalışıyor
[✓] Flow stats toplanıyor
[✓] ML API ayrı servis olarak çalışıyor
[✓] Controller ML API’ye istek atabiliyor
[✓] Prediction logları tutuluyor
[✓] Trafik senaryoları ayrıştırılmış durumda
[✓] Git local commit süreci başladı
```

Bu sistem artık sadece ping çalışan bir Mininet demosu değildir; controller, inference servisi ve loglama bileşenleri olan araştırma platformu haline gelmiştir.

---

## 12. Mevcut Sınırlamalar

### 12.1 `ip_proto` Boş Geliyor

Çünkü flow rule şu şekildedir:

```python
parser.OFPMatch(
    eth_type=ether_types.ETH_TYPE_IP,
    ipv4_src=src_ip,
    ipv4_dst=dst_ip
)
```

Yani ICMP/TCP/UDP ayrımı yapılmamaktadır.

Sonraki aşamada şu protokol ayrımları eklenecektir:

```text
ip_proto=1   # ICMP
ip_proto=6   # TCP
ip_proto=17  # UDP
```

### 12.2 `packet_rate` Toplam Ortalama Olarak Hesaplanıyor

Şu anda:

```text
packet_rate = packet_count / duration_sec
byte_rate   = byte_count / duration_sec
```

Bu, flow’un ömrü boyunca ortalama hız vermektedir. Trafik bittikten sonra duration artmaya devam ettiği için hız düşmektedir.

Daha doğru IDS için:

```text
delta_packet_rate =
    current_packet_count - previous_packet_count
    -------------------------------------------
    current_time - previous_time
```

ve:

```text
delta_byte_rate =
    current_byte_count - previous_byte_count
    ---------------------------------------
    current_time - previous_time
```

hesaplanmalıdır.

### 12.3 Aynı Flow Yol Üzerindeki Tüm Switchlerde Loglanıyor

Örneğin `h1 → h14` akışı şu switchlerden geçmektedir:

```text
s4 → s2 → s1 → s3 → s6
```

Bu yüzden aynı flow için 5 ayrı `datapath_id` ile kayıt oluşmaktadır.

Bu araştırma açısından faydalı olabilir. Ancak ML kararını tekilleştirmek için sonraki aşamada yalnızca edge switchler üzerinde karar verilebilir:

```text
s4, s5, s6, s7
```

veya sadece kaynak hostun bağlı olduğu access switch üzerinde karar üretilebilir.

### 12.4 Gerçek ML Modeli Henüz Entegre Değil

Şu anda kullanılan model:

```text
heuristic_baseline
```

Bu iyi bir entegrasyon testi sağlamaktadır; fakat akademik değerlendirme için daha sonra gerçek model bağlanacaktır:

```text
scikit-learn model.pkl
scaler.pkl
feature_order.json
```

veya:

```text
PyTorch .pt model
```

### 12.5 Gerçek Mitigation Yok

Şu anda ML API şunu döndürebilmektedir:

```text
allow
monitor
rate_limit
drop
```

Ancak controller henüz bu aksiyonları uygulamamaktadır.

İleride şunlar eklenecektir:

```text
drop rule
meter/rate-limit
quarantine forwarding
```

---

## 13. Kullandığımız Ana Komut Akışı

### ML API Başlatma

```bash
cd ~/sdn-campus-security-platform
source venv/bin/activate
cd ml-service
uvicorn app:app --host 127.0.0.1 --port 8000
```

### V4 Controller Başlatma

```bash
cd ~/sdn-campus-security-platform
source venv/bin/activate
ryu-manager controller/campus_l3_ids_controller_v4.py
```

### Mininet Başlatma

```bash
cd ~/sdn-campus-security-platform

sudo mn -c

sudo mn --custom topology/campus_topology_v1.py \
  --topo campus_v1 \
  --controller=remote,ip=127.0.0.1,port=6653 \
  --switch ovsk,protocols=OpenFlow13 \
  --link tc
```

### Routing Testi

```bash
h1 ping -c 5 10.10.40.14
h14 ping -c 5 10.10.10.1
```

### Log İzleme

```bash
tail -f logs/flow_stats.csv
tail -f logs/predictions.csv
tail -f ml-service/logs/inference_log.csv
```

### Hızlı Analiz

```bash
grep "10.10.60.12,10.10.40.14" logs/predictions.csv | tail -20
grep ",drop," logs/predictions.csv | tail -30
grep ",rate_limit," logs/predictions.csv | tail -30
grep -v ",ok$" logs/predictions.csv | tail -30
```

---

## 14. Bundan Sonraki Yol Haritası

### Aşama 8 — Delta-Based Flow Rate + ip_proto + Edge Filtering

Bir sonraki aşama budur.

Hedef:

```text
1. packet_rate ve byte_rate hesaplamasını delta-based hale getirmek
2. ICMP/TCP/UDP ayrımı için ip_proto eklemek
3. Sadece edge switchlerde ML kararı üretmek
4. predictions.csv içindeki tekrarları azaltmak
5. ML API’ye daha anlamlı feature göndermek
```

Bu aşama çok önemlidir. Çünkü gerçek zamanlı IDS/IPS için toplam ortalama hız değil, son ölçüm aralığındaki hız daha anlamlıdır.

### Aşama 9 — Policy Engine

ML API sonucu doğrudan uygulanmayacak; controller içinde policy engine olacaktır.

Örnek:

```text
confidence < 0.70
    allow

0.70 ≤ confidence < 0.85
    monitor

0.85 ≤ confidence < 0.95
    rate_limit

confidence ≥ 0.95
    drop

aynı kaynak 3 kez drop önerisi aldıysa
    quarantine
```

Dosya/mimari:

```text
policy_engine.py
```

veya ilk sürümde controller içine gömülü basit yapı.

### Aşama 10 — Mitigation V1: Drop Rule

İlk gerçek önleme:

```text
src_ip=10.10.60.12
dst_ip=10.10.40.14
action=drop
idle_timeout=60
priority=200
```

Ancak kontrollü şekilde:

```text
mitigation.enabled = false/true
```

şeklinde config ile yönetilecektir.

### Aşama 11 — Rate-Limit

OpenFlow meter veya OVS QoS tabanlı rate-limit eklenecektir.

İlk yaklaşım:

```text
saldırgan kaynak için düşük hız limiti
```

İkinci yaklaşım:

```text
sadece hedef sunucuya giden trafik için limit
```

### Aşama 12 — Quarantine

Saldırgan host normal ağa erişemeyecek, sadece quarantine segmentine yönlendirilecektir.

Örnek:

```text
h12 → h16 izinli
h12 → diğer segmentler drop
```

### Aşama 13 — Gerçek ML Model Entegrasyonu

Heuristic baseline yerine gerçek model:

```text
model.pkl
scaler.pkl
feature_order.json
```

veya:

```text
PyTorch .pt model
```

Model registry daha aktif kullanılacaktır:

```text
model_id
model_name
dataset
feature_set
model_version
```

### Aşama 14 — Deney Runner

Elle Mininet komutları yazmak yerine deneyler YAML’dan çalıştırılacaktır.

Örnek:

```text
experiments/scenarios/e01_normal_traffic.yaml
experiments/scenarios/e02_udp_flood_lab.yaml
```

Runner:

```text
experiments/run_experiment.py
```

Yapacakları:

```text
senaryo başlat
trafik üret
logları ayır
sonuçları results/ içine kaydet
özet rapor çıkar
```

### Aşama 15 — Metrik ve Raporlama

Üretilecek metrikler:

```text
prediction count
recommended action count
api latency
controller roundtrip latency
flow count
packet_rate / byte_rate dağılımı
attack traffic reduction
false positive / false negative
```

Üretilecek dosyalar:

```text
reports/experiment_summary.csv
reports/figures/
reports/tables/
```

### Aşama 16 — Monitoring

Daha sonra Prometheus/Grafana eklenebilir.

İzlenecekler:

```text
controller CPU/RAM
ML API latency
prediction count
drop/rate_limit/quarantine count
flow count
packet-in count
```

### Aşama 17 — Yayın/Tez Düzeyi Katkı Formülasyonu

Çalışmanın akademik katkısı şu eksene oturacaktır:

```text
Kampüs SDN ortamlarında gerçek zamanlı DDoS tespiti için hafif flow-stat tabanlı feature çıkarımı,
ML tabanlı saldırı sınıflandırması ve OpenFlow tabanlı çok seviyeli önleme mekanizması.
```

Daha güçlü katkı cümlesi:

```text
Bu çalışma, kampüs ağına yakın segmentli bir SDN test yatağında, controller seviyesinde üretilen hafif akış özellikleriyle gerçek zamanlı DDoS tespiti ve tespit sonrası policy-based OpenFlow mitigation mekanizmasını değerlendiren modüler bir IDS/IPS çerçevesi sunar.
```

---

## 15. Şu Anda En Kritik Teknik Karar

Bundan sonraki en önemli teknik düzeltme Aşama 8’dir.

Çünkü şu anda:

```text
packet_rate = toplam paket / toplam süre
```

Bu uzun süreli flowlarda yanıltıcı olabilir.

Aşama 8’den sonra:

```text
delta_packet_rate = son 5 saniyedeki paket artışı / 5 saniye
delta_byte_rate   = son 5 saniyedeki byte artışı / 5 saniye
```

hesaplanacaktır.

Bu, ML API’nin daha doğru karar vermesini sağlayacaktır.

Ayrıca sadece edge switchlerde karar vererek tekrar eden kayıtlar azaltılacaktır:

```text
EDGE_SWITCHES = {4, 5, 6, 7}
```

ve özellikle kaynak hostun bağlı olduğu edge switchte karar üretmeye yaklaşılacaktır.

---

## 16. Mevcut Durumun Kısa Özeti

Tek cümleyle:

```text
Şu anda segmentli kampüs SDN topolojisi üzerinde L3 routing yapan, flow istatistiklerini toplayan,
bu istatistikleri ayrı çalışan ML inference API’ye gönderen ve tahmin sonuçlarını loglayan çalışan
bir IDS/IPS prototip altyapımız var.
```

Henüz yapılmayan ama sıradaki kritik işler:

```text
delta-rate hesaplama
protokol ayrımı
edge switch filtering
policy engine
gerçek mitigation
gerçek ML model entegrasyonu
deney otomasyonu
raporlama
```

---

## 17. Sonraki Adım

Bir sonraki teknik adım:

```text
Aşama 8 — Delta-based flow rate calculation + ip_proto ayrımı + edge switch filtering
```

Bu aşamada `campus_l3_ids_controller_v5.py` dosyası oluşturularak V4 controller daha doğru IDS feature üretimi yapacak şekilde geliştirilecektir.
