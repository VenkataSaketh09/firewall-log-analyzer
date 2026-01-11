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

### Log ingestion

The backend automatically monitors local log files on the server:
- Log ingestion starts automatically with the backend server
- Monitors log files: `/var/log/auth.log`, `/var/log/ufw.log`, `/var/log/kern.log`, `/var/log/syslog`, `/var/log/messages`
- Logs are parsed and stored directly in MongoDB

The backend also exposes an HTTP ingestion endpoint (`POST /api/logs/ingest`) for manual log ingestion and batch processing.