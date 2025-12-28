"""
Schemas for log ingestion API
"""
from typing import Optional, List
from pydantic import BaseModel, Field


class LogIngestionRequest(BaseModel):
    """Request model for log ingestion"""
    logs: List[str] = Field(..., description="List of raw log lines to ingest")
    log_source: Optional[str] = Field(None, description="Optional hint about log source (auth.log, ufw.log, iptables, syslog, sql.log)")


class LogIngestionResponse(BaseModel):
    """Response model for log ingestion"""
    success: bool
    ingested_count: int = Field(..., description="Number of logs successfully ingested")
    failed_count: int = Field(..., description="Number of logs that failed to parse")
    total_received: int = Field(..., description="Total number of log lines received")
    message: str

