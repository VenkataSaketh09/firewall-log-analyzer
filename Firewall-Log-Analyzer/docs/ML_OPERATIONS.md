## ML Operations Guide (Phases 9–11)

### What’s deployed
- **Anomaly model**: `ml_engine/models/anomaly_detector.pkl` (IsolationForest + calibration)
- **Threat classifier**: `ml_engine/models/threat_classifier.pkl` (RandomForest; trained labels: NORMAL/BRUTE_FORCE/SUSPICIOUS)
- **Shared scaler**: `ml_engine/models/feature_scaler.pkl`
- **Label encoder**: `ml_engine/models/label_encoder.pkl`
- **Metrics**: `ml_engine/models/anomaly_metrics.json`, `ml_engine/models/classifier_metrics.json`
- **Metadata**: `ml_engine/models/model_metadata.json`

### Backend endpoints (monitoring)
- **Backend health**: `GET /health`
- **ML health**: `GET /health/ml`
- **ML status**: `GET /api/ml/status`
- **ML metrics**: `GET /api/ml/metrics`
- **Manual prediction**: `POST /api/ml/predict`
- **Retrain (background)**: `POST /api/ml/retrain`

### Threat endpoints (ML enrichment)
Threat endpoints now include optional ML fields per detection:
- `ml_anomaly_score`
- `ml_predicted_label`
- `ml_confidence`
- `ml_risk_score` (0–100)
- `ml_reasoning` (list of strings)

Endpoints:
- `GET /api/threats/brute-force?include_ml=true`
- `GET /api/threats/ddos?include_ml=true`
- `GET /api/threats/port-scan?include_ml=true`

### Phase 7 storage (MongoDB collections)
- **`ml_predictions`**: stored prediction records (best-effort)
- **`ml_training_history`**: retrain runs and outcomes
- **`ml_features_cache`**: cached engineered feature rows (TTL)

### Environment variables
Backend ML toggles:
- **`ML_ENABLED`**: `true|false` (default `true`)
- **`ML_STORE_PREDICTIONS`**: `true|false` (default `true`)
- **`ML_CACHE_FEATURES`**: `true|false` (default `true`)
- **`ML_FEATURE_CACHE_TTL_HOURS`**: integer hours (default `24`)

### Low-latency tips
- Keep `ML_CACHE_FEATURES=true` to avoid recomputing engineered features for repeated identical inputs.
- Avoid per-log scoring inside large loops; prefer scoring one representative log for aggregated detections (as implemented).

### Retraining (manual)
Trigger retraining:

```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"train_anomaly":true,"train_classifier":true}' \
  http://localhost:8000/api/ml/retrain
```

### Model versioning (Phase 11)
Every retrain creates two snapshots in `ml_engine/models/versions/`:
- **pre**: before retraining (safety snapshot)
- **post**: after retraining (marked active)

List versions:

```bash
curl http://localhost:8000/api/ml/versions
```

Rollback:

```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"version_id":"2025-12-30_20-40-12"}' \
  http://localhost:8000/api/ml/rollback
```

### Auto retraining (optional)
Enable automatic retraining worker via env vars:
- `ML_AUTO_RETRAIN=true`
- `ML_AUTO_RETRAIN_INTERVAL_HOURS=168` (default: 7 days)

Check retrain status:

```bash
curl http://localhost:8000/api/ml/status
```


