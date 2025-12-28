from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field


class ActiveAlert(BaseModel):
    """Model for an active alert"""
    type: str = Field(..., description="Alert type: BRUTE_FORCE or DDOS")
    source_ip: str
    severity: str = Field(..., description="CRITICAL, HIGH, MEDIUM, LOW")
    detected_at: datetime
    description: str
    threat_count: Optional[int] = None  # For brute force: total attempts, for DDoS: total requests


class ThreatSummary(BaseModel):
    """Summary of threats"""
    total_brute_force: int = Field(0, description="Total brute force detections in last 24 hours")
    total_ddos: int = Field(0, description="Total DDoS detections in last 24 hours")
    critical_count: int = Field(0, description="Number of CRITICAL severity threats")
    high_count: int = Field(0, description="Number of HIGH severity threats")
    medium_count: int = Field(0, description="Number of MEDIUM severity threats")
    low_count: int = Field(0, description="Number of LOW severity threats")


class TopIP(BaseModel):
    """Model for top IP statistics"""
    source_ip: str
    total_logs: int
    severity_breakdown: Dict[str, int] = Field(default_factory=dict, description="Breakdown by severity")
    last_seen: Optional[datetime] = None


class SystemHealth(BaseModel):
    """System health metrics"""
    database_status: str = Field(..., description="Status: healthy, degraded, or down")
    total_logs_24h: int = Field(0, description="Total logs in last 24 hours")
    high_severity_logs_24h: int = Field(0, description="High severity logs in last 24 hours")
    last_log_timestamp: Optional[datetime] = None
    uptime_seconds: Optional[float] = None


class DashboardSummaryResponse(BaseModel):
    """Response model for dashboard summary"""
    active_alerts: List[ActiveAlert] = Field(default_factory=list, description="Recent active alerts")
    threats: ThreatSummary = Field(..., description="Threat summary statistics")
    top_ips: List[TopIP] = Field(default_factory=list, description="Top source IPs")
    system_health: SystemHealth = Field(..., description="System health metrics")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="When this summary was generated")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

