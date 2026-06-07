# SDN Campus Security Platform — Roadmap

Bu dosya, kampüs ağına yakın bir SDN test ortamında IDS/IPS prototipi geliştirmek için yapılan aşamaları, eklenen dosyaları, test komutlarını, test sonuçlarını ve sonraki adımları takip etmek amacıyla hazırlanmıştır.

## Genel Amaç

Bu projenin amacı, kampüs ağına benzeyen segmentli bir SDN test yatağı üzerinde:

1. Mininet ile kampüs benzeri ağ topolojisi kurmak,
2. Ryu controller ile L3 routing yapmak,
3. OpenFlow flow istatistiklerini toplamak,
4. Flow tabanlı özellikleri ML inference API’ye göndermek,
5. ML sonucuna göre policy kararı üretmek,
6. Policy sonucuna göre rate-limit, drop ve quarantine gibi önleme mekanizmalarını uygulamak,
7. Daha sonra heuristic model yerine gerçek ML modelini entegre etmektir.

---

## Mevcut Ana Mimari

```text
+-----------------------------+
|      ML Inference API       |
| FastAPI                     |
| /predict, /health           |
| heuristic + real model load |
+--------------^--------------+
               |
               | HTTP POST /predict
               |
+--------------+--------------+
|       Ryu SDN Controller    |
| campus_l3_ids_controller_v9 |
| - L3 routing                |
| - Flow stats collection     |
| - ML API integration        |
| - Policy engine             |
| - Rate-limit mitigation     |
| - Drop mitigation           |
| - Quarantine forwarding     |
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

---

## Mevcut Expected Structure

```text
~/sdn-campus-security-platform/
├── controller/
│   ├── campus_l3_controller_v2.py
│   ├── campus_l3_ids_controller_v3.py
│   ├── campus_l3_ids_controller_v4.py
│   ├── campus_l3_ids_controller_v5.py
│   ├── campus_l3_ids_controller_v6.py
│   ├── campus_l3_ids_controller_v7.py
│   ├── campus_l3_ids_controller_v8.py
│   └── campus_l3_ids_controller_v9.py
│
├── topology/
│   └── campus_topology_v1.py
│
├── ml-service/
│   ├── app.py
│   ├── app_heuristic_backup.py
│   ├── logs/
│   │   └── inference_log.csv
│   │
│   └── models/
│       └── active/
│           ├── model.pkl              # gerçek model varsa
│           ├── scaler.pkl             # opsiyonel
│           ├── feature_order.json
│           ├── label_mapping.json
│           └── model_metadata.json
│
├── traffic-generator/
│   ├── normal_traffic_commands.txt
│   ├── udp_high_rate_commands.txt
│   └── tcp_high_rate_commands.txt
│
├── logs/
│   ├── flow_stats.csv
│   ├── predictions.csv
│   ├── policy_decisions.csv
│   ├── mitigation_log.csv
│   ├── rate_limit_log.csv
│   └── quarantine_log.csv
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
├── docs/
│   └── roadmap.md
│
├── reports/
├── monitoring/
├── notebooks/
├── infrastructure/
├── mitigation/
├── config.yaml
├── README.md
├── requirements.txt
├── .gitignore
└── venv/
```

---

## Kampüs Topolojisi

### Katmanlar

```text
Core Layer:
  s1

Distribution Layer:
  s2, s3

Access Layer:
  s4, s5, s6, s7
```

### Hostlar

```text
h1-h4     student
h5-h7     academic
h8-h9     administrative
h10-h11   guest
h12-h13   attacker_lab
h14       server
h15       monitoring
h16       quarantine
```

### IP Planı

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

### Gateway Planı

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

### Virtual Gateway MAC

```text
00:00:00:00:fe:fe
```

---

# Aşamalar

## Aşama 1 — Profesyonel Proje İskeleti

### Durum
Tamamlandı.

### Yapılan İşler
- Ana proje klasörü oluşturuldu.
- Python virtual environment oluşturuldu.
- Temel klasör yapısı oluşturuldu.
- `requirements.txt` üretildi.
- `README.md`, `.gitignore`, `config.yaml` eklendi.
- Git local repo başlatıldı.
- İlk commit alındı.
- Ryu/eventlet uyumsuzluğu için `eventlet==0.30.2` pinleme yaklaşımı uygulandı.

### Temel Klasörler
- `controller/`
- `topology/`
- `ml-service/`
- `traffic-generator/`
- `logs/`
- `experiments/`
- `datasets/`
- `docs/`
- `reports/`

### Bilinen Notlar
- GitHub remote bağlantısı şimdilik yapılmadı; proje local repoda tutuluyor.

---

## Aşama 2 — Kampüs Topolojisi

### Durum
Tamamlandı.

### Eklenen Dosyalar
- `topology/campus_topology_v1.py`

### Yapılan İşler
- Core–distribution–access katmanlı Mininet topolojisi oluşturuldu.
- 7 switch ve 16 host içeren segmentli yapı kuruldu.
- Hostlara statik IP/MAC ve gateway bilgileri verildi.
- Link hızları ve gecikmeleri tanımlandı.

### Mininet Başlatma Komutu

```bash
cd ~/sdn-campus-security-platform

sudo mn --custom topology/campus_topology_v1.py \
  --topo campus_v1 \
  --controller=remote,ip=127.0.0.1,port=6653 \
  --switch ovsk,protocols=OpenFlow13 \
  --link tc
```

### Bilinen Notlar
- İlk denemelerde `--controller=default` kullanıldığında `Could not find a default OpenFlow controller` hatası alındı.
- Sonrasında remote controller yaklaşımı benimsendi.

---

## Aşama 3 — L3-Aware Ryu Controller

### Durum
Tamamlandı.

### Eklenen Dosyalar
- `controller/campus_l3_controller_v2.py`

### Yapılan İşler
- Simple L2 switch mantığından L3 routing mantığına geçildi.
- Virtual gateway ARP cevapları eklendi.
- Statik IP → MAC ve IP → edge switch eşleşmeleri eklendi.
- Statik switch port haritası tanımlandı.
- IPv4 routed forwarding yapısı kuruldu.
- Ethernet source/destination rewrite yapıldı.
- OpenFlow 1.3 flow rule installation çalıştırıldı.

### Test Komutları

```bash
h1 ping -c 5 10.10.40.14
h14 ping -c 5 10.10.10.1
```

### Beklenen Sonuç

```text
5 packets transmitted, 5 received, 0% packet loss
```

### Sonuç
Başarılı. Segmentler arası routing çalıştı.

---

## Aşama 4 — Flow Statistics Collection

### Durum
Tamamlandı.

### Eklenen Dosyalar
- `controller/campus_l3_ids_controller_v3.py`

### Yapılan İşler
- V2 controller üzerine IDS hazırlık katmanı eklendi.
- Datapath registry eklendi.
- Monitor thread oluşturuldu.
- Her 5 saniyede bir flow stats request gönderildi.
- `EventOFPFlowStatsReply` işlendi.
- `logs/flow_stats.csv` oluşturuldu.
- `packet_count`, `byte_count`, `duration_sec` loglandı.
- İlk sürümde `packet_rate` ve `byte_rate` cumulative olarak hesaplandı.

### Flow Stats CSV Başlığı

```csv
timestamp,datapath_id,priority,ipv4_src,ipv4_dst,ip_proto,duration_sec,packet_count,byte_count,packet_rate,byte_rate
```

### Bilinen Sınırlamalar
- İlk aşamada `ip_proto` boş gelebiliyordu.
- Aynı flow yol üzerindeki tüm switchlerde loglandığı için tekrar eden kayıtlar oluşuyordu.
- Rate hesabı cumulative olduğu için uzun flow’larda yanıltıcı olabiliyordu.

---

## Aşama 5 — ML Inference API v1

### Durum
Tamamlandı.

### Eklenen Dosyalar
- `ml-service/app.py`
- `ml-service/logs/inference_log.csv`
- `ml-service/models/model_registry.csv`

### Yapılan İşler
- FastAPI tabanlı ML inference servisi oluşturuldu.
- `/health` endpoint’i eklendi.
- `/predict` endpoint’i eklendi.
- İlk model olarak deterministic heuristic baseline kullanıldı.
- ML inference kayıtları `ml-service/logs/inference_log.csv` dosyasına yazıldı.

### ML API Başlatma

```bash
cd ~/sdn-campus-security-platform
source venv/bin/activate

cd ml-service
uvicorn app:app --host 127.0.0.1 --port 8000
```

### Heuristic Baseline Mantığı

```text
packet_rate veya byte_rate düşükse:
  benign / allow

orta seviyedeyse:
  anomaly_observed / monitor
  veya suspicious / rate_limit

yüksek seviyedeyse:
  ddos_suspected / drop
```

### Bilinen Notlar
- Bu aşamadaki model gerçek ML modeli değil, entegrasyon testi için kullanılan heuristic modeldir.

---

## Aşama 6 — Controller → ML API Entegrasyonu

### Durum
Tamamlandı.

### Eklenen Dosyalar
- `controller/campus_l3_ids_controller_v4.py`

### Yapılan İşler
- Controller flow stats kayıtlarını ML API’ye göndermeye başladı.
- `/predict` endpoint’i ile HTTP entegrasyonu kuruldu.
- `logs/predictions.csv` oluşturuldu.
- ML API unavailable olduğunda fail-open davranışı eklendi.

### Önemli Teknik Not
İlk başta `requests` kullanıldı; ancak Ryu/eventlet ortamında SSL recursion problemi oluştu. Bu nedenle standart kütüphane kullanıldı:

```python
import http.client
```

### Fail-Open Davranışı

```text
ML API çalışmazsa:
prediction = api_unreachable
recommended_action = allow
api_status = unreachable
```

### Predictions CSV Başlığı

```csv
timestamp,datapath_id,ipv4_src,ipv4_dst,ip_proto,duration_sec,packet_count,byte_count,packet_rate,byte_rate,prediction,confidence,recommended_action,model_id,model_name,inference_latency_ms,controller_ml_roundtrip_ms,api_status
```

---

## Aşama 7 — Kontrollü Trafik Senaryoları

### Durum
Tamamlandı.

### Eklenen Dosyalar
- `traffic-generator/normal_traffic_commands.txt`
- `traffic-generator/udp_high_rate_commands.txt`
- `traffic-generator/tcp_high_rate_commands.txt`

### Normal Trafik Testi

```bash
h14 iperf3 -s &

h1 ping -c 10 10.10.40.14
h2 ping -c 10 10.10.40.14
h3 ping -c 10 10.10.40.14

h1 iperf3 -c 10.10.40.14 -t 20 -b 1M
h2 iperf3 -c 10.10.40.14 -t 20 -b 2M
h3 iperf3 -c 10.10.40.14 -t 20 -b 1M
```

### UDP Yüksek Trafik Testi

```bash
h14 iperf3 -s &
h12 iperf3 -u -c 10.10.40.14 -b 20M -t 30
```

### TCP Yüksek Trafik Testi

```bash
h14 iperf3 -s &
h12 iperf3 -c 10.10.40.14 -t 30 -b 20M
```

### Sonuç
- Normal trafik için genellikle `allow/monitor`.
- Yüksek hacimli trafik için `rate_limit/drop`.
- Bu aşamada mitigation uygulanmadı; sadece ML önerileri loglandı.

---

## Aşama 8 — Delta-Based Flow Rate, Protocol Awareness and Edge Filtering

### Durum
Tamamlandı.

### Eklenen Dosyalar
- `controller/campus_l3_ids_controller_v5.py`

### Yapılan İşler
- Delta-based `packet_rate` hesaplama eklendi.
- Delta-based `byte_rate` hesaplama eklendi.
- `ip_proto` flow match içine eklendi.
- ICMP/TCP/UDP ayrımı yapılabilir hale geldi.
- ML tahminleri sadece source-edge switchlerde üretilecek şekilde filtrelendi.
- `flow_stats.csv` tüm switchlerden kayıt almaya devam etti.
- `predictions.csv` yalnızca source-edge switchlerden tahmin kaydı üretmeye başladı.

### Yeni Flow Stats Alanları

```text
cumulative_packet_rate
cumulative_byte_rate
delta_time_sec
delta_packet_count
delta_byte_count
packet_rate
byte_rate
is_source_edge
```

### Başarı Kriterleri
- `ip_proto=1` ICMP için görüldü.
- `ip_proto=6` TCP için görüldü.
- `ip_proto=17` UDP için görüldü.
- `packet_rate` ve `byte_rate` delta-based hesaplandı.
- `predictions.csv` tekrar eden yol üzeri switch kararlarını azalttı.

---

## Aşama 9 — Policy Engine

### Durum
Tamamlandı.

### Eklenen Dosyalar
- `controller/campus_l3_ids_controller_v6.py`
- `logs/policy_decisions.csv`

### Yapılan İşler
- ML API çıktısı doğrudan uygulanmak yerine Policy Engine’den geçirildi.
- Final action yapısı oluşturuldu:
  - `allow`
  - `monitor`
  - `rate_limit`
  - `drop`
  - `quarantine_candidate`
- Confidence tabanlı karar eşikleri tanımlandı.
- Kaynak bazlı risk sayacı eklendi.
- `policy_decisions.csv` dosyası oluşturuldu.
- ML API hatasında fail-open davranışı korundu.

### Policy Eşikleri

```text
confidence < 0.70           → allow
0.70 <= confidence < 0.85   → monitor
0.85 <= confidence < 0.95   → rate_limit
confidence >= 0.95          → drop
tekrar eden yüksek risk      → quarantine_candidate
```

### Test Komutları

```bash
tail -f logs/policy_decisions.csv

grep "10.10.60.12,10.10.40.14" logs/policy_decisions.csv | tail -30
grep "quarantine_candidate" logs/policy_decisions.csv | tail -20
```

### Sonuç
- Normal trafik için `allow/monitor`.
- Yoğun trafik için `rate_limit/drop`.
- Tekrarlı yüksek güvenli saldırı için `quarantine_candidate` mantığı oluşturuldu.

---

## Aşama 10 — Mitigation V1: OpenFlow Drop Rule

### Durum
Tamamlandı.

### Eklenen Dosyalar
- `controller/campus_l3_ids_controller_v7.py`
- `logs/mitigation_log.csv`

### Yapılan İşler
- Policy Engine sonucu `drop` veya `quarantine_candidate` olduğunda gerçek OpenFlow drop kuralı basıldı.
- Drop rule priority değeri `300` olarak belirlendi.
- Drop kuralları süreli yapıldı:
  - `idle_timeout=60`
  - `hard_timeout=120`
- Aynı mitigation kuralının tekrar tekrar kurulmasını önlemek için `active_mitigations` eklendi.

### Test Komutları

```bash
h14 iperf3 -s &
h12 iperf3 -u -c 10.10.40.14 -b 80M -t 30

tail -f logs/mitigation_log.csv
ovs-ofctl -O OpenFlow13 dump-flows s6 | grep "10.10.60.12"
```

### Beklenen Flow

```text
priority=300,udp,nw_src=10.10.60.12,nw_dst=10.10.40.14 actions=drop
```

### Sonuç
Başarılı. OpenFlow drop rule gerçek switch flow table üzerinde doğrulandı.

---

## Aşama 11 — Rate-Limit Mitigation

### Durum
Tamamlandı.

### Eklenen Dosyalar
- `controller/campus_l3_ids_controller_v8.py`
- `logs/rate_limit_log.csv`

### Yapılan İşler
- V7’deki drop mitigation korundu.
- `rate_limit` final action için OpenFlow meter tabanlı sınırlama eklendi.
- Rate-limit yalnızca source-edge switch üzerinde uygulandı.
- Meter değeri `2000 kbps` olarak tanımlandı.
- Rate-limit priority değeri `250` olarak belirlendi.
- Rate-limit kuralları süreli yapılandırıldı:
  - `idle_timeout=60`
  - `hard_timeout=120`

### Rate-Limit Testi

```bash
h14 iperf3 -s &
h12 iperf3 -u -c 10.10.40.14 -b 12M -t 30
```

### Kontrol Komutları

```bash
tail -20 logs/rate_limit_log.csv
ovs-ofctl -O OpenFlow13 dump-meters s6
ovs-ofctl -O OpenFlow13 dump-flows s6 | grep "priority=250"
```

### Beklenen Meter

```text
meter=1 kbps
type=drop rate=2000
```

### Beklenen Flow

```text
priority=250,udp,nw_src=10.10.60.12,nw_dst=10.10.40.14 actions=meter:1,...
```

### Sonuç
Başarılı. Rate-limit gerçek OpenFlow meter ile uygulanabildi.

---

## Aşama 12 — Quarantine Forwarding

### Durum
Tamamlandı.

### Eklenen Dosyalar
- `controller/campus_l3_ids_controller_v9.py`
- `logs/quarantine_log.csv`

### Yapılan İşler
- V8’deki drop ve rate-limit mekanizmaları korundu.
- `quarantine_candidate` artık drop yerine quarantine forwarding tetikleyecek şekilde ayrıştırıldı.
- Karantina hostu `h16 / 10.10.99.16` olarak tanımlandı.
- Karantina MAC adresi `00:00:00:00:99:16` olarak kullanıldı.
- `QUARANTINE_PRIORITY=350` ile en yüksek mitigation önceliği verildi.
- Kaynak IP ve protokol bazlı karantina yönlendirme eklendi.
- Trafik `ipv4_dst=10.10.99.16` ve `eth_dst=00:00:00:00:99:16` olacak şekilde yeniden yazıldı.
- Trafik statik topolojiye göre h16 yönüne gönderildi.

### Önemli Düzeltme
Başlangıçta `quarantine_candidate` oluşmuyordu. Bunun nedeni risk sayacının yalnızca kaynak IP bazlı tutulmasıydı. Benign TCP control trafiği veya 0 pps flow stats kayıtları risk sayacını düşürüyordu.

Risk sayacı şu mantığa yaklaştırıldı:

```text
(src_ip, dst_ip, ip_proto) bazlı takip
```

Bu sayede `10.10.60.12 → 10.10.40.14 UDP` akışı ayrı takip edildi.

### Quarantine Testi

```bash
h14 iperf3 -s &

h12 iperf3 -u -c 10.10.40.14 -b 80M -t 20
h12 iperf3 -u -c 10.10.40.14 -b 80M -t 20
h12 iperf3 -u -c 10.10.40.14 -b 80M -t 20
```

### Policy Kontrolü

```bash
grep "quarantine_candidate" logs/policy_decisions.csv | tail -20
```

### OVS Kontrolü

```bash
for s in s1 s2 s3 s4 s5 s6 s7; do
  echo "===== $s ====="
  ovs-ofctl -O OpenFlow13 dump-flows $s | grep "priority=350"
done
```

### Beklenen Flow Örneği

```text
priority=350,udp,nw_src=10.10.60.12 actions=set_field:00:00:00:00:fe:fe->eth_src,set_field:00:00:00:00:99:16->eth_dst,set_field:10.10.99.16->ip_dst,output:...
```

### Sonuç
Başarılı. Quarantine forwarding gerçek OpenFlow flow table üzerinde doğrulandı.

---

## Aşama 13 — Real ML Model Integration

### Durum
Devam ediyor.

### Eklenen / Değiştirilen Dosyalar
- `ml-service/app.py`
- `ml-service/app_heuristic_backup.py`
- `ml-service/models/active/feature_order.json`
- `ml-service/models/active/label_mapping.json`
- `ml-service/models/active/model_metadata.json`
- `ml-service/models/active/model.pkl` gerçek model dosyası eklendiğinde
- `ml-service/models/active/scaler.pkl` varsa

### Yapılan İşler
- ML API gerçek model yükleyebilecek şekilde yeniden düzenleniyor.
- `model.pkl` için joblib tabanlı model loading planlandı.
- Opsiyonel `scaler.pkl` desteği planlandı.
- `feature_order.json` ile model feature sırası kontrol altına alınıyor.
- `label_mapping.json` ile model çıktı sınıfları normalize ediliyor.
- `/model-info` endpoint’i eklenecek.
- `/reload-model` endpoint’i eklenecek.
- Model yüklenemezse heuristic fallback korunacak şekilde fail-safe yapı kurulacak.

### Beklenen ML-Service Structure

```text
ml-service/
├── app.py
├── app_heuristic_backup.py
├── logs/
│   └── inference_log.csv
└── models/
    └── active/
        ├── model.pkl
        ├── scaler.pkl
        ├── feature_order.json
        ├── label_mapping.json
        └── model_metadata.json
```

### Varsayılan Feature Order

```json
[
  "ip_proto",
  "duration_sec",
  "packet_count",
  "byte_count",
  "packet_rate",
  "byte_rate",
  "src_segment_id",
  "dst_segment_id",
  "is_same_segment",
  "is_server_dst",
  "is_attacker_lab_src",
  "is_udp",
  "is_tcp",
  "is_icmp"
]
```

### Health Kontrolü

```bash
cd ~/sdn-campus-security-platform
source venv/bin/activate

cd ml-service
uvicorn app:app --host 127.0.0.1 --port 8000
```

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/model-info
```

### Beklenen Durumlar

Gerçek model yoksa:

```json
{
  "model_status": "fallback"
}
```

Gerçek model varsa:

```json
{
  "model_status": "loaded"
}
```

### Bilinen Sınırlamalar
- Gerçek modelin eğitim feature sırası `feature_order.json` ile birebir uyumlu olmalıdır.
- CIC-DDoS2019 gibi farklı dataset feature set’iyle eğitilmiş model doğrudan bu SDN flow schema ile uyumlu olmayabilir.
- Şu an scikit-learn/joblib tabanlı model yükleme hedeflenmektedir.
- PyTorch/TensorFlow modeli için ayrı loader eklenmelidir.

### Sonraki Aşama
Aşama 14 — Dataset Generation and Experiment Runner

---

# Genel Test Komutları

## ML API

```bash
cd ~/sdn-campus-security-platform
source venv/bin/activate
cd ml-service
uvicorn app:app --host 127.0.0.1 --port 8000
```

## Controller

Son aşamadaki controller:

```bash
cd ~/sdn-campus-security-platform
source venv/bin/activate
ryu-manager controller/campus_l3_ids_controller_v9.py
```

## Mininet

```bash
cd ~/sdn-campus-security-platform

sudo mn -c

sudo mn --custom topology/campus_topology_v1.py \
  --topo campus_v1 \
  --controller=remote,ip=127.0.0.1,port=6653 \
  --switch ovsk,protocols=OpenFlow13 \
  --link tc
```

## Normal Routing

```bash
h1 ping -c 5 10.10.40.14
h14 ping -c 5 10.10.10.1
```

## Rate-Limit Test

```bash
h14 iperf3 -s &
h12 iperf3 -u -c 10.10.40.14 -b 12M -t 30
```

## Drop Test

```bash
h14 iperf3 -s &
h12 iperf3 -u -c 10.10.40.14 -b 80M -t 30
```

## Quarantine Test

```bash
h14 iperf3 -s &

h12 iperf3 -u -c 10.10.40.14 -b 80M -t 20
h12 iperf3 -u -c 10.10.40.14 -b 80M -t 20
h12 iperf3 -u -c 10.10.40.14 -b 80M -t 20
```

## Log Kontrolleri

```bash
tail -20 logs/flow_stats.csv
tail -20 logs/predictions.csv
tail -20 logs/policy_decisions.csv
tail -20 logs/rate_limit_log.csv
tail -20 logs/mitigation_log.csv
tail -20 logs/quarantine_log.csv
tail -20 ml-service/logs/inference_log.csv
```

## OVS Kontrolleri

```bash
ovs-ofctl -O OpenFlow13 dump-meters s6
ovs-ofctl -O OpenFlow13 dump-flows s6 | grep "priority=250"
ovs-ofctl -O OpenFlow13 dump-flows s6 | grep "priority=300"
ovs-ofctl -O OpenFlow13 dump-flows s6 | grep "priority=350"
```

---

# Bir Sonraki Plan

## Aşama 14 — Dataset Generation and Experiment Runner

Planlanan işler:

1. Deneyleri YAML senaryolarından çalıştırmak,
2. Trafik üretimini otomatikleştirmek,
3. Logları deney bazlı klasörlere taşımak,
4. Flow feature + label dataset üretmek,
5. ML eğitim datasetini oluşturmak,
6. `model.pkl`, `scaler.pkl`, `feature_order.json` üretim hattını hazırlamak,
7. Deney sonuçlarından özet raporlar üretmek.

Beklenen dosyalar:

```text
experiments/run_experiment.py
experiments/scenarios/e01_normal_traffic.yaml
experiments/scenarios/e02_udp_flood_lab.yaml
experiments/results/<experiment_id>/
datasets/processed/campus_flow_dataset.csv
ml-service/models/active/model.pkl
ml-service/models/active/scaler.pkl
```

---

# Commit Hatırlatma

Aşama 12 sonrası önerilen commit:

```bash
cd ~/sdn-campus-security-platform

git add controller/campus_l3_ids_controller_v9.py docs/roadmap.md
git commit -m "Add quarantine forwarding for repeated attack sources"
```

Aşama 13 sonrası önerilen commit:

```bash
cd ~/sdn-campus-security-platform

git add ml-service/app.py \
        ml-service/app_heuristic_backup.py \
        ml-service/models/active/feature_order.json \
        ml-service/models/active/label_mapping.json \
        ml-service/models/active/model_metadata.json \
        docs/roadmap.md

git commit -m "Integrate real ML model loading with heuristic fallback"
```
