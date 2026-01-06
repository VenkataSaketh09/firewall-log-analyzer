"""
Automatic IP Blocking Service
Uses ML + rules-based approach to automatically block malicious IPs
"""
import os
import logging
from typing import Optional, Dict, List
from datetime import datetime, timezone
from app.services.ip_blocking_service import IPBlockingService
from app.services.email_service import email_service
from app.db.mongo import blacklisted_ips_collection

logger = logging.getLogger(__name__)


class AutoIPBlockingService:
    """Service for automatically blocking IPs based on threat detection"""
    
    def __init__(self):
        # Configuration from environment variables
        self.enabled = os.getenv("AUTO_IP_BLOCKING_ENABLED", "true").lower() == "true"
        
        # Rules-based thresholds
        self.severity_threshold = os.getenv("AUTO_BLOCK_SEVERITY_THRESHOLD", "HIGH")  # CRITICAL, HIGH, MEDIUM, LOW
        self.auto_block_critical = os.getenv("AUTO_BLOCK_CRITICAL", "true").lower() == "true"
        self.auto_block_high = os.getenv("AUTO_BLOCK_HIGH", "true").lower() == "true"
        self.auto_block_medium = os.getenv("AUTO_BLOCK_MEDIUM", "false").lower() == "true"
        self.auto_block_low = os.getenv("AUTO_BLOCK_LOW", "false").lower() == "true"
        
        # ML-based thresholds
        self.ml_risk_score_threshold = float(os.getenv("AUTO_BLOCK_ML_RISK_THRESHOLD", "75.0"))
        self.ml_anomaly_score_threshold = float(os.getenv("AUTO_BLOCK_ML_ANOMALY_THRESHOLD", "0.7"))
        self.ml_confidence_threshold = float(os.getenv("AUTO_BLOCK_ML_CONFIDENCE_THRESHOLD", "0.7"))
        self.require_ml_confirmation = os.getenv("AUTO_BLOCK_REQUIRE_ML", "false").lower() == "true"
        
        # Attack-specific thresholds
        self.brute_force_attempt_threshold = int(os.getenv("AUTO_BLOCK_BRUTE_FORCE_THRESHOLD", "20"))
        self.ddos_request_threshold = int(os.getenv("AUTO_BLOCK_DDOS_THRESHOLD", "500"))
        self.port_scan_ports_threshold = int(os.getenv("AUTO_BLOCK_PORT_SCAN_THRESHOLD", "25"))
        
        # Cooldown period (don't re-block recently unblocked IPs)
        self.cooldown_hours = int(os.getenv("AUTO_BLOCK_COOLDOWN_HOURS", "24"))
        
        logger.info(f"Auto IP Blocking Service initialized (enabled={self.enabled})")
        if self.enabled:
            logger.info(f"  Severity thresholds: CRITICAL={self.auto_block_critical}, HIGH={self.auto_block_high}, "
                       f"MEDIUM={self.auto_block_medium}, LOW={self.auto_block_low}")
            logger.info(f"  ML thresholds: Risk={self.ml_risk_score_threshold}, "
                       f"Anomaly={self.ml_anomaly_score_threshold}, Confidence={self.ml_confidence_threshold}")
    
    def should_auto_block(
        self,
        threat_type: str,
        severity: str,
        source_ip: str,
        ml_risk_score: Optional[float] = None,
        ml_anomaly_score: Optional[float] = None,
        ml_confidence: Optional[float] = None,
        ml_predicted_label: Optional[str] = None,
        attack_metrics: Optional[Dict] = None
    ) -> tuple:
        """
        Determine if an IP should be automatically blocked based on ML + rules.
        
        Returns:
            (should_block: bool, reason: str)
        """
        if not self.enabled:
            return False, "Auto-blocking is disabled"
        
        # Check if IP is already blocked
        if IPBlockingService.is_blocked(source_ip):
            return False, "IP is already blocked"
        
        # Check cooldown period (don't re-block recently unblocked IPs)
        if self._is_in_cooldown(source_ip):
            return False, f"IP is in cooldown period ({self.cooldown_hours}h)"
        
        # Rules-based decision
        rules_decision, rules_reason = self._rules_based_decision(
            threat_type, severity, attack_metrics
        )
        
        # ML-based decision
        ml_decision, ml_reason = self._ml_based_decision(
            ml_risk_score, ml_anomaly_score, ml_confidence, ml_predicted_label
        )
        
        # Combine decisions
        if self.require_ml_confirmation:
            # Both rules and ML must agree
            if rules_decision and ml_decision:
                reason = f"Rules: {rules_reason}; ML: {ml_reason}"
                return True, reason
            else:
                return False, f"ML confirmation required but not met. Rules: {rules_decision}, ML: {ml_decision}"
        else:
            # Either rules or ML can trigger blocking
            if rules_decision:
                reason = f"Rules-based: {rules_reason}"
                if ml_decision:
                    reason += f"; ML confirmed: {ml_reason}"
                return True, reason
            elif ml_decision:
                return True, f"ML-based: {ml_reason}"
            else:
                return False, f"Thresholds not met. Rules: {rules_reason}, ML: {ml_reason}"
    
    def _rules_based_decision(
        self,
        threat_type: str,
        severity: str,
        attack_metrics: Optional[Dict]
    ) -> tuple:
        """Rules-based decision making"""
        severity_upper = severity.upper()
        
        # Check severity-based blocking
        if severity_upper == "CRITICAL" and self.auto_block_critical:
            return True, f"CRITICAL severity {threat_type} detected"
        elif severity_upper == "HIGH" and self.auto_block_high:
            return True, f"HIGH severity {threat_type} detected"
        elif severity_upper == "MEDIUM" and self.auto_block_medium:
            return True, f"MEDIUM severity {threat_type} detected"
        elif severity_upper == "LOW" and self.auto_block_low:
            return True, f"LOW severity {threat_type} detected"
        
        # Check attack-specific thresholds
        if attack_metrics:
            if threat_type == "BRUTE_FORCE":
                attempts = attack_metrics.get("total_attempts", 0)
                if attempts >= self.brute_force_attempt_threshold:
                    return True, f"Brute force: {attempts} attempts (threshold: {self.brute_force_attempt_threshold})"
            
            elif threat_type == "DDOS":
                requests = attack_metrics.get("total_requests", 0)
                if requests >= self.ddos_request_threshold:
                    return True, f"DDoS: {requests} requests (threshold: {self.ddos_request_threshold})"
            
            elif threat_type == "PORT_SCAN":
                ports = attack_metrics.get("unique_ports_attempted", 0)
                if ports >= self.port_scan_ports_threshold:
                    return True, f"Port scan: {ports} ports (threshold: {self.port_scan_ports_threshold})"
        
        return False, f"Rules thresholds not met (severity: {severity}, type: {threat_type})"
    
    def _ml_based_decision(
        self,
        ml_risk_score: Optional[float],
        ml_anomaly_score: Optional[float],
        ml_confidence: Optional[float],
        ml_predicted_label: Optional[str]
    ) -> tuple:
        """ML-based decision making"""
        if ml_risk_score is None and ml_anomaly_score is None:
            return False, "No ML data available"
        
        reasons = []
        decision = False
        
        # Check risk score
        if ml_risk_score is not None:
            if ml_risk_score >= self.ml_risk_score_threshold:
                decision = True
                reasons.append(f"Risk score {ml_risk_score:.1f} >= {self.ml_risk_score_threshold}")
            else:
                reasons.append(f"Risk score {ml_risk_score:.1f} < {self.ml_risk_score_threshold}")
        
        # Check anomaly score
        if ml_anomaly_score is not None:
            if ml_anomaly_score >= self.ml_anomaly_score_threshold:
                decision = True
                reasons.append(f"Anomaly score {ml_anomaly_score:.3f} >= {self.ml_anomaly_score_threshold}")
            else:
                reasons.append(f"Anomaly score {ml_anomaly_score:.3f} < {self.ml_anomaly_score_threshold}")
        
        # Check predicted label
        if ml_predicted_label:
            threat_labels = ["BRUTE_FORCE", "DDOS", "PORT_SCAN", "MALICIOUS", "ATTACK"]
            if ml_predicted_label.upper() in threat_labels:
                if ml_confidence and ml_confidence >= self.ml_confidence_threshold:
                    decision = True
                    reasons.append(f"ML label: {ml_predicted_label} (confidence: {ml_confidence:.1%})")
        
        reason_str = "; ".join(reasons) if reasons else "ML thresholds not met"
        return decision, reason_str
    
    def _is_in_cooldown(self, ip_address: str) -> bool:
        """Check if IP is in cooldown period (recently unblocked)"""
        record = blacklisted_ips_collection.find_one({"ip_address": ip_address})
        if not record:
            return False
        
        unblocked_at = record.get("unblocked_at")
        if not unblocked_at:
            return False
        
        from datetime import timedelta
        cooldown_end = unblocked_at + timedelta(hours=self.cooldown_hours)
        return datetime.now(timezone.utc) < cooldown_end
    
    def auto_block_ip(
        self,
        source_ip: str,
        threat_type: str,
        severity: str,
        reason: str,
        ml_risk_score: Optional[float] = None,
        ml_anomaly_score: Optional[float] = None,
        ml_confidence: Optional[float] = None,
        attack_metrics: Optional[Dict] = None
    ) -> Dict:
        """
        Automatically block an IP address and send email notification.
        
        Returns:
            Dict with blocking status and details
        """
        try:
            # Block the IP
            block_result = IPBlockingService.block_ip(
                ip_address=source_ip,
                reason=f"AUTO-BLOCK: {reason}",
                blocked_by="auto_blocking_service"
            )
            
            if not block_result.get("success"):
                logger.error(f"Failed to auto-block IP {source_ip}: {block_result}")
                return {
                    "success": False,
                    "ip_address": source_ip,
                    "message": f"Failed to block IP: {block_result.get('message', 'Unknown error')}"
                }
            
            # Send email notification
            email_sent = self._send_block_notification_email(
                source_ip=source_ip,
                threat_type=threat_type,
                severity=severity,
                reason=reason,
                ml_risk_score=ml_risk_score,
                ml_anomaly_score=ml_anomaly_score,
                ml_confidence=ml_confidence,
                attack_metrics=attack_metrics
            )
            
            logger.info(f"✓ Auto-blocked IP {source_ip} ({threat_type}, {severity}). Email sent: {email_sent}")
            
            return {
                "success": True,
                "ip_address": source_ip,
                "message": f"IP {source_ip} automatically blocked due to {threat_type}",
                "reason": reason,
                "email_sent": email_sent,
                "ufw_output": block_result.get("ufw_output")
            }
            
        except Exception as e:
            logger.error(f"Error auto-blocking IP {source_ip}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "success": False,
                "ip_address": source_ip,
                "message": f"Error auto-blocking IP: {str(e)}"
            }
    
    def _send_block_notification_email(
        self,
        source_ip: str,
        threat_type: str,
        severity: str,
        reason: str,
        ml_risk_score: Optional[float] = None,
        ml_anomaly_score: Optional[float] = None,
        ml_confidence: Optional[float] = None,
        attack_metrics: Optional[Dict] = None
    ) -> bool:
        """Send email notification about auto-blocked IP"""
        try:
            # Build description
            description = f"IP {source_ip} has been automatically blocked due to {threat_type.replace('_', ' ').lower()} detection."
            description += f"\n\nBlocking Reason: {reason}"
            
            if attack_metrics:
                description += "\n\nAttack Details:"
                for key, value in attack_metrics.items():
                    if key not in ["attack_windows", "attempts", "timeline"]:  # Skip large nested data
                        description += f"\n  - {key.replace('_', ' ').title()}: {value}"
            
            description += "\n\nYou can view and manage blocked IPs in the IP Blocking page of the dashboard."
            description += "\nIf you believe this is a false positive, you can manually unblock the IP."
            
            # Send email
            return email_service.send_alert_email(
                alert_type=f"AUTO_BLOCKED_{threat_type}",
                severity=severity,
                source_ip=source_ip,
                description=description,
                ml_risk_score=ml_risk_score,
                ml_anomaly_score=ml_anomaly_score,
                ml_confidence=ml_confidence,
                count=attack_metrics.get("total_attempts") if attack_metrics else None,
                first_seen=attack_metrics.get("first_attempt") if attack_metrics else None,
                last_seen=attack_metrics.get("last_attempt") if attack_metrics else None,
                details={
                    "threat_type": threat_type,
                    "blocking_reason": reason,
                    "attack_metrics": {k: v for k, v in (attack_metrics or {}).items() 
                                     if k not in ["attack_windows", "attempts", "timeline"]}
                }
            )
        except Exception as e:
            logger.error(f"Error sending auto-block notification email: {e}")
            return False


# Global singleton instance
auto_ip_blocking_service = AutoIPBlockingService()

