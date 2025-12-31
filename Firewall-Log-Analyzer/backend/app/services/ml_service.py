"""
ML Service Wrapper

Responsibilities:
- Initialize/load ML models from ml_engine
- Provide anomaly scoring + threat classification
- Provide a unified risk scoring API
- Gracefully fallback to rule-based results on failure
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from app.services.ml_storage import (
    make_cache_key,
    cache_get_features,
    cache_set_features,
    store_prediction,
)


def _ensure_repo_root_on_path() -> Path:
    """
    Ensure repository root is on sys.path so `import ml_engine` works even when
    backend is started from `backend/` directory.
    """
    repo_root = Path(__file__).resolve().parents[3]  # services/ -> app/ -> backend/ -> repo_root/
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    return repo_root


def _month_abbr(dt: datetime) -> str:
    return dt.strftime("%b")


def _time_hms(dt: datetime) -> str:
    return dt.strftime("%H:%M:%S")


def _severity_to_confidence(sev: str) -> float:
    s = (sev or "").strip().upper()
    return {
        "CRITICAL": 0.95,
        "HIGH": 0.85,
        "MEDIUM": 0.70,
        "LOW": 0.55,
    }.get(s, 0.50)


def _clip01(x: float) -> float:
    return max(0.0, min(1.0, float(x)))


@dataclass
class MLResult:
    ml_enabled: bool
    ml_available: bool
    anomaly_score: Optional[float] = None
    predicted_label: Optional[str] = None
    confidence: Optional[float] = None
    risk_score: Optional[float] = None  # 0-100
    reasoning: list[str] = None
    error: Optional[str] = None


class MLService:
    def __init__(self) -> None:
        self.enabled = os.getenv("ML_ENABLED", "true").lower() == "true"
        self.store_predictions = os.getenv("ML_STORE_PREDICTIONS", "true").lower() == "true"
        self.cache_features = os.getenv("ML_CACHE_FEATURES", "true").lower() == "true"
        self._initialized = False
        self._last_error: Optional[str] = None
        self._repo_root: Optional[Path] = None

        # Lazy-imported ml_engine hooks
        self._predict_anomaly = None
        self._predict_threat_type = None
        self._load_models = None
        self._models = None
        self._raw_to_unit_interval = None
        self._FeatureExtractor = None

    def initialize(self, force_reload: bool = False) -> bool:
        if not self.enabled:
            self._initialized = True
            self._last_error = None
            return False

        try:
            self._repo_root = _ensure_repo_root_on_path()

            from ml_engine.inference.model_loader import load_models
            from ml_engine.training.train_anomaly_detector import raw_to_unit_interval
            from ml_engine.features.feature_extractor import FeatureExtractor

            # Warm-load models (and validate model artifacts exist)
            self._models = load_models(force_reload=force_reload)

            self._load_models = load_models
            self._raw_to_unit_interval = raw_to_unit_interval
            self._FeatureExtractor = FeatureExtractor

            self._initialized = True
            self._last_error = None
            return True
        except Exception as e:
            self._initialized = True
            self._last_error = str(e)
            return False

    def status(self) -> Dict[str, Any]:
        if not self._initialized:
            self.initialize()

        available = self.enabled and self._last_error is None

        details: Dict[str, Any] = {
            "enabled": self.enabled,
            "available": available,
            "initialized": self._initialized,
            "last_error": self._last_error,
        }

        # Add model artifact visibility (best-effort)
        try:
            if self._repo_root is None:
                self._repo_root = _ensure_repo_root_on_path()
            models_dir = self._repo_root / "ml_engine" / "models"
            details["models_dir"] = str(models_dir)
            if models_dir.exists():
                details["artifacts"] = sorted([p.name for p in models_dir.iterdir() if p.is_file()])
        except Exception:
            pass

        return details

    def _build_ml_input(
        self,
        *,
        timestamp: Optional[datetime],
        log_source: Optional[str],
        event_type: Optional[str],
        raw_log: Optional[str],
    ) -> Dict[str, Any]:
        dt = timestamp or datetime.now(timezone.utc)
        return {
            # Keys used by ml_engine predictor's "raw log row" heuristic
            "Month": _month_abbr(dt),
            "Date": int(dt.day),
            "Time": _time_hms(dt),
            "Component": (log_source or "unknown"),
            "Content": (raw_log or ""),
            "EventId": (event_type or "UNKNOWN"),
            "EventTemplate": "",
        }

    def _get_or_compute_feature_row(self, ml_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Returns a single-row feature dict (engineered numeric features).
        Uses Mongo feature cache when enabled.
        """
        key_payload = {
            "v": 1,
            "ml_input": ml_input,
        }
        cache_key = make_cache_key(key_payload)

        if self.cache_features:
            cached = cache_get_features(cache_key)
            if cached is not None:
                # Remove time_since_last from cached data if present (legacy cache entries)
                if 'time_since_last' in cached:
                    cached = {k: v for k, v in cached.items() if k != 'time_since_last'}
                return cached

        extractor = self._FeatureExtractor()
        import pandas as pd

        df = pd.DataFrame([ml_input])
        feat_df = extractor.extract_features(df)
        # #region agent log
        try:
            with open('/home/nulumohan/firewall-log-analyzer/Firewall-Log-Analyzer/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "A",
                    "location": "ml_service.py:_get_or_compute_feature_row:after_extract",
                    "message": "after extract_features",
                    "data": {
                        "feat_df_columns": list(feat_df.columns)[:10],
                        "has_time_since_last": "time_since_last" in feat_df.columns
                    },
                    "timestamp": int(__import__('time').time() * 1000)
                }) + '\n')
        except: pass
        # #endregion
        X, _ = extractor.get_feature_matrix(feat_df)
        # #region agent log
        try:
            with open('/home/nulumohan/firewall-log-analyzer/Firewall-Log-Analyzer/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "A",
                    "location": "ml_service.py:_get_or_compute_feature_row:after_get_matrix",
                    "message": "after get_feature_matrix",
                    "data": {
                        "X_columns": list(X.columns)[:10],
                        "has_time_since_last": "time_since_last" in X.columns,
                        "X_shape": list(X.shape)
                    },
                    "timestamp": int(__import__('time').time() * 1000)
                }) + '\n')
        except: pass
        # #endregion
        row = X.iloc[0].to_dict()
        # #region agent log
        try:
            with open('/home/nulumohan/firewall-log-analyzer/Firewall-Log-Analyzer/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "A",
                    "location": "ml_service.py:_get_or_compute_feature_row:before_return",
                    "message": "before returning row",
                    "data": {
                        "row_keys": list(row.keys())[:10],
                        "has_time_since_last": "time_since_last" in row
                    },
                    "timestamp": int(__import__('time').time() * 1000)
                }) + '\n')
        except: pass
        # #endregion

        if self.cache_features:
            cache_set_features(cache_key, row)

        return row

    def score(
        self,
        *,
        source_ip: Optional[str] = None,
        threat_type_hint: Optional[str] = None,
        severity_hint: Optional[str] = None,
        timestamp: Optional[datetime] = None,
        log_source: Optional[str] = None,
        event_type: Optional[str] = None,
        raw_log: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> MLResult:
        """
        Score a single representative log line.

        - threat_type_hint: optional rule-based label like BRUTE_FORCE / DDOS / PORT_SCAN
        - severity_hint: optional rule-based severity to seed confidence when classifier isn't applicable
        """
        if not self._initialized:
            self.initialize()

        reasoning: list[str] = []

        if not self.enabled:
            return MLResult(
                ml_enabled=False,
                ml_available=False,
                reasoning=["ML disabled via ML_ENABLED=false"],
            )

        if self._last_error is not None or self._models is None:
            return MLResult(
                ml_enabled=True,
                ml_available=False,
                reasoning=["ML unavailable; falling back to rules"],
                error=self._last_error,
            )

        anomaly_score: Optional[float] = None
        predicted_label: Optional[str] = None
        confidence: Optional[float] = None
        risk: Optional[float] = None

        try:
            x = self._build_ml_input(
                timestamp=timestamp,
                log_source=log_source,
                event_type=event_type,
                raw_log=raw_log,
            )

            # Build engineered features and run models directly (enables feature cache)
            feature_row = self._get_or_compute_feature_row(x)

            import pandas as pd
            X = pd.DataFrame([feature_row])
            # Drop time_since_last if present (should be excluded by get_feature_matrix, but handle cached data)
            if 'time_since_last' in X.columns:
                X = X.drop(columns=['time_since_last'])
            # #region agent log
            import json
            try:
                with open('/home/nulumohan/firewall-log-analyzer/Firewall-Log-Analyzer/.cursor/debug.log', 'a') as f:
                    f.write(json.dumps({
                        "sessionId": "debug-session",
                        "runId": "run1",
                        "hypothesisId": "A",
                        "location": "ml_service.py:score:before_transform",
                        "message": "before scaler.transform",
                        "data": {
                            "X_columns": list(X.columns),
                            "has_time_since_last": "time_since_last" in X.columns,
                            "feature_row_keys": list(feature_row.keys())[:10]
                        },
                        "timestamp": int(__import__('time').time() * 1000)
                    }) + '\n')
            except: pass
            # #endregion
            X_scaled = self._models.scaler.transform(X).to_numpy()

            anomaly_score = None
            try:
                anomaly_pkg = self._models.anomaly_package
                if anomaly_pkg is not None:
                    model = anomaly_pkg["model"]
                    calibration = anomaly_pkg.get("calibration", {"q_low": 0.0, "q_high": 1.0})
                    raw = (-model.decision_function(X_scaled)).astype(float)
                    scores = self._raw_to_unit_interval(raw, calibration)
                    anomaly_score = float(scores[0])
                    reasoning.append(f"ml.anomaly_score={anomaly_score:.3f}")
            except Exception as e:
                reasoning.append(f"ml.anomaly_error={e}")

            predicted_label = None
            confidence = None

            # Only use classifier for auth-like events; for others, classifier labels are not trained.
            is_auth_like = (log_source or "").lower().find("auth") >= 0 or (event_type or "").startswith("SSH_")

            if is_auth_like:
                try:
                    pkg = self._models.classifier_package
                    le_data = self._models.label_encoder_data
                    if pkg is not None and le_data is not None:
                        clf = pkg["model"]
                        classes = list(le_data.get("classes", le_data["label_encoder"].classes_))
                        proba = clf.predict_proba(X_scaled)[0]
                        pred_idx = int(proba.argmax())
                        predicted_label = str(classes[pred_idx])
                        confidence = float(proba[pred_idx])
                        reasoning.append(f"ml.class={predicted_label} conf={confidence:.3f}")
                except Exception as e:
                    reasoning.append(f"ml.class_error={e}")

            # If classifier unavailable or not applicable, fall back to hint or infer from event_type
            if predicted_label is None:
                # Try threat_type_hint first
                if threat_type_hint:
                    predicted_label = str(threat_type_hint)
                    confidence = _severity_to_confidence(severity_hint or "")
                    reasoning.append(f"rule.label={predicted_label} conf_seed={confidence:.2f}")
                # Otherwise, infer from event_type
                elif event_type:
                    event_upper = (event_type or "").upper()
                    # Map event types to threat labels
                    if "BRUTE_FORCE" in event_upper or "SSH_FAILED" in event_upper:
                        predicted_label = "BRUTE_FORCE"
                    elif "DDOS" in event_upper or "FLOOD" in event_upper:
                        predicted_label = "DDOS"
                    elif "PORT_SCAN" in event_upper or "SCAN" in event_upper:
                        predicted_label = "PORT_SCAN"
                    elif "SQL" in event_upper or "INJECTION" in event_upper:
                        predicted_label = "SQL_INJECTION"
                    elif "SUSPICIOUS" in event_upper:
                        predicted_label = "SUSPICIOUS"
                    elif "SSH_SUCCESS" in event_upper or "LOGIN_SUCCESS" in event_upper:
                        predicted_label = "NORMAL"
                    else:
                        # Default based on severity
                        if severity_hint and severity_hint.upper() in ["CRITICAL", "HIGH"]:
                            predicted_label = "SUSPICIOUS"
                        else:
                            predicted_label = "NORMAL"
                    
                    confidence = _severity_to_confidence(severity_hint or "")
                    reasoning.append(f"inferred.label={predicted_label} from event_type={event_type} conf={confidence:.2f}")
                else:
                    # Last resort: use severity-based default
                    if severity_hint and severity_hint.upper() in ["CRITICAL", "HIGH"]:
                        predicted_label = "SUSPICIOUS"
                    else:
                        predicted_label = "NORMAL"
                    confidence = _severity_to_confidence(severity_hint or "")
                    reasoning.append(f"default.label={predicted_label} from severity={severity_hint} conf={confidence:.2f}")

            # Compute risk score (0-100)
            # Risk is driven by anomaly score + confidence-weighted label severity.
            label_weight = {
                "NORMAL": 0.10,
                "SUSPICIOUS": 0.60,
                "BRUTE_FORCE": 0.80,
                "DDOS": 0.90,
                "PORT_SCAN": 0.90,
            }.get((predicted_label or "").upper(), 0.50)

            a = _clip01(anomaly_score) if anomaly_score is not None else 0.0
            c = _clip01(confidence) if confidence is not None else _severity_to_confidence(severity_hint or "")
            risk = 100.0 * _clip01((0.55 * a) + (0.45 * c * label_weight))
            reasoning.append(f"ml.risk_score={risk:.1f}")
            result = MLResult(
                ml_enabled=True,
                ml_available=True,
                anomaly_score=anomaly_score,
                predicted_label=predicted_label,
                confidence=confidence,
                risk_score=risk,
                reasoning=reasoning,
            )
        except Exception as e:
            # Even on failure, compute a fallback risk score from hints
            reasoning = [f"ml.error={str(e)}", "ML scoring failed; falling back to rules"]
            fallback_risk = None
            fallback_label = None
            fallback_confidence = None
            
            if threat_type_hint or severity_hint:
                fallback_label = str(threat_type_hint) if threat_type_hint else None
                fallback_confidence = _severity_to_confidence(severity_hint or "")
                label_weight = {
                    "NORMAL": 0.10,
                    "SUSPICIOUS": 0.60,
                    "BRUTE_FORCE": 0.80,
                    "DDOS": 0.90,
                    "PORT_SCAN": 0.90,
                }.get((fallback_label or "").upper(), 0.50)
                fallback_risk = 100.0 * _clip01(0.45 * fallback_confidence * label_weight)
                reasoning.append(f"fallback.risk_score={fallback_risk:.1f}")
            
            result = MLResult(
                ml_enabled=True,
                ml_available=False,
                predicted_label=fallback_label,
                confidence=fallback_confidence,
                risk_score=fallback_risk,
                reasoning=reasoning,
                error=str(e),
            )
        # Store prediction record (best-effort)
        if self.store_predictions:
            try:
                store_prediction(
                    {
                        "source_ip": source_ip,
                        "log_source": log_source,
                        "event_type": event_type,
                        "threat_type_hint": threat_type_hint,
                        "severity_hint": severity_hint,
                        "context": context or {},
                        "anomaly_score": result.anomaly_score,
                        "predicted_label": result.predicted_label,
                        "confidence": result.confidence,
                        "risk_score": result.risk_score,
                        "ml_enabled": result.ml_enabled,
                        "ml_available": result.ml_available,
                        "error": result.error,
                    }
                )
            except Exception:
                pass

        return result


# Singleton used across routes/services
ml_service = MLService()


