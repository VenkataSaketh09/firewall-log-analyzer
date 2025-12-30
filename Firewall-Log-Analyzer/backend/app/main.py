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
from app.middleware.rate_limit import RateLimitMiddleware
from app.config import validate_environment
from app.services.retention_service import start_log_retention_worker
from app.services.ml_service import ml_service
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


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    # Start log retention worker
    start_log_retention_worker()
    print("✓ Log retention worker started")
    # Initialize ML (best-effort)
    if ml_service.initialize():
        print("✓ ML service initialized")
    else:
        print("! ML service not available (falling back to rule-based)")
    print("✓ FastAPI application started successfully")


@app.get("/health")
def health_check():
    return {"status": "Backend is running"}


@app.get("/health/ml")
def ml_health_check():
    status = ml_service.status()
    return {"ml": status}


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
