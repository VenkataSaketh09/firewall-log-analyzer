"""
Alert Monitor Worker
Background worker that monitors for new alerts and triggers email notifications.
"""
import time
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Any
from app.services.alert_service import get_or_compute_alerts
from app.services.alert_notification_service import alert_notification_service
from app.db.mongo import alerts_collection, email_notifications_collection
import logging

logger = logging.getLogger(__name__)


class AlertMonitorWorker:
    """Background worker that monitors alerts and sends notifications"""
    
    def __init__(self, check_interval_seconds: int = 120):
        """
        Initialize the alert monitor worker.
        
        Args:
            check_interval_seconds: How often to check for new alerts (default: 2 minutes)
        """
        self.check_interval = check_interval_seconds
        self.running = False
        self.thread = None
        self.last_check_time = None
        self.processed_alert_keys = set()  # Track processed alerts to avoid duplicates
    
    def start(self):
        """Start the background worker thread"""
        if self.running:
            logger.warning("Alert monitor worker is already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True, name="alert-monitor-worker")
        self.thread.start()
        logger.info(f"✓ Alert monitor worker started (check interval: {self.check_interval}s)")
    
    def stop(self):
        """Stop the background worker"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("✓ Alert monitor worker stopped")
    
    def _run(self):
        """Main worker loop"""
        logger.info("Alert monitor worker running...")
        
        while self.running:
            try:
                self._check_and_process_alerts()
            except Exception as e:
                logger.error(f"✗ Error in alert monitor worker: {e}")
            
            # Sleep until next check
            time.sleep(self.check_interval)
    
    def _check_and_process_alerts(self):
        """Check for new alerts and process them"""
        try:
            # Get alerts from alert service (uses caching)
            start_date, end_date, alert_docs = get_or_compute_alerts(
                lookback_seconds=24 * 3600,  # Last 24 hours
                bucket_minutes=5,
            )
            
            logger.info(f"Alert check: Found {len(alert_docs) if alert_docs else 0} total alert(s) in last 24 hours")
            
            if not alert_docs:
                logger.debug("No alerts found in current time window")
                return
            
            # Filter for alerts that haven't been processed yet
            new_alerts = self._filter_new_alerts(alert_docs)
            
            logger.info(f"Alert check: {len(new_alerts)} new alert(s) to process (out of {len(alert_docs)} total)")
            
            if not new_alerts:
                logger.debug(f"No new alerts to process (total alerts: {len(alert_docs)})")
                # Log some details about existing alerts for debugging
                if alert_docs:
                    sample_alert = alert_docs[0]
                    logger.debug(f"Sample alert: {sample_alert.get('alert_type')} from {sample_alert.get('source_ip')} "
                               f"(severity: {sample_alert.get('severity')})")
                return
            
            logger.info(f"Processing {len(new_alerts)} new alert(s)")
            
            # Process each new alert
            for alert in new_alerts:
                try:
                    result = alert_notification_service.process_alert_with_ml(alert)
                    
                    if result["sent"]:
                        # Mark as processed
                        alert_key = self._get_alert_key(alert)
                        self.processed_alert_keys.add(alert_key)
                        logger.info(f"✓ Notification processed for {alert.get('alert_type')} from {alert.get('source_ip')}")
                    else:
                        logger.debug(f"Notification not sent: {result.get('reason')}")
                
                except Exception as e:
                    logger.error(f"✗ Error processing alert {alert.get('source_ip')}: {e}")
            
            self.last_check_time = datetime.utcnow()
        
        except Exception as e:
            logger.error(f"✗ Error checking alerts: {e}")
    
    def _filter_new_alerts(self, alert_docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter alerts to only include new ones that haven't been processed"""
        new_alerts = []
        
        for alert in alert_docs:
            # Check if notification was already sent (from database) - this is the source of truth
            dedup_key = alert_notification_service._generate_deduplication_key(alert)
            if alert_notification_service._notification_already_sent(dedup_key):
                # Already sent, skip
                alert_key = self._get_alert_key(alert)
                self.processed_alert_keys.add(alert_key)
                logger.debug(f"Alert already processed: {alert.get('alert_type')} from {alert.get('source_ip')}")
                continue
            
            # Check if we've already processed this alert in this session
            alert_key = self._get_alert_key(alert)
            if alert_key in self.processed_alert_keys:
                continue
            
            # This is a new alert that hasn't been processed
            new_alerts.append(alert)
            logger.debug(f"New alert found: {alert.get('alert_type')} from {alert.get('source_ip')} "
                        f"(severity: {alert.get('severity')})")
        
        return new_alerts
    
    def _get_alert_key(self, alert: Dict[str, Any]) -> str:
        """Generate a unique key for an alert"""
        return f"{alert.get('alert_type')}|{alert.get('source_ip')}|{alert.get('bucket_end')}"
    
    def get_status(self) -> Dict[str, Any]:
        """Get worker status"""
        return {
            "running": self.running,
            "check_interval_seconds": self.check_interval,
            "last_check_time": self.last_check_time.isoformat() if self.last_check_time else None,
            "processed_alerts_count": len(self.processed_alert_keys),
        }


# Global singleton instance
alert_monitor_worker = AlertMonitorWorker()

