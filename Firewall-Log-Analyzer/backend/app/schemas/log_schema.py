from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class VirusTotalReputation(BaseModel):
    """VirusTotal IP reputation data"""
    detected: bool = False
    reputation_score: int = Field(0, ge=0, le=100, description="Reputation score 0-100 (higher = more malicious)")
    threat_level: str = Field("UNKNOWN", description="CRITICAL, HIGH, MEDIUM, LOW, CLEAN, UNKNOWN")
    malicious_count: int = 0
    suspicious_count: int = 0
    total_engines: int = 0
    last_analysis_date: Optional[str] = None
    country: Optional[str] = None
    asn: Optional[int] = None
    as_owner: Optional[str] = None
    categories: list[str] = Field(default_factory=list)
    detection_names: list[str] = Field(default_factory=list)
    virustotal_url: Optional[str] = None


class LogResponse(BaseModel):
    """Response model for a single log entry"""
    id: Optional[str] = Field(None, alias="_id")
    timestamp: datetime
    source_ip: str
    destination_port: Optional[int] = None
    protocol: Optional[str] = None
    log_source: str
    event_type: str
    severity: str
    username: Optional[str] = None
    raw_log: str
    virustotal: Optional[VirusTotalReputation] = None

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class LogsResponse(BaseModel):
    """Response model for paginated logs"""
    logs: list[LogResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class StatsResponse(BaseModel):
    """Response model for statistics"""
    total_logs: int
    severity_counts: dict[str, int]
    event_type_counts: dict[str, int]
    protocol_counts: dict[str, int]
    logs_by_hour: list[dict]  # [{"hour": "2024-01-01T10:00:00", "count": 100}]
    top_source_ips: list[dict]  # [{"source_ip": "192.168.1.1", "count": 50}]
    top_ports: list[dict]  # [{"port": 22, "count": 100}]


class TopIPResponse(BaseModel):
    """Response model for top IPs"""
    source_ip: str
    count: int
    severity_breakdown: dict[str, int]  # {"HIGH": 10, "MEDIUM": 5, "LOW": 2}
    virustotal: Optional[VirusTotalReputation] = None


class TopPortResponse(BaseModel):
    """Response model for top ports"""
    port: int
    count: int
    protocol: Optional[str] = None

