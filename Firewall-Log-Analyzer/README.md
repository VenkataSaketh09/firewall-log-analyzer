# Firewall Log Analyzer and Monitoring Tool

Tech Stack:
- FastAPI (Python)
- React.js
- MongoDB Atlas
- Rule-based + ML detection

This project analyzes Linux firewall logs in real time to detect
brute force, port scanning, and anomalous behavior.

### ML operations

**Important**: ML services are automatically integrated into the backend and initialize on startup. No separate ML service startup is required.

The backend will automatically:
- Initialize ML models on startup (if models exist in `ml_engine/models/`)
- Fall back to rule-based detection if ML models are unavailable
- Provide ML predictions via `/api/ml/predict` endpoint
- Include ML analysis in threat detection endpoints (brute force, DDoS, port scan)

Check ML status:
- Backend health: `GET /health/ml`
- Detailed status: `GET /api/ml/status`

See `docs/ML_OPERATIONS.md` for:
- ML health/status endpoints
- Retraining and metrics endpoints
- DB collections for ML predictions/training history/feature cache

### Remote log forwarding (many VMs)

The backend exposes an HTTP ingestion endpoint (`POST /api/logs/ingest`). To collect logs from **many VMs**, run the included forwarding agent on each VM:

- `backend/agent/log_forwarder.py` (see `backend/agent/README.md`)