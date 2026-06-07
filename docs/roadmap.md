# SDN Campus Security Platform — Roadmap

Bu dosya, kampüs ağına yakın bir SDN test ortamında IDS/IPS prototipi geliştirmek, sezgisel IDS/IPS yaklaşımını makine öğrenmesi tabanlı IDS modeliyle bütünleştirmek ve Azure ML Studio tabanlı önceki model geliştirme sürecini açık kaynak Python ML araçlarıyla yeniden gerçeklemek için hazırlanmıştır.

Ana hedef; Mininet üzerinde kurulan kampüs ağı topolojisi, Ryu tabanlı SDN denetleyici, sezgisel IDS/IPS karar mekanizması, FastAPI tabanlı inference servisi ve CIC-DDoS2019 veri seti üzerinde eğitilecek ML modelini birlikte çalıştıran hibrit bir IDS/IPS mimarisi geliştirmektir.

---

## Genel Amaç

Bu projenin amacı, kampüs ağına benzeyen segmentli bir SDN test yatağı üzerinde:

1. Mininet ile kampüs benzeri ağ topolojisi kurmak,
2. Ryu controller ile L3 routing yapmak,
3. OpenFlow flow istatistiklerini toplamak,
4. Flow tabanlı özellikleri ML inference API’ye göndermek,
5. Sezgisel IDS/IPS modeliyle hızlı ilk karar katmanı oluşturmak,
6. CIC-DDoS2019 ve Mininet/SDN trafiği üzerinden eğitilmiş ML modeliyle ikinci karar katmanı oluşturmak,
7. Sezgisel skor ve ML skorunu birleştirerek nihai policy kararı üretmek,
8. Policy sonucuna göre allow, alert, rate-limit, drop ve quarantine gibi önleme mekanizmalarını uygulamak,
9. ML başarısını klasik metriklerle; controller etkisini ise runtime SDN metrikleriyle ölçmek,
10. Azure ML Studio yerine açık kaynak Python ML pipeline oluşturmak.

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
| campus_l3_ids_controller_v10_ml_ready |
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

## Hedef Hibrit Mimari

```text
Mininet / SDN Campus Topology
        ↓
Ryu Controller
        ↓
Flow / Traffic Feature Extraction
        ↓
+-----------------------------+
|     Heuristic IDS Engine    |
+-----------------------------+
        ↓
+-----------------------------+
|      ML-based IDS Engine    |
| CIC-DDoS2019 + SDN traffic  |
+-----------------------------+
        ↓
Decision Fusion Layer
        ↓
Policy Decision
        ↓
ALLOW / ALERT / RATE_LIMIT / DROP / QUARANTINE
        ↓
OpenFlow Rule Enforcement
        ↓
Metric Collection and Reporting
```

Bu mimaride ML servis yalnızca tahmin, saldırı olasılığı ve önerilen aksiyon üretir. Nihai karar controller tarafındaki policy katmanı tarafından verilir.

---

## Güncel Expected Structure

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
│   ├── campus_l3_ids_controller_v9.py
│   └── campus_l3_ids_controller_v10_ml_ready.py
│
├── topology/
│   └── campus_topology_v1.py
│
├── ml-service/
│   ├── app.py
│   ├── app_heuristic_fallback.py
│   │
│   ├── training/
│   │   ├── 00_prepare_cicddos_subset.py
│   │   ├── 01_clean_dataset.py
│   │   ├── 02_feature_reduction.py
│   │   ├── 03_feature_selection.py
│   │   ├── 04_train_models.py
│   │   ├── 05_evaluate_models.py
│   │   ├── 06_export_best_model.py
│   │   └── 07_generate_figures.py
│   │
│   ├── datasets/
│   │   ├── raw/
│   │   ├── processed/
│   │   └── samples/
│   │
│   ├── experiments/
│   │   ├── ml_metrics/
│   │   ├── sdn_metrics/
│   │   ├── figures/
│   │   └── reports/
│   │
│   ├── logs/
│   │   └── inference_log.csv
│   │
│   └── models/
│       └── active/
│           ├── model.pkl
│           ├── scaler.pkl
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
│   ├── quarantine_log.csv
│   ├── controller_resource_usage.csv
│   ├── flow_rule_timing.csv
│   └── mitigation_latency.csv
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
student          10.10.10.0/24
academic         10.10.20.0/24
administrative   10.10.30.0/24
server           10.10.40.0/24
guest            10.10.50.0/24
attacker_lab     10.10.60.0/24
monitoring       10.10.70.0/24
quarantine       10.10.99.0/24
```

### Gateway Planı

```text
student          10.10.10.254
academic         10.10.20.254
administrative   10.10.30.254
server           10.10.40.254
guest            10.10.50.254
attacker_lab     10.10.60.254
monitoring       10.10.70.254
quarantine       10.10.99.254
```

### Virtual Gateway MAC

```text
00:00:00:00:fe:fe
```

---

# Aşamalar

---

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

```text
controller/
topology/
ml-service/
traffic-generator/
logs/
experiments/
datasets/
docs/
reports/
```

### Bilinen Notlar

- GitHub remote bağlantısı şimdilik yapılmadı; proje local repoda tutuluyor.

---

## Aşama 2 — Kampüs Topolojisi

### Durum

Tamamlandı.

### Eklenen Dosyalar

```text
topology/campus_topology_v1.py
```

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

```text
controller/campus_l3_controller_v2.py
```

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

```text
controller/campus_l3_ids_controller_v3.py
logs/flow_stats.csv
```

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

```text
ml-service/app.py
ml-service/logs/inference_log.csv
ml-service/models/model_registry.csv
```

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

```text
controller/campus_l3_ids_controller_v4.py
logs/predictions.csv
```

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

```text
traffic-generator/normal_traffic_commands.txt
traffic-generator/udp_high_rate_commands.txt
traffic-generator/tcp_high_rate_commands.txt
```

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

```text
controller/campus_l3_ids_controller_v5.py
```

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

```text
controller/campus_l3_ids_controller_v6.py
logs/policy_decisions.csv
```

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

```text
controller/campus_l3_ids_controller_v7.py
logs/mitigation_log.csv
```

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

```text
controller/campus_l3_ids_controller_v8.py
logs/rate_limit_log.csv
```

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

```text
controller/campus_l3_ids_controller_v9.py
logs/quarantine_log.csv
```

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

## Aşama 13 — Real ML Model Integration / ML-Ready Controller

### Durum

Devam ediyor.

### Eklenen / Değiştirilen Dosyalar

```text
controller/campus_l3_ids_controller_v10_ml_ready.py
ml-service/app.py
ml-service/app_heuristic_fallback.py
ml-service/models/active/feature_order.json
ml-service/models/active/label_mapping.json
ml-service/models/active/model_metadata.json
ml-service/models/active/model.pkl
ml-service/models/active/scaler.pkl
```

### Yapılan İşler

- ML API gerçek model yükleyebilecek şekilde yeniden düzenleniyor.
- `model.pkl` için joblib tabanlı model loading planlandı.
- Opsiyonel `scaler.pkl` desteği planlandı.
- `feature_order.json` ile model feature sırası kontrol altına alınıyor.
- `label_mapping.json` ile model çıktı sınıfları normalize ediliyor.
- `/model-info` endpoint’i eklenecek.
- `/reload-model` endpoint’i eklenecek.
- Model yüklenemezse heuristic fallback korunacak şekilde fail-safe yapı kurulacak.
- `v9` controller stabil heuristic IDS/IPS sürümü olarak korunacak.
- `v10_ml_ready` controller ML entegrasyonuna hazır sürüm olarak kullanılacak.

### Varsayılan SDN Runtime Feature Order

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
- CIC-DDoS2019 gibi farklı dataset feature set’iyle eğitilmiş model doğrudan mevcut SDN runtime flow schema ile uyumlu olmayabilir.
- Bu nedenle iki ayrı model hattı değerlendirilecektir:
  - CIC-DDoS2019 offline model hattı,
  - SDN/Mininet runtime flow model hattı.
- Şu an scikit-learn/joblib tabanlı model yükleme hedeflenmektedir.
- PyTorch/TensorFlow modeli için ayrı loader eklenmelidir.

---

## Aşama 13.1 — Hybrid ML + Heuristic IDS/IPS Decision Fusion

### Durum

Planlandı.

### Amaç

Mevcut sezgisel IDS/IPS sistemini, ML tabanlı IDS motoru ile birlikte çalışacak hibrit bir IDS/IPS mimarisine dönüştürmek.

### Çalışma Modları

```text
heuristic_only
ml_only
hybrid
```

### Hibrit Karar Mantığı

```text
final_score = heuristic_weight × heuristic_score + ml_weight × ml_score
```

Önerilen başlangıç ağırlıkları:

```text
heuristic_weight = 0.40
ml_weight        = 0.60
```

Önerilen karar eşikleri:

```text
0.00–0.54  → ALLOW
0.55–0.74  → ALERT
0.75–0.84  → RATE_LIMIT
0.85–0.94  → QUARANTINE
0.95–1.00  → DROP
```

DROP kararı için ek güvenlik şartı:

```text
final_score >= 0.95
ve aynı kaynak/flow için en az 3 ardışık pencere saldırı
```

### Başarı Kriterleri

- Sezgisel skor üretilebilmelidir.
- ML skoru üretilebilmelidir.
- Hybrid final score hesaplanabilmelidir.
- Controller, nihai aksiyonu kendisi verebilmelidir.
- Tüm kararlar loglanmalıdır.

---

## Aşama 14 — Azure ML Pipeline Migration to Open-Source Python ML Stack

### Durum

Devam ediyor.

### Amaç

Makaledeki Azure Machine Learning Studio tabanlı IDS model geliştirme sürecini açık kaynak Python tabanlı ve tekrarlanabilir bir ML pipeline olarak yeniden gerçeklemek.

### Kapsam

- CIC-DDoS2019 veri seti kullanılacaktır.
- NSL-KDD bu fazda kullanılmayacaktır.
- Veri seti açık kaynak yapılmayacaktır.
- Azure ML Studio yerine Python tabanlı araçlar kullanılacaktır.
- Feature reduction, feature selection, model eğitimi, ROC curve, F1 score, FAR, FPR ve controller runtime metrikleri üretilecektir.

### Kullanılacak Araçlar

```text
pandas
numpy
scikit-learn
LightGBM
XGBoost
imbalanced-learn
zoofs / mealpy / niapy
MLflow
FastAPI
joblib / ONNX
Docker
psutil
matplotlib
```

### ML Metrikleri

```text
Accuracy
Precision
Recall
F1-Score
AUC
ROC Curve
FPR
FAR
Confusion Matrix
Feature count
Training time
Inference latency
```

### SDN Runtime Metrikleri

```text
Controller CPU usage
Controller memory usage
Flow rule installation time
Detection latency
Mitigation latency
Throughput before/after mitigation
Packet loss
Drop count
Rate-limit count
Quarantine count
False mitigation count
```

### Başarı Kriterleri

- Azure ML olmadan CIC-DDoS2019 üzerinde model eğitilebilmelidir.
- Feature reduction ve metaheuristic feature selection uygulanabilmelidir.
- En iyi model `ml-service/models/active/` altına export edilebilmelidir.
- FastAPI inference servisi exported modeli kullanabilmelidir.
- Controller, ML tahminlerini sezgisel modelle birlikte değerlendirebilmelidir.
- ML ve SDN metrikleri grafik ve tablo olarak üretilebilmelidir.

---

## Aşama 14.1 — Python ML Pipeline Klasör Yapısı

### Durum

Planlandı / uygulanıyor.

### Amaç

Azure ML Studio tabanlı IDS model geliştirme sürecini Python tabanlı, tekrarlanabilir bir ML pipeline yapısına taşımak için klasör ve script iskeletini hazırlamak.

### Oluşturulacak Alanlar

```text
ml-service/training/
ml-service/datasets/raw/
ml-service/datasets/processed/
ml-service/datasets/samples/
ml-service/experiments/ml_metrics/
ml-service/experiments/sdn_metrics/
ml-service/experiments/figures/
ml-service/experiments/reports/
```

### Eğitim Scriptleri

```text
ml-service/training/00_prepare_cicddos_subset.py
ml-service/training/01_clean_dataset.py
ml-service/training/02_feature_reduction.py
ml-service/training/03_feature_selection.py
ml-service/training/04_train_models.py
ml-service/training/05_evaluate_models.py
ml-service/training/06_export_best_model.py
ml-service/training/07_generate_figures.py
```

### Başarı Kriteri

- Eğitim, değerlendirme ve grafik üretim scriptleri oluşturulmuş olmalıdır.
- Gerekli temel Python ML paketleri kurulmuş olmalıdır.
- Proje yapısı Azure ML bağımlılığı olmadan model geliştirmeye hazır hale gelmiş olmalıdır.

---

## Aşama 14.1-B — Requirements Güncellemesi

### Durum

Planlandı / uygulanıyor.

### Mevcut Dosyada Zaten Bulunan Paketler

```text
pandas==2.0.3
numpy==1.24.4
scikit-learn==1.3.2
fastapi==0.124.4
uvicorn==0.33.0
joblib==1.4.2
psutil==7.2.2
requests==2.32.4
```

### Eklenecek Paketler

```text
lightgbm==4.3.0
xgboost==2.0.3
imbalanced-learn==0.12.4
mlflow==2.17.2
skl2onnx==1.16.0
onnxruntime==1.16.3
matplotlib==3.7.5
```

### Not

`pkg_resources==0.0.0` satırı kurulumda sorun çıkarırsa kaldırılacaktır.

### Başarı Kriteri

Aşağıdaki paketler hata vermeden import edilebilmelidir:

```text
pandas
numpy
sklearn
lightgbm
xgboost
imblearn
mlflow
fastapi
joblib
psutil
matplotlib
skl2onnx
onnxruntime
```

---

## Aşama 14.2 — CIC-DDoS2019 Veri Temizleme

### Durum

Planlandı / script tasarlandı.

### Amaç

Azure ML Studio'da yapılan veri temizleme fazını Python tabanlı pipeline'a taşımak.

### Yapılan İşlemler

- CSV dosyası pandas ile okunur.
- Kolon isimleri normalize edilir.
- NaN ve infinity değerler temizlenir.
- Duplicate satırlar kaldırılır.
- Sayısal olmayan feature'lar tespit edilir.
- Sabit / tek-değerli feature'lar kaldırılır.
- Label kolonu binary IDS formatına dönüştürülür:
  - `0 = BENIGN`
  - `1 = ATTACK`
- Temizlenmiş veri `ml-service/datasets/processed/` altına kaydedilir.
- Temizlik özeti `ml-service/experiments/reports/cleaning_report.json` olarak üretilir.

### Üretilecek Script

```text
ml-service/training/01_clean_dataset.py
```

### Örnek Çıktılar

```text
ml-service/datasets/processed/cicddos2019_clean.csv
ml-service/experiments/reports/cleaning_report.json
```

### Başarı Kriterleri

- Temizlenmiş dataset içinde NaN, infinity ve duplicate satır bulunmamalıdır.
- Label kolonu yalnızca 0 ve 1 değerlerinden oluşmalıdır.
- Silinen feature'lar raporlanmalıdır.

---

## Aşama 14.2 Ek Not — CIC-DDoS2019 Kaynakları ve Dataset Stratejisi

### İncelenen Kaynaklar

```text
saghal/CIC-DDoS2019-ML-Detection
Kaggle DDoS Detection notebook
ahlashkari/NTLFlowLyzer
```

### Dataset Kararı

- İlk aşamada CIC-DDoS2019 resmi CSV feature dosyaları kullanılacaktır.
- PCAP dosyaları sonraki aşamada, kendi Mininet trafiğimizden feature çıkarmak için kullanılacaktır.
- İlk model binary IDS olacaktır:
  - `0 = BENIGN`
  - `1 = ATTACK`
- İlk prototip için SYN, UDP ve UDP-Lag saldırılarıyla başlanacaktır.
- Daha sonra tüm CIC-DDoS2019 attack family'leriyle genişletilmiş binary model kurulacaktır.
- Son aşamada multi-class saldırı sınıflandırması değerlendirilecektir.

---

## Aşama 14.2-B — CIC-DDoS2019 SYN/UDP/UDP-Lag Subset Hazırlama

### Durum

Planlandı / script tasarlandı.

### Amaç

İlk ML pipeline doğrulaması için CIC-DDoS2019 veri setinden SDN/Mininet testleriyle uyumlu SYN, UDP ve UDP-Lag saldırılarını içeren küçük ve yönetilebilir bir binary IDS veri seti hazırlamak.

### Yapılan İşlemler

- `ml-service/datasets/raw/` altındaki CSV dosyaları taranır.
- Dosya adına göre SYN, UDP ve UDP-Lag aday dosyaları seçilir.
- Label değerleri normalize edilir.
- BENIGN, SYN, UDP ve UDP-LAG kayıtları birleştirilir.
- Birleşik ham subset `ml-service/datasets/processed/` altına kaydedilir.
- Subset hazırlama raporu `ml-service/experiments/reports/subset_report.json` olarak üretilir.
- Ardından `01_clean_dataset.py` ile binary temiz dataset oluşturulur.

### Üretilecek Script

```text
ml-service/training/00_prepare_cicddos_subset.py
```

### Örnek Çıktılar

```text
ml-service/datasets/processed/cicddos2019_syn_udp_udplag_raw_subset.csv
ml-service/datasets/processed/cicddos2019_syn_udp_udplag_clean.csv
ml-service/experiments/reports/subset_report.json
ml-service/experiments/reports/cleaning_report_syn_udp_udplag.json
```

### Başarı Kriterleri

- Temizlenmiş dataset içinde hem BENIGN hem ATTACK kayıtları bulunmalıdır.
- Dataset NaN, infinity ve duplicate kayıt içermemelidir.
- Sonraki feature reduction ve model eğitim fazları için hazır olmalıdır.

---

## Aşama 14.3 — Feature Reduction

### Durum

Planlandı / script tasarlandı.

### Amaç

Metaheuristic feature selection öncesinde CIC-DDoS2019 temiz veri setindeki gereksiz feature'ları azaltmak.

### Yapılan İşlemler

- Sayısal olmayan feature'lar kaldırılır.
- Düşük varyanslı veya sabit feature'lar kaldırılır.
- Yüksek korelasyonlu feature'lar filtrelenir.
- Mutual Information tabanlı feature ranking üretilir.
- Reduced dataset `ml-service/datasets/processed/` altına kaydedilir.
- Feature reduction raporu `ml-service/experiments/reports/feature_reduction_report.json` olarak üretilir.
- MI sıralaması `ml-service/experiments/ml_metrics/mutual_information_ranking.csv` olarak kaydedilir.

### Üretilecek Script

```text
ml-service/training/02_feature_reduction.py
```

### Örnek Çıktılar

```text
ml-service/datasets/processed/cicddos2019_syn_udp_udplag_reduced.csv
ml-service/experiments/reports/feature_reduction_report.json
ml-service/experiments/ml_metrics/mutual_information_ranking.csv
```

### Başarı Kriterleri

- Reduced dataset başarıyla oluşturulmalıdır.
- Feature sayısı raporlanmalıdır.
- Silinen feature'lar JSON raporda listelenmelidir.
- Mutual Information ranking dosyası üretilmelidir.

---

## Aşama 14.4-A — Baseline Model Eğitimi

### Durum

Planlandı.

### Amaç

Feature selection uygulanmadan önce reduced dataset üzerinde temel modelleri eğitmek.

### Planlanan Modeller

```text
Logistic Regression
Random Forest
Extra Trees
Gradient Boosting
LightGBM
XGBoost
MLP
```

### İlk Hedef Model

```text
LightGBM
```

### Üretilecek Çıktılar

```text
ml-service/experiments/ml_metrics/classification_report.csv
ml-service/experiments/ml_metrics/confusion_matrix.csv
ml-service/experiments/ml_metrics/baseline_model_metrics.json
ml-service/experiments/figures/roc_curve_lightgbm.png
ml-service/experiments/figures/precision_recall_curve_lightgbm.png
```

### Başarı Kriterleri

- Baseline LightGBM modeli eğitilmelidir.
- Accuracy, precision, recall, F1, AUC, FPR ve FAR hesaplanmalıdır.
- ROC curve ve confusion matrix üretilmelidir.
- En iyi baseline model sonraki feature selection karşılaştırması için referans alınmalıdır.

---

## Aşama 14.4-B — Metaheuristic Feature Selection

### Durum

Planlandı.

### Amaç

Makaledeki feature selection yaklaşımını Python tabanlı açık kaynak araçlarla yeniden gerçeklemek.

### Planlanan Yöntemler

```text
HHO
PSO
GWO
DFO
```

### Aday Araçlar

```text
zoofs
mealpy
niapy
custom binary wrapper
```

### Karşılaştırma Hedefleri

```text
Feature count
Accuracy
Precision
Recall
F1-Score
AUC
FPR
FAR
Inference latency
```

### Başarı Kriterleri

- HHO/PSO/GWO/DFO feature subset’leri üretilebilmelidir.
- Her subset ile LightGBM/XGBoost modelleri eğitilebilmelidir.
- Feature selection olmayan baseline ile karşılaştırma yapılabilmelidir.
- HHO-BDT/LightGBM hattı ana aday olarak değerlendirilebilmelidir.

---

## Aşama 14.5 — Model Export

### Durum

Planlandı.

### Amaç

En iyi modeli controller ile çalışabilecek şekilde dışa aktarmak.

### Planlanan Çıktılar

```text
ml-service/models/active/model.pkl
ml-service/models/active/scaler.pkl
ml-service/models/active/feature_order.json
ml-service/models/active/label_mapping.json
ml-service/models/active/model_metadata.json
```

### Opsiyonel Çıktı

```text
ml-service/models/active/model.onnx
```

### Başarı Kriterleri

- Model `joblib` ile kaydedilebilmelidir.
- Scaler varsa ayrı kaydedilebilmelidir.
- Feature sırası JSON olarak saklanmalıdır.
- FastAPI servisi modeli yükleyebilmelidir.

---

## Aşama 14.6 — FastAPI Inference Service Güncellemesi

### Durum

Planlandı.

### Amaç

`ml-service/app.py` dosyasını gerçek ML modelini kullanacak şekilde güncellemek.

### Beklenen API Çıktısı

```json
{
  "prediction": "ATTACK",
  "attack_probability": 0.94,
  "recommended_action": "QUARANTINE",
  "model_mode": "ml",
  "feature_count": 30,
  "inference_latency_ms": 2.7
}
```

### Başarı Kriterleri

- Model varsa gerçek ML tahmini yapılmalıdır.
- Model yoksa heuristic fallback çalışmalıdır.
- `/model-info` endpoint’i model durumunu göstermelidir.
- `/reload-model` endpoint’i modeli tekrar yükleyebilmelidir.
- Inference latency loglanmalıdır.

---

## Aşama 14.7 — Controller Runtime Metrics

### Durum

Planlandı.

### Amaç

Ryu controller çalışma zamanı metriklerini toplamak.

### Ölçülecek Metrikler

```text
Controller CPU usage
Controller memory usage
Flow rule installation time
Detection latency
Mitigation latency
Throughput before/after mitigation
Packet loss
Drop count
Rate-limit count
Quarantine count
```

### Üretilecek Dosyalar

```text
logs/controller_resource_usage.csv
logs/flow_rule_timing.csv
logs/mitigation_latency.csv
```

### Başarı Kriterleri

- Controller process CPU ve memory tüketimi ölçülebilmelidir.
- FlowMod gönderim zamanı loglanmalıdır.
- Mümkünse Barrier Reply ile gerçek flow rule installation time ölçülmelidir.
- Detection ve mitigation latency ayrıştırılmalıdır.

---

## Aşama 14.8 — Deneysel Karşılaştırma

### Durum

Planlandı.

### Amaç

Sezgisel, ML ve hibrit IDS/IPS modlarını karşılaştırmak.

### Deney Modları

```text
heuristic_only
ml_only
hybrid
```

### Karşılaştırılacak Değerler

```text
F1-Score
FAR
FPR
AUC
Inference latency
Controller CPU usage
Controller memory usage
Flow rule installation time
Mitigation latency
Throughput preservation
False mitigation count
```

### Başarı Kriterleri

- Aynı trafik senaryoları üç modda da çalıştırılmalıdır.
- Her mod için ML ve SDN runtime metrikleri üretilmelidir.
- Hybrid yaklaşımın avantaj/dezavantajları sayısal olarak gösterilmelidir.

---

## Aşama 14.9 — Grafik ve Rapor Üretimi

### Durum

Planlandı.

### Amaç

ML ve SDN metriklerini tez/makale için görselleştirmek.

### Üretilecek Grafikler

```text
ROC Curve
Precision-Recall Curve
Confusion Matrix
Feature Count Comparison
F1 Score Comparison
FAR Comparison
FPR Comparison
Inference Latency Comparison
Controller CPU Usage Over Time
Controller Memory Usage Over Time
Flow Rule Installation Time Boxplot
Mitigation Latency Comparison
Throughput Before/After Mitigation
```

### Çıktı Klasörü

```text
ml-service/experiments/figures/
```

---

## Aşama 15 — Dataset Generation and Experiment Runner

### Durum

Planlandı.

### Amaç

Mininet/SDN ortamındaki deneyleri otomatikleştirmek, trafik senaryolarını YAML dosyalarından çalıştırmak, logları deney bazlı klasörlere taşımak ve SDN runtime dataset üretmek.

### Planlanan İşler

1. Deneyleri YAML senaryolarından çalıştırmak,
2. Trafik üretimini otomatikleştirmek,
3. Logları deney bazlı klasörlere taşımak,
4. Flow feature + label dataset üretmek,
5. ML eğitim datasetini oluşturmak,
6. `model.pkl`, `scaler.pkl`, `feature_order.json` üretim hattını hazırlamak,
7. Deney sonuçlarından özet raporlar üretmek.

### Beklenen Dosyalar

```text
experiments/run_experiment.py
experiments/scenarios/e01_normal_traffic.yaml
experiments/scenarios/e02_udp_flood_lab.yaml
experiments/results/<experiment_id>/
datasets/processed/campus_flow_dataset.csv
ml-service/models/active/model.pkl
ml-service/models/active/scaler.pkl
```

### Başarı Kriterleri

- Normal trafik ve saldırı trafik senaryoları otomatik koşturulabilmelidir.
- Her deney için ayrı sonuç klasörü oluşmalıdır.
- Loglar deney bazlı saklanmalıdır.
- SDN runtime flow dataset üretilebilmelidir.

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

Stabil heuristic controller:

```bash
cd ~/sdn-campus-security-platform
source venv/bin/activate
ryu-manager controller/campus_l3_ids_controller_v9.py
```

ML-ready controller:

```bash
cd ~/sdn-campus-security-platform
source venv/bin/activate
ryu-manager controller/campus_l3_ids_controller_v10_ml_ready.py
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

# Güncel Öncelik Sırası

1. `requirements.txt` dosyasına eksik ML paketlerinin eklenmesi.
2. `ml-service/training/` ve alt ML pipeline klasörlerinin oluşturulması.
3. `00_prepare_cicddos_subset.py` ile SYN/UDP/UDP-Lag subset üretimi.
4. `01_clean_dataset.py` ile temiz binary dataset üretimi.
5. `02_feature_reduction.py` ile reduced dataset üretimi.
6. `04_train_models.py` ile baseline LightGBM modeli eğitimi.
7. ROC, F1, FAR, FPR metriklerinin üretilmesi.
8. Model artifact export.
9. FastAPI inference entegrasyonu.
10. Ryu controller ile ML skorunun sezgisel skorla birlikte kullanılması.
11. Controller CPU/memory ve flow rule timing ölçümleri.
12. Heuristic-only, ML-only ve Hybrid karşılaştırması.

---

# Commit Hatırlatma

## Aşama 12 sonrası önerilen commit

```bash
cd ~/sdn-campus-security-platform

git add controller/campus_l3_ids_controller_v9.py docs/roadmap.md
git commit -m "Add quarantine forwarding for repeated attack sources"
```

## Aşama 13 sonrası önerilen commit

```bash
cd ~/sdn-campus-security-platform

git add controller/campus_l3_ids_controller_v10_ml_ready.py \
        ml-service/app.py \
        ml-service/app_heuristic_fallback.py \
        ml-service/models/active/feature_order.json \
        ml-service/models/active/label_mapping.json \
        ml-service/models/active/model_metadata.json \
        docs/roadmap.md

git commit -m "Integrate real ML model loading with heuristic fallback"
```

## Aşama 14 ML pipeline sonrası önerilen commit

```bash
cd ~/sdn-campus-security-platform

git add requirements.txt \
        ml-service/training/ \
        ml-service/datasets/ \
        ml-service/experiments/ \
        docs/roadmap.md

git commit -m "Add open-source ML pipeline for CIC-DDoS2019 IDS modeling"
```
## Aşama 14.4-A — Baseline Model Eğitimi

### Durum

Tamamlandı.

### Sonuç

Reduced CIC-DDoS2019 SYN/UDP/UDP-Lag dataset üzerinde baseline modeller eğitildi. LightGBM modeli F1-Score, AUC, FPR ve FAR değerleri dikkate alınarak en iyi baseline model olarak seçildi.

### Üretilen Metrics Dosyaları

```text
ml-service/experiments/ml_metrics/baseline_model_metrics.csv
ml-service/experiments/ml_metrics/baseline_model_metrics.json
ml-service/experiments/ml_metrics/baseline_confusion_matrices.json

### Üretilen Figure Dosyaları

ml-service/experiments/figures/baseline_accuracy_comparison.png
ml-service/experiments/figures/baseline_precision_comparison.png
ml-service/experiments/figures/baseline_recall_comparison.png
ml-service/experiments/figures/baseline_f1_comparison.png
ml-service/experiments/figures/baseline_auc_comparison.png
ml-service/experiments/figures/baseline_far_comparison.png
ml-service/experiments/figures/baseline_fpr_comparison.png
ml-service/experiments/figures/baseline_training_time_comparison.png
ml-service/experiments/figures/baseline_inference_latency_comparison.png
ml-service/experiments/figures/confusion_matrix_lightgbm.png

### Üretilen Model Artifact Dosyaları

ml-service/models/baseline/best_model.pkl
ml-service/models/baseline/feature_order.json
ml-service/models/baseline/feature_name_mapping.json
ml-service/models/baseline/label_mapping.json
ml-service/models/baseline/model_metadata.json


```markdown
## Aşama 14.4-C — Baseline Modeli Active Modele Taşıma ve FastAPI Testi

### Durum

Tamamlandı.

### Sonuç

Baseline LightGBM modeli `ml-service/models/active/` altına taşındı ve FastAPI servisi tarafından başarıyla yüklendi.

### Kanıt

```text
/health      → model_status=loaded
/model-info  → model_name=lightgbm, feature_count=38
/predict-cicddos → HTTP 200 OK


```markdown
## Aşama 14.4-D — Baseline Metrics and Figures Output Fix

### Durum

Tamamlandı.

### Sonuç

Baseline eğitim sırasında oluşan metrics dosyaları doğrulandı. Eksik kalan figure çıktıları ayrı ve tekrar çalıştırılabilir `04d_generate_baseline_figures.py` scripti ile üretildi.

### Üretilen Script

```text
ml-service/training/04d_generate_baseline_figures.py

## Aşama 14.9-B — TikZ/PGFPlots Publication Figures

### Amaç

ML ve SDN runtime metriklerini tez/makale kalitesinde LaTeX/TikZ/PGFPlots formatında üretmek.

### Üretilecek Dosyalar

```text
reports/tikz/baseline_f1_comparison.tex
reports/tikz/baseline_far_comparison.tex
reports/tikz/baseline_fpr_comparison.tex
reports/tikz/hybrid_ids_ips_architecture.tex
reports/tikz/controller_decision_fusion.tex
reports/latex_tables/baseline_model_metrics_table.tex

## Aşama 14.5 — FastAPI / Controller Feature Schema Compatibility

### Durum

Uygulanıyor.

### Amaç

CIC-DDoS2019 ile eğitilen active modelin beklediği feature set’i ile Ryu controller’ın runtime ortamda ürettiği feature set’inin doğrudan uyumlu olup olmadığını analiz etmek.

### Üretilen Script

```text
ml-service/training/08_feature_schema_compatibility.py

### Üretilen Rapor
ml-service/experiments/reports/feature_schema_compatibility_report.json

### Beklenen Karar

```markdown
## Aşama 14.9-B — TikZ/PGFPlots Publication Figures

### Durum

Uygulanıyor.

### Amaç

Baseline ML metriklerinden tez/makale kalitesinde LaTeX/TikZ/PGFPlots grafik ve tablo çıktıları üretmek.

### Üretilen Script

```text
ml-service/training/09_generate_tikz_baseline_figures.py

### Beklenen Çıktılar
reports/tikz/baseline_f1_comparison.tex
reports/tikz/baseline_far_comparison.tex
reports/tikz/baseline_fpr_comparison.tex
reports/tikz/baseline_inference_latency_comparison.tex
reports/latex_tables/baseline_model_metrics_table.tex

## Aşama 14.4-G — Balanced Dataset Validation

### Durum

Tamamlandı.

### Amaç

Attack ağırlıklı pilot veri setinden elde edilen sonuçların yanıltıcı olup olmadığını test etmek için 1:1 balanced ve 1:5 moderate imbalance veri setleri üzerinde yeniden doğrulama yapmak.

### Sonuç

38 feature LightGBM baseline ve 13 feature PSO-LightGBM modelleri balanced veri setlerinde de güçlü performans göstermiştir.

### PSO-LightGBM Balanced Validation Sonuçları

| Dataset | Feature | F1 | AUC | FPR | FAR |
|---|---:|---:|---:|---:|---:|
| pilot_imbalanced_pso | 13 | 0.999997 | 1.000000 | 0.000000 | 0.000003 |
| balanced_1to1_pso | 13 | 0.999701 | 1.000000 | 0.000000 | 0.000299 |
| balanced_1to5_pso | 13 | 0.999940 | 1.000000 | 0.000000 | 0.000060 |

### Karar

PSO-LightGBM, 13 feature ile güçlü performansını dengeli doğrulama veri setlerinde de koruduğu için active model adayı olarak seçilmiştir.

## Aşama 14.7-D — Runtime Heuristic Prediction Endpoint

### Durum

Tamamlandı.

### Amaç

FastAPI `/predict` endpoint’ini SDN controller runtime flow statistics formatına uygun hale getirmek.

### Sonuç

`/predict` endpoint’i CIC-DDoS2019 modelinden ayrılmış ve `runtime_heuristic_v1` olarak yapılandırılmıştır. Normal TCP trafiği benign/allow olarak değerlendirilmiş, yüksek UDP trafik attack/drop olarak işaretlenmiştir.

### Gözlem

Normal trafik kesilmeden tamamlanmıştır. Yüksek UDP trafik sonrasında controller önce drop, tekrar eden yüksek güvenli saldırı davranışında quarantine_candidate kararı üretmiştir.

### Üretilen Loglar

```text
logs/policy_decisions.csv
logs/mitigation_log.csv
logs/quarantine_log.csv
logs/mitigation_latency.csv


## Aşama 14.7-E — Runtime Metrics Summary ve Grafik Üretimi

### Durum

Uygulanıyor.

### Amaç

Runtime IDS/IPS testlerinden üretilen policy, mitigation, flow rule timing ve controller resource loglarını özetlemek ve tezde kullanılabilecek grafiklere dönüştürmek.

### Girdi Logları

```text
logs/policy_decisions.csv
logs/mitigation_latency.csv
logs/mitigation_log.csv
logs/quarantine_log.csv
logs/flow_rule_timing.csv

reports/runtime/runtime_summary.json
reports/runtime/runtime_policy_action_distribution.csv
reports/runtime/runtime_mitigation_latency_summary.csv
reports/runtime/runtime_flow_rule_timing_summary.csv
reports/runtime/runtime_controller_resource_summary.csv
reports/runtime/figures/*.png

logs/controller_resource_usage_observe_only.csv

## Aşama 14.7-F — Runtime LaTeX Tablo ve TikZ/PGFPlots Üretimi

### Durum

Uygulanıyor.

### Amaç

Runtime IDS/IPS deneylerinden elde edilen policy, mitigation latency, flow rule timing ve controller resource summary sonuçlarını LaTeX tablo ve TikZ/PGFPlots formatına dönüştürmek.

### Üretilen Script

```text
monitoring/generate_runtime_latex_tikz_reports.py


## Aşama 14.9-B — Decision Mode Experiments

### Durum
Tamamlandı.

### Modlar
- heuristic_only
- ml_only
- hybrid

### Ana Bulgular
Üç modda da benign trafiğin yanlışlıkla mitigation’a gitmediği görülmüştür. Heuristic-only mod daha agresif quarantine davranışı üretirken, ml_only mod bir rate-limit kararı üretmiştir. Hybrid mod false mitigation üretmeden saldırı-benzeri UDP akışlara müdahale etmiş ve bu deneyde en düşük ortalama mitigation latency değerini sağlamıştır.

### İlk Karşılaştırma Özeti
- heuristic_only: mean mitigation latency = 0.191710 ms
- ml_only: mean mitigation latency = 0.313220 ms
- hybrid: mean mitigation latency = 0.174341 ms
- benign_but_mitigated = 0 for all modes

## Aşama 14.9-D — Decision Mode Comparison Metni

### Durum
Tamamlandı.

### Karşılaştırılan Modlar
- heuristic_only
- ml_only
- hybrid

### Ana Bulgular
- Üç modda da benign_but_mitigated = 0 olarak ölçülmüştür.
- Heuristic-only mod daha agresif quarantine davranışı üretmiştir.
- ML-only mod bir adet rate_limit kararı üretmiştir.
- Hybrid mod en düşük ortalama mitigation latency değerini sağlamıştır.
- Policy row sayıları küçük farklılıklar göstermektedir; bu durum flow statistics polling ve runtime timing etkileriyle açıklanmıştır.

### Sonraki Faz
Aşama 14.10 — CICFlowMeter / NTLFlowLyzer benzeri araçlarla runtime flow feature üretimi ve gerçek ML-runtime entegrasyonu.

## Aşama 14.10-A — PCAP Yakalama ve İlk Flow CSV Pipeline

### Durum
Devam ediyor.

### Bulgular
Mininet h12 → h14 trafiği `s6-eth2` üzerinden PCAP olarak yakalanmıştır. PCAP içinde `10.10.60.12 → 10.10.40.14` trafiği doğrulanmıştır.

### Sorun
`compare_runtime_flow_schema.py` scripti ilk çalıştırmada `experiments/flow_features/flows.csv` dosyası henüz üretilmediği için FileNotFoundError vermiştir.

### Çözüm
PCAP’ten önce packet-level CSV, ardından basic flow-level CSV üretilecek. Bu dosya geçici pipeline doğrulama için kullanılacak; nihai runtime ML entegrasyonu için CICFlowMeter-style gerçek feature extraction kullanılacaktır.

### Aşama 14.10 Araç Uyumluluk Notu

Runtime trafik PCAP olarak başarıyla yakalanmıştır. PCAP içinde 51.796 UDP paket doğrulanmıştır. Python `cicflowmeter` paketi denenmiş ancak ilgili PCAP için 0 byte CSV üretmiştir. `pyflowmeter` paketi ise mevcut Python 3.8 ortamında `numpy==1.26.1` bağımlılığı nedeniyle kurulmamıştır. Ana proje ortamını bozmamak için bu araçların kurulumu ayrı Python 3.10 venv veya Docker/Java CICFlowMeter ortamına ertelenmiştir.

Mevcut aşamada basic packet-to-flow converter ile üretilen `flows.csv` üzerinden schema comparison yapılacak; nihai runtime ML entegrasyonu için CICFlowMeter-style feature extraction korunacaktır.

## Aşama 14.10-C — Runtime Flow Feature Vector Test

### Durum
Tamamlandı.

### Amaç
Mininet runtime trafiğinden yakalanan PCAP dosyasını flow-level feature vektörüne dönüştürerek aktif PSO-LightGBM modelinin `/predict-cicddos` endpoint’i üzerinden teknik çıkarım yapıp yapamadığını doğrulamak.

### Girdi
```text
experiments/pcaps/h12_to_h14_udp_s6eth2.pcap
experiments/flow_features/flows.csv
ml-service/models/active/feature_order.json

## Aşama 14.10-D — Feature Semantics Analizi

### Durum
Tamamlandı.

### Bulgular
- Basic flow CSV aktif modelin beklediği 13 feature’ın tamamını kolon düzeyinde karşılamıştır.
- Missing feature sayısı 0’dır.
- Ancak bazı feature’lar placeholder değerlerle üretilmiştir.
- Bu nedenle pipeline teknik olarak doğrulanmış, fakat nihai ML runtime performansı için CICFlowMeter-style feature extraction gerekli görülmüştür.

### Kritik Ayrım
```text
Schema compatibility: başarılı
Semantic compatibility: kısmi

## Aşama 14.10-E — CICFlowMeter-style Extractor Değerlendirmesi

### Durum
Başlatıldı.

### Gerekçe
Basic flow extractor ile aktif modelin 13 feature’ı kolon düzeyinde karşılanmıştır; ancak bazı feature’lar placeholder olduğu için semantic uyum kısmi kalmıştır. Nihai runtime ML entegrasyonu için CICFlowMeter-style feature semantics gereklidir.

### Değerlendirilecek Yollar
1. Java/Docker CICFlowMeter
2. CICFlowMeter-compatible maintained extractor
3. Custom 13-feature bidirectional flow extractor

### Karar
Ana proje Python venv’i bozulmayacaktır. Flow extractor bağımlılıkları Docker veya ayrı araç ortamında izole edilecektir.

### Kısa Vadeli Hedef
PCAP → CICFlowMeter-style CSV üretmek ve çıkan CSV’yi aktif `feature_order.json` ile karşılaştırmak.

### Uzun Vadeli Hedef
Runtime ML-only ve hybrid modların gerçek CICFlowMeter-compatible feature set’iyle çalışması.

## Aşama 14.10-F — Custom CICFlowMeter-compatible Selected Feature Extractor

### Karar
Extractor yalnızca mevcut 13 PSO-selected feature’a hardcoded şekilde bağlanmayacaktır. Bunun yerine CICFlowMeter-compatible feature üretimi yapacak, modelin ihtiyaç duyduğu feature set’i `feature_order.json` üzerinden seçecektir.

### Gerekçe
Mevcut model CIC-DDoS2019’un küçük/reduced bir bölümüyle eğitilmiştir. İleride daha büyük veya tam CIC-DDoS2019 veri setiyle model yeniden eğitildiğinde seçilen feature sayısı ve feature listesi değişebilir. Extractor’ın yeniden yazılmaması için feature üretimi genel, model input seçimi ise `feature_order.json` tabanlı olacaktır.

### İlk Sürüm
İlk sürüm aktif PSO-LightGBM modelinin beklediği 13 feature’ı destekleyecektir. Ancak mimari ileride 20, 38 veya daha fazla CICFlowMeter-style feature’a genişleyebilecek şekilde tasarlanacaktır.

## Aşama 14.10-F — Custom CICFlowMeter-compatible Selected Feature Extractor

### Durum
Tamamlandı / doğrulama aşamasında.

### Amaç
PCAP dosyalarından CICFlowMeter-style selected feature üretmek ve aktif modelin `feature_order.json` dosyasına göre model input vektörü hazırlamak.

### Üretilen Script
```text
ml-service/tools/pcap_to_cicflowmeter_features.py

## Aşama 14.10-F — Custom CICFlowMeter-compatible Selected Feature Extractor

### Durum
Tamamlandı.

### Üretilen Script
```text
ml-service/tools/pcap_to_cicflowmeter_features.py

## Aşama 14.10-G — Runtime Feature Extraction Methodology

### Durum
Tamamlandı.

### Ana Çıktılar
- `ml-service/tools/pcap_to_cicflowmeter_features.py`
- `experiments/flow_features/runtime_cicflowmeter_features.csv`
- `experiments/flow_features/runtime_selected_features.csv`
- `experiments/flow_features/runtime_selected_features_semantics_report.json`
- `experiments/results/flow_extraction/runtime_selected_feature_predictions.csv`

### Ana Bulgular
- PCAP içinden 2 bidirectional flow çıkarılmıştır.
- Selected CSV içinde 3 metadata kolonu ve 13 aktif model feature’ı bulunmaktadır.
- Missing model feature count = 0’dır.
- Runtime selected feature vektörleri `/predict-cicddos` endpoint’ine başarıyla gönderilmiştir.
- İki flow da aktif model tarafından ATTACK/DROP olarak sınıflandırılmıştır.
- Bu sonuç nihai model performansı değil, runtime ML entegrasyon doğrulaması olarak değerlendirilmiştir.

### Kritik Tasarım Kararı
Extractor yalnızca mevcut 13 feature’a hardcoded değildir. Modelin ihtiyaç duyduğu feature listesi `feature_order.json` üzerinden seçilmektedir. Bu sayede ileride daha büyük CIC-DDoS2019 veri setiyle yeniden eğitim yapıldığında extractor genişletilerek kullanılabilecektir.

### Sonraki Faz
Aşama 14.11 — Daha büyük veya tam CIC-DDoS2019 veri setiyle modelin yeniden eğitilmesi ve geliştirilmesi.

## Aşama 14.11 — Büyük/Tam CIC-DDoS2019 ile Yeniden Eğitim

### Durum
Planlandı.

### Gerekçe
Mevcut aktif model CIC-DDoS2019’un küçük/reduced bir alt kümesiyle eğitilmiştir. Bu model pipeline doğrulama ve runtime entegrasyon için kullanılmıştır. Nihai tez modeli için daha büyük ve daha temsil edici CIC-DDoS2019 verisiyle yeniden eğitim yapılacaktır.

### Hedefler
- Daha fazla saldırı türünü kapsayan büyük dataset oluşturmak
- Binary ve multiclass label yapılarını saklamak
- Benign/attack dengesizliğini kontrollü ele almak
- LightGBM, XGBoost, RF, ExtraTrees ve MLP modellerini yeniden karşılaştırmak
- PSO/HHO/GWO feature selection süreçlerini yeniden çalıştırmak
- Yeni selected feature set ile model eğitmek
- Yeni feature_order.json dosyasını runtime extractor ile test etmek
- FastAPI aktif modeli güncellemek
- ML-only ve hybrid runtime deneylerini yeni modelle tekrarlamak

### Önerilen Scriptler
```text
ml-service/training/05_build_large_cicddos_dataset.py
ml-service/training/06_profile_large_dataset.py
ml-service/training/07_train_large_baselines.py
ml-service/training/08_feature_selection_large.py
ml-service/training/09_train_large_selected_model.py
ml-service/training/10_export_large_active_model.py

## Aşama 14.11-A — CIC-DDoS2019 Cross-day Dataset Strategy

### Karar
CIC-DDoS2019 veri setindeki `CSV-01-12.zip` ana training/validation kaynağı, `CSV-03-11.zip` ise holdout testing kaynağı olarak kullanılacaktır.

### Gerekçe
Resmi CIC-DDoS2019 açıklamasında 01-12 tarafı training day, 03-11 tarafı testing day olarak sunulmaktadır. 01-12 daha fazla DDoS saldırı türü içerdiği için model eğitimi için daha uygundur. 03-11 ayrı gün olarak kullanıldığında modelin cross-day genellenebilirliği ölçülebilir.

### Özel Durumlar
- PortScan yalnızca testing day’de yer aldığı ve DDoS saldırısı olmadığı için ana binary DDoS test metriklerinden ayrı tutulacaktır.
- WebDDoS düşük hacimli olduğu için sonuçları dikkatli yorumlanacaktır.

## Dataset Scope Decision

Portmap and PortScan traffic will be excluded from the main CIC-DDoS2019 training and evaluation pipeline. The main focus remains SDN-based DDoS detection and prevention. Therefore, the holdout test set will include LDAP, MSSQL, NetBIOS, SYN, UDP and UDP-Lag, while Portmap will be filtered out from CSV-03-11.


## Aşama 14.11-B — Chunk-based Large Dataset Builder

### Gerekçe
İlk cross-day builder tüm CSV dosyalarını belleğe almaya çalıştığı için büyük CIC-DDoS2019 dosyalarında işletim sistemi tarafından sonlandırılmıştır (`Killed`). Bu nedenle dataset builder chunk-based hale getirilmiştir.

### Yeni Yaklaşım
CSV dosyaları parçalar halinde okunur, her attack type için manifest’te tanımlanan maksimum satır sayısına ulaşılana kadar örnekleme yapılır ve çıktı dosyası append modunda yazılır.

### Avantaj
- RAM kullanımı sınırlanır
- Büyük CIC-DDoS2019 dosyaları işlenebilir
- Portmap/PortScan filtrelemesi korunur
- LightGBM-safe feature name sanitization korunur

## Aşama 14.11-D — Model-ready Large Dataset Preparation

### Durum
Başlatıldı.

### Amaç
Profiling sonucunda train ve holdout tarafında sabit olduğu tespit edilen feature’ları çıkararak model eğitimine daha uygun bir büyük CIC-DDoS2019 dataset üretmek.

### Girdi
- `cicddos2019_train_01_12_sampled.csv`
- `cicddos2019_holdout_03_11_sampled.csv`
- `large_dataset_profile_report.json`

### Beklenen Çıktı
- `cicddos2019_train_01_12_model_ready.csv`
- `cicddos2019_holdout_03_11_model_ready.csv`
- `feature_order_all_features.json`
- `model_ready_large_dataset_report.json`

### Beklenen Feature Azaltımı
81 ortak feature’dan 12 sabit feature çıkarılarak yaklaşık 69 model-ready feature kalacaktır.

## Aşama 14.11-E — Large LightGBM Baseline Training

### Durum
Başlatıldı.

### Amaç
Büyük cross-day CIC-DDoS2019 dataset üzerinde LightGBM baseline modeli eğitmek.

### Girdi
- `cicddos2019_train_01_12_model_ready.csv`
- `cicddos2019_holdout_03_11_model_ready.csv`
- `feature_order_all_features.json`

### Çıktılar
- `ml-service/models/large_baseline_lightgbm/best_model.pkl`
- `ml-service/models/large_baseline_lightgbm/feature_order.json`
- `ml-service/models/large_baseline_lightgbm/model_metadata.json`
- `ml-service/experiments/ml_metrics/large_lightgbm_baseline_metrics.csv`
- `ml-service/experiments/ml_metrics/large_lightgbm_confusion_matrices.json`

### Değerlendirme
Model hem CSV-01-12 validation split üzerinde hem de CSV-03-11 holdout test üzerinde değerlendirilecektir.

## Aşama 14.12 — Large Model Comparison and Feature Reduction

### Gerekçe
Large LightGBM baseline modeli holdout testte güçlü performans göstermiştir; ancak false negative sayısı IDS/IPS bağlamında iyileştirilmesi gereken bir noktadır.

### Hedefler
1. LightGBM sonucunu görselleştirmek
2. Alternatif sınıflandırma algoritmalarını test etmek
3. Holdout false negative sayısını azaltabilecek modelleri incelemek
4. Threshold tuning ile recall/FNR dengesini analiz etmek
5. Feature importance ve feature reduction sürecine geçmek
6. Selected-feature final model oluşturmak

### Değerlendirilecek Modeller
- LightGBM
- XGBoost
- ExtraTrees
- RandomForest
- HistGradientBoosting
- LogisticRegression
- CatBoost, kuruluysa

### Kritik Metrikler
- Holdout Recall
- Holdout FNR
- Holdout FN count
- Holdout FPR
- Holdout F1-score
- Inference latency
- Feature count

## Aşama 14.12-B — LightGBM Threshold Tuning

### Durum
Tamamlandı.

### Bulgular
LightGBM holdout tahminleri üzerinde 0.50 ile 0.10 arasında farklı karar eşikleri denenmiştir. Threshold düşürülmesine rağmen false negative sayısı değişmemiştir.

### Sonuç
- FN: 33.226 olarak sabit kalmıştır.
- FNR: 0.022123 olarak sabit kalmıştır.
- Recall: 0.977877 olarak sabit kalmıştır.
- Threshold düştükçe yalnızca FP artmıştır.

### Yorum
Kaçırılan saldırı örnekleri model tarafından düşük saldırı olasılığı ile sınıflandırılmaktadır. Bu nedenle FN azaltımı için yalnızca threshold tuning yeterli değildir. Alternatif model aileleri, ensemble yöntemleri ve feature selection analizleri gereklidir.



## Aşama 14.12-C — Large Model Comparison

### Durum
Tamamlandı.

### Örneklem Yapısı
- Train sample: 1.156.863 satır
- Holdout sample: 558.838 satır
- Feature count: 69
- Threshold: 0.5

### Ana Bulgular
LightGBM holdout örnekleminde yüksek FN üretmiştir:
- FN: 22.044
- FNR: 0.043923
- Recall: 0.956077

Hata kırılımı, LightGBM false negative hatalarının büyük ölçüde SYN trafiğinde yoğunlaştığını göstermiştir:
- SYN FN: 22.042 / 100.000
- UDPLag FN: 2 / 1.873

Alternatif modeller bu sorunu ciddi biçimde azaltmıştır:
- ExtraTrees: FN=0, FP=127
- RandomForest: FN=0, FP=428
- XGBoost: FN=5, FP=14
- HistGradientBoosting: FN=5, FP=16
- SoftVoting(LightGBM+XGBoost+ExtraTrees): FN=3, FP=21

### Yorum
LightGBM’in cross-day genelleme problemi genel DDoS tespitinden ziyade SYN saldırı ailesinde yoğunlaşmaktadır. Bu nedenle final model adayları XGBoost, ExtraTrees ve soft-voting ensemble olarak belirlenmiştir.

### Sonraki Faz
En iyi adaylar full cross-day dataset üzerinde yeniden eğitilecek ve değerlendirilecektir.

## Aşama 14.12-D — Full Candidate Model Training

### Durum
Tamamlandı.

### Test Yapısı
- Train source: CIC-DDoS2019 CSV-01-12
- Holdout source: CIC-DDoS2019 CSV-03-11
- Feature count: 69
- Holdout rows: 1.558.838
- Portmap / PortScan excluded

### Full Holdout Sonuçları

| Model | Accuracy | Precision | Recall | F1-score | FPR | FNR | FP | FN |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| LightGBM | 0.978547 | 0.999850 | 0.977880 | 0.988743 | 0.003862 | 0.022120 | 220 | 33.222 |
| XGBoost | 0.999993 | 0.999995 | 0.999998 | 0.999996 | 0.000140 | 0.000002 | 8 | 3 |
| ExtraTrees | 0.999916 | 0.999913 | 1.000000 | 0.999956 | 0.002300 | 0.000000 | 131 | 0 |
| SoftVoting(LGBM+XGB+ET) | 0.999990 | 0.999992 | 0.999998 | 0.999995 | 0.000211 | 0.000002 | 12 | 3 |

### Ana Bulgular
- LightGBM modelinin cross-day holdout false negative problemi doğrulanmıştır.
- XGBoost, LightGBM’e göre FN sayısını 33.222’den 3’e düşürmüştür.
- ExtraTrees FN=0 üretmiştir; ancak FP sayısı XGBoost’a göre daha yüksektir.
- Soft voting ensemble güçlü sonuç vermiştir; ancak XGBoost tek başına daha dengeli kalmıştır.

### Karar
Full-feature final model adayı olarak XGBoost seçilecektir. ExtraTrees FN-minimizing alternatif model olarak raporlanacaktır. Soft voting ensemble ise ek karşılaştırma modeli olarak sunulacaktır.

## Aşama 14.13-B — XGBoost Top-K Ablation

### Durum
Tamamlandı.

### Senaryolar
- Normal: Tüm model-ready feature’lar içinden Top-K
- Without Inbound: `Inbound` çıkarıldıktan sonra Top-K
- Without Inbound + Ports: `Inbound`, `Source_Port`, `Destination_Port` çıkarıldıktan sonra Top-K

### Ana Bulgular
Normal Top-20 XGBoost modeli en iyi dengeyi sağlamıştır:
- Feature count: 20
- Accuracy: 0.999994
- Precision: 0.999995
- Recall: 0.999998
- F1-score: 0.999997
- FPR: 0.000123
- FNR: 0.000002
- FP: 7
- FN: 3

Full 69-feature XGBoost modeline göre:
- FN aynı kalmıştır: 3
- FP 8’den 7’ye düşmüştür
- Feature count 69’dan 20’ye düşmüştür

### Ablation Yorumu
`Inbound` çıkarıldığında FN düşük kalmış; ancak FP belirgin biçimde artmıştır. Bu durum `Inbound` özelliğinin özellikle false alarm oranını azaltmada etkili olduğunu göstermektedir.

### Karar
Final selected-feature model adayı olarak `xgboost_normal_top_20` seçilecektir.

## Aşama 14.13-C — Final XGBoost Top-20 Model Export

### Durum
Başlatıldı / tamamlanacak.

### Seçilen Model
`xgboost_normal_top_20`

### Gerekçe
- 69 feature yerine 20 feature kullanılmıştır.
- Full holdout testte FN sayısı korunmuştur: 3.
- FP sayısı 8’den 7’ye düşmüştür.
- FPR: 0.000123
- FNR: 0.000002
- F1-score: 0.999997

### Çıktı Klasörü
`ml-service/models/final_xgboost_top20/`

### Çıktı Dosyaları
- `best_model.pkl`
- `feature_order.json`
- `label_mapping.json`
- `training_metrics.json`
- `model_metadata.json`

### Not
Source IP ve Destination IP feature set’e dahil değildir. Inbound feature’ı final modelde korunmuştur; ablation deneyleri Inbound çıkarıldığında false positive sayısının ciddi biçimde arttığını göstermiştir.

## Aşama 14.13-D — Final XGBoost Top-20 Active Model Deployment

### Durum
Tamamlandı.

### Aktif Model
`final_xgboost_top20`

### Endpoint Testleri
- `/health`: başarılı
- `/model-info`: model loaded
- `/predict-cicddos`: başarılı
- Tekil benign örnek: BENIGN / ALLOW
- Tekil attack örnek: ATTACK / DROP
- 1000 satırlık API test: 1000/1000 doğru

### Not
Active model klasörü `model.pkl` dosyası beklediği için `best_model.pkl` ayrıca `model.pkl` adıyla kopyalanmıştır.

## Aşama 14.13-E — Runtime Extractor for Final XGBoost Top-20

### Durum
Başlatıldı.

### Sorun
Mevcut runtime flow CSV yalnızca 10/20 final model feature’ını karşılıyordu. Eksik feature’lar:
- Active_Max
- Active_Mean
- Bwd_Header_Length
- Bwd_Packet_Length_Max
- Bwd_Packet_Length_Min
- Fwd_PSH_Flags
- Fwd_Packets_s
- Min_Packet_Length
- act_data_pkt_fwd
- min_seg_size_forward

### Çözüm
`pcap_to_final_top20_features.py` scripti oluşturularak final modelin beklediği 20 feature’ın tamamı pcap üzerinden üretilir hale getirilecektir.

### Beklenen Çıktı
- `experiments/flow_features/final_top20_flows.csv`
- Schema check: Matched=20, Missing=0
- Active model prediction test: başarılı

## Aşama 14.13-E — Runtime Extractor for Final XGBoost Top-20

### Durum
Tamamlandı.

### Amaç
Final seçilen `final_xgboost_top20` modelinin beklediği 20 feature’ın runtime PCAP üzerinden üretilebilirliğini test etmek.

### Girdi
- PCAP: `experiments/pcaps/h12_to_h14_udp_s6eth2.pcap`
- Active feature order: `ml-service/models/active/feature_order.json`

### Çıktı
- `experiments/flow_features/final_top20_flows.csv`
- `experiments/flow_features/final_top20_flows.schema_report.json`
- `experiments/results/flow_extraction/final_top20_runtime_predictions.csv`

### Schema Sonucu
- Expected feature count: 20
- Matched: 20
- Missing: 0
- Extra: 2 metadata column (`Source_IP`, `Destination_IP`)

### Prediction Sonucu
İki runtime flow da aktif final model tarafından ATTACK olarak sınıflandırılmıştır:
- Flow 1: attack_probability = 0.999979, action = DROP
- Flow 2: attack_probability = 0.995483, action = DROP

### Yorum
Final selected-feature modelin runtime extraction tarafında kullanılabilir olduğu doğrulanmıştır.

## Aşama 14.13-F — Final Top-20 Runtime ML Pipeline

### Durum
Başlatıldı.

### Amaç
Final XGBoost Top-20 modelinin runtime PCAP tabanlı akışta uçtan uca kullanılabilirliğini tek komutla test etmek.

### Pipeline
PCAP → final Top-20 feature extraction → schema validation → active FastAPI prediction → report

### Script
`ml-service/tools/run_final_top20_runtime_pipeline.py`

### Beklenen Çıktılar
- `final_top20_flows.csv`
- `final_top20_flows.schema_report.json`
- `final_top20_runtime_predictions.csv`
- `runtime_pipeline_summary.json`
- `runtime_pipeline_report.md`

### Başarı Kriterleri
- Schema matched: 20/20
- Missing features: 0
- Active model status: loaded
- Prediction endpoint returns valid ATTACK/BENIGN decisions

## Aşama 14.14-A/B — Runtime Prediction to Policy Decision Conversion

### Durum
Başlatıldı.

### Amaç
Final Top-20 runtime ML prediction çıktısını controller policy decision formatına yaklaştırmak.

### Girdi
- `final_top20_runtime_predictions.csv`

### Çıktılar
- `final_top20_policy_decisions.csv`
- `final_top20_policy_decisions_summary.json`
- `final_top20_policy_decisions_report.md`

### Beklenen Sonuç
Runtime prediction çıktısındaki ATTACK/DROP kararları controller benzeri policy decision formatına dönüştürülür.

### Sonraki Faz
Controller policy engine ve mitigation logları ile final Top-20 runtime policy kararlarının karşılaştırılması.

## Aşama 14.14-C — Controller Policy Compatibility

### Durum
Tamamlandı.

### Bulgular
Controller `policy_decisions.csv` dosyasında `src_port` ve `dst_port` alanları bulunmamaktadır. Bu nedenle final Top-20 runtime pipeline çıktılarıyla birebir flow-key eşleşmesi yapılamamıştır.

### Controller Log Şeması
Controller policy logları şu düzeyde karar üretmektedir:
- `ipv4_src`
- `ipv4_dst`
- `ip_proto`
- `packet_rate`
- `byte_rate`
- `ml_prediction`
- `ml_confidence`
- `ml_recommended_action`
- `policy_final_action`

### Final Top-20 Pipeline Şeması
Final pipeline şu düzeyde karar üretmektedir:
- `src_ip`
- `dst_ip`
- `src_port`
- `dst_port`
- `prediction`
- `attack_probability`
- `policy_final_action`

### Sonuç
Exact flow match yapılamamıştır; çünkü controller logları port-aware değildir. Ancak IP/protocol/action düzeyinde final Top-20 pipeline kararları ile controller mitigation logları aynı saldırı akışını işaret etmektedir:
- `10.10.60.12 → 10.10.40.14`
- `ip_proto=17`
- `DROP`

### Sonraki Gereksinim
Controller log şeması `src_port` ve `dst_port` alanlarıyla genişletilmelidir.

## Aşama 14.14-D — Controller Log Schema Alignment

### Durum
Tamamlandı.

### Amaç
Controller loglarının final Top-20 runtime ML pipeline çıktılarıyla daha iyi karşılaştırılabilmesi için port-aware hale getirilmesi.

### Yapılan Değişiklik
Aşağıdaki log dosyalarına `src_port` ve `dst_port` kolonları eklendi:
- `policy_decisions.csv`
- `mitigation_log.csv`
- `rate_limit_log.csv`
- `quarantine_log.csv`

### Doğrulama
Yeni hybrid controller run sonucunda tüm log dosyalarının header’larında `src_port` ve `dst_port` kolonlarının oluştuğu doğrulanmıştır.

### Sonuç
- `policy_decisions.csv`: 2266 satır
- `mitigation_log.csv`: 7 satır
- `quarantine_log.csv`: 7 satır
- `rate_limit_log.csv`: 1 satır

### Not
Mevcut controller sürümü henüz gerçek TCP/UDP port bilgisini üretmediği için `src_port` ve `dst_port` değerleri şimdilik `0` olarak yazılmaktadır. Sonraki aşamada port bilgisinin PacketIn veya OpenFlow match üzerinden çıkarılması planlanmaktadır.

## Aşama 14.14-E — Final Model Hybrid Controller Run Summary

### Durum
Başlatıldı.

### Amaç
Final model aktifken çalıştırılan hybrid controller run sonuçlarını deney raporu haline getirmek.

### Girdi
`experiments/results/final_model_controller_tests/hybrid_<timestamp>/`

### Çıktılar
- `controller_final_model_summary.json`
- `controller_final_model_summary.md`

### Özetlenecek Alanlar
- Policy decision action dağılımı
- ML prediction dağılımı
- Mitigation/drop/rate-limit/quarantine sayıları
- Port-aware schema doğrulaması
- Source-destination bazlı karar özeti

### Beklenen Sonuç
Controller logları final model sonrası port-aware şemaya sahip olacak ve hybrid policy kararları raporlanacaktır.

## Aşama 14.15-A — FlowStats Match Port Extraction

### Durum
Tamamlandı.

### Yapılan İş
Controller’a `extract_transport_ports_from_match()` fonksiyonu eklendi. FlowStats içindeki `stat.match` alanlarından `tcp_src`, `tcp_dst`, `udp_src`, `udp_dst` değerleri okunmaya çalışıldı.

### Deney Sonucu
Yeni hybrid run:
`experiments/results/final_model_controller_tests/hybrid_20260513_235333`

Port kontrolü:
- `policy_decisions.csv`: src_port=[0], dst_port=[0]
- `mitigation_log.csv`: src_port=[0], dst_port=[0]
- `rate_limit_log.csv`: src_port=[0], dst_port=[0]
- `quarantine_log.csv`: src_port=[0], dst_port=[0]

### Yorum
FlowStats match alanlarında transport-layer port bilgisi bulunmadığı görülmüştür. Bu nedenle gerçek port bilgisini elde etmek için PacketIn tabanlı port cache mekanizmasına geçilecektir.

## Aşama 14.15-B — PacketIn Port Cache

### Durum
Tamamlandı.

### Amaç
Controller’ın FlowStats tabanlı IDS/IPS kararlarına gerçek TCP/UDP port bilgisini taşıması.

### Yapılan İş
- `tcp` ve `udp` packet parser import edildi.
- `transport_port_cache` eklendi.
- PacketIn sırasında TCP/UDP portları yakalandı.
- FlowStats sırasında `stat.match` içinde port yoksa cache üzerinden port çözümü yapıldı.
- `policy_decisions.csv`, `mitigation_log.csv`, `quarantine_log.csv` port-aware hale getirildi.

### Doğrulanan Akış
`10.10.60.12:32895 → 10.10.40.14:5201`, `ip_proto=17`

### Deney Sonucu
- `policy_decisions.csv`: port bilgisi başarıyla yazıldı.
- `mitigation_log.csv`: DROP loglarında port bilgisi başarıyla yazıldı.
- `quarantine_log.csv`: quarantine forwarding loglarında port bilgisi başarıyla yazıldı.
- `rate_limit_log.csv`: bu run’da rate-limit oluşmadığı için boş kaldı.

### Yorum
Controller artık PacketIn tabanlı port cache ile FlowStats kararlarına transport-layer port bilgisini taşıyabilmektedir. Bu, final Top-20 runtime pipeline ile controller loglarının flow-key düzeyinde karşılaştırılmasını mümkün hale getirmiştir.

## Aşama 14.16-A — Existing Final Pipeline vs Port-Aware Controller Comparison

### Durum
Tamamlandı.

### Sonuç
Port-aware karşılaştırma scripti başarıyla çalıştı.

### Girdi
- Final Top-20 runtime pipeline: eski PCAP/run
- Controller policy logs: yeni port-cache hybrid run

### Bulgular
- Final pipeline action: `DROP = 2`
- Controller policy actions:
  - `allow = 3083`
  - `quarantine_candidate = 11`
  - `drop = 2`
  - `monitor = 1`
- Controller mitigation:
  - `drop = 7`
- Controller quarantine:
  - `quarantine_candidate = 7`

### Eşleşme
- Exact flow-key match: `0`
- IP-port relaxed match: `0`

### Yorum
Bu sonuç hata değildir. Final Top-20 pipeline ve controller logları farklı trafik çalıştırmalarından geldiği için ephemeral UDP source port değerleri farklıdır. Bu nedenle port-aware flow-key düzeyinde eşleşme oluşmamıştır.

## Aşama 14.16-B — Same-Run Port-Aware Final Pipeline vs Controller Comparison

### Durum
Tamamlandı.

### Girdi
Aynı Mininet çalıştırmasından elde edilen:
- PCAP tabanlı Final Top-20 runtime pipeline çıktısı
- Controller policy logları
- Controller mitigation logları
- Controller quarantine logları

### Eşleşme Anahtarı
`src_ip | dst_ip | src_port | dst_port`

### Genel Sonuçlar
- Final policy rows: `2`
- Controller policy rows: `3015`
- Mitigation log rows: `7`
- Quarantine log rows: `7`
- Relaxed IP-port controller matches: `2`
- Matched DROP mitigation logs: `1`
- Matched quarantine logs: `1`

### Kritik UDP Veri Akışı
`10.10.60.12:40205 → 10.10.40.14:5201`

Final Top-20 modeli:
- prediction: `ATTACK`
- attack_probability: `0.9942249655723572`
- final_action: `DROP`

Controller:
- prediction: `attack`
- confidence: `0.98`
- final_action: `quarantine_candidate`
- matched_mitigation_drop: `True`
- matched_quarantine: `True`

### Yorum
Bu sonuç, PacketIn tabanlı port cache mekanizması sonrasında controller logları ile PCAP tabanlı final ML pipeline çıktılarının flow-key düzeyinde karşılaştırılabildiğini göstermektedir. UDP veri akışı için hem external ML pipeline hem de controller policy/mitigation hattı saldırı davranışını yakalamıştır.


## Aşama 14.17 — UDP-aware Final Policy ve Security-Compatible Comparison

### Durum
Tamamlandı.

### Amaç
Final Top-20 runtime pipeline çıktısında iperf3 TCP kontrol akışı ile UDP veri akışını ayırmak ve controller policy çıktılarıyla daha adil bir karşılaştırma yapmak.

### Genel Sonuçlar
- Final policy rows: `2`
- Controller policy rows: `3015`
- Relaxed IP-port controller matches: `2`
- Security-compatible action matches: `2`
- Matched DROP mitigation logs: `1`
- Matched quarantine logs: `1`

### Final Action Dağılımı
- `ALLOW_CONTROL_FLOW`: `1`
- `DROP`: `1`

### Controller Action Dağılımı
- `allow`: `3009`
- `quarantine_candidate`: `3`
- `drop`: `2`
- `monitor`: `1`

### Flow-Level Bulgular

#### TCP Control Flow
`10.10.60.12:41664 → 10.10.40.14:5201`

- Final UDP-aware action: `ALLOW_CONTROL_FLOW`
- Controller action: `allow`
- Security-compatible: `True`

Bu akış iperf3 kontrol bağlantısı olarak ele alındı. Final model ham tahmininde `ATTACK` dese de UDP-aware policy bu akışı veri saldırı akışı olarak değerlendirmeyip `ALLOW_CONTROL_FLOW` verdi. Controller da aynı flow için `allow` kararı verdi.

#### UDP Data Flow
`10.10.60.12:40205 → 10.10.40.14:5201`

- Final UDP-aware action: `DROP`
- Controller action: `quarantine_candidate`
- Controller prediction: `attack`
- Controller confidence: `0.98`
- Matched DROP mitigation: `True`
- Matched quarantine: `True`
- Security-compatible: `True`

Bu akış asıl UDP saldırı/veri akışıdır. Final XGBoost Top-20 modeli saldırı olarak işaretlemiş, controller ise aynı akış için önce DROP mitigation üretmiş, ardından tekrarlı yüksek güven nedeniyle quarantine seviyesine yükseltmiştir.

Aşama 15.3 tamamlandı:
Mixed benign + malicious traffic experiment was executed. The final XGBoost Top-20 model classified benign flows as benign and malicious UDP flows as attack. The Ryu hybrid IDS/IPS controller produced security-compatible mitigation actions including rate-limit, drop, and quarantine forwarding.



---

## Aşama 15.4 — Mixed Benign and Malicious Runtime Traffic Experiment

Bu aşamada, geliştirilen SDN tabanlı IDS/IPS prototipi karma benign ve zararlı trafik altında test edilmiştir. Amaç, yalnızca offline model başarısını değil, aynı zamanda runtime SDN ortamında tespit, karar üretimi ve önleme mekanizmalarının birlikte çalıştığını göstermektir.

### Yapılanlar

- Mininet/Ryu tabanlı kampüs SDN test ortamı kullanıldı.
- Benign TCP/UDP trafik ile zararlı yüksek hacimli UDP trafik aynı deney içinde üretildi.
- Trafik `tcpdump` ile PCAP olarak yakalandı.
- PCAP dosyası Final XGBoost Top-20 runtime pipeline üzerinden işlendi.
- PCAP içinden seçilmiş 20 özellik çıkarıldı.
- Aktif model `final_xgboost_top20` ile flow bazlı tahmin yapıldı.
- Ryu controller tarafındaki `policy_decisions.csv`, `mitigation_log.csv`, `rate_limit_log.csv` ve `quarantine_log.csv` çıktıları toplandı.
- Final ML pipeline kararları ile controller policy kararları port-aware ve protocol-aware olarak karşılaştırıldı.
- Deney özeti ve raporu üretildi:
  - `mixed_traffic_experiment_report.md`
  - `mixed_traffic_experiment_summary.json`

### Öne çıkan sonuçlar

- Final runtime pipeline 7 flow çıkardı.
- Bu flowların 4 tanesi benign, 3 tanesi attack olarak sınıflandırıldı.
- Benign/control akışlar `ALLOW` veya `ALLOW_CONTROL_FLOW` olarak yorumlandı.
- Zararlı UDP akış `DROP` olarak işaretlendi.
- Controller tarafında saldırı davranışı için `rate_limit`, `drop` ve `quarantine_candidate` aksiyonları üretildi.
- Protocol-aware karşılaştırmada 5 exact controller flow-key match elde edildi.
- Security-compatible action count değeri 5 olarak raporlandı.
- Zararlı UDP akış için drop, quarantine ve rate-limit loglarıyla eşleşme sağlandı.

### Tez açısından önemi

Bu aşama, önerilen mimarinin yalnızca offline CIC-DDoS2019 modeliyle sınıflandırma yapan bir yapı olmadığını; aynı zamanda canlı SDN test ortamında karma trafik altında IDS/IPS davranışı gösterebildiğini ortaya koymuştur.

Bu deney, doktora tezinin yöntem ve deneysel doğrulama bölümlerinde şu iddiayı destekler:

> Önerilen SDN tabanlı hibrit IDS/IPS mimarisi, benign trafiği korurken yüksek hacimli UDP tabanlı zararlı trafiği tespit edebilmekte ve controller seviyesinde rate-limit, drop ve quarantine aksiyonlarıyla güvenlik açısından uyumlu önleme davranışı üretebilmektedir.

### Üretilen dosyalar

- `experiments/results/mixed_traffic_experiments/20260515_134819_mixed_benign_malicious_replay_v1/mixed_traffic_experiment_report.md`
- `experiments/results/mixed_traffic_experiments/20260515_134819_mixed_benign_malicious_replay_v1/mixed_traffic_experiment_summary.json`
- `experiments/results/mixed_traffic_experiments/20260515_134819_mixed_benign_malicious_replay_v1/runtime_pipeline/20260515_105336_mixed_benign_malicious_live_final_top20/runtime_pipeline_report.md`
- `experiments/results/mixed_traffic_experiments/20260515_134819_mixed_benign_malicious_replay_v1/comparison/port_aware_protocol_aware_v2/final_top20_vs_port_aware_controller_report.md`

### Durum

Tamamlandı.


---

## Aşama 15.5-B — Protocol-Aware Final Policy Builder

Bu aşamada, Final XGBoost Top-20 runtime pipeline çıktılarının controller logları ile daha doğru karşılaştırılabilmesi için protocol-aware final policy üretimi kalıcı bir araca dönüştürülmüştür.

### Yapılanlar

- `ml-service/tools/build_protocol_aware_final_policy.py` aracı oluşturuldu.
- Araç, `final_top20_runtime_predictions.csv` dosyasını ve aynı deneyde yakalanan PCAP dosyasını birlikte kullanmaktadır.
- PCAP içinden TCP/UDP protokol bilgisi `tcpdump` üzerinden çıkarılmaktadır.
- Flow bazında `ip_proto` ve `proto_packet_count` alanları üretilmektedir.
- TCP tabanlı iperf3 control/control-like akışlar `ALLOW_CONTROL_FLOW` olarak yorumlanmaktadır.
- UDP saldırı akışları model çıktısına göre `DROP` olarak korunmaktadır.
- Quarantine IP yönüne giden akışlar `QUARANTINE_OBSERVED` olarak ayrıştırılmaktadır.
- Bu çıktı, port-aware ve protocol-aware controller karşılaştırmasına girdi olarak kullanılabilir hale getirilmiştir.
- `prepare_traffic_scenario_run.py` script’i güncellenerek scenario runner komut zincirine protocol-aware policy üretimi eklenmiştir.

### Üretilen / Güncellenen Dosyalar

- `ml-service/tools/build_protocol_aware_final_policy.py`
- `ml-service/tools/prepare_traffic_scenario_run.py`
- `final_top20_policy_decisions_protocol_aware.csv`
- `final_top20_policy_decisions_protocol_aware.summary.json`

### Tez Açısından Önemi

Bu adım, PCAP tabanlı model çıktıları ile SDN controller tarafından üretilen policy ve enforcement logları arasındaki karşılaştırmanın daha metodolojik yapılmasını sağlar. Özellikle TCP control flow, UDP attack flow ve quarantine sonrası gözlenen akışların ayrıştırılması, deneysel doğrulama sonuçlarının tezde daha savunulabilir şekilde yorumlanmasına katkı sağlar.

### Durum

Tamamlandı.


---

## Aşama 15.5-C — Scenario Manifest and Reproducibility Checklist

Bu aşamada, mixed benign/malicious runtime deneylerinin tekrar üretilebilir ve akademik olarak izlenebilir hale getirilmesi için deney manifestosu ve reproducibility checklist üretimi eklendi.

### Yapılanlar

- `ml-service/tools/generate_experiment_manifest.py` aracı oluşturuldu.
- Her deney klasörü için `experiment_manifest.json` ve `experiment_manifest.md` çıktıları üretilebilir hale getirildi.
- Manifest içinde deney klasörü, runtime pipeline klasörü, comparison klasörü, senaryo dosyası, controller dosyası ve kullanılan model bilgileri kayıt altına alındı.
- PCAP, controller logları, final runtime prediction çıktıları, protocol-aware final policy çıktısı, comparison raporu ve mixed traffic raporu tek bir manifest dosyasında ilişkilendirildi.
- Row count değerleri, temel comparison metrikleri ve reproducibility checklist otomatik üretildi.
- Scenario runner komut zincirine manifest üretimi eklenmesi planlandı / uygulandı.

### Üretilen Dosyalar

- `ml-service/tools/generate_experiment_manifest.py`
- `experiment_manifest.json`
- `experiment_manifest.md`

### Tez Açısından Önemi

Bu aşama, deneylerin yalnızca sonuç üretmesini değil, aynı zamanda aynı koşullar altında tekrar çalıştırılabilir ve savunulabilir olmasını sağlar. Tez savunmasında "Bu deney nasıl üretildi?", "Hangi model kullanıldı?", "Hangi PCAP ve loglar karşılaştırıldı?", "Controller hangi modda çalıştı?" gibi sorulara doğrudan yanıt verir.

### Durum

Tamamlandı.


---

## Aşama 15.5-D — Multi-Run Mixed Traffic Experiment Aggregation

Bu aşamada, mixed benign/malicious runtime deneylerinin birden fazla koşu üzerinden analiz edilebilmesi için aggregate raporlama altyapısı eklenmiştir.

### Yapılanlar

- `ml-service/tools/aggregate_mixed_traffic_runs.py` aracı oluşturuldu.
- Araç, `mixed_traffic_experiment_summary.json` dosyalarını deney klasörlerinden otomatik olarak toplar.
- Her koşu için controller policy, flow stats, prediction, mitigation, quarantine, rate-limit ve comparison metriklerini tek tabloya indirger.
- Çoklu koşular için ortalama, standart sapma, minimum, maksimum ve toplam değerler hesaplanır.
- CSV, JSON ve Markdown formatlarında aggregate rapor üretir.
- Bu yapı, aynı senaryonun 3 veya 5 kez tekrar edilmesiyle tezde daha güçlü istatistiksel değerlendirme yapılmasına imkân sağlar.

### Üretilen Dosyalar

- `ml-service/tools/aggregate_mixed_traffic_runs.py`
- `experiments/results/mixed_traffic_experiments/aggregate_reports/mixed_traffic_multi_run_summary_*.csv`
- `experiments/results/mixed_traffic_experiments/aggregate_reports/mixed_traffic_multi_run_summary_*.json`
- `experiments/results/mixed_traffic_experiments/aggregate_reports/mixed_traffic_multi_run_report_*.md`

### Tez Açısından Önemi

Bu aşama, sistemin yalnızca tek bir deney koşusunda değil, tekrarlandığında da benzer güvenlik davranışları üretip üretmediğini değerlendirmek için gereklidir. Böylece benign trafik koruma, saldırı tespiti, rate-limit, drop ve quarantine enforcement mekanizmaları çoklu koşular üzerinden raporlanabilir.

### Durum

Tamamlandı / İlk tek koşu ile test edilecek.


---

## Aşama 15.5-C — Mixed Traffic Runtime Validation Experiment

Bu aşamada SDN tabanlı IDS/IPS prototipi, benign ve malicious trafiklerin aynı deney koşusunda birlikte üretildiği karma trafik senaryosu altında test edilmiştir.

### Amaç

Bu deneyin amacı, offline olarak eğitilmiş Final XGBoost Top-20 modelinin, PCAP tabanlı runtime feature extraction pipeline'ı ve Ryu controller üzerindeki hybrid IDS/IPS policy engine ile birlikte aynı trafik örneği üzerinde tutarlı ve güvenlik açısından uyumlu kararlar üretip üretmediğini doğrulamaktır.

### Deney Senaryosu

- Benign trafik kaynakları:
  - `10.10.10.2`
  - `10.10.10.3`
- Hedef sunucu:
  - `10.10.40.14`
- Zararlı trafik kaynağı:
  - `10.10.60.12`
- Quarantine host:
  - `10.10.99.16`

Senaryo içinde TCP control/control-like akışlar, benign TCP/UDP trafikler ve yüksek hacimli UDP saldırı akışı birlikte gözlenmiştir.

### Kullanılan Bileşenler

- Mininet tabanlı kampüs ağı topolojisi
- Ryu tabanlı SDN controller
- Hybrid IDS/IPS decision mode
- Final XGBoost Top-20 ML modeli
- PCAP tabanlı runtime feature extraction pipeline
- Protocol-aware final policy builder
- Port-aware/protocol-aware controller comparison aracı

### Başarılı Deney Dizini

- `experiments/results/mixed_traffic_experiments/repeated_mixed_runtime_20260516_130204/run_03_aligned_clean`

### Temel Sonuçlar

- Controller policy decision satırı: `3219`
- Flow stats satırı: `11078`
- Final runtime prediction satırı: `9`
- Controller allow kararı: `3206`
- Controller drop kararı: `2`
- Controller quarantine_candidate kararı: `10`
- OpenFlow drop mitigation log satırı: `7`
- Quarantine forwarding log satırı: `7`
- Rate-limit log satırı: `0`
- Exact controller flow-key match: `5`
- Security-compatible action count: `5`
- Matched mitigation drop count: `1`
- Matched quarantine count: `1`

### Yorum

Deney sonucunda benign ve control-flow akışların korunabildiği, zararlı UDP akışının ise controller tarafından drop ve quarantine mekanizmalarıyla ele alındığı görülmüştür. Bu koşuda rate-limit gözlenmemiştir; çünkü saldırı akışı kısa sürede yüksek güven skoruna ulaşarak drop ve ardından quarantine_candidate seviyesine yükselmiştir.

### Tez Açısından Önemi

Bu aşama, çalışmanın yalnızca offline sınıflandırma başarısına dayanmadığını göstermektedir. Aynı trafik koşusunda PCAP yakalama, seçilmiş özellik çıkarımı, Final Top-20 XGBoost çıkarımı, controller-side policy decision ve OpenFlow tabanlı mitigation mekanizmalarının birlikte çalıştığı gösterilmiştir. Bu nedenle tezde yöntem ve deneysel doğrulama bölümleri için güçlü bir runtime validation kanıtı üretmektedir.

### Durum

Tamamlandı.


---

## Aşama 15.7 — Clean Mixed-Traffic Runtime Validation and Aggregate Reporting

Bu aşamada, benign ve malicious trafik içeren karma bir runtime deney koşusu temizlenmiş, protokol-duyarlı final policy çıktısı ile SDN controller logları karşılaştırılmış ve tezde kullanılabilecek deney raporları üretilmiştir.

### Deney Koşusu

- Deney dizini: `experiments/results/mixed_traffic_experiments/repeated_mixed_runtime_20260516_130204/run_03_aligned_clean`
- Runtime pipeline dizini: `runtime_pipeline/20260518_182719_mixed_benign_malicious_live_final_top20_run_03_aligned_clean_api_ok`
- Karşılaştırma dizini: `comparison/port_aware_protocol_aware_api_ok`
- Kullanılan PCAP: `pcaps/mixed_benign_malicious_live_5201_only.pcap`
- Rapor: `mixed_traffic_experiment_report.md`
- Özet: `mixed_traffic_experiment_summary.json`

### Trafik Senaryosu

- Benign trafik kaynakları:
  - `10.10.10.2 -> 10.10.40.14`
  - `10.10.10.3 -> 10.10.40.14`
- Zararlı trafik kaynağı:
  - `10.10.60.12 -> 10.10.40.14`
- Quarantine host:
  - `10.10.99.16`

### Elde Edilen Temel Çıktılar

- Controller policy kararları: `3219`
- Flow statistics satırları: `11078`
- Runtime Final Top-20 prediction satırları: `9`
- Protocol-aware final policy satırları: `9`
- Comparison satırları: `9`

### Controller Action Dağılımı

- `allow`: `3206`
- `drop`: `2`
- `quarantine_candidate`: `10`
- `monitor`: `1`
- `rate_limit`: `0`

### Enforcement Logları

- Drop mitigation log satırı: `7`
- Quarantine log satırı: `7`
- Rate-limit log satırı: `0`

### Final Top-20 Runtime Model Sonucu

Final XGBoost Top-20 modeli PCAP tabanlı runtime feature extraction çıktıları üzerinde benign ve attack akışlarını ayırmıştır. Protocol-aware final policy çıktısında TCP control/control-like akışlar `ALLOW_CONTROL_FLOW`, benign UDP akışlar `ALLOW`, zararlı UDP akış ise `DROP` olarak yorumlanmıştır. Quarantine sonrasında gözlenen akış `QUARANTINE_OBSERVED` olarak ayrıştırılmıştır.

### Controller ile Karşılaştırma Sonucu

- Exact controller flow-key match: `5`
- Relaxed IP-port match: `5`
- Security-compatible action count: `5`
- Matched DROP mitigation: `1`
- Matched quarantine: `1`
- Matched rate-limit: `0`

### Yorum

Bu sonuçlar, karma trafik altında benign/control akışların korunabildiğini ve yüksek hacimli malicious UDP akışın controller tarafında drop ve quarantine mekanizmalarıyla karşılandığını göstermektedir. Bu koşuda rate-limit tetiklenmemiştir; çünkü malicious UDP akış kısa sürede daha yüksek şiddette mitigation olan quarantine aşamasına yükselmiştir.

### Tez Açısından Önemi

Bu aşama, yalnızca offline sınıflandırma başarısını değil, PCAP yakalama, runtime feature extraction, aktif XGBoost modeli ile tahmin, protocol-aware final policy üretimi, Ryu controller policy kararı ve OpenFlow tabanlı mitigation zincirini birlikte doğrulamaktadır. Bu nedenle yöntem ve deneysel sonuçlar bölümü için kullanılabilecek güçlü bir uçtan uca runtime doğrulama çıktısı üretmiştir.

### Durum

Tamamlandı.


---

## Aşama 16 — Mixed Traffic Runtime Validation Experiment Documentation

Bu aşamada, benign ve malicious trafiğin birlikte üretildiği karma trafik senaryosu başarıyla doğrulanmış ve tez/makale çıktıları için raporlanabilir hale getirilmiştir.

### Canonical Successful Run

- Deney: `run_03_aligned_clean`
- Dizin: `experiments/results/mixed_traffic_experiments/repeated_mixed_runtime_20260516_130204/run_03_aligned_clean`

### Temel Bulgular

- Benign TCP/UDP trafik korunmuştur.
- Malicious UDP trafik Final XGBoost Top-20 modeli tarafından saldırı olarak sınıflandırılmıştır.
- Controller tarafında malicious UDP akış için drop ve quarantine mekanizmaları gözlenmiştir.
- Rate-limit bu koşuda tetiklenmemiştir; saldırı akışı doğrudan drop ve quarantine_candidate seviyesine yükselmiştir.
- Protocol-aware final policy üretimi sayesinde TCP control flow, UDP benign flow, UDP attack flow ve quarantine-observed flow ayrıştırılmıştır.
- Final model çıktıları ile controller policy/enforcement logları arasında güvenlik açısından uyumlu sonuçlar elde edilmiştir.

### Üretilen Çıktılar

- `mixed_traffic_experiment_report.md`
- `mixed_traffic_experiment_summary.json`
- `final_top20_policy_decisions_protocol_aware.csv`
- `final_top20_vs_port_aware_controller_comparison.csv`
- `final_top20_vs_port_aware_controller_report.md`
- `artifacts_manifest.md`
- `experiment_status.json`

### Tez Açısından Önemi

Bu aşama, önerilen SDN tabanlı ML destekli IDS/IPS mimarisinin yalnızca offline sınıflandırma başarımıyla sınırlı kalmadığını; runtime ortamda trafik üretimi, PCAP yakalama, özellik çıkarımı, model çıkarımı, controller kararı ve OpenFlow tabanlı mitigation zinciriyle uçtan uca çalışabildiğini göstermektedir.

### Durum

Tamamlandı.


---

## Aşama 17 — Canonical Mixed Traffic Runtime Experiment Packaging

Bu aşamada, daha önce başarıyla tamamlanan `run_03_aligned_clean` karma trafik deneyi tez ve makale yazımı için paketlenmiş ve canonical başarılı deney olarak işaretlenmiştir.

### Yapılanlar

- `run_03_aligned_clean` başarılı deney koşusu olarak seçildi.
- Deneyin durumunu tanımlayan `experiment_status.json` dosyası oluşturuldu.
- Tez/makale yazımında kullanılacak çıktıların listelendiği `artifacts_manifest.md` dosyası oluşturuldu.
- Runtime model çıktıları, protocol-aware final policy dosyaları, controller logları ve karşılaştırma raporları bir arada belgelenmiştir.
- Drop ve quarantine mekanizmalarının gözlendiği; rate-limit mekanizmasının ise bu koşuda tetiklenmediği açık şekilde not edilmiştir.

### Canonical Run

- `experiments/results/mixed_traffic_experiments/repeated_mixed_runtime_20260516_130204/run_03_aligned_clean`

### Tez Açısından Önemi

Bu aşama, deneysel çalışmanın yeniden izlenebilirliğini artırır. Hangi CSV, JSON, Markdown ve PCAP çıktısının tezde hangi tablo veya şekil için kullanılacağı açıkça belirlenmiştir. Böylece deneysel sonuçlar yalnızca terminal çıktısı olarak kalmamış, tez/makale yazımına doğrudan aktarılabilecek artifact yapısına dönüştürülmüştür.

### Durum

Tamamlandı.


---

## Aşama 18 — Port-Aware Canonical Runtime Validation Experiment

Bu aşamada, önceki tekrar deneylerinde gözlenen port bilgisinin eksik kalması problemi giderilmiş ve `run_05_port_aware_repeat_validation` deneyi canonical port-aware runtime validation koşusu olarak tamamlanmıştır.

### Yapılanlar

- Ryu controller `campus_l3_ids_controller_v13_decision_modes.py` ile çalıştırıldı.
- Controller loglarında `src_port` ve `dst_port` alanlarının üretildiği doğrulandı.
- Karma trafik senaryosu yeniden koşturuldu.
- Benign TCP/UDP trafik ve zararlı yüksek hacimli UDP trafik aynı deney koşusunda üretildi.
- PCAP yakalama, Final XGBoost Top-20 runtime pipeline, protocol-aware final policy üretimi ve controller karşılaştırması tamamlandı.
- Model çıktısı ve controller aksiyonları port-aware/protocol-aware flow key üzerinden karşılaştırıldı.
- Rate-limit, drop ve quarantine mekanizmalarının aynı deneyde gözlendiği doğrulandı.

### Canonical Run

- `experiments/results/mixed_traffic_experiments/repeated_mixed_runtime_20260516_130204/run_05_port_aware_repeat_validation`

### Temel Sonuçlar

- `policy_decisions.csv`: 3203 satır
- `flow_stats.csv`: 10941 satır
- `final_runtime_predictions.csv`: 9 satır
- `final_protocol_aware_policy.csv`: 9 satır
- Controller action distribution:
  - allow: 3179
  - quarantine_candidate: 22
  - drop: 1
  - rate_limit: 1
- Mitigation log:
  - drop: 7
- Quarantine log:
  - quarantine_candidate: 7
- Rate-limit log:
  - rate_limit: 1
- Comparison summary:
  - matched_controller_exact_count: 5
  - matched_controller_ip_port_count: 5
  - security_compatible_action_count: 5
  - matched_mitigation_drop_count: 1
  - matched_quarantine_count: 1
  - matched_rate_limit_count: 1

### Tez Açısından Önemi

Bu aşama, önerilen SDN tabanlı hibrit IDS/IPS mimarisinin yalnızca offline sınıflandırma başarısını değil, gerçek zamanlıya yakın runtime ortamda controller seviyesinde uygulanabilirliğini göstermektedir. Özellikle aynı zararlı UDP akışı için model tarafında saldırı kararı üretilmesi ve controller tarafında rate-limit, drop ve quarantine aksiyonlarının port-aware/protocol-aware olarak doğrulanması, yöntemin deneysel geçerliliğini güçlendirmektedir.

### Durum

Tamamlandı.


---

## Aşama 18.1 — Aggregate Runtime Validation Report Update

Bu ara aşamada, canonical port-aware runtime validation deneyi olan `run_05_port_aware_repeat_validation` aggregate raporlama sürecine dahil edilmiştir.

### Yapılanlar

- Repeated mixed runtime deneyleri için aggregate rapor yeniden üretildi.
- `run_05_port_aware_repeat_validation` deneyinin tezde ana deney olarak kullanılmasına karar verildi.
- `run_03_aligned_clean` destekleyici başarılı doğrulama koşusu olarak konumlandırıldı.
- `run_04_repeat_mixed_validation` ise controller loglarında port bilgisi eksik olduğu için diagnostic/partial repetition olarak değerlendirildi.

### Tez Açısından Önemi

Bu ayrım, deneysel sonuçların akademik olarak daha temiz sunulmasını sağlar. Ana sonuçlar port-aware ve protocol-aware eşleştirmenin eksiksiz yapılabildiği run_05 üzerinden raporlanırken, önceki koşular geliştirme sürecini ve doğrulama tekrarlarını destekleyici bağlam olarak kullanılacaktır.

### Durum

Tamamlandı.


---

## Aşama 18.2 — Canonical and Diagnostic Aggregate Separation

Bu aşamada, tekrar edilen karma trafik runtime deneyleri canonical ve diagnostic koşular olarak ayrıştırılmıştır.

### Yapılanlar

- `run_03_aligned_clean`, ilk başarılı runtime validation koşusu olarak korunmuştur.
- `run_05_port_aware_repeat_validation`, port-aware/protocol-aware en güçlü canonical koşu olarak belirlenmiştir.
- `run_04_repeat_mixed_validation`, controller loglarında port bilgisi eksik olduğu için diagnostic/partial repetition olarak sınıflandırılmıştır.
- Tüm valid run’ları içeren genel aggregate rapor korunmuştur.
- Tezde kullanılmak üzere yalnızca canonical run’ları içeren ayrı aggregate rapor yapısı hazırlanmıştır.

### Canonical Runs

- `run_03_aligned_clean`
- `run_05_port_aware_repeat_validation`

### Diagnostic Run

- `run_04_repeat_mixed_validation`

### Tez Açısından Önemi

Bu ayrım, deneysel bulguların akademik olarak daha doğru raporlanmasını sağlar. Diagnostic koşular geliştirme sürecinin şeffaflığını gösterirken, ana performans ve doğrulama sonuçları yalnızca port-aware/protocol-aware olarak geçerli canonical koşular üzerinden sunulacaktır.

### Durum

Tamamlandı.


---

---

## Aşama 18.3 — Thesis-Ready Table and Figure Artifact Generation

Bu aşamada, canonical runtime validation deneylerinden tez ve makale yazımında kullanılacak tablo ve şekil çıktılarının otomatik üretilmesi için yeni bir araç hazırlanmıştır.

### Yapılanlar

- `ml-service/tools/generate_thesis_figures.py` aracı oluşturuldu.
- Araç, `run_05_port_aware_repeat_validation` deneyini ana canonical deney olarak kullanacak şekilde tasarlandı.
- Canonical aggregate CSV çıktısı ile run_05 runtime, policy, mitigation, quarantine ve comparison logları birlikte işlendi.
- Tezde kullanılabilecek tablo çıktıları `tables/` klasörü altında CSV ve Markdown formatında üretilecek şekilde hazırlandı.
- Tezde kullanılabilecek şekil çıktıları `figures/` klasörü altında PNG formatında üretilecek şekilde hazırlandı.
- Üretilen tüm tablo ve şekiller için `thesis_artifacts_manifest.md` dosyası oluşturulacak şekilde artifact yönetimi eklendi.

### Üretilecek Ana Tablolar

- Canonical repeated runtime validation summary
- Controller action distribution
- Final Top-20 prediction distribution
- Protocol-aware final policy distribution
- Enforcement action summary
- Flow-level model-controller comparison
- Protocol-aware attack probability summary

### Üretilecek Ana Şekiller

- Controller policy action distribution
- Final Top-20 runtime prediction distribution
- Protocol-aware final policy distribution
- SDN controller enforcement action summary

### Tez Açısından Önemi

Bu aşama, deney sonuçlarının yalnızca ham CSV ve terminal çıktısı olarak kalmasını engeller. Elde edilen runtime validation bulguları doğrudan tezde kullanılabilecek tablo ve şekil artifactlerine dönüştürülür. Böylece deneysel bölümde kullanılacak görsel ve sayısal kanıtlar tekrarlanabilir, izlenebilir ve düzenli bir yapıya kavuşur.

### Durum

Hazırlandı. Çalıştırma sonrası çıktıların `experiments/results/thesis_artifacts/run_05_port_aware_runtime_validation/` altında oluşması beklenmektedir.


---

## Aşama 19 — Thesis Runtime Validation Results Packaging

Bu aşamada, port-aware canonical runtime validation deneyinden elde edilen çıktıların tez/makale yazımında kullanılabilecek şekilde paketlenmesi tamamlanmıştır.

### Yapılanlar

- `docs/thesis_results_section_runtime_validation.md` dosyası oluşturuldu.
- Runtime validation sonuçları tez bölümü formatında açıklandı.
- `docs/thesis_runtime_validation_package.md` dosyası oluşturuldu.
- Tezde kullanılacak tablo ve şekiller ana artifact klasörüyle ilişkilendirildi.
- `docs/thesis_runtime_validation_table_figure_checklist.md` dosyası oluşturuldu.
- Ana canonical deney olarak `run_05_port_aware_repeat_validation` konumlandırıldı.
- `run_03_aligned_clean` destekleyici canonical koşu olarak korundu.
- `run_04_repeat_mixed_validation` diagnostic/partial repetition olarak sınıflandırıldı.

### Ana Artifact Dizini

- `experiments/results/thesis_artifacts/run_05_port_aware_runtime_validation`

### Tez Açısından Önemi

Bu aşama, deneysel çıktıların terminal ve CSV seviyesinden çıkarılarak tez yazımında doğrudan kullanılabilecek bir sonuç bölümü, tablo/şekil listesi ve artifact paketi haline getirilmesini sağlamıştır. Böylece runtime validation bulguları; model tahmini, protocol-aware yorumlama, controller-side policy decision ve OpenFlow mitigation zinciri üzerinden akademik olarak sunulabilir hale gelmiştir.

### Durum

Tamamlandı.


---

## Aşama 19.1 — Turkish Thesis and Article Results Drafting

Bu aşamada, runtime validation deneylerinden elde edilen canonical sonuçlar Türkçe tez bölümü ve makale Results/Discussion taslağına dönüştürülmüştür.

### Yapılanlar

- `docs/tez_runtime_validation_bolumu_tr.md` dosyası oluşturuldu.
- Runtime validation sonuçları Türkçe akademik tez diliyle yeniden yazıldı.
- Deney senaryosu, artifact yapısı, tablo/şekil referansları, controller action dağılımı, model tahminleri, protocol-aware final policy, enforcement aksiyonları ve flow-level karşılaştırma ayrı alt başlıklar altında açıklandı.
- `docs/article_results_discussion_runtime_validation_tr.md` dosyası oluşturuldu.
- Makale için daha kısa Results/Discussion formatında bir metin hazırlandı.

### Tez Açısından Önemi

Bu aşama, teknik deney çıktılarının akademik anlatıma dönüştürülmesini sağlamıştır. Böylece `run_05_port_aware_repeat_validation` koşusu yalnızca CSV, JSON ve PNG çıktılarıyla değil, doğrudan tez ve makale metnine taşınabilecek bir yorumlama çerçevesiyle de belgelenmiştir.

### Durum

Tamamlandı.


---

## Aşama 20 — Turkish Methodology Chapter Draft

Bu aşamada, SDN tabanlı makine öğrenmesi destekli IDS/IPS mimarisinin yöntem bölümü Türkçe akademik tez diliyle hazırlanmıştır.

### Yapılanlar

- `docs/tez_yontem_sdn_ids_ips_runtime_validation_tr.md` dosyası oluşturuldu.
- SDN veri düzlemi, Ryu kontrol düzlemi, FastAPI tabanlı ML inference servisi ve hibrit politika motoru yöntemsel olarak açıklandı.
- Mininet/Open vSwitch deney ortamı ve kampüs ağı benzeri topoloji mantığı anlatıldı.
- Final XGBoost Top-20 modeli ve runtime feature extraction pipeline tez diliyle tanımlandı.
- Protocol-aware final policy katmanı açıklandı.
- Rate-limit, drop ve quarantine önleme mekanizmaları ayrı alt başlıklarda anlatıldı.
- Loglama, izlenebilirlik ve model-controller karşılaştırma yöntemi açıklandı.
- Canonical, supporting ve diagnostic run ayrımı yöntem bölümüne dahil edildi.

### Tez Açısından Önemi

Bu aşama, daha önce üretilen runtime validation sonuçlarının öncesine yerleştirilecek yöntemsel açıklamayı oluşturmuştur. Böylece tezde önce sistemin nasıl tasarlandığı ve deneysel doğrulamanın nasıl yürütüldüğü açıklanabilecek, ardından `tez_runtime_validation_bolumu_tr.md` dosyasındaki sonuçlar sunulabilecektir.

### Durum

Tamamlandı.


---

## Aşama 20.1 — Combined Turkish Thesis Chapter Draft

Bu aşamada, yöntem bölümü ve runtime validation sonuç bölümü tek bir Word’e aktarılabilir ana tez bölümü altında birleştirilmiştir.

### Yapılanlar

- `docs/bolum_4_yontem_ve_runtime_dogrulama_tr.md` dosyası oluşturuldu.
- `docs/tez_yontem_sdn_ids_ips_runtime_validation_tr.md` içeriği ana bölümün yöntem kısmı olarak eklendi.
- `docs/tez_runtime_validation_bolumu_tr.md` içeriği ana bölümün çalışma zamanı doğrulama ve deneysel bulgular kısmı olarak eklendi.
- Bölüm başına, yöntemi ve deneysel doğrulamayı bağlayan giriş paragrafı eklendi.
- Dosya, Word veya Google Docs ortamına taşınabilecek ana tez bölüm taslağı olarak hazırlandı.

### Tez Açısından Önemi

Bu aşama, geliştirilen SDN tabanlı ML destekli IDS/IPS prototipinin hem yöntemsel tasarımını hem de runtime validation sonuçlarını tek bir bütünlüklü tez bölümü haline getirmiştir. Böylece tezde sistem mimarisi, deney akışı, model entegrasyonu, policy engine, mitigation mekanizmaları ve deneysel bulgular ardışık ve akademik bir anlatı içinde sunulabilir hale gelmiştir.

### Durum

Tamamlandı.


---

## Aşama 20 — Turkish Methodology Chapter Draft

Bu aşamada, SDN tabanlı makine öğrenmesi destekli IDS/IPS mimarisinin yöntem bölümü Türkçe akademik tez diliyle hazırlanmıştır.

### Yapılanlar

- `docs/tez_yontem_sdn_ids_ips_runtime_validation_tr.md` dosyası oluşturuldu.
- SDN veri düzlemi, Ryu kontrol düzlemi, FastAPI tabanlı ML inference servisi ve hibrit politika motoru yöntemsel olarak açıklandı.
- Mininet/Open vSwitch deney ortamı ve kampüs ağı benzeri topoloji mantığı anlatıldı.
- Final XGBoost Top-20 modeli ve runtime feature extraction pipeline tez diliyle tanımlandı.
- Protocol-aware final policy katmanı açıklandı.
- Rate-limit, drop ve quarantine önleme mekanizmaları ayrı alt başlıklarda anlatıldı.
- Loglama, izlenebilirlik ve model-controller karşılaştırma yöntemi açıklandı.
- Canonical, supporting ve diagnostic run ayrımı yöntem bölümüne dahil edildi.

### Tez Açısından Önemi

Bu aşama, daha önce üretilen runtime validation sonuçlarının öncesine yerleştirilecek yöntemsel açıklamayı oluşturmuştur. Böylece tezde önce sistemin nasıl tasarlandığı ve deneysel doğrulamanın nasıl yürütüldüğü açıklanabilecek, ardından `tez_runtime_validation_bolumu_tr.md` dosyasındaki sonuçlar sunulabilecektir.

### Durum

Tamamlandı.


---

## Aşama 20.2 — Table and Figure Placeholder Mapping

Bu aşamada, birleştirilmiş Türkçe tez bölümüne tablo ve şekil yer tutucuları eklenmiştir.

### Yapılanlar

- `docs/bolum_4_yontem_ve_runtime_dogrulama_tr.md` dosyasında Tablo 1–7 ve Şekil 1–4 için görünür ekleme noktaları oluşturuldu.
- Her tablo ve şekil için ilgili artifact dosya yolu metin içine eklendi.
- `docs/bolum_4_tablo_sekil_insert_map.md` dosyası oluşturuldu.
- Word veya Google Docs ortamına aktarım sırasında hangi tablo/şeklin hangi bölüme ekleneceği belgelendi.

### Tez Açısından Önemi

Bu aşama, deneysel bulguların metne entegrasyonunu kolaylaştırmaktadır. Tablo ve şekil yerleri açıkça işaretlendiği için tez dosyasına aktarım sırasında artifact dosyalarının kaybolması, yanlış sırayla eklenmesi veya yanlış başlıklandırılması riski azaltılmıştır.

### Durum

Tamamlandı.


---

## Aşama 20.3 — DOCX Thesis Chapter Generation

Bu aşamada, yöntem ve runtime validation sonuçlarını içeren ana Türkçe tez bölümü Word formatına dönüştürülmüştür.

### Yapılanlar

- `ml-service/tools/build_thesis_chapter_docx.py` aracı oluşturuldu.
- `docs/bolum_4_yontem_ve_runtime_dogrulama_tr.md` dosyası kaynak metin olarak kullanıldı.
- `experiments/results/thesis_artifacts/run_05_port_aware_runtime_validation` altındaki tablo ve şekiller Word belgesine eklendi.
- Tablo 1–7 ve Şekil 1–4 otomatik olarak belgeye yerleştirildi.
- Çıktı dosyası oluşturuldu:
  - `docs/bolum_4_yontem_ve_runtime_dogrulama_tr.docx`

### Tez Açısından Önemi

Bu aşama, geliştirilen SDN tabanlı ML destekli IDS/IPS prototipinin yöntem ve deneysel doğrulama bölümünü Word formatında kullanılabilir hale getirmiştir. Böylece tez yazımı için gerekli metin, tablo ve şekiller tek bir belge altında toplanmıştır.

### Durum

Tamamlandı.


---

## Aşama 20.4 — DOCX Table and Figure Insertion Fix

Bu aşamada, Word çıktısında tablo ve şekillerin doğru şekilde yerleştirilmesi sağlanmıştır.

### Yapılanlar

- `ml-service/tools/build_thesis_chapter_docx.py` script’i güncellendi.
- Markdown içindeki `[TABLO EKLEME NOKTASI]` ve `[ŞEKİL EKLEME NOKTASI]` marker’larının daha güvenilir yakalanması sağlandı.
- Tablo başlıklarının marker sonrası `Başlık:` satırından okunması iyileştirildi.
- `docs/bolum_4_yontem_ve_runtime_dogrulama_tr.docx` dosyası yeniden üretildi.
- DOCX içinde 7 tablo ve 4 şeklin yer aldığı doğrulandı.

### Tez Açısından Önemi

Bu aşama, yöntem ve runtime validation bölümünün yalnızca metin olarak değil, tablo ve şekilleriyle birlikte Word formatında kullanılabilir hale gelmesini sağlamıştır. Böylece tez yazımına doğrudan aktarılabilecek bütünleşik bir bölüm çıktısı elde edilmiştir.

### Durum

Tamamlandı.


---

## Aşama 20.6 — DOCX Chapter with Appendix Artifacts

Bu aşamada, Bölüm 4 için yöntem, runtime validation metni, tablolar ve şekilleri içeren bütünleşik Word dosyası başarıyla üretilmiştir.

### Yapılanlar

- `ml-service/tools/build_thesis_chapter_docx_with_appendix_artifacts.py` aracı oluşturuldu.
- `docs/bolum_4_yontem_ve_runtime_dogrulama_tr.md` kaynak metin olarak kullanıldı.
- `experiments/results/thesis_artifacts/run_05_port_aware_runtime_validation` dizinindeki tez tabloları ve şekilleri Word dosyasına eklendi.
- Tablo 1–7 ve Şekil 1–4 belge sonunda `Ek: Tez Tablo ve Şekilleri` başlığı altında toplandı.
- Çıktı dosyası oluşturuldu:
  - `docs/bolum_4_yontem_ve_runtime_dogrulama_tr_with_artifacts.docx`
- DOCX doğrulamasında şu sonuç elde edildi:
  - Paragraphs: 311
  - Tables: 7
  - Inline shapes: 4

### Tez Açısından Önemi

Bu aşama, Bölüm 4’ün yalnızca metinsel bir taslak olmaktan çıkıp, tablo ve şekilleriyle birlikte Word formatında kullanılabilir bir tez bölümüne dönüşmesini sağlamıştır. Böylece yöntem, deneysel doğrulama, canonical runtime validation sonuçları, controller action dağılımları, model tahmin dağılımları ve enforcement görselleri tek bir dosyada birleştirilmiştir.

### Durum

Tamamlandı.


---

## Aşama 21 — Turkish Discussion, Limitations and Future Work Draft

Bu aşamada, tez için `Bölüm 5. Tartışma, Sınırlılıklar ve Gelecek Çalışmalar` taslağı oluşturulmuştur.

### Yapılanlar

- `docs/bolum_5_tartisma_sinirliliklar_gelecek_calismalar_tr.md` dosyası oluşturuldu.
- Bölüm 4’te elde edilen runtime validation bulguları akademik bağlamda tartışıldı.
- SDN açısından değerlendirme yapıldı.
- Makine öğrenmesi modelinin runtime kullanımı tartışıldı.
- Protocol-aware ve port-aware değerlendirmenin önemi açıklandı.
- Rate-limit, drop ve quarantine önleme aksiyonları yorumlandı.
- Çalışmanın güçlü yönleri ve sınırlılıkları yazıldı.
- Gelecek çalışmalar için trafik çeşitliliği, daha büyük veriyle eğitim, controller overhead analizi, reinforcement learning policy engine ve gerçek testbed önerileri eklendi.

### Tez Açısından Önemi

Bu aşama, deneysel sonuçların yalnızca raporlanmasını değil, akademik olarak yorumlanmasını sağlamaktadır. Bölüm 5, çalışmanın katkılarını, sınırlılıklarını ve gelecekte geliştirilebilecek yönlerini sistematik olarak sunarak tez bütünlüğünü güçlendirmektedir.

### Durum

Tamamlandı.


---

## Aşama 21.1 — Discussion Chapter DOCX Generation

Bu aşamada, Bölüm 5 tartışma, sınırlılıklar ve gelecek çalışmalar taslağı Word formatına dönüştürülmüştür.

### Yapılanlar

- `ml-service/tools/build_simple_markdown_docx.py` aracı oluşturuldu.
- `docs/bolum_5_tartisma_sinirliliklar_gelecek_calismalar_tr.md` dosyası kaynak metin olarak kullanıldı.
- Bölüm 5 için sade Word çıktısı üretildi:
  - `docs/bolum_5_tartisma_sinirliliklar_gelecek_calismalar_tr.docx`
- DOCX çıktısı paragraf, tablo ve şekil sayıları açısından kontrol edilebilir hale getirildi.

### Tez Açısından Önemi

Bu aşama, deneysel bulguların akademik tartışma, sınırlılık ve gelecek çalışmalar bağlamında Word formatında kullanılabilir bir tez bölümüne dönüştürülmesini sağlamıştır. Böylece Bölüm 4’te sunulan yöntem ve runtime validation bulguları, Bölüm 5’te yorumlanabilir hale getirilmiştir.

### Durum

Tamamlandı.

---

## Aşama 21.2 — Thesis Chapter Package README

Bu aşamada, tez yazımı için üretilen Bölüm 4 ve Bölüm 5 dosyaları ile deneysel artifact çıktıları tek bir README dosyasında indekslenmiştir.

### Yapılanlar

- docs/tez_bolum_paketi_readme.md dosyası oluşturuldu.
- Bölüm 4 ve Bölüm 5 Word dosyaları listelendi.
- Markdown kaynak dosyaları listelendi.
- Ana canonical deney olarak run_05_port_aware_repeat_validation işaretlendi.
- Destekleyici canonical deney olarak run_03_aligned_clean belirtildi.
- Diagnostic koşu olarak run_04_repeat_mixed_validation açıklandı.
- Tezde kullanılacak tablo ve şekil dosyaları tek tek listelendi.
- Ana sonuç cümlesi ve dikkat edilecek noktalar eklendi.

### Tez Açısından Önemi

Bu aşama, tez yazımı sırasında dosya karmaşasını azaltmak ve hangi çıktının hangi amaçla kullanılacağını açıkça göstermek için hazırlanmıştır. Böylece yöntem, runtime validation, tartışma, tablo, şekil ve deney artifact dosyaları izlenebilir bir paket yapısına kavuşturulmuştur.

### Durum

Tamamlandı.

---

## Aşama 22 — Thesis Introduction Chapter Draft

Bu aşamada, tez için `Bölüm 1. Giriş` taslağı oluşturulmuştur.

### Yapılanlar

- `docs/bolum_1_giris_tr.md` dosyası oluşturuldu.
- Araştırmanın arka planı yazıldı.
- Yazılım tanımlı ağlar ve güvenlik potansiyeli açıklandı.
- Makine öğrenmesi tabanlı DDoS tespiti bağlamı kuruldu.
- Problem tanımı ve araştırma soruları yazıldı.
- Araştırmanın amacı ve katkıları belirtildi.
- Deneysel yaklaşımın özeti eklendi.
- Tezin organizasyonu oluşturuldu.
- Markdown dosyası Word formatına dönüştürüldü:
  - `docs/bolum_1_giris_tr.docx`

### Tez Açısından Önemi

Bu aşama, tez metninin giriş bölümünü oluşturmuştur. Böylece çalışma, problem bağlamı, araştırma amacı, katkılar ve tez organizasyonu açısından akademik bir başlangıç yapısına kavuşmuştur.

### Durum

Tamamlandı.

---

## Aşama 23 — Conceptual and Theoretical Background Chapter Draft

Bu aşamada, tez için `Bölüm 2. Kavramsal ve Kuramsal Arka Plan` taslağı oluşturulmuştur.

### Yapılanlar

- `docs/bolum_2_kavramsal_kuramsal_arka_plan_tr.md` dosyası oluşturuldu.
- Geleneksel ağ mimarileri ve SDN mimarisi açıklandı.
- Kontrol düzlemi, veri düzlemi, OpenFlow, Ryu, Mininet ve Open vSwitch kavramları işlendi.
- DDoS saldırıları ve kampüs ağlarındaki etkileri açıklandı.
- IDS/IPS kavramları tanımlandı.
- Makine öğrenmesi tabanlı saldırı tespiti, CIC-DDoS2019, CICFlowMeter uyumlu özellikler ve model değerlendirme metrikleri anlatıldı.
- Runtime feature extraction, SDN tabanlı önleme aksiyonları ve hibrit politika mantığı açıklandı.
- Bölüm 2 Word formatına dönüştürüldü:
  - `docs/bolum_2_kavramsal_kuramsal_arka_plan_tr.docx`

### Tez Açısından Önemi

Bu aşama, tez çalışmasının yöntem ve deney bölümlerinin anlaşılabilmesi için gerekli teknik ve kavramsal altyapıyı sağlamaktadır. Böylece SDN, DDoS, ML tabanlı IDS/IPS ve runtime enforcement bileşenleri arasında kuramsal bütünlük kurulmuştur.

### Durum

Tamamlandı.

---

## Aşama 24 — Literature Review and Related Work Chapter Draft

Bu aşamada, tez için `Bölüm 3. Literatür Taraması ve İlgili Çalışmalar` taslağı oluşturulmuştur.

### Yapılanlar

- `docs/bolum_3_literatur_taramasi_ve_ilgili_calismalar_tr.md` dosyası oluşturuldu.
- Literatür tarama stratejisi yazıldı.
- Dahil etme ve hariç tutma ölçütleri belirlendi.
- Literatür sınıflandırma matrisi oluşturuldu.
- SDN tabanlı DDoS tespit çalışmaları tartışıldı.
- Makine öğrenmesi ve derin öğrenme tabanlı yaklaşımlar karşılaştırıldı.
- Özellik seçimi ve hafif model tasarımları ele alındı.
- SDN denetleyicisiyle bütünleşik önleme çalışmaları değerlendirildi.
- Mininet, Ryu ve OpenFlow tabanlı deneysel çalışmalar tartışıldı.
- Literatürdeki boşluklar ve bu tez çalışmasının konumu açıklandı.
- Bölüm 3 Word formatına dönüştürüldü:
  - `docs/bolum_3_literatur_taramasi_ve_ilgili_calismalar_tr.docx`

### Tez Açısından Önemi

Bu aşama, çalışmanın literatürdeki yerini belirlemek için hazırlanmıştır. Bölüm 3, mevcut çalışmaların çoğunlukla çevrimdışı sınıflandırma veya sınırlı mitigation senaryolarına odaklandığını; bu tez çalışmasının ise runtime SDN IDS/IPS entegrasyonu, port-aware/protocol-aware karşılaştırma ve aktif enforcement zinciriyle ayrıştığını göstermektedir.

### Durum

Tamamlandı.

---

## Aşama 25 — Conclusion and Recommendations Chapter Draft

Bu aşamada, tez için `Bölüm 6. Sonuç ve Öneriler` taslağı oluşturulmuştur.

### Yapılanlar

- `docs/bolum_6_sonuc_ve_oneriler_tr.md` dosyası oluşturuldu.
- Çalışmanın genel özeti yazıldı.
- Elde edilen temel bulgular özetlendi.
- Araştırma sorularına yanıtlar verildi.
- Akademik ve pratik katkılar açıklandı.
- Sınırlılıklar özetlendi.
- Gelecek çalışmalar için öneriler yazıldı.
- Bölüm 6 Word formatına dönüştürüldü:
  - `docs/bolum_6_sonuc_ve_oneriler_tr.docx`

### Tez Açısından Önemi

Bu aşama, tez ana gövdesinin sonuç bölümünü tamamlamaktadır. Böylece problem, yöntem, literatür, deneysel doğrulama, tartışma ve sonuç bölümleri arasında bütünlüklü bir akademik kapanış sağlanmıştır.

### Durum

Tamamlandı.

---

## Aşama 25.1 — Thesis File Inventory

Bu aşamada, tez bölümleri, destekleyici dokümanlar, deney dizinleri ve tez artifact dosyaları için merkezi bir dosya envanteri oluşturulmuştur.

### Yapılanlar

- `docs/tez_dosya_envanteri.md` dosyası oluşturuldu.
- Bölüm 1–6 Markdown ve DOCX dosyaları listelendi.
- Destekleyici README, checklist, insert map ve roadmap dosyaları listelendi.
- Canonical, destekleyici ve diagnostic deney dizinleri ayrıştırıldı.
- Run 05 tez tabloları ve şekilleri tek tek listelendi.
- Dosya/dizin varlık kontrolü ve boyut bilgileri eklendi.

### Tez Açısından Önemi

Bu envanter, tez yazımı sırasında hangi dosyanın nerede olduğunu ve hangi çıktının hangi amaçla kullanılacağını hızlıca görmeyi sağlar. Böylece deneysel artifact, Word bölümleri ve Markdown kaynakları arasında izlenebilirlik korunur.

### Durum

Tamamlandı.

---

## Aşama 25.2 — Main Thesis Draft DOCX Merge

Bu aşamada, Bölüm 1–6 Word dosyaları tek bir ana tez taslağı altında birleştirilmiştir.

### Yapılanlar

- `ml-service/tools/merge_thesis_chapters_docx.py` aracı oluşturuldu.
- Bölüm 1, Bölüm 2, Bölüm 3, Bölüm 4, Bölüm 5 ve Bölüm 6 DOCX dosyaları birleştirildi.
- Bölüm 4 için artifact içeren dosya kullanıldı:
  - `docs/bolum_4_yontem_ve_runtime_dogrulama_tr_with_artifacts.docx`
- Birleşik ana tez taslağı oluşturuldu:
  - `docs/tez_ana_taslak_tr.docx`
- Ana DOCX dosyası paragraf, tablo ve şekil sayıları açısından kontrol edilebilir hale getirildi.
- `docs/tez_dosya_envanteri.md` içine ana tez taslağı bölümü eklendi.

### Tez Açısından Önemi

Bu aşama, ayrı ayrı hazırlanan tez bölümlerinin tek bir ana Word dosyasında toplanmasını sağlamıştır. Böylece giriş, kuramsal arka plan, literatür taraması, yöntem ve runtime doğrulama, tartışma ve sonuç bölümleri bütünleşik bir tez taslağına dönüştürülmüştür.

### Durum

Tamamlandı.

---

## Aşama 25.3 — Thesis Front Matter Draft

Bu aşamada, birleşik ana tez taslağına akademik ön sayfa yapısı eklenmiştir.

### Yapılanlar

- `ml-service/tools/add_frontmatter_to_thesis_docx.py` aracı oluşturuldu.
- `docs/tez_ana_taslak_tr.docx` dosyası kaynak olarak kullanıldı.
- Aşağıdaki yer tutucu bölümler eklendi:
  - Kapak sayfası
  - Tez onay sayfası
  - Beyan
  - Özet
  - Abstract
  - İçindekiler
  - Tablo listesi
  - Şekil listesi
- Front matter içeren ana taslak üretildi:
  - `docs/tez_ana_taslak_tr_frontmatter.docx`
- Dosya paragraf, tablo ve şekil sayıları açısından kontrol edilebilir hale getirildi.
- `docs/tez_dosya_envanteri.md` içine front matter içeren ana taslak bilgisi eklendi.

### Tez Açısından Önemi

Bu aşama, tez metninin yalnızca bölüm içeriklerinden oluşan bir taslak olmaktan çıkarılıp akademik tez formatına yaklaşmasını sağlamıştır. Kapak, özet, abstract, içindekiler, tablo ve şekil listesi yer tutucuları sonraki biçimlendirme aşamaları için temel oluşturur.

### Durum

Tamamlandı.

---

## Aşama 25.4 — Thesis Abstract and Öz Güncellemesi

Bu aşamada, front matter içeren ana tez taslağındaki Türkçe Özet ve İngilizce Abstract bölümleri gerçek runtime validation sonuçlarına göre güncellenmiştir.

### Yapılanlar

- `ml-service/tools/update_thesis_abstracts_docx.py` aracı oluşturuldu.
- `docs/tez_ana_taslak_tr_frontmatter.docx` kaynak olarak kullanıldı.
- Türkçe Özet bölümü run_05 canonical runtime validation ve canonical aggregate sonuçlarına göre yeniden yazıldı.
- İngilizce Abstract bölümü aynı deneysel bulgulara göre hazırlandı.
- Güncellenmiş ana tez dosyası üretildi:
  - `docs/tez_ana_taslak_tr_frontmatter_ozetli.docx`
- Dosya paragraf, tablo, şekil ve başlık kontrolünden geçirilebilir hale getirildi.
- `docs/tez_dosya_envanteri.md` içine güncel ana tez taslağı eklendi.

### Tez Açısından Önemi

Bu aşama, tez ön sayfalarındaki özet bölümlerini yer tutucu olmaktan çıkarıp gerçek deneysel bulgulara dayalı akademik metinlere dönüştürmüştür. Böylece tez taslağı savunma/ön inceleme sürecine daha yakın bir yapıya kavuşmuştur.

### Durum

Tamamlandı.

---

## Aşama 26.1 — Seed Literature Records and Paper Extraction Checklist

Bu aşamada, literatür takip tablosuna başlangıç çekirdek kaynak kayıtları eklenmiş ve makale inceleme checklist dosyası oluşturulmuştur.

### Yapılanlar

- `docs/literature_review/literature_tracking_table.csv` dosyasına ilk çekirdek literatür kayıtları eklendi.
- Doldurulmuş Markdown görünümü oluşturuldu:
  - `docs/literature_review/literature_tracking_table_filled_seed.md`
- Makale okuma ve bilgi çıkarma checklist dosyası oluşturuldu:
  - `docs/literature_review/paper_extraction_checklist.md`
- Kaynaklar SDN-DDoS, ML/DL, controller/testbed, dataset, mitigation ve runtime/offline ayrımı açısından sınıflandırılacak şekilde yapılandırıldı.

### Tez Açısından Önemi

Bu aşama, Bölüm 3 literatür taramasının gerçek kaynaklarla sistematik şekilde güçlendirilmesi için ilk veri girişini sağlar. Bundan sonraki adımda Web of Science, Scopus, IEEE Xplore ve Google Scholar üzerinden seçilecek makaleler aynı tabloya eklenerek literatür bölümü daha akademik ve kanıta dayalı hale getirilecektir.

### Durum

Tamamlandı.

---

## Aşama 26.2 — BibTeX and Uploaded Literature Source Integration

Bu aşamada, kullanıcı tarafından sağlanan BibTeX dosyası, örnek doktora tezi ve yayın aşamasındaki manuscript dosyası literatür altyapısına dahil edilmiştir.

### Yapılanlar

- Literatür kaynak dosyaları için kaynak dizini hazırlandı:
  - `docs/literature_review/source_files/`
- BibTeX içe aktarma aracı oluşturuldu:
  - `ml-service/tools/ingest_bibtex_literature.py`
- Ek kaynak envanteri aracı oluşturuldu:
  - `ml-service/tools/build_literature_source_inventory.py`
- BibTeX kayıtlarının literatür takip tablosuna aktarılması için otomatik akış hazırlandı.
- Ek kaynakların tezde kullanım ilkeleri belirlendi:
  - `SDN-ML-Security_Referans.bib`: Bölüm 3 literatür havuzu
  - `tez1.pdf`: SDN/OpenFlow/OpenSec ve tez organizasyonu için örnek kaynak
  - `Manuscript.docx`: yayınlanmamış ilişkili çalışma; tezde dikkatli ve iç bağlam olarak kullanılacak kaynak

### Tez Açısından Önemi

Bu aşama, Bölüm 3 literatür taramasının gerçek bibliyografik kayıtlarla güçlendirilmesini sağlar. Ayrıca örnek doktora tezi üzerinden tez organizasyonu, şekil/tablo listesi ve SDN/OpenFlow anlatım biçimi incelenebilecek; yayın aşamasındaki manuscript ise bu tezde geliştirilen runtime SDN entegrasyonunun önceki ML/feature-selection çalışmasıyla nasıl ilişkilendiğini açıklamak için kullanılacaktır.

### Durum

Tamamlandı.

---

## Aşama 26.4 — Chapter 3 Literature Synthesis Report

Bu aşamada, literatür takip tablosu ve full-text envanterinden Bölüm 3 için literatür sentez raporu oluşturulmuştur.

### Yapılanlar

- `ml-service/tools/generate_chapter3_literature_synthesis_report.py` aracı oluşturuldu.
- Bölüm 3 için literatür sentez raporu üretildi:
  - `docs/literature_review/synthesis/chapter3_literature_synthesis_report.md`
- Literatür boşluk analizi taslağı üretildi:
  - `docs/literature_review/synthesis/chapter3_literature_gap_analysis.md`
- Bölüm 3 revizyon planı oluşturuldu:
  - `docs/literature_review/chapter3_revision_plan.md`
- Kaynaklar tematik olarak ayrıştırıldı:
  - SDN/DDoS/OpenFlow
  - ML/DL tabanlı IDS
  - Özellik seçimi
  - Runtime/controller entegrasyonu
  - Mitigation/prevention
  - Veri kümesi odaklı çalışmalar

### Tez Açısından Önemi

Bu aşama, Bölüm 3’ün gerçek kaynaklara dayalı olarak revize edilmesi için doğrudan kullanılabilecek sentez altyapısını sağlar. Böylece literatür bölümü yalnızca genel anlatı olmaktan çıkarılıp kaynak kümelerine dayalı karşılaştırmalı bir yapıya dönüştürülebilecektir.

### Durum

Tamamlandı.

---

## Aşama 26.5 — Literature-Supported Chapter 3 Draft

Bu aşamada, literatür sentez aday tablosu kullanılarak Bölüm 3 için literatür destekli yeni bir taslak oluşturulmuştur.

### Yapılanlar

- `ml-service/tools/revise_chapter3_from_literature_synthesis.py` aracı oluşturuldu.
- Literatür sentez tablosu kaynak olarak kullanıldı:
  - `docs/literature_review/synthesis/chapter3_literature_synthesis_candidates.csv`
- Yeni Bölüm 3 taslağı üretildi:
  - `docs/bolum_3_literatur_taramasi_ve_ilgili_calismalar_tr_literature_supported.md`
- Bölüm 3 kaynak özet dosyası üretildi:
  - `docs/literature_review/synthesis/chapter3_revision_source_summary.md`
- Yeni Bölüm 3 Word dosyasına dönüştürüldü:
  - `docs/bolum_3_literatur_taramasi_ve_ilgili_calismalar_tr_literature_supported.docx`

### Tez Açısından Önemi

Bu aşama, Bölüm 3’ün genel anlatıdan çıkarılarak gerçek literatür havuzuna dayalı, kategori bazlı ve tez katkısını açıkça konumlandıran bir yapıya dönüştürülmesini sağlar. Özellikle runtime/controller/testbed ve mitigation/prevention kategorilerindeki sınırlı çalışma sayısı, bu tez çalışmasının literatürdeki boşluğunu daha güçlü biçimde desteklemektedir.

### Durum

Tamamlandı.

---

## Aşama 26.6 — Literature-Supported Chapter 3 Regeneration

Bu aşamada, güncellenmiş BibTeX havuzu, full-text envanteri, manuel eşleştirme düzeltmeleri ve yeni eklenen manuel literatür kayıtları kullanılarak Bölüm 3 yeniden üretilmiştir.

### Yapılanlar

- Genişletilmiş literatür sentez aday tablosu kullanıldı:
  - `docs/literature_review/synthesis/chapter3_literature_synthesis_candidates.csv`
- Literatür destekli Bölüm 3 Markdown taslağı yeniden üretildi:
  - `docs/bolum_3_literatur_taramasi_ve_ilgili_calismalar_tr_literature_supported.md`
- Literatür destekli Bölüm 3 DOCX dosyası üretildi:
  - `docs/bolum_3_literatur_taramasi_ve_ilgili_calismalar_tr_literature_supported.docx`
- Eski Bölüm 3 dosyaları zaman damgalı olarak yedeklendi.
- Literatür destekli yeni Bölüm 3 aktif bölüm dosyası olarak kopyalandı:
  - `docs/bolum_3_literatur_taramasi_ve_ilgili_calismalar_tr.md`
  - `docs/bolum_3_literatur_taramasi_ve_ilgili_calismalar_tr.docx`

### Tez Açısından Önemi

Bu aşama, Bölüm 3’ü genel literatür anlatısından çıkarıp genişletilmiş kaynak havuzuna dayalı, tematik sınıflandırılmış ve tez katkısını daha net konumlandıran bir yapıya dönüştürür. Özellikle runtime/controller/testbed ve mitigation/prevention kategorilerindeki sınırlı çalışma sayısı, tez çalışmasının port-aware/protocol-aware aktif SDN IDS/IPS katkısını destekleyen temel literatür boşluğunu güçlendirmektedir.

### Durum

Tamamlandı.

---

## Aşama 26.7 — Literature Comparison Tables Integrated into Chapters 3 and 5

Bu aşamada, mevcut literatür ile bu tez çalışmasını karşılaştıran iki tablo üretilmiş ve ilgili bölümlere entegre edilmiştir.

### Yapılanlar

- Bölüm 3 için yöntemsel karşılaştırma tablosu üretildi:
  - `docs/literature_review/synthesis/table_chapter3_methodological_comparison.csv`
  - `docs/literature_review/synthesis/table_chapter3_methodological_comparison.md`
- Bölüm 5 için sonuç ve işlevsellik karşılaştırma tablosu üretildi:
  - `docs/literature_review/synthesis/table_chapter5_result_functionality_comparison.csv`
  - `docs/literature_review/synthesis/table_chapter5_result_functionality_comparison.md`
- Tablolar Bölüm 3 ve Bölüm 5 Markdown dosyalarına eklendi:
  - `docs/bolum_3_literatur_taramasi_ve_ilgili_calismalar_tr.md`
  - `docs/bolum_5_tartisma_sinirliliklar_gelecek_calismalar_tr.md`
- Bölüm 3 ve Bölüm 5 DOCX dosyaları yeniden üretildi.

### Tez Açısından Önemi

Bu aşama, önerilen yöntemin mevcut literatür karşısındaki konumunu daha görünür hale getirir. Bölüm 3’te yöntemsel boşluklar; Bölüm 5’te ise deneysel ve işlevsel katkılar literatürle karşılaştırmalı olarak sunulmuştur. Özellikle port/protocol-aware analiz ve rate-limit/drop/quarantine aksiyonlarının birlikte doğrulanması, tez çalışmasının ayırt edici yönü olarak vurgulanmıştır.

### Durum

Tamamlandı.

---

## Aşama 26.9 — Main Thesis Rebuild with Real DOCX Comparison Tables

Bu aşamada, Bölüm 3 ve Bölüm 5’e eklenen literatür karşılaştırma tablolarının ana tez DOCX dosyasında gerçek Word tablosu olarak yer alması sağlanmıştır.

### Yapılanlar

- Bölüm 3 ve Bölüm 5 Markdown dosyaları, Markdown tablolarını gerçek DOCX tablolarına dönüştüren araçla yeniden DOCX’e çevrildi.
- Ana tez DOCX dosyası güncel bölüm dosyalarıyla yeniden oluşturuldu:
  - `docs/tez_ana_taslak_tr.docx`
  - `docs/tez_ana_taslak_tr_frontmatter.docx`
  - `docs/tez_ana_taslak_tr_frontmatter_ozetli.docx`
- Özet ve Abstract bölümleri tekrar güncellendi.
- Kalite kontrol raporu yeniden üretildi:
  - `docs/tez_taslak_kalite_kontrol_raporu.md`
  - `docs/tez_taslak_kalite_kontrol_raporu.json`

### Doğrulama Sonucu

- Eksik başlık: 0
- Eksik dosya: 0
- Eksik artifact: 0
- Ana DOCX tablo sayısı: 15
- Ana DOCX şekil sayısı: 4

### Tez Açısından Önemi

Bu aşama, literatür karşılaştırma tablolarının yalnızca Markdown metni olarak değil, gerçek Word tablo nesneleri olarak ana tez taslağına girmesini sağlamıştır. Böylece Bölüm 3’te yöntemsel literatür karşılaştırması, Bölüm 5’te ise sonuç ve işlevsellik karşılaştırması tez formatına daha uygun hale getirilmiştir.

### Durum

Tamamlandı.

---

## Aşama 26.10 — Draft References Section from Literature Tracking

Bu aşamada, literatür takip tablosu ve Bölüm 3/5 karşılaştırma tablolarından otomatik kaynakça taslağı üretilmiş ve ana tez DOCX dosyasına kaynakça bölümü olarak eklenmiştir.

### Yapılanlar

- Literatür takip tablosundan kaynakça taslağı üretildi:
  - `docs/kaynakca_taslagi_literature_tracking.md`
  - `docs/kaynakca_taslagi_literature_tracking.csv`
- Kaynakça bölümü oluşturuldu:
  - `docs/bolum_7_kaynakca_taslagi.md`
  - `docs/bolum_7_kaynakca_taslagi.docx`
- Ana tez DOCX dosyası kaynakça bölümüyle yeniden birleştirildi:
  - `docs/tez_ana_taslak_tr_frontmatter_ozetli.docx`
- Kalite kontrol raporu tekrar üretildi:
  - `docs/tez_taslak_kalite_kontrol_raporu.md`
  - `docs/tez_taslak_kalite_kontrol_raporu.json`

### Tez Açısından Önemi

Bu aşama, literatür sentezi ve karşılaştırma tablolarında kullanılan kaynakların ana tez metniyle izlenebilir bir kaynakça taslağına bağlanmasını sağlar. Kaynakça henüz nihai biçimlendirme değildir; ancak tez yazımı ilerledikçe APA/IEEE veya üniversite tez yazım kılavuzuna uygun biçime dönüştürülebilecek izlenebilir bir temel sunar.

### Durum

Tamamlandı.

---

## Aşama 27.1 — SAÜ FBE Thesis Guide and Template Compliance Layer

Bu aşamada, Sakarya Üniversitesi Fen Bilimleri Enstitüsü Lisansüstü Tez Yazım Kılavuzu ve Tez Hazırlama Şablonu proje kaynaklarına dahil edilerek tez üretim ve kalite kontrol sürecinin bu kurallara göre yürütülmesi hedeflenmiştir.

### Yapılacaklar

- Kılavuz ve şablon dosyaları standart klasöre alınacaktır:
  - `docs/thesis_template_sources/fbe_lisansustu_tez_yazim_kilavuzu.pdf`
  - `docs/thesis_template_sources/tez_hazirlama_sablonu.docx`
- Kılavuzdan sayfa düzeni, başlık hiyerarşisi, tablo/şekil başlığı, kaynakça ve ön sayfa kuralları çıkarılacaktır.
- Şablon DOCX dosyasındaki stiller incelenecektir.
- `docs/tez_format_kontrol_kriterleri.md` dosyası oluşturulacaktır.
- `check_thesis_draft_quality.py` aracı SAÜ FBE format kontrollerini içerecek şekilde genişletilecektir.
- Ana tez DOCX build süreci, mümkün olduğunca şablon stillerine uyumlu hale getirilecektir.

### Tez Açısından Önemi

Bu aşama, tez taslağının yalnızca içerik ve deneysel sonuç açısından değil, enstitü teslim formatı açısından da denetlenmesini sağlar. Bundan sonraki DOCX üretimleri, tablo/şekil düzenlemeleri, başlık yapısı, ön sayfalar ve kaynakça kontrolleri SAÜ FBE tez yazım kurallarına göre yürütülecektir.

### Durum

Başlatıldı.

---

## Aşama 27.2 — SAÜ FBE Preliminary Format Quality Checks

Bu aşamada, Sakarya Üniversitesi Fen Bilimleri Enstitüsü Lisansüstü Tez Yazım Kılavuzu ve Tez Hazırlama Şablonu proje kaynaklarına alınmış ve mevcut tez kalite kontrol aracına ön format uyum kontrolleri eklenmiştir.

### Yapılanlar

- Kılavuz ve şablon kaynakları standart klasörde doğrulandı:
  - `docs/thesis_template_sources/fbe_lisansustu_tez_yazim_kilavuzu.pdf`
  - `docs/thesis_template_sources/fbe_lisansustu_tez_yazim_kilavuzu.txt`
  - `docs/thesis_template_sources/tez_hazirlama_sablonu.docx`
- Format kontrol kriterleri dosyası üretildi:
  - `docs/tez_format_kontrol_kriterleri.md`
- `check_thesis_draft_quality.py` aracına SAÜ FBE format uyum ön kontrol bölümü eklendi.
- Kalite kontrol raporunda aşağıdaki alanlar görünür hale getirildi:
  - kılavuz PDF/TXT varlığı,
  - tez hazırlama şablonu DOCX varlığı,
  - format kontrol kriterleri dosyası,
  - Özet, Abstract, İçindekiler, Tablo Listesi, Şekil Listesi ve Kaynakça varlığı,
  - Word tablo nesnesi sayısı,
  - Word şekil nesnesi sayısı,
  - kenar boşluğu okunabilirliği,
  - Normal stil yazı tipi/punto bilgisi.

### Doğrulama Sonucu

- SAÜ FBE format uyum bölümü kalite kontrol raporuna eklendi.
- Ana tez DOCX içinde tablo ve şekil sayıları raporlanmaktadır.
- Kılavuz ve şablon dosyaları kalite kontrol raporunda izlenebilir hale geldi.

### Tez Açısından Önemi

Bu aşama, tez taslağının yalnızca içerik bütünlüğü bakımından değil, enstitü kılavuzu ve tez hazırlama şablonu bakımından da denetlenmeye başlamasını sağlar. Sonraki aşamada bu ön kontroller, kılavuzdaki kesin biçimsel değerlere göre pass/fail format kontrolüne dönüştürülecektir.

### Durum

Tamamlandı.

---

## Aşama 27.3 — SAÜ FBE Format Rules JSON and DOCX Format Alignment

Bu aşamada, SAÜ FBE tez hazırlama şablonundan sayfa boyutu, kenar boşluğu ve temel stil değerleri çıkarılarak makine tarafından okunabilir format kural dosyası oluşturulmuş ve ana tez DOCX dosyasına uygulanmıştır.

### Yapılanlar

- Şablon DOCX üzerinden format kuralları çıkarıldı:
  - `docs/sau_fbe_format_rules.json`
- Ana tez DOCX dosyası SAÜ FBE format kurallarına göre düzenlendi:
  - A4 sayfa boyutu
  - Sol kenar boşluğu 4.0 cm
  - Üst/alt/sağ kenar boşluğu 2.5 cm
  - Header/footer mesafesi 1.25 cm
  - Normal stil Times New Roman 12 punto
- SAÜ FBE format kontrol raporu üretildi:
  - `docs/sau_fbe_format_check_report.md`
  - `docs/sau_fbe_format_check_report.json`
- Genel tez kalite kontrol raporu yeniden üretildi:
  - `docs/tez_taslak_kalite_kontrol_raporu.md`
  - `docs/tez_taslak_kalite_kontrol_raporu.json`

### Tez Açısından Önemi

Bu aşama, ana tez DOCX dosyasının varsayılan Word/Letter biçiminden çıkarılarak SAÜ FBE tez hazırlama şablonundaki A4, kenar boşluğu ve temel yazı stili ayarlarına yaklaştırılmasını sağlamıştır. Böylece tez taslağı içerik bütünlüğünün yanında biçimsel uygunluk açısından da daha kontrollü hale gelmiştir.

### Durum

Tamamlandı.

---

## Aşama 27.4 — Reference Relevance Cleanup and Final Format Recheck

Bu aşamada, tez kaynakça taslağındaki konu dışı, düşük ilgililik düzeyindeki ve manuel tekrar olabilecek kaynaklar filtrelenmiş; ardından ana tez DOCX dosyası yeniden oluşturularak SAÜ FBE format kontrolleri tekrar çalıştırılmıştır.

### Yapılanlar

- Kaynakçadan hariç tutulacak ID listesi oluşturuldu:
  - `docs/reference_exclusion_ids.txt`
- Düşük ilgililik alanına sahip olmasına rağmen tez bağlamında korunacak kaynaklar gerekçelendirildi:
  - `docs/reference_keep_low_ids.txt`
- Kaynakça taslağı yeniden üretildi:
  - `docs/kaynakca_taslagi_literature_tracking.md`
  - `docs/kaynakca_taslagi_literature_tracking.csv`
- Kaynakça bölümü yeniden oluşturuldu:
  - `docs/bolum_7_kaynakca_taslagi.md`
  - `docs/bolum_7_kaynakca_taslagi.docx`
- Ana tez DOCX dosyası güncel kaynakça ile yeniden build edildi.
- SAÜ FBE sayfa/stil formatı tekrar uygulandı.
- Aşağıdaki kalite kontrol raporları yeniden üretildi:
  - `docs/reference_relevance_audit_report.md`
  - `docs/sau_fbe_format_check_report.md`
  - `docs/tez_caption_reference_check_report.md`
  - `docs/tez_taslak_kalite_kontrol_raporu.md`

### Tez Açısından Önemi

Bu aşama, tez kaynakçasını daha savunulabilir ve konu odaklı hale getirir. Manuel kopya kayıtları ve açıkça konu dışı kaynaklar kaynakça taslağından çıkarılmış; temel ML, IDS, feature selection ve SDN/DDoS savunma kaynakları ise gerekçeli olarak korunmuştur. Böylece kaynakça, hem literatür senteziyle hem de tez katkısıyla daha tutarlı hale getirilmiştir.

### Durum

Tamamlandı.

---

## Aşama 27.5 — SAÜ FBE Frontmatter-Based Main Thesis Build

Bu aşamada, SAÜ FBE tez yazım kılavuzu ve tez hazırlama şablonu esas alınarak ayrı bir frontmatter DOCX dosyası üretilmiş ve ana tez dosyası bu frontmatter ile yeniden oluşturulmuştur.

### Yapılanlar

- Tez metadata yapılandırma dosyası oluşturuldu:
  - `docs/thesis_metadata.yaml`
- SAÜ FBE uyumlu ön sayfa/frontmatter üretici araç oluşturuldu:
  - `ml-service/tools/build_sau_fbe_frontmatter_docx.py`
- Üretilen frontmatter dosyası:
  - `docs/sau_fbe_frontmatter_generated.docx`
- SAÜ FBE frontmatter kullanan ana tez build aracı oluşturuldu:
  - `ml-service/tools/build_main_thesis_with_sau_fbe_frontmatter.py`
- Yeni ana tez taslağı üretildi:
  - `docs/tez_ana_taslak_tr_sau_fbe.docx`
- SAÜ FBE format, tablo/şekil/kaynakça ve genel kalite kontrol raporları ayrı dosyalar halinde üretildi.

### Tez Açısından Önemi

Bu aşama, ana tez taslağının klasik otomatik frontmatter yerine SAÜ FBE kılavuzuna daha yakın bir ön sayfa yapısıyla oluşturulmasını sağlar. Dış kapak, iç kapak, onay sayfası, beyan, teşekkür, içindekiler/listeler ve özet/abstract bölümleri ayrı bir frontmatter dosyası olarak yönetilebilir hale getirilmiştir.

### Durum

Tamamlandı.

---

## Aşama 27.6 — Thesis Metadata Quality Control for SAÜ FBE Frontmatter

Bu aşamada, SAÜ FBE frontmatter üretiminde kullanılan tez metadata dosyası için kalite kontrol ve TODO alanı denetimi eklenmiştir.

### Yapılanlar

- Tez metadata dosyası ana bilgi kaynağı olarak tanımlandı:
  - `docs/thesis_metadata.yaml`
- Metadata kalite kontrol aracı oluşturuldu:
  - `ml-service/tools/check_thesis_metadata.py`
- Metadata kalite kontrol raporları üretildi:
  - `docs/thesis_metadata_quality_report.md`
  - `docs/thesis_metadata_quality_report.json`
- SAÜ FBE ana tez build aracına metadata TODO/check koruması eklendi:
  - `ml-service/tools/build_main_thesis_with_sau_fbe_frontmatter.py`
- TODO alanları varken build işlemi ancak `--allow-todo-metadata` parametresiyle yapılabilir hale getirildi.
- Güncel ana aday dosya tekrar üretildi:
  - `docs/tez_ana_taslak_tr_guncel_sau_fbe.docx`

### Tez Açısından Önemi

Bu aşama, dış kapak, iç kapak, onay sayfası ve özet sayfalarında kullanılacak tez bilgilerinin merkezi ve denetlenebilir bir metadata dosyasından yönetilmesini sağlar. Nihai teslim öncesinde `TODO_*` alanları temizlenmeden final build yapılması engellenebilir.

### Durum

Tamamlandı; gerçek öğrenci/danışman/jüri bilgileri girildiğinde final build tekrar çalıştırılacaktır.

---

## Aşama 28.1 — Chapter-Level Academic Quality Audit

Bu aşamada, tez bölümlerinin akademik içerik kalitesini değerlendirmek için bölüm bazlı otomatik kontrol raporları oluşturulmuştur.

### Yapılanlar

- Bölüm bazlı akademik kalite kontrol aracı oluşturuldu:
  - `ml-service/tools/check_chapter_academic_quality.py`
- Bölüm kalite raporu üretildi:
  - `docs/chapter_academic_quality_report.md`
  - `docs/chapter_academic_quality_report.json`
- Bölümlerin açılış ve kapanış paragraflarını inceleyen yardımcı rapor üretildi:
  - `docs/chapter_opening_closing_review.md`

### Kontrol Alanları

- Kelime sayısı
- Başlık sayısı
- Referans/atıf işareti sayısı
- Tablo/şekil atfı
- Tez alanına özgü terim sinyalleri
- Akademik bağlayıcı sinyaller
- TODO veya zayıf placeholder sinyalleri

### Tez Açısından Önemi

Bu aşama, biçimsel kontrollerden sonra tez metninin akademik bütünlüğünü bölüm bazında değerlendirmeye başlar. Sonraki aşamada zayıf görünen bölümler için iyileştirme önerileri ve doğrudan metin revizyonları hazırlanacaktır.

### Durum

Başlatıldı.

---

## Aşama 28.2 — Chapter Reference Anchor Integration

Bu aşamada, bölüm bazlı akademik kalite kontrol raporunda referans eksikliği görünen Bölüm 2, Bölüm 3 ve Bölüm 5 için literatür bağlantı paragrafları eklenmiştir.

### Yapılanlar

- Bölüm 2’ye kavramsal arka plan ve temel ML/IDS kaynak bağlantısı eklendi.
- Bölüm 3’e SDN-DDoS literatür sentezi ve karşılaştırma kaynak bağlantısı eklendi.
- Bölüm 5’e tartışma ve mevcut literatürle karşılaştırma kaynak bağlantısı eklendi.
- Kullanılan kaynak işaretleri `[BIBxxx]` ve `[LRxxx]` biçiminde izlenebilir hale getirildi.
- Bölüm kalite kontrol raporu yeniden çalıştırılmak üzere hazırlandı.

### Tez Açısından Önemi

Bu aşama, bölüm metinlerinin kaynakça taslağı ile daha görünür biçimde ilişkilendirilmesini sağlar. Böylece Bölüm 2, 3 ve 5 yalnızca açıklayıcı metinler olmaktan çıkarak literatür temelli akademik bölümler haline gelir.

### Durum

Tamamlandı.

---

## Aşama 28.3 — Weak Signal Cleanup in Chapter Drafts

Bu aşamada, bölüm bazlı akademik kalite kontrol raporunda zayıf/TODO sinyali olarak görünen ancak çoğu bağlamsal olarak normal olan ifadeler akademik dile dönüştürülmüştür.

### Yapılanlar

- Bölüm 2’de “Daha sonra” ve “eksik özellik” ifadeleri daha akademik karşılıklarla düzenlendi.
- Bölüm 4’te “eksik özellik”, “port bilgisinin eksik olması” ve “daha sonra” ifadeleri revize edildi.
- Bölüm 5’te “port bilgisi eksik olan koşular” ifadesi “port bilgisinin bulunmadığı koşular” biçiminde düzenlendi.
- Bölüm kalite kontrol raporu yeniden çalıştırılmak üzere hazırlandı.
- Güncellenen Markdown bölümlerinden ilgili DOCX dosyaları yeniden üretildi.

### Tez Açısından Önemi

Bu aşama, metindeki taslak izlenimi verebilecek ifadeleri azaltarak akademik dil tutarlılığını güçlendirmiştir. Ayrıca otomatik kalite kontrol aracının gerçek TODO/placeholder ile akademik bağlamdaki ifadeleri daha sağlıklı ayırt etmesine yardımcı olacak bir temizlik yapılmıştır.

### Durum

Tamamlandı.

---

## Aşama 28.3 — Weak Signal Cleanup and Rebuild Preparation

Bu aşamada, bölüm bazlı akademik kalite kontrol raporunda zayıf/TODO sinyali üreten ifadeler akademik dile dönüştürülmüş ve bölüm kalite kontrolü temiz hale getirilmiştir.

### Yapılanlar

- Bölüm 2’de “Daha sonra” ve “eksik özellik” gibi otomatik kalite kontrol tarafından zayıf sinyal olarak algılanan ifadeler revize edildi.
- Bölüm 4’te “eksik özellik”, “port bilgisinin eksik olması” ve “daha sonra” ifadeleri daha akademik karşılıklarla düzenlendi.
- Bölüm 5’te “port bilgisi eksik olan koşular” ifadesi “port bilgisinin bulunmadığı koşular” biçiminde düzenlendi.
- Bölüm 2, 3 ve 5 DOCX dosyaları güncel Markdown içeriklerinden yeniden üretildi.
- Bölüm bazlı akademik kalite kontrol raporu yeniden çalıştırıldı.

### Doğrulama Sonucu

- Chapter count: 6
- OK: 6
- Check: 0
- Zayıf/TODO sinyali: yok

### Tez Açısından Önemi

Bu aşama, tez bölümlerinin taslak izlenimi verebilecek ifadelerden arındırılmasını ve akademik dil bütünlüğünün güçlendirilmesini sağlamıştır. Bölüm bazlı otomatik kalite kontrolün temiz geçmesi, sonraki ana DOCX build ve final kalite kontrol aşamaları için daha sağlam bir zemin oluşturmuştur.

### Durum

Tamamlandı.

---

## Aşama 29.1 — Experimental Defense Review and Canonical/Diagnostic Justification

Bu aşamada, çalışma zamanı doğrulama deneyleri jüri/savunma perspektifinden eleştirel olarak değerlendirilmiş ve canonical/diagnostic deney ayrımı tez metnine daha açık şekilde bağlanmıştır.

### Yapılanlar

- Deneysel savunma değerlendirme aracı oluşturuldu:
  - `ml-service/tools/generate_experimental_defense_review.py`
- Savunma/jüri perspektifi raporu üretildi:
  - `docs/experimental_defense_review_report.md`
  - `docs/experimental_defense_review_report.json`
- `run_05_port_aware_repeat_validation` koşulunun ana deney olarak seçilme gerekçesi açıklandı.
- `run_03_aligned_clean` koşulunun destekleyici canonical koşu olduğu belirtildi.
- `run_04_repeat_mixed_validation` koşulunun diagnostic/partial repetition olarak kullanılma nedeni açıklandı.
- Bölüm 4’e canonical/diagnostic deney ayrımını açıklayan savunma paragrafı eklendi.
- Bölüm 4 artifact’li DOCX ve ana SAÜ FBE tez dosyası yeniden üretildi.

### Tez Açısından Önemi

Bu aşama, deneysel sonuçların yalnızca tablo ve şekil olarak sunulmasını değil, aynı zamanda tez savunmasında gelebilecek eleştirel sorulara karşı yöntemsel gerekçelerle açıklanmasını sağlar. Canonical ve diagnostic deney ayrımı, sonuçların akademik şeffaflığını ve savunulabilirliğini güçlendirmektedir.

### Durum

Tamamlandı.

---

## Aşama 29.2 — Original Contribution and Literature Gap Strengthening

Bu aşamada, Bölüm 5 tartışma bölümüne tezin özgün katkılarını ve literatürdeki boşlukla ilişkisini daha açık biçimde ortaya koyan yeni bir alt başlık eklenmiştir.

### Yapılanlar

- Bölüm 5’e `Tezin Özgün Katkıları ve Literatürdeki Boşlukla İlişkisi` alt başlığı eklendi.
- Tezin katkıları dört eksende yapılandırıldı:
  - offline ML başarımından çalışma zamanı SDN davranışına geçiş,
  - canonical/diagnostic deney ayrımının şeffaf raporlanması,
  - IDS ve IPS işlevlerinin aynı prototip içinde birleştirilmesi,
  - artifact tabanlı deneysel raporlama yaklaşımı.
- Bölüm 5 DOCX dosyası yeniden üretildi.
- Ana SAÜ FBE tez dosyası yeniden build edildi:
  - `docs/tez_ana_taslak_tr_guncel_sau_fbe.docx`
- Bölüm kalite, SAÜ FBE format ve genel tez kalite kontrolleri yeniden çalıştırıldı.

### Tez Açısından Önemi

Bu aşama, savunmada sorulabilecek “Bu tezin özgün katkısı nedir?” sorusuna daha güçlü ve doğrudan cevap verilmesini sağlar. Katkıların literatürdeki boşluklarla ilişkilendirilmesi, çalışmanın yalnızca teknik bir prototip değil, akademik olarak konumlandırılmış bir doktora tezi olarak sunulmasını güçlendirir.

### Durum

Tamamlandı.

---

## Aşama 29.3 — SAÜ FBE Frontmatter-Aware Quality Check Fix

Bu aşamada, kalite kontrol araçlarının SAÜ FBE frontmatter başlık sırasını ve büyük/küçük harf farklılıklarını doğru değerlendirmesi sağlanmıştır.

### Yapılanlar

- `check_sau_fbe_format_rules.py` aracı case-insensitive ve Türkçe karakter uyumlu hale getirildi.
- `check_thesis_draft_quality.py` içindeki başlık arama mantığı SAÜ FBE frontmatter yapısına göre güncellendi.
- `ABSTRACT`, `İÇİNDEKİLER`, `TABLO LİSTESİ` ve `ŞEKİL LİSTESİ` başlıklarının hatalı biçimde eksik görünmesi düzeltildi.
- Heading order kontrolü, SAÜ FBE sırasına göre değerlendirilecek şekilde güncellendi:
  - İçindekiler
  - Tablo Listesi
  - Şekil Listesi
  - Özet
  - Abstract
  - Bölüm 1–6
- Eski patch’ten kalan `all_texts` uyarı bloğu kaldırıldı.

### Tez Açısından Önemi

Bu aşama, tez dosyasında doğru şekilde bulunan ön bölüm başlıklarının kalite raporlarında hatalı biçimde eksik veya sırası bozuk görünmesini engellemiştir. Böylece kalite kontrol raporları SAÜ FBE frontmatter yapısıyla uyumlu hale getirilmiştir.

### Durum

Tamamlandı.

---

## Aşama 29.4 — Chapter 6 Contribution-Aligned Conclusion Strengthening

Bu aşamada, Bölüm 6 Sonuç ve Öneriler bölümü Bölüm 5’te eklenen özgün katkı ve literatür boşluğu tartışmasıyla hizalanmıştır.

### Yapılanlar

- Bölüm 6’ya `Tezin Akademik Katkısının Sonuç Açısından Değerlendirilmesi` alt başlığı eklendi.
- Tezin katkıları sonuç bölümünde dört eksende yeniden özetlendi:
  - ML modelinin SDN çalışma zamanı ortamına entegrasyonu,
  - port-aware/protocol-aware doğrulama yaklaşımı,
  - IDS ve IPS davranışlarının aynı prototip içinde birleştirilmesi,
  - artifact tabanlı yeniden üretilebilir deneysel raporlama zinciri.
- Bölüm 6 DOCX dosyası yeniden üretildi.
- Ana SAÜ FBE tez dosyası tekrar build edildi:
  - `docs/tez_ana_taslak_tr_guncel_sau_fbe.docx`
- Bölüm kalite, SAÜ FBE format, caption/reference ve genel tez kalite kontrolleri yeniden çalıştırıldı.

### Tez Açısından Önemi

Bu aşama, sonuç bölümünün yalnızca bulguları tekrar eden bir kapanış olmaktan çıkıp, tezin akademik katkısını literatürdeki boşlukla ilişkilendiren daha güçlü bir final bölümüne dönüşmesini sağlamıştır.

### Durum

Tamamlandı.

---

## Aşama 29.5 — Chapter 1 Contribution Alignment with Final Thesis Claims

Bu aşamada, Bölüm 1’deki araştırma katkıları kısmı Bölüm 5 ve Bölüm 6’da güçlendirilen nihai katkı diliyle hizalanmıştır.

### Yapılanlar

- Bölüm 1’de `1.6. Araştırmanın Katkıları` kısmının sonuna katkı hizalama paragrafı eklendi.
- Tezin katkıları giriş bölümünde dört eksende yeniden konumlandırıldı:
  - ML modelinin SDN çalışma zamanı ortamına entegrasyonu,
  - port-aware/protocol-aware doğrulama yaklaşımı,
  - IDS ve IPS işlevlerinin aynı prototip zincirinde ele alınması,
  - artifact tabanlı yeniden üretilebilir deneysel raporlama yapısı.
- Bölüm 1 DOCX dosyası yeniden üretildi.
- Ana SAÜ FBE tez dosyası tekrar build edildi:
  - `docs/tez_ana_taslak_tr_guncel_sau_fbe.docx`
- Bölüm kalite, SAÜ FBE format, caption/reference ve genel tez kalite kontrolleri yeniden çalıştırıldı.

### Tez Açısından Önemi

Bu aşama, giriş bölümünde vaat edilen katkılar ile tartışma ve sonuç bölümlerinde savunulan katkıların aynı akademik eksende ifade edilmesini sağlar. Böylece tez metninde giriş–tartışma–sonuç bütünlüğü güçlendirilmiştir.

### Durum

Tamamlandı.

---

## Aşama 30.1 — Inline Reference Marker Audit and APA Conversion Planning

Bu aşamada, tez bölümlerinde kullanılan teknik `[BIBxxx]`, `[LRxxx]` ve `[MANxxx]` atıf işaretleri envanterlenmiş ve APA7/SAÜ FBE uyumlu metin içi atıf dönüşümü için plan hazırlanmıştır.

### Yapılanlar

- Teknik atıf işaretlerini tarayan araç oluşturuldu:
  - `ml-service/tools/audit_inline_reference_markers.py`
- Teknik atıf işareti envanteri üretildi:
  - `docs/inline_reference_marker_audit.md`
  - `docs/inline_reference_marker_audit.csv`
  - `docs/inline_reference_marker_audit.json`
- APA benzeri metin içi atıf öneri aracı oluşturuldu:
  - `ml-service/tools/generate_inline_citation_replacement_plan.py`
- Atıf dönüşüm öneri dosyaları üretildi:
  - `docs/inline_citation_replacement_plan.md`
  - `docs/inline_citation_replacement_plan.csv`
- Teknik atıf işaretlerinin nihai tez diline dönüştürülmesi için politika dosyası oluşturuldu:
  - `docs/reference_conversion_policy.md`

### Tez Açısından Önemi

Bu aşama, tez metnindeki geliştirme amaçlı teknik kaynak işaretlerinin nihai akademik yazım diline dönüştürülmesi için güvenli bir ara katman oluşturur. Doğrudan otomatik replace yapılmadan önce hangi işaretlerin nerede kullanıldığı ve hangi APA benzeri atıfa karşılık geldiği görünür hale getirilmiştir.

### Durum

Tamamlandı; otomatik dönüşüm henüz uygulanmadı.

---

## Aşama 30.2 — Safe Inline Citation Replacement Pass

Bu aşamada, teknik `[BIBxxx]`, `[LRxxx]` ve `[MANxxx]` atıf işaretlerinin nihai APA7/SAÜ FBE tez diline dönüştürülmesi için güvenli ilk geçiş yapılmıştır.

### Yapılanlar

- Otomatik öneri tablosu incelendi ve doğrudan replace yapılmasının bazı marker’lar için riskli olduğu belirlendi.
- Manuel override tablosu oluşturuldu:
  - `docs/inline_citation_manual_override.csv`
  - `docs/inline_citation_manual_override.md`
- Güvenli görülen sınırlı marker’lar için kontrollü dönüşüm aracı oluşturuldu:
  - `ml-service/tools/apply_safe_inline_citation_replacements.py`
- İlk güvenli dönüşüm seti uygulandı:
  - `LR001`
  - `LR005`
  - `BIB053`
- Kalan marker’lar manuel doğrulama için korunmuştur.
- Atıf marker envanteri yeniden üretildi.
- İlgili bölüm DOCX dosyaları ve ana SAÜ FBE tez dosyası yeniden build edildi.

### Tez Açısından Önemi

Bu aşama, kaynak gösterme biçiminin nihai akademik dile yaklaştırılması için güvenli ve geri alınabilir bir yaklaşım sunar. Potansiyel olarak yanlış eşleşmiş kaynakların otomatik biçimde nihai metne aktarılması engellenmiş, yalnızca bağlamı güvenli görülen marker’lar dönüştürülmüştür.

### Durum

Kısmen tamamlandı; kalan marker’lar manuel doğrulama beklemektedir.

---

## Aşama 30.3 — Remaining Inline Citation Manual Review Pass

Bu aşamada, otomatik dönüştürülmeyen teknik atıf marker’ları için bağlam odaklı manuel kontrol dosyası üretilmiş ve güvenli görülen ek marker’lar nihai metin içi atıf biçimine dönüştürülmüştür.

### Yapılanlar

- Kalan marker’lar için bağlam odaklı manuel inceleme dosyası üretildi:
  - `docs/remaining_inline_marker_manual_review.md`
  - `docs/remaining_inline_marker_manual_review.csv`
- Manuel override tablosu güncellendi:
  - `docs/inline_citation_manual_override.csv`
  - `docs/inline_citation_manual_override.md`
- İkinci güvenli dönüşüm turunda bazı marker’lar APA benzeri metin içi atıflara dönüştürüldü.
- Kalan teknik marker’lar yeniden envanterlendi:
  - `docs/inline_reference_marker_audit.md`
  - `docs/inline_reference_marker_audit.csv`
  - `docs/inline_reference_marker_audit.json`
- İlgili bölüm DOCX dosyaları ve ana SAÜ FBE tez dosyası yeniden üretildi.

### Tez Açısından Önemi

Bu aşama, atıf dönüşümünün hızlı fakat hataya açık bir otomatik replace işlemi olmaktan çıkarılıp, bağlam temelli ve geri alınabilir bir akademik doğrulama sürecine dönüşmesini sağlar. Böylece yanlış kaynak-yazar eşleşmelerinin nihai tez metnine taşınma riski azaltılmıştır.

### Durum

Kısmen tamamlandı; kalan marker’lar için manuel doğrulama devam etmektedir.

---

## Aşama 30.4 — Final Inline Technical Marker Removal

Bu aşamada, tez bölümlerinde kalan teknik `[BIBxxx]`, `[LRxxx]` ve `[MANxxx]` atıf işaretleri, APA7’ye yakın metin içi atıf biçimleriyle değiştirilmiştir.

### Yapılanlar

- Kalan teknik marker’ların yalnızca kaynak bağlantısı paragraflarında geçtiği doğrulandı.
- Bölüm 2, Bölüm 3 ve Bölüm 5 kaynak bağlantısı paragrafları yeniden yazıldı.
- Teknik marker’lar şu biçimlere dönüştürüldü:
  - `(Mitchell, 2013)`
  - `(Balasaraswathi vd., 2017)`
  - `(Thaseen ve Kumar, 2017)`
  - `(Gaikwad ve Thool, 2015)`
  - `(Abreu Maranhão vd., 2020)`
  - `(Naik vd., 2020)`
  - `(Kalkan vd., 2017)`
  - `(Goeschel, 2016)`
  - `(Batool vd., 2025)`
  - `(Ganeshan vd., 2026)`
  - `(Chouhan vd., 2023)`
- Inline reference marker audit raporu yeniden üretildi.
- İlgili bölüm DOCX dosyaları ve ana SAÜ FBE tez dosyası yeniden build edildi.

### Doğrulama Hedefi

- `docs/inline_reference_marker_audit.md` içinde teknik marker sayısı `0` olmalıdır.
- Bölüm kalite raporu `OK: 6, Check: 0` olmalıdır.
- SAÜ FBE format raporu `OK: 22, Check: 0` olmalıdır.
- Genel tez kalite raporunda missing heading/file/artifact bulunmamalıdır.

### Tez Açısından Önemi

Bu aşama, geliştirme sürecinde kullanılan teknik kaynak işaretlerinin nihai akademik tez diline dönüştürülmesini sağlamıştır. Böylece metin içi atıflar, okuyucu ve jüri açısından daha doğal ve APA7/SAÜ FBE’ye daha yakın bir forma taşınmıştır.

### Durum

Tamamlandı.

---

## Aşama 31.1 — APA Inline Citation and Bibliography Consistency Audit

Bu aşamada, teknik atıf marker’ları temizlendikten sonra metin içi APA-benzeri atıflar ve kaynakça tutarlılığı denetlenmiştir.

### Yapılanlar

- Metin içi APA-benzeri atıfları tarayan araç oluşturuldu:
  - `ml-service/tools/audit_apa_inline_citations.py`
- APA metin içi atıf envanteri üretildi:
  - `docs/apa_inline_citation_audit.md`
  - `docs/apa_inline_citation_audit.csv`
  - `docs/apa_inline_citation_audit.json`
- Metin içi atıf–tracking tablosu tutarlılığını kontrol eden araç oluşturuldu:
  - `ml-service/tools/check_citation_bibliography_consistency.py`
- Tutarlılık raporu üretildi:
  - `docs/citation_bibliography_consistency_report.md`
  - `docs/citation_bibliography_consistency_report.csv`
  - `docs/citation_bibliography_consistency_report.json`
- APA7’ye yakın otomatik kaynakça üretim aracı oluşturuldu:
  - `ml-service/tools/generate_apa_like_references_md.py`
- APA-benzeri kaynakça taslağı üretildi:
  - `docs/references_apa_like.md`
  - `docs/references_apa_like.csv`

### Tez Açısından Önemi

Bu aşama, metin içi atıfların kaynakça kayıtlarıyla izlenebilirliğini artırır ve teknik geliştirme marker’larından akademik kaynak gösterme biçimine geçişi tamamlamaya yönelik temel altyapıyı oluşturur.

### Durum

Başlatıldı; nihai APA7 manuel kontrolü devam etmektedir.

---

## Aşama 31.3 — Canonical APA-Like Bibliography Generation

Bu aşamada, APA-benzeri kaynakça üretiminde duplicate MAN kayıtlarının ve hatalı `al.,` yazar biçimlerinin kaynakçaya girmesi engellenmiştir.

### Yapılanlar

- `generate_apa_like_references_md.py` aracı canonical override dosyasını esas alacak şekilde güncellendi.
- Kaynakça üretiminde `MAN` duplicate kayıtları ve `To verify from full text` placeholder kayıtları filtrelendi.
- Canonical consistency raporu için yeni araç oluşturuldu:
  - `ml-service/tools/check_citation_bibliography_consistency_canonical.py`
- Tutarlılık raporu canonical override tablosuna göre yeniden üretildi.
- APA-benzeri kaynakça yalnızca seçilmiş canonical `BIB`/`LR` ID’lerinden yeniden oluşturuldu:
  - `docs/references_apa_like.md`
  - `docs/references_apa_like.csv`

### Doğrulama Hedefleri

- `docs/citation_bibliography_consistency_report.md` içinde tüm atıflar `matched_by_override` olmalıdır.
- `docs/references_apa_like.md` içinde `al.,` biçimli hatalı yazar satırı kalmamalıdır.
- `docs/references_apa_like.md` içinde `To verify from full text` placeholder satırı kalmamalıdır.
- Kaynakça yaklaşık 11 canonical kayıt içermelidir.

### Tez Açısından Önemi

Bu aşama, metin içi atıflar ile kaynakça arasında canonical, izlenebilir ve daha temiz bir eşleşme sağlar. Böylece duplicate manuel kayıtların ve kısaltılmış geçici kaynakça satırlarının nihai tez taslağına taşınması engellenmiştir.

### Durum

Tamamlandı; nihai APA7 ayrıntı kontrolü manuel olarak sürdürülecektir.

---

## Aşama 31.4 — Manual APA Reference Override for LR Review Records

Bu aşamada, otomatik APA-benzeri kaynakça üretiminde LR review kayıtlarında oluşan hatalı `al., B. e.` ve `al., G. e.` yazar biçimleri manuel override mekanizmasıyla düzeltilmiştir.

### Yapılanlar

- Manuel kaynakça override dosyası oluşturuldu:
  - `docs/reference_apa_manual_override.csv`
- `generate_apa_like_references_md.py` aracı ID bazlı manuel kaynakça satırı override desteğiyle güncellendi.
- `LR001` ve `LR005` kayıtları için otomatik parser yerine manuel APA-benzeri kaynakça satırları kullanıldı.
- APA-benzeri kaynakça yeniden üretildi:
  - `docs/references_apa_like.md`
  - `docs/references_apa_like.csv`
- Kaynakça içinde hatalı `al.,` yazar biçimi ve `To verify from full text` placeholder satırları kontrol edildi.

### Tez Açısından Önemi

Bu aşama, otomatik BibTeX/LR ayrıştırma hatalarının nihai kaynakça taslağına taşınmasını engeller. Özellikle review makalelerinde kısaltılmış veya eksik yazar alanlarından kaynaklanan hatalar manuel override ile kontrol altına alınmıştır.

### Durum

Tamamlandı; nihai APA7 yazar listesi kontrolü Zotero/BibTeX kayıtları üzerinden ayrıca yapılacaktır.

---

## Aşama 31.6 — Clean DOCX Rebuild with Integrated APA-Like References

Bu aşamada, APA-benzeri kaynakça entegrasyonundan sonra oluşabilecek eski kaynakça kalıntıları ve boş paragraf şişmesi riskini azaltmak için ana tez DOCX dosyası temiz parçalardan yeniden oluşturulmuştur.

### Yapılanlar

- DOCX kaynakça temizlik denetim aracı oluşturuldu:
  - `ml-service/tools/audit_docx_reference_cleanup.py`
- Kaynakça Markdown dosyası tez bölümü formatına hazırlandı:
  - `docs/bolum_kaynakca_tr.md`
- Kaynakça DOCX üretim aracı oluşturuldu:
  - `ml-service/tools/build_references_docx.py`
- Kaynakça DOCX dosyası üretildi:
  - `docs/bolum_kaynakca_tr.docx`
- SAÜ FBE frontmatter, Bölüm 1–6 ve kaynakça DOCX parçalarını temiz biçimde birleştiren araç oluşturuldu:
  - `ml-service/tools/build_main_thesis_from_docx_parts.py`
- Ana tez dosyası temiz DOCX parçalarından yeniden üretildi:
  - `docs/tez_ana_taslak_tr_guncel_sau_fbe.docx`
- Rebuild öncesi yedek alındı:
  - `docs/tez_ana_taslak_tr_guncel_sau_fbe.before_clean_rebuild_with_references.docx`
- Kaynakça temizlik, SAÜ FBE format, genel tez kalite ve caption/reference kontrolleri yeniden çalıştırıldı.

### Tez Açısından Önemi

Bu aşama, kaynakçayı geçici olarak DOCX sonunda eklemek yerine, build zincirinin parçası haline getirir. Böylece eski kaynakça paragrafları, teknik marker kalıntıları, hatalı `al.,` yazar satırları ve gereksiz boş paragrafların ana tez dosyasında kalma riski azaltılmıştır.

### Durum

Tamamlandı; nihai Word alanları, içindekiler, tablo/şekil listeleri ve APA7 ayrıntı kontrolü daha sonraki aşamada yapılacaktır.

---

## Aşama 31.10 — Promote Selected MAN References to Canonical Bibliography Records

Bu aşamada, kullanıcı tarafından `manual_review` sayfasında `promote_to_canonical` olarak işaretlenen MAN kayıtları yeni canonical BIB kayıtlarına dönüştürülmüştür.

### Yapılanlar

- Kullanıcı `manual_review` kararlarını tamamladı:
  - `promote_to_canonical`: 16 kayıt
  - `canonical_duplicate`: 4 kayıt
- MAN kayıtlarını canonical BIB kayıtlarına dönüştüren araç oluşturuldu:
  - `ml-service/tools/promote_manual_references_to_canonical.py`
- Promote edilen MAN kayıtları için yeni `BIB900+` ID’leri üretildi.
- Eski MAN kayıtları `manual_promoted_to_canonical` / `Duplicate` olarak işaretlendi.
- Yeni BIB kayıtları `canonical_from_manual` olarak tracking tablosuna eklendi.
- Promotion mapping dosyası üretildi:
  - `docs/manual_to_canonical_promotion_map.csv`
- Promotion raporu üretildi:
  - `docs/manual_to_canonical_promotion_report.md`
- Expanded bibliography selection ve APA-like references yeniden üretildi.
- Ana tez DOCX kaynakçası güncellendi ve kalite kontrolleri yeniden çalıştırıldı.

### Tez Açısından Önemi

Bu aşama, daha önce yalnızca manuel/kırpılmış kayıt olarak tutulan fakat tez için değerli görülen çalışmaların izlenebilir canonical kaynak kayıtlarına dönüştürülmesini sağlar. Böylece kaynakça kapsamı güçlendirilmiş, MAN kayıtlarının belirsizliği azaltılmış ve literatür karşılaştırması ile kaynakça arasındaki tutarlılık artırılmıştır.

### Durum

Tamamlandı. Sonraki aşamada APA7 ayrıntı kalitesi, yazar adı biçimi, DOI/URL doğruluğu ve dergi/konferans alanları denetlenecektir.

---

## Aşama 32.5 — Zotero Reviewed Kaynakların Tez Bölümlerine Entegrasyonu

Bu aşamada reviewed Zotero kaynakça seçimi temel alınarak, tez metninde henüz açık biçimde kullanılmayan kaynaklar için bölüm bazlı yerleştirme planı oluşturulmuş ve Bölüm 2, Bölüm 3 ve Bölüm 5’e kontrollü sentez paragrafları eklenmiştir.

### Yapılanlar

- Reviewed Zotero kaynakça seçimi doğrulandı:
  - `docs/literature_review/zotero_clean/zotero_final_bibliography_selection_reviewed.csv`
  - `docs/references_zotero_apa_like_reviewed.md`
- Kaynak kullanım denetimi üretildi:
  - `docs/bibliography_reference_usage_audit_zotero_reviewed.md`
- Tez metninde açıkça kullanılmayan kaynaklar için bölüm hedefleme planı oluşturuldu:
  - `docs/literature_review/zotero_clean/uncited_reference_placement_plan.md`
  - `docs/literature_review/zotero_clean/uncited_reference_placement_plan.xlsx`
- Bölüm 2’ye SDN, IDS, özellik seçimi ve veri kümesi arka planını güçlendiren Zotero reviewed kaynak entegrasyon paragrafları eklendi.
- Bölüm 3’e SDN-DDoS, mitigation, feature selection, runtime/testbed ve anomaly detection literatürünü genişleten sentez paragrafları eklendi.
- Bölüm 5’e runtime doğrulama, veri kümesi sınırlılıkları, controller taraflı önleme davranışı ve gelecek çalışma tartışmasını güçlendiren paragraflar eklendi.

### Tez Açısından Önemi

Bu aşama, kaynakçanın yalnızca liste olarak kalmasını engelleyip, reviewed Zotero kaynaklarının tez metnindeki kavramsal arka plan, literatür sentezi ve tartışma bölümleriyle ilişkilendirilmesini sağlamıştır. Böylece kaynakça–metin tutarlılığı ve akademik izlenebilirlik güçlendirilmiştir.

### Durum

Tamamlandı. Bir sonraki aşamada güncellenen Markdown bölümleri ana DOCX’e yeniden işlenecek, kaynakça entegrasyonu ve atıf kullanım denetimi DOCX üzerinden tekrar çalıştırılacaktır.

---

## Aşama 32.8 — Zotero APA Metadata Düzeltmeleri ve Final Kaynakça Kalite Kontrolü

Bu aşamada reviewed Zotero kaynakça içindeki kalan APA-like metadata sorunları denetlenmiş ve tespit edilen son iki kayıt düzeltilmiştir.

### Yapılanlar

- Zotero APA kaynakça kalite denetim aracı çalıştırıldı:
  - `ml-service/tools/audit_zotero_apa_reference_quality.py`
- Denetim sonucunda iki sorunlu kayıt tespit edildi:
  - `ghada_abdelmoumin_performance_2021`: metadata içinde tekrar eden yazar kayıtları
  - `mohammad_bio-inspired_2022`: eksik venue bilgisi
- `ghada_abdelmoumin_performance_2021` için yazar listesi tekilleştirildi.
- `mohammad_bio-inspired_2022` için venue bilgisi `Computers, Materials & Continua` olarak düzeltildi.
- Reviewed kaynakça CSV, Markdown kaynakça dosyası ve kaynakça DOCX dosyası güncellendi:
  - `docs/references_zotero_apa_like_reviewed.csv`
  - `docs/references_zotero_apa_like_reviewed.md`
  - `docs/bolum_kaynakca_tr.md`
  - `docs/bolum_kaynakca_tr.docx`
- Ana tez DOCX dosyası güncel kaynakça ile yeniden oluşturuldu:
  - `docs/tez_ana_taslak_tr_guncel_sau_fbe.docx`
- Kaynakça temizlik, caption/reference, SAÜ FBE format ve genel tez kalite raporları yeniden üretildi.

### Tez Açısından Önemi

Bu aşama, kaynakça listesinin yalnızca sayısal olarak tamamlanmasını değil, Zotero’dan gelen metadata tekrarları, eksik dergi/konferans bilgileri ve APA-like biçim sorunları açısından da temizlenmesini sağlamıştır. Böylece kaynakça, tez metniyle tutarlı ve daha güvenilir bir nihai kontrol seviyesine taşınmıştır.

### Durum

Tamamlandı. Bir sonraki aşamada Word içindekiler, tablo listesi, şekil listesi, tablo/şekil numaralandırması ve nihai teslim öncesi manuel kontrol notları ele alınacaktır.

---

## Aşama 32.9 — Word Alanları, Caption Numaralandırması ve Teslim Öncesi Manuel Kontrol Notu

Bu aşamada ana tez DOCX dosyasının otomatik kalite kontrollerinden sonra Microsoft Word üzerinde yapılması gereken nihai alan güncelleme ve manuel kontrol adımları belgelenmiştir.

### Yapılanlar

- Tablo/şekil başlık numaralandırmasını denetleyen araç oluşturuldu:
  - `ml-service/tools/audit_caption_numbering_consistency.py`
- Ana tez DOCX üzerinde caption numaralandırma denetimi yapıldı:
  - `docs/caption_numbering_consistency_audit.md`
  - `docs/caption_numbering_consistency_audit.json`
- Nihai Word manuel kontrol notu oluşturuldu:
  - `docs/final_word_manual_check_note.md`

### Kontrol Edilecek Başlıca Konular

- Word içindekiler alanı
- Tablo Listesi
- Şekil Listesi
- Sayfa numaraları
- Bölüm bazlı tablo/şekil numaralandırması
- TODO metadata alanları
- Onay sayfası ve jüri bilgileri
- APA7 kaynakça ayrıntıları

### Tez Açısından Önemi

Bu aşama, otomatik üretilen DOCX dosyasının enstitü teslimine yaklaşmadan önce Word üzerinde güncellenmesi gereken dinamik alanlarını ve manuel biçimsel kontrollerini açık hale getirir. Böylece teknik build zinciri ile nihai teslim formatı arasındaki son kontrol adımları izlenebilir biçimde belgelenmiştir.

### Durum

Tamamlandı. Bir sonraki aşamada caption numaralandırma raporuna göre gerekiyorsa Bölüm 4 ve Bölüm 5 tablo/şekil numaraları düzeltilecektir.

---

## Aşama 32.10 — Tablo ve Şekil Numaralandırma Temizliği

Bu aşamada ana tez DOCX dosyasındaki tablo ve şekil başlık numaralandırmaları denetlenmiş ve tekrar eden veya geçici numara içeren başlıklar temizlenmiştir.

### Yapılanlar

- Caption numaralandırma denetimi çalıştırıldı:
  - `docs/caption_numbering_consistency_audit.md`
- İlk denetimde şu sorunlar görüldü:
  - `Tablo 3.x` placeholder numarası
  - `Tablo 5.x` placeholder numarası
  - Bölüm 4 deney tablo/şekillerinin Bölüm 5 içinde tekrar görünmesi
  - Bölüm 4 içinde düz `Tablo 1`, `Şekil 1` biçiminde numaralandırma
- Bölüm 3 placeholder numarası düzeltildi:
  - `Tablo 3.x` → `Tablo 3.7`
- Bölüm 4 deney çıktıları bölüm bazlı numaralandırmaya dönüştürüldü:
  - `Tablo 4.4.1`–`Tablo 4.4.7`
  - `Şekil 4.4.1`–`Şekil 4.4.4`
- Bölüm 5 literatür karşılaştırma tablosu düzeltildi:
  - `Tablo 5.x` → `Tablo 5.1`
- Tekrarlı caption grupları temizlendi.
- Güncel denetim sonucu:
  - Duplicate number groups: `0`
  - Suspicious caption count: `0`

### Tez Açısından Önemi

Bu aşama, tablo ve şekil başlıklarının tez boyunca daha tutarlı görünmesini sağlar. Özellikle Bölüm 4 runtime doğrulama çıktılarının bölüm/alt bölüm bağlamında numaralandırılması, Word üzerinde oluşturulacak Tablo Listesi ve Şekil Listesi için daha temiz bir temel oluşturur.

### Durum

Tamamlandı. Sonraki aşamada görsellerin DOCX içinde korunup korunmadığı ve Word alanlarının manuel güncelleme süreci kontrol edilecektir.

---

## Aşama 32.11 — Artifact Görsellerinin Korunması ve Final Caption Kontrolü

Bu aşamada Bölüm 4 runtime doğrulama artifact’lerinin ana tez DOCX içinde korunması ve tablo/şekil başlıklarının tutarlı biçimde algılanması sağlanmıştır.

### Yapılanlar

- Normal Bölüm 4 DOCX kullanıldığında ana tez dosyasında görsellerin düştüğü tespit edildi:
  - `Inline shape count: 0`
- Bu nedenle ana tez build sürecinde yeniden artifact’li Bölüm 4 dosyası kullanıldı:
  - `docs/bolum_4_yontem_ve_runtime_dogrulama_tr_with_artifacts.docx`
- Artifact’li Bölüm 4 dosyasındaki tekrar eden kapanış bölümü caption’ları pasifleştirildi.
- Çok noktalı tablo/şekil numaralarını algılayacak şekilde caption/reference kontrol aracı yeniden yazıldı:
  - `ml-service/tools/check_thesis_captions_and_references.py`
- Ana tez DOCX yeniden oluşturuldu:
  - `docs/tez_ana_taslak_tr_guncel_sau_fbe.docx`

### Güncel Kontrol Sonuçları

- Genel kalite kontrol:
  - Table count: `15`
  - Inline shape count: `4`
  - Heading order: `True`
  - Missing headings/files/artifacts: `0`
- Caption/reference kontrolü:
  - OK: `6`
  - Check: `0`
  - Detected table captions: `15`
  - Detected figure captions: `4`
- Caption numbering kontrolü:
  - Caption count: `19`
  - Duplicate number groups: `0`
  - Suspicious caption count: `0`

### Tez Açısından Önemi

Bu aşama, Bölüm 4’teki deneysel tablo ve şekillerin kaybolmadan ana tez dosyasına entegre edilmesini ve aynı zamanda Word Tablo/Şekil Listesi için tekrar eden veya geçici caption numaralarının temizlenmesini sağlamıştır. Böylece runtime validation artifact’leri tez metni içinde korunmuş ve biçimsel tutarlılık güçlendirilmiştir.

### Durum

Tamamlandı. Sonraki aşama, final teslim paketi envanteri ve nihai Word manuel kontrol sürecidir.

---

## Aşama 32.12 — Placeholder / TODO Temizliği ve Final Ön Bölüm Kontrolü

Bu aşamada ana tez DOCX dosyasında beklenmeyen geçici ifade, TODO, placeholder ve revizyon sinyali kalıp kalmadığı denetlenmiştir.

### Yapılanlar

- Placeholder denetim aracı oluşturuldu:
  - `ml-service/tools/audit_thesis_placeholders.py`
- Ana tez DOCX üzerinde placeholder denetimi çalıştırıldı:
  - `docs/thesis_placeholder_audit.md`
  - `docs/thesis_placeholder_audit.json`
- İlk denetimde iki gözden geçirme kaydı tespit edildi:
  - Teşekkür bölümündeki geçici ifade
  - Bölüm 5 içinde geçen `daha sonra` ifadesi
- Bu ifadeler akademik ve nötr biçimde güncellendi.
- Frontmatter, Bölüm 5 ve ana tez DOCX yeniden oluşturuldu.

### Güncel Sonuç

- Hit count: `9`
- Expected frontmatter TODO count: `9`
- Review count: `0`
- Beklenmeyen placeholder: `yok`

### Kalan Beklenen Alanlar

Aşağıdaki alanlar nihai teslim öncesinde gerçek bilgilerle doldurulmalıdır:

- `TODO_AD_SOYAD`
- `TODO_DANISMAN`
- `TODO_JURI_1`
- `TODO_JURI_2`
- `TODO_JURI_3`
- `TODO_JURI_4`
- `TODO_JURI_5`

### Tez Açısından Önemi

Bu aşama, tez metninde geçici çalışma notu, yarım bırakılmış ifade veya beklenmeyen TODO kalmadığını doğrulamıştır. Kalan TODO alanları yalnızca kapak, danışman ve jüri bilgilerine aittir; bu nedenle nihai kişisel/kurumsal bilgiler girilene kadar beklenen durumdadır.

### Durum

Tamamlandı. Sonraki aşama, Microsoft Word üzerinde içindekiler, tablo listesi, şekil listesi ve sayfa numaralarının güncellenmesidir.

---

## Aşama 34.x — Manuscript_without_author Literatür Tablosu Eşleştirme Planı

Bu aşama henüz uygulanmamıştır; A Grubu full text evidence card üretiminden sonra yapılacaktır.

### Amaç

Kullanıcının henüz yayımlanmamış makalesindeki literatür karşılaştırma tablolarını, tezdeki Zotero reviewed kaynakça ve full text evidence card çıktılarıyla eşleştirmek.

### Notlar

- Makaledeki bazı bölümler tezde kullanılabilir; ancak metin tez diliyle yeniden uyarlanmalıdır.
- NSL-KDD tez omurgasına alınmayacaktır.
- NSL-KDD yalnızca tarihsel/bağlamsal olarak, gerekli yerlerde yüzeysel anılacaktır.
- Tez sonrası makale revizyonunda NSL-KDD ile ilgili kısımlar çıkarılacak ve çalışma CIC-DDoS2019 / CICFlowMeter-style features / SDN runtime IDS/IPS eksenine taşınacaktır.

### Beklenen Çıktılar

- `docs/literature_review/manuscript_to_thesis_integration_plan.md`
- Makaledeki kaynaklar ile reviewed Zotero kaynakları arasında eşleştirme tablosu
- Bölüm 3 ve Bölüm 5 için güncelleme önerileri

### Durum

Planlandı; A Grubu full text evidence card üretiminden sonra uygulanacak.

---

## Aşama 34.4 — Bölüm 5 Full Text Destekli Tartışma Güçlendirme

Bu aşamada A Grubu full text evidence card çıktıları ve literatürdeki SDN/DDoS/IDS-IPS çalışma zamanı doğrulama boşlukları dikkate alınarak Bölüm 5'e kontrollü bir tartışma bloğu eklenmiştir.

### Yapılanlar

- Bölüm 5'e şu alt başlık altında yeni tartışma bloğu eklendi:
  - `5.x. Çalışma Zamanı IDS/IPS Uygulanabilirliği Açısından Tartışma`
- Eklenen tartışma bloğunda şu noktalar güçlendirildi:
  - Literatürdeki detection-only yaklaşımların sınırlılığı
  - Offline sınıflandırma başarımı ile SDN runtime uygulanabilirliği arasındaki boşluk
  - Model çıktısının controller policy kararına dönüştürülmesinin önemi
  - OpenFlow tabanlı `drop`, `rate-limit` ve `quarantine` aksiyonlarının tez katkısı içindeki yeri
  - Yanlış pozitiflerin SDN tabanlı IPS sistemlerinde operasyonel etkisi
  - F1-score, AUC, FAR/FPR ve çalışma zamanı doğrulama çıktılarının birlikte değerlendirilmesi gereği
- Bölüm 5 DOCX yeniden üretildi:
  - `docs/bolum_5_tartisma_sinirliliklar_gelecek_calismalar_tr.docx`
- Ana tez DOCX yeniden oluşturuldu:
  - `docs/tez_ana_taslak_tr_guncel_sau_fbe.docx`
- Rebuild sırasında Bölüm 4 için artifact'li DOCX korunmuştur:
  - `docs/bolum_4_yontem_ve_runtime_dogrulama_tr_with_artifacts.docx`

### Kontrol Sonuçları

- Caption/reference kontrolü:
  - OK: `6`
  - Check: `0`
  - Word table count: `15`
  - Inline shape count: `4`
  - Detected table captions: `15`
  - Detected figure captions: `4`
- Caption numbering kontrolü:
  - Duplicate number groups: `0`
  - Suspicious caption count: `0`
- Placeholder kontrolü:
  - Review count: `0`
  - Beklenmeyen placeholder: `yok`

### Tez Açısından Önemi

Bu aşama, tezin literatürdeki çevrimdışı sınıflandırma odaklı DDoS tespit çalışmalarından nasıl ayrıldığını daha açık hale getirmiştir. Eklenen tartışma, tez katkısını yalnızca yüksek model başarımı üzerinden değil, model çıktısının SDN denetleyici üzerinde uygulanabilir IPS aksiyonlarına dönüştürülmesi üzerinden temellendirmektedir.

### Durum

Tamamlandı. Sonraki aşama, Bölüm 3 literatür tablolarının full text evidence card çıktılarıyla güçlendirilmesi veya manuscript tablosu ile Zotero/full text kaynaklarının eşleştirilmesidir.

---

## Aşama 34.5-B — Bölüm 3 Tablolarının Full Text Evidence Card ile Fiilî Güncellenmesi

Bu aşama planlanmıştır; Bölüm 3'e full text destekli genel sentez eklendikten sonra uygulanacaktır.

### Amaç

Bölüm 3'teki literatür tablolarını, A Grubu full text evidence card sonuçlarıyla daha ayrıntılı ve yöntemsel olarak güçlü hale getirmek.

### Güncellenecek Öncelikli Tablolar

- `Tablo 3.4. Runtime/Controller/Testbed Odaklı Seçilmiş Çalışmalar`
- `Tablo 3.5. Mitigation/Prevention Odaklı Seçilmiş Çalışmalar`
- `Tablo 3.7. SDN tabanlı DDoS tespit ve önleme çalışmalarının yöntemsel karşılaştırması`

### Kullanılacak Plan Dosyaları

- `docs/literature_review/zotero_clean/chapter_3_table_revision_plan.md`
- `docs/literature_review/zotero_clean/chapter_3_table_revision_plan.csv`
- `docs/literature_review/zotero_clean/fulltext_evidence_cards_A_core.md`
- `docs/literature_review/zotero_clean/fulltext_evidence_cards_A_core.csv`

### Güncelleme İlkeleri

- Tabloya bütün adaylar eklenmeyecek; tez katkısını en iyi destekleyen kaynaklar seçilecektir.
- Detection-only çalışmalar ile runtime/controller/testbed doğrulaması yapan çalışmalar açık ayrıştırılacaktır.
- Mitigation/prevention aksiyonu üreten çalışmalar ayrıca işaretlenecektir.
- NSL-KDD deneysel omurga olarak kullanılmayacak; yalnızca tarihsel/bağlamsal not düzeyinde tutulacaktır.
- CIC-DDoS2019 ve CICFlowMeter-style özellikler tez veri seti yönelimiyle uyumlu biçimde vurgulanacaktır.

### Durum

Planlandı. Bir sonraki içerik revizyon aşamasında uygulanacaktır.

---

## Aşama 35 — Manuscript Literatür Tablolarının Zotero/Full Text Kaynaklarıyla Eşleştirilmesi

Bu aşamada tez sonrası geliştirilecek makale taslağı içinde yer alan `Manuscript.docx` dosyasındaki literatür ve karşılaştırma tabloları, reviewed Zotero kaynakçası ve full text temelli literatür iş akışıyla eşleştirilmiştir.

### Kullanılan Dosyalar

- Manuscript kaynak dosyası:
  - `docs/literature_review/source_files/Manuscript.docx`
- Manuscript tablo envanteri:
  - `docs/literature_review/manuscript_alignment/manuscript_table_inventory.md`
  - `docs/literature_review/manuscript_alignment/manuscript_table_inventory.csv`
- Zotero eşleştirme çıktıları:
  - `docs/literature_review/manuscript_alignment/manuscript_zotero_alignment_v2.csv`
  - `docs/literature_review/manuscript_alignment/manuscript_zotero_alignment_report_v2.md`
- Karar raporları:
  - `docs/literature_review/manuscript_alignment/manuscript_alignment_decisions.csv`
  - `docs/literature_review/manuscript_alignment/manuscript_alignment_decision_report.md`

### Manuscript Tablo Envanteri

`Manuscript.docx` içinde toplam 6 tablo tespit edilmiştir.

Öne çıkan tablolar:

- Table 1:
  - 35 satır, 5 sütun
  - Genel literatür karşılaştırma tablosu
- Table 5:
  - 20 satır, 11 sütun
  - Ayrıntılı literatür / metrik karşılaştırma tablosu
- Table 6:
  - 7 satır, 11 sütun
  - Özet/final karşılaştırma tablosu
- Table 4:
  - 32 satır, 12 sütun
  - Model/hiperparametre ve CIC-DDoS2019 sonuç tablosu

### Zotero Eşleştirme Sonuçları

`manuscript_zotero_alignment_v2.csv` üzerinden yapılan gelişmiş soyad-yıl tabanlı eşleştirme sonucunda:

- Toplam karşılaştırılan satır: 59
- Güçlü soyad-yıl eşleşmesi: 53
- Güvenli eşleşmeyen satır: 4
- Proposed Model satırı: 2

### Karar Raporu Sonuçları

`manuscript_alignment_decision_report.md` çıktısına göre:

- Tez literatürü veya karşılaştırma tartışması için kullanılabilir satır: 40
- NSL-KDD / tarihsel-bağlamsal düzeyde tutulacak satır: 10
- Destekleyici düzeyde tutulacak satır: 5
- Manuel kontrol gerektiren satır: 2
- Makale sonucu olarak kalacak Proposed Model satırı: 2

### NSL-KDD Politikası

Manuscript tablolarında NSL-KDD içeren satırlar tezde deneysel omurga olarak kullanılmamıştır. Bu satırlar yalnızca eski benchmark odaklı literatürü tarihsel ve bağlamsal düzeyde göstermek amacıyla değerlendirilmiştir.

Bu politika, tezdeki mevcut veri seti yönelimiyle uyumludur:

- NSL-KDD tez deneylerinde kullanılmaz.
- NSL-KDD yalnızca literatürdeki klasik IDS çalışmalarının bağlamı için sınırlı biçimde anılır.
- Tezin deneysel omurgası CIC-DDoS2019 ve CICFlowMeter-style akış özellikleri üzerine kuruludur.
- Tez sonrası makalede NSL-KDD odaklı satırlar azaltılacak veya çıkarılacaktır.

### Bölüm 5'e Eklenen Tartışma

Manuscript–Zotero/full text eşleştirme bulgularına dayanarak Bölüm 5'e kısa bir ek tartışma bölümü eklenmiştir:

- CIC-DDoS2019 tabanlı çalışmaların çoğunda yüksek sınıflandırma başarımı raporlandığı,
- ancak bu başarıların çoğu zaman controller-level runtime decision, port/protocol-aware traffic interpretation ve aktif prevention aksiyonlarıyla birlikte değerlendirilmediği,
- bu tezin Final XGBoost Top-20 modeli, FastAPI inference servisi, Ryu denetleyicisi, OpenFlow kural üretimi ve `drop`, `rate-limit`, `quarantine` aksiyonlarıyla bu boşluğu hedeflediği vurgulanmıştır.

### Son Kontrol Durumu

Aşama sonunda ana tez DOCX dosyası yeniden üretilmiş ve kalite kontrolleri çalıştırılmıştır.

Son durum:

- General quality: OK
- Paragraph count: 851
- Non-empty paragraph count: 766
- Table count: 15
- Inline shape count: 4
- Heading order: OK
- Caption/reference summary: OK 6 / Check 0
- Detected table captions: 15
- Detected figure captions: 4
- Caption duplicate groups: 0
- Suspicious caption count: 0
- Unexpected placeholder review count: 0

### Durum

Tamamlandı.

