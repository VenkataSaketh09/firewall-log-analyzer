from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.mongo import logs_collection
from app.routes.logs import router as logs_router
from app.routes.threats import router as threats_router
from app.routes.reports import router as reports_router
from app.routes.ip_reputation import router as ip_reputation_router
from app.routes.dashboard import router as dashboard_router
from datetime import datetime

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

# Include routers
app.include_router(logs_router)
app.include_router(threats_router)
app.include_router(reports_router)
app.include_router(ip_reputation_router)
app.include_router(dashboard_router)


@app.get("/health")
def health_check():
    return {"status": "Backend is running"}


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
