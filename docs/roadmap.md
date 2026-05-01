## Aşama 8 — Delta-Based Flow Rate, Protocol Awareness and Edge Filtering

### Durum
Devam ediyor / Test edildiğinde tamamlandı olarak işaretlenecek.

### Eklenen Dosyalar
- `controller/campus_l3_ids_controller_v5.py`

### Yapılan Değişiklikler
- Controller V5 sürümü oluşturuldu.
- Flow istatistiklerinde delta-based hız hesabı eklendi.
- `packet_rate` artık toplam ortalama yerine son ölçüm aralığındaki paket/saniye değerini temsil ediyor.
- `byte_rate` artık toplam ortalama yerine son ölçüm aralığındaki byte/saniye değerini temsil ediyor.
- `cumulative_packet_rate` ve `cumulative_byte_rate` ayrıca loglanmaya başlandı.
- `ip_proto` değeri flow match içine eklendi.
- ICMP/TCP/UDP akışlarının ayrıştırılması için temel yapı kuruldu.
- ML tahmini yalnızca kaynak hostun bağlı olduğu edge switch üzerinde yapılacak şekilde filtreleme eklendi.
- `flow_stats.csv` tüm switchlerden kayıt almaya devam ediyor.
- `predictions.csv` sadece source-edge switchlerde tahmin kaydı üretiyor.

### Test Komutları

ML API:

```bash
cd ~/sdn-campus-security-platform
source venv/bin/activate
cd ml-service
uvicorn app:app --host 127.0.0.1 --port 8000

---

## Aşama 9 — Policy Engine

### Durum
Devam ediyor / Test edildiğinde tamamlandı olarak işaretlenecek.

### Eklenen Dosyalar
- `controller/campus_l3_ids_controller_v6.py`

### Yapılan Değişiklikler
- Controller V6 sürümü oluşturuldu.
- ML API çıktısını doğrudan uygulamak yerine policy engine katmanı eklendi.
- `allow`, `monitor`, `rate_limit`, `drop`, `quarantine_candidate` final action yapısı oluşturuldu.
- Confidence tabanlı karar eşikleri tanımlandı.
- Kaynak IP bazlı tekrar sayacı eklendi.
- Tekrarlayan yüksek güvenli saldırı kararları için `quarantine_candidate` üretimi eklendi.
- `logs/policy_decisions.csv` dosyası eklendi.
- Sistem hâlâ fail-open çalışıyor; ML API hatasında final action `allow` oluyor.
- Bu aşamada gerçek OpenFlow mitigation uygulanmıyor, sadece politika kararı loglanıyor.

### Policy Eşikleri
- `confidence < 0.70` → `allow`
- `0.70 <= confidence < 0.85` → `monitor`
- `0.85 <= confidence < 0.95` → `rate_limit`
- `confidence >= 0.95` → `drop`
- Aynı kaynak IP için yüksek güvenli saldırı kararı 3 kez tekrar ederse → `quarantine_candidate`

### Test Komutları

ML API:

```bash
cd ~/sdn-campus-security-platform
source venv/bin/activate
cd ml-service
uvicorn app:app --host 127.0.0.1 --port 8000
