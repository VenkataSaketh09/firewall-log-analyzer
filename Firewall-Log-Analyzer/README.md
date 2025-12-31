# Firewall Log Analyzer and Monitoring Tool

Tech Stack:
- FastAPI (Python)
- React.js
- MongoDB Atlas
- Rule-based + ML detection

This project analyzes Linux firewall logs in real time to detect
brute force, port scanning, and anomalous behavior.

### ML operations

See `docs/ML_OPERATIONS.md` for:
- ML health/status endpoints
- Retraining and metrics endpoints
- DB collections for ML predictions/training history/feature cache

### Remote log forwarding (many VMs)

The backend exposes an HTTP ingestion endpoint (`POST /api/logs/ingest`). To collect logs from **many VMs**, run the included forwarding agent on each VM:

- `backend/agent/log_forwarder.py` (see `backend/agent/README.md`)