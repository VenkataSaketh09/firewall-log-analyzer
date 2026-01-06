from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.mongo import logs_collection
from app.routes.logs import router as logs_router
from app.routes.threats import router as threats_router
from app.routes.reports import router as reports_router
from app.routes.ip_reputation import router as ip_reputation_router
from app.routes.dashboard import router as dashboard_router
from app.routes.alerts import router as alerts_router
from app.routes.ml import router as ml_router
from app.routes.websocket import router as websocket_router
from app.routes.ip_blocking import router as ip_blocking_router
from app.middleware.rate_limit import RateLimitMiddleware
from app.config import validate_environment
from app.services.retention_service import start_log_retention_worker
from app.services.ml_service import ml_service
from app.services.ml_auto_retrain_worker import start_auto_retrain_worker
from app.services.log_ingestor import start_log_ingestion
from app.services.raw_log_broadcaster import raw_log_broadcaster
from app.services.alert_monitor_worker import alert_monitor_worker
from app.services.redis_cache import redis_log_cache
import asyncio
from datetime import datetime
import sys

# Validate environment on startup
try:
    validate_environment()
    print("✓ Environment variables validated")
except ValueError as e:
    print(f"✗ ERROR: {e}", file=sys.stderr)
    sys.exit(1)

app = FastAPI(
    title="Firewall Log Analyzer Backend",
    description="API for firewall log analysis and monitoring",
    version="1.0.0"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting middleware
app.add_middleware(RateLimitMiddleware)

# Include routers
app.include_router(logs_router)
app.include_router(threats_router)
app.include_router(reports_router)
app.include_router(ip_reputation_router)
app.include_router(dashboard_router)
app.include_router(alerts_router)
app.include_router(ml_router)
app.include_router(websocket_router)
app.include_router(ip_blocking_router)


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    # Initialize Redis cache (will fallback to in-memory if Redis unavailable)
    if redis_log_cache.enabled:
        print("✓ Redis cache initialized")
    else:
        print("! Redis cache not available - using in-memory fallback")
    
    # Set event loop for raw log broadcaster (for async operations from sync threads)
    try:
        loop = asyncio.get_event_loop()
        raw_log_broadcaster.set_event_loop(loop)
        print("✓ Raw log broadcaster initialized with event loop")
    except Exception as e:
        print(f"! Warning: Could not set event loop for broadcaster: {e}")
        # Try to get the running loop
        try:
            loop = asyncio.get_running_loop()
            raw_log_broadcaster.set_event_loop(loop)
            print("✓ Raw log broadcaster initialized with running event loop")
        except Exception as e2:
            print(f"! Warning: Could not get running event loop: {e2}")
    
    # Start log retention worker
    start_log_retention_worker()
    print("✓ Log retention worker started")
    
    # Start log ingestion service (auto-starts with server)
    import threading
    ingestion_thread = threading.Thread(target=start_log_ingestion, daemon=True, name="log-ingestion-service")
    ingestion_thread.start()
    print("✓ Log ingestion service started")
    
    # Initialize ML (best-effort)
    if ml_service.initialize():
        print("✓ ML service initialized")
    else:
        print("! ML service not available (falling back to rule-based)")
    # Optional auto retraining (env-controlled)
    start_auto_retrain_worker()
    
    # Start alert monitor worker for email notifications
    alert_monitor_worker.start()
    print("✓ Alert monitor worker started")
    
    # Initialize auto IP blocking service (logs its own status)
    from app.services.auto_ip_blocking_service import auto_ip_blocking_service
    if auto_ip_blocking_service.enabled:
        print(f"✓ Auto IP blocking service enabled")
        print(f"  - Severity thresholds: CRITICAL={auto_ip_blocking_service.auto_block_critical}, "
              f"HIGH={auto_ip_blocking_service.auto_block_high}, "
              f"MEDIUM={auto_ip_blocking_service.auto_block_medium}, "
              f"LOW={auto_ip_blocking_service.auto_block_low}")
        print(f"  - Attack thresholds: BruteForce={auto_ip_blocking_service.brute_force_attempt_threshold}, "
              f"DDoS={auto_ip_blocking_service.ddos_request_threshold}, "
              f"PortScan={auto_ip_blocking_service.port_scan_ports_threshold}")
    else:
        print("! Auto IP blocking service disabled")
    
    print("✓ FastAPI application started successfully")


@app.get("/health")
def health_check():
    return {"status": "Backend is running"}


@app.get("/health/websocket")
def websocket_health_check():
    """Check if WebSocket route is registered"""
    from app.routes.websocket import router as ws_router
    routes = [str(r.path) for r in ws_router.routes]
    return {
        "status": "WebSocket routes registered",
        "routes": routes,
        "connection_count": raw_log_broadcaster.get_connection_count()
    }


@app.get("/health/ml")
def ml_health_check():
    status = ml_service.status()
    return {"ml": status}


@app.get("/health/notifications")
def notification_health_check():
    """Check notification service status"""
    from app.services.email_service import email_service
    from app.services.alert_notification_service import alert_notification_service
    from app.services.alert_monitor_worker import alert_monitor_worker
    from app.db.mongo import email_notifications_collection, alerts_collection
    
    # Get recent notifications count
    from datetime import datetime, timedelta
    recent_cutoff = datetime.utcnow() - timedelta(hours=24)
    recent_notifications = email_notifications_collection.count_documents({
        "email_sent_at": {"$gte": recent_cutoff}
    })
    
    # Get recent alerts count
    recent_alerts = alerts_collection.count_documents({
        "computed_at": {"$gte": recent_cutoff}
    })
    
    return {
        "email_service": {
            "enabled": email_service.enabled,
            "recipients_count": len(email_service.recipients),
            "recipients": email_service.recipients,
        },
        "notification_service": {
            "enabled": alert_notification_service.enabled,
            "severity_threshold": alert_notification_service.severity_threshold,
            "ml_risk_threshold": alert_notification_service.ml_risk_threshold,
            "rate_limit_minutes": alert_notification_service.rate_limit_minutes,
        },
        "alert_monitor_worker": alert_monitor_worker.get_status(),
        "recent_notifications_24h": recent_notifications,
        "recent_alerts_24h": recent_alerts,
    }


@app.get("/health/auto-blocking")
def auto_blocking_health_check():
    """Check auto IP blocking service status"""
    from app.services.auto_ip_blocking_service import auto_ip_blocking_service
    from app.db.mongo import blacklisted_ips_collection
    from datetime import datetime, timedelta
    
    # Get recent auto-blocked IPs count
    recent_cutoff = datetime.utcnow() - timedelta(hours=24)
    recent_auto_blocks = blacklisted_ips_collection.count_documents({
        "blocked_by": "auto_blocking_service",
        "blocked_at": {"$gte": recent_cutoff}
    })
    
    # Get total active auto-blocks
    active_auto_blocks = blacklisted_ips_collection.count_documents({
        "blocked_by": "auto_blocking_service",
        "is_active": True
    })
    
    return {
        "auto_blocking_service": {
            "enabled": auto_ip_blocking_service.enabled,
            "severity_thresholds": {
                "critical": auto_ip_blocking_service.auto_block_critical,
                "high": auto_ip_blocking_service.auto_block_high,
                "medium": auto_ip_blocking_service.auto_block_medium,
                "low": auto_ip_blocking_service.auto_block_low,
            },
            "attack_thresholds": {
                "brute_force": auto_ip_blocking_service.brute_force_attempt_threshold,
                "ddos": auto_ip_blocking_service.ddos_request_threshold,
                "port_scan": auto_ip_blocking_service.port_scan_ports_threshold,
            },
            "ml_thresholds": {
                "risk_score": auto_ip_blocking_service.ml_risk_score_threshold,
                "anomaly_score": auto_ip_blocking_service.ml_anomaly_score_threshold,
                "confidence": auto_ip_blocking_service.ml_confidence_threshold,
                "require_ml_confirmation": auto_ip_blocking_service.require_ml_confirmation,
            },
            "cooldown_hours": auto_ip_blocking_service.cooldown_hours,
        },
        "statistics": {
            "active_auto_blocks": active_auto_blocks,
            "recent_auto_blocks_24h": recent_auto_blocks,
        }
    }


@app.post("/test/email")
def test_email_notification():
    """Test email notification (for debugging)"""
    from app.services.email_service import email_service
    from datetime import datetime
    
    if not email_service.enabled:
        return {"error": "Email service is disabled"}
    
    # Create a test alert
    test_alert = {
        "alert_type": "TEST_ALERT",
        "severity": "HIGH",
        "source_ip": "192.168.1.100",
        "description": "This is a test alert to verify email notifications are working",
        "count": 1,
        "first_seen": datetime.utcnow(),
        "last_seen": datetime.utcnow(),
    }
    
    try:
        success = email_service.send_alert_email(
            alert_type=test_alert["alert_type"],
            severity=test_alert["severity"],
            source_ip=test_alert["source_ip"],
            description=test_alert["description"],
            ml_risk_score=85.0,
            ml_anomaly_score=0.95,
            ml_confidence=0.90,
            count=test_alert["count"],
            first_seen=test_alert["first_seen"],
            last_seen=test_alert["last_seen"],
        )
        
        return {
            "success": success,
            "message": "Test email sent" if success else "Failed to send test email",
            "recipients": email_service.recipients,
        }
    except Exception as e:
        import traceback
        return {
            "success": False,
            "message": f"Error sending test email: {str(e)}",
            "error": str(e),
            "traceback": traceback.format_exc(),
            "recipients": email_service.recipients,
        }


@app.post("/test/alert-notification")
def test_alert_notification():
    """Test alert notification system (simulates threat detection)"""
    from app.services.alert_notification_service import alert_notification_service
    from datetime import datetime, timezone
    
    # Create a test alert that would trigger notification
    test_alert = {
        "alert_type": "BRUTE_FORCE",
        "severity": "HIGH",
        "source_ip": "192.168.1.200",
        "description": "TEST: Simulated brute force attack detected for testing email notifications",
        "count": 25,
        "first_seen": datetime.now(timezone.utc),
        "last_seen": datetime.now(timezone.utc),
        "bucket_end": datetime.now(timezone.utc),
    }
    
    try:
        result = alert_notification_service.process_alert_with_ml(test_alert)
        
        return {
            "success": result.get("sent", False),
            "message": "Alert notification test completed",
            "result": result,
            "alert": test_alert,
        }
    except Exception as e:
        import traceback
        return {
            "success": False,
            "message": f"Error testing alert notification: {str(e)}",
            "error": str(e),
            "traceback": traceback.format_exc(),
        }


@app.post("/test/auto-block")
def test_auto_block_with_notification():
    """Test auto-blocking with email notification (simulates automatic IP blocking)"""
    from app.services.auto_ip_blocking_service import auto_ip_blocking_service
    from app.services.ip_blocking_service import IPBlockingService
    from datetime import datetime, timezone
    import random
    
    # Generate a test IP that's unlikely to conflict
    test_ip = f"192.168.{random.randint(200, 254)}.{random.randint(1, 254)}"
    
    # Check if IP is already blocked
    if IPBlockingService.is_blocked(test_ip):
        return {
            "success": False,
            "message": f"Test IP {test_ip} is already blocked. Please unblock it first or use a different IP.",
            "ip_address": test_ip,
        }
    
    try:
        # Simulate auto-blocking with notification
        block_result = auto_ip_blocking_service.auto_block_ip(
            source_ip=test_ip,
            threat_type="BRUTE_FORCE",
            severity="HIGH",
            reason="TEST: Simulated brute force attack for testing auto-blocking and email notifications",
            ml_risk_score=85.0,
            ml_anomaly_score=0.95,
            ml_confidence=0.90,
            attack_metrics={
                "total_attempts": 25,
                "unique_usernames_attempted": 5,
                "first_attempt": datetime.now(timezone.utc),
                "last_attempt": datetime.now(timezone.utc),
            }
        )
        
        # Verify IP is blocked
        is_blocked = IPBlockingService.is_blocked(test_ip)
        
        return {
            "success": block_result.get("success", False),
            "message": "Auto-blocking test completed",
            "ip_address": test_ip,
            "block_result": block_result,
            "is_blocked_verified": is_blocked,
            "email_sent": block_result.get("email_sent", False),
            "note": f"IP {test_ip} has been blocked for testing. You can unblock it via /api/ip-blocking/unblock endpoint.",
        }
    except Exception as e:
        import traceback
        return {
            "success": False,
            "message": f"Error testing auto-blocking: {str(e)}",
            "error": str(e),
            "traceback": traceback.format_exc(),
            "ip_address": test_ip,
        }


@app.post("/test/auto-block-cleanup/{ip_address}")
def test_auto_block_cleanup(ip_address: str):
    """Unblock a test IP address (cleanup after testing)"""
    from app.services.ip_blocking_service import IPBlockingService
    
    try:
        if not IPBlockingService.is_blocked(ip_address):
            return {
                "success": False,
                "message": f"IP {ip_address} is not currently blocked",
            }
        
        result = IPBlockingService.unblock_ip(ip_address, unblocked_by="test_cleanup")
        
        return {
            "success": result.get("success", False),
            "message": f"IP {ip_address} unblocked successfully",
            "result": result,
        }
    except Exception as e:
        import traceback
        return {
            "success": False,
            "message": f"Error unblocking IP: {str(e)}",
            "error": str(e),
            "traceback": traceback.format_exc(),
        }


@app.get("/")
def root():
    return {
        "message": "Firewall Log Analyzer API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.post("/test-db")
def test_db():
    logs_collection.insert_one({
        "message": "MongoDB Atlas connected",
        "timestamp": datetime.utcnow()
    })
    return {"status": "Inserted into Atlas"}
