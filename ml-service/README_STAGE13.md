# Stage 13 ML Service Artifacts

Copy these files into:

```text
~/sdn-campus-security-platform/ml-service/
```

Expected structure:

```text
ml-service/
├── app.py
├── logs/
└── models/
    └── active/
        ├── model.pkl
        ├── scaler.pkl              # optional
        ├── feature_order.json
        ├── label_mapping.json
        └── model_metadata.json
```

If `model.pkl` is missing, the API automatically uses the heuristic fallback model.

Run:

```bash
cd ~/sdn-campus-security-platform
source venv/bin/activate
cd ml-service
uvicorn app:app --host 127.0.0.1 --port 8000
```

Check:

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/model-info
```
