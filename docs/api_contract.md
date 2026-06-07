# SDN Campus Security Platform — ML API Contract

Bu doküman, `ml-service/app.py` FastAPI servisinin endpoint yapısını tanımlar.

---

## Genel Ayrım

Servis iki farklı tahmin hattını destekler:

1. SDN Controller Runtime Prediction
   - Endpoint: `/predict`
   - Kullanım: Ryu controller tarafından çağrılır.
   - Feature formatı: controller runtime flow statistics.

2. CIC-DDoS2019 / Offline ML Prediction
   - Endpoint: `/predict-cicddos`
   - Kullanım: CIC-DDoS2019 / CICFlowMeter-style feature set ile eğitilmiş modelin test edilmesi.
   - Aktif model: PSO-LightGBM selected model.
   - Feature count: 13.

---

## GET /health

Servis sağlık durumunu ve model yükleme durumunu döndürür.

Örnek çıktı:

```json
{
  "status": "healthy",
  "model_status": "loaded",
  "active_model_dir": "/root/sdn-campus-security-platform/ml-service/models/active"
}
