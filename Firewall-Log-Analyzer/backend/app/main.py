from fastapi import FastAPI
from app.db.mongo import logs_collection
from datetime import datetime

app = FastAPI(title="Firewall Log Analyzer Backend")

@app.get("/health")
def health_check():
    return {"status": "Backend is running"}

@app.post("/test-db")
def test_db():
    logs_collection.insert_one({
        "message": "MongoDB Atlas connected",
        "timestamp": datetime.utcnow()
    })
    return {"status": "Inserted into Atlas"}
