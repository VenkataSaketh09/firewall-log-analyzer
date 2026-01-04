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
from app.middleware.rate_limit import RateLimitMiddleware
from app.config import validate_environment
from app.services.retention_service import start_log_retention_worker
from app.services.ml_service import ml_service
from app.services.ml_auto_retrain_worker import start_auto_retrain_worker
from app.services.log_ingestor import start_log_ingestion
from app.services.raw_log_broadcaster import raw_log_broadcaster
from app.services.alert_monitor_worker import alert_monitor_worker
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


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
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
