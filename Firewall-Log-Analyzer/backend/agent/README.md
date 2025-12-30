### Remote log forwarding agent

This agent solves the “many VMs” collection problem by shipping each VM’s local logs to the central backend **over HTTP** using the existing ingestion endpoint:

- `POST /api/logs/ingest` (requires `X-API-Key`)

### Run (manual)

Set your backend URL + API key:

```bash
export FLA_INGEST_URL="http://<backend-host>:8000/api/logs/ingest"
export FLA_API_KEY="<your-api-key>"
```

Run with defaults (tails `auth.log` and `ufw.log`):

```bash
python3 backend/agent/log_forwarder.py
```

Or specify explicit sources (repeat `--source`):

```bash
python3 backend/agent/log_forwarder.py \
  --source /var/log/auth.log:auth.log \
  --source /var/log/ufw.log:ufw.log
```

### Notes

- **Batching**: sends batches of log lines to reduce overhead (`--batch-size`, `--flush-seconds`).
- **Rotation**: best-effort handling of log rotation (similar to `tail -F`).
- **Security**: use a dedicated API key and restrict backend access (firewall / VPN / allowlist).


