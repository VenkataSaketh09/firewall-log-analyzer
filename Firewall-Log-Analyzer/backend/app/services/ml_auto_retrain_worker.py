"""
Phase 11: Optional auto-retrain worker

Controlled via env vars:
- ML_AUTO_RETRAIN=true|false (default false)
- ML_AUTO_RETRAIN_INTERVAL_HOURS (default 168 = 7 days)
"""

from __future__ import annotations

import os
import threading
import time
from datetime import datetime

from app.services.ml_storage import start_training_run, finish_training_run
from app.services.ml_retrain_pipeline import run_retrain


def start_auto_retrain_worker() -> None:
    enabled = os.getenv("ML_AUTO_RETRAIN", "false").lower() == "true"
    if not enabled:
        return

    interval_hours = int(os.getenv("ML_AUTO_RETRAIN_INTERVAL_HOURS", "168"))
    interval_seconds = max(60, interval_hours * 3600)

    def _loop():
        while True:
            try:
                requested = {"train_anomaly": True, "train_classifier": True, "trigger": "auto"}
                run_id = start_training_run(requested)
                try:
                    payload = run_retrain(True, True, run_id=run_id)
                    finish_training_run(run_id, status="completed", results=payload)
                except Exception as e:
                    finish_training_run(run_id, status="failed", error=str(e))
            except Exception:
                # If DB is down or env not set, don't crash the server; try again next interval.
                pass

            time.sleep(interval_seconds)

    t = threading.Thread(target=_loop, daemon=True, name="ml_auto_retrain_worker")
    t.start()


