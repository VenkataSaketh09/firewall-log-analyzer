"""
Alert Notification Service
Handles notification logic, ML integration, and deduplication for email alerts.
"""
import os
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
from app.db.mongo import email_notifications_collection
from app.services.email_service import email_service
from app.services.ml_service import ml_service
import logging

logger = logging.getLogger(__name__)


class AlertNotificationService:
    """Service for managing alert notifications with ML integration"""
    
    def __init__(self):
        self.enabled = os.getenv("EMAIL_ENABLED", "false").lower() == "true"
        self.severity_threshold = os.getenv("NOTIFICATION_SEVERITY_THRESHOLD", "HIGH").upper()
        self.ml_risk_threshold = float(os.getenv("NOTIFICATION_ML_RISK_THRESHOLD", "70"))
        self.rate_limit_minutes = int(os.getenv("NOTIFICATION_RATE_LIMIT_MINUTES", "15"))
        
        # Severity order for threshold checking
        self.severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        
        logger.info(f"Alert notification service initialized. Enabled: {self.enabled}, "
                   f"Severity threshold: {self.severity_threshold}, ML risk threshold: {self.ml_risk_threshold}")
    
    def should_send_notification(self, alert: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Determine if an alert should trigger an email notification.
        
        Returns: (should_send: bool, reason: Optional[str])
        """
        if not self.enabled:
            return False, "Email notifications disabled"
        
        # Check if notification was already sent (deduplication)
        dedup_key = self._generate_deduplication_key(alert)
        if self._notification_already_sent(dedup_key):
            return False, "Notification already sent (deduplication)"
        
        # Check rate limiting (prevent spam)
        if self._is_rate_limited(alert):
            return False, "Rate limit exceeded"
        
        # Check severity threshold
        alert_severity = alert.get("severity", "LOW").upper()
        threshold_severity_order = self.severity_order.get(self.severity_threshold, 99)
        alert_severity_order = self.severity_order.get(alert_severity, 99)
        
        if alert_severity_order > threshold_severity_order:
            return False, f"Severity {alert_severity} below threshold {self.severity_threshold}"
        
        # If severity meets threshold, send notification
        return True, None
    
    def process_alert_with_ml(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an alert with ML scoring and send notification if warranted.
        
        Returns: dict with notification result
        """
        should_send, reason = self.should_send_notification(alert)
        
        if not should_send:
            logger.info(f"Skipping notification for alert {alert.get('source_ip')} - {alert.get('alert_type')}: {reason}")
            return {
                "sent": False,
                "reason": reason,
                "ml_scored": False,
            }
        
        logger.info(f"Processing notification for {alert.get('alert_type')} from {alert.get('source_ip')} "
                   f"(severity: {alert.get('severity')})")
        
        # Run ML scoring on the alert
        ml_result = self._score_alert_with_ml(alert)
        
        # Check ML risk threshold (even if severity meets threshold, ML might flag it as low risk)
        ml_risk_score = ml_result.risk_score if ml_result else None
        
        # Decision logic:
        # - CRITICAL severity: Always send (regardless of ML)
        # - HIGH severity: Send if ML risk >= threshold OR ML unavailable
        # - MEDIUM/LOW severity: Only send if ML risk >= threshold
        alert_severity = alert.get("severity", "LOW").upper()
        
        if alert_severity == "CRITICAL":
            # Always send CRITICAL alerts
            pass
        elif alert_severity == "HIGH":
            # HIGH alerts: send if ML risk meets threshold or ML unavailable
            if ml_risk_score is not None and ml_risk_score < self.ml_risk_threshold:
                return {
                    "sent": False,
                    "reason": f"ML risk score {ml_risk_score:.1f} below threshold {self.ml_risk_threshold}",
                    "ml_scored": True,
                    "ml_risk_score": ml_risk_score,
                }
        else:
            # MEDIUM/LOW: Only send if ML risk meets threshold
            if ml_risk_score is None or ml_risk_score < self.ml_risk_threshold:
                return {
                    "sent": False,
                    "reason": f"ML risk score {ml_risk_score:.1f if ml_risk_score else 'N/A'} below threshold {self.ml_risk_threshold}",
                    "ml_scored": ml_result is not None,
                    "ml_risk_score": ml_risk_score,
                }
        
        # Generate deduplication key for recording
        dedup_key = self._generate_deduplication_key(alert)
        
        # Send email notification
        logger.info(f"Attempting to send email notification for {alert.get('alert_type')} from {alert.get('source_ip')}")
        success = self._send_notification(alert, ml_result)
        
        if success:
            # Record notification in database
            self._record_notification(alert, ml_result, dedup_key)
            logger.info(f"✓ Notification sent successfully for {alert.get('alert_type')} from {alert.get('source_ip')}")
        else:
            logger.error(f"✗ Failed to send notification for {alert.get('alert_type')} from {alert.get('source_ip')}")
        
        return {
            "sent": success,
            "reason": "Notification sent" if success else "Failed to send email",
            "ml_scored": ml_result is not None,
            "ml_risk_score": ml_risk_score,
            "ml_anomaly_score": ml_result.anomaly_score if ml_result else None,
            "ml_confidence": ml_result.confidence if ml_result else None,
        }
    
    def _score_alert_with_ml(self, alert: Dict[str, Any]) -> Optional[Any]:
        """Run ML scoring on an alert"""
        try:
            source_ip = alert.get("source_ip")
            alert_type = alert.get("alert_type", "")
            severity = alert.get("severity", "LOW")
            last_seen = alert.get("last_seen")
            
            # Get a representative log entry for this alert
            # We'll use the alert details to construct ML input
            from app.db.mongo import logs_collection
            from pymongo import DESCENDING
            
            # Try to find a recent log entry for this IP
            log_entry = logs_collection.find_one(
                {"source_ip": source_ip},
                sort=[("timestamp", DESCENDING)]
            )
            
            if log_entry:
                ml_result = ml_service.score(
                    source_ip=source_ip,
                    threat_type_hint=alert_type,
                    severity_hint=severity,
                    timestamp=log_entry.get("timestamp"),
                    log_source=log_entry.get("log_source"),
                    event_type=log_entry.get("event_type"),
                    raw_log=log_entry.get("raw_log"),
                )
                return ml_result
            else:
                # No log entry found, score with minimal info
                ml_result = ml_service.score(
                    source_ip=source_ip,
                    threat_type_hint=alert_type,
                    severity_hint=severity,
                    timestamp=last_seen,
                )
                return ml_result
        
        except Exception as e:
            logger.error(f"Error scoring alert with ML: {e}")
            return None
    
    def _send_notification(self, alert: Dict[str, Any], ml_result: Optional[Any]) -> bool:
        """Send email notification for an alert"""
        try:
            return email_service.send_alert_email(
                alert_type=alert.get("alert_type", "UNKNOWN"),
                severity=alert.get("severity", "LOW"),
                source_ip=alert.get("source_ip", "Unknown"),
                description=alert.get("description", ""),
                ml_risk_score=ml_result.risk_score if ml_result else None,
                ml_anomaly_score=ml_result.anomaly_score if ml_result else None,
                ml_confidence=ml_result.confidence if ml_result else None,
                count=alert.get("count"),
                first_seen=alert.get("first_seen"),
                last_seen=alert.get("last_seen"),
                details=alert.get("details"),
            )
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            return False
    
    def _generate_deduplication_key(self, alert: Dict[str, Any]) -> str:
        """Generate a unique key for deduplication"""
        # Use alert type, source IP, and bucket_end to create unique key
        key_parts = [
            alert.get("alert_type", ""),
            alert.get("source_ip", ""),
            str(alert.get("bucket_end", "")),
        ]
        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _notification_already_sent(self, dedup_key: str) -> bool:
        """Check if notification was already sent for this alert"""
        existing = email_notifications_collection.find_one({"deduplication_key": dedup_key})
        return existing is not None
    
    def _is_rate_limited(self, alert: Dict[str, Any]) -> bool:
        """Check if we're rate limited for this alert type/IP"""
        source_ip = alert.get("source_ip", "")
        alert_type = alert.get("alert_type", "")
        
        # Check if we sent a notification for this IP/type within rate limit window
        cutoff_time = datetime.utcnow() - timedelta(minutes=self.rate_limit_minutes)
        
        recent_notification = email_notifications_collection.find_one({
            "source_ip": source_ip,
            "alert_type": alert_type,
            "email_sent_at": {"$gte": cutoff_time},
            "notification_sent": True,
        })
        
        return recent_notification is not None
    
    def _record_notification(self, alert: Dict[str, Any], ml_result: Optional[Any], dedup_key: str):
        """Record notification in database"""
        try:
            notification_doc = {
                "alert_type": alert.get("alert_type"),
                "source_ip": alert.get("source_ip"),
                "severity": alert.get("severity"),
                "ml_risk_score": ml_result.risk_score if ml_result else None,
                "ml_anomaly_score": ml_result.anomaly_score if ml_result else None,
                "ml_confidence": ml_result.confidence if ml_result else None,
                "email_sent_at": datetime.utcnow(),
                "recipients": email_service.recipients,
                "email_subject": f"[ALERT] {alert.get('severity')} {alert.get('alert_type')} detected from {alert.get('source_ip')}",
                "notification_sent": True,
                "deduplication_key": dedup_key,
                "alert_details": {
                    "description": alert.get("description"),
                    "count": alert.get("count"),
                    "first_seen": alert.get("first_seen"),
                    "last_seen": alert.get("last_seen"),
                },
            }
            
            email_notifications_collection.insert_one(notification_doc)
        
        except Exception as e:
            logger.error(f"Error recording notification: {e}")


# Global singleton instance
alert_notification_service = AlertNotificationService()

