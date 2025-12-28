from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ThreatSummary(BaseModel):
    """Model for threat summary statistics"""
    total_brute_force_attacks: int
    total_ddos_attacks: int
    total_threats: int
    critical_threats: int
    high_threats: int
    medium_threats: int
    low_threats: int


class ReportSummary(BaseModel):
    """Model for report summary"""
    total_logs: int
    security_score: int = Field(ge=0, le=100, description="Security score from 0-100")
    security_status: str = Field(description="Security status: SECURE, MODERATE, WARNING, CRITICAL")
    threat_summary: ThreatSummary


class BruteForceAttackSummary(BaseModel):
    """Summary of brute force attack for reports"""
    source_ip: str
    total_attempts: int
    severity: str
    first_attempt: Optional[str] = None
    last_attempt: Optional[str] = None


class DDoSAttackSummary(BaseModel):
    """Summary of DDoS attack for reports"""
    attack_type: str
    source_ip_count: int
    total_requests: int
    peak_request_rate: float
    target_port: Optional[int] = None
    target_protocol: Optional[str] = None
    severity: str
    first_request: Optional[str] = None
    last_request: Optional[str] = None


class ThreatDetections(BaseModel):
    """Model for threat detections in reports"""
    brute_force_attacks: List[BruteForceAttackSummary]
    ddos_attacks: List[DDoSAttackSummary]


class ThreatSourceSummary(BaseModel):
    """Model for threat source summary"""
    ip: str
    brute_force_attacks: int
    ddos_attacks: int
    total_attempts: int
    severity: str


class ReportPeriod(BaseModel):
    """Model for report period"""
    start: str  # ISO format datetime
    end: str    # ISO format datetime


class SecurityReport(BaseModel):
    """Complete security report model"""
    report_type: str = Field(description="Report type: DAILY, WEEKLY, or CUSTOM")
    report_date: str = Field(description="When the report was generated (ISO format)")
    period: ReportPeriod
    summary: ReportSummary
    log_statistics: Dict[str, Any] = Field(description="Log statistics including distributions, top IPs, ports, etc.")
    threat_detections: ThreatDetections
    top_threat_sources: List[ThreatSourceSummary]
    recommendations: List[str]
    time_breakdown: Optional[List[Dict[str, Any]]] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class DailyReportResponse(BaseModel):
    """Response model for daily report"""
    report: SecurityReport


class WeeklyReportResponse(BaseModel):
    """Response model for weekly report"""
    report: SecurityReport


class CustomReportResponse(BaseModel):
    """Response model for custom date range report"""
    report: SecurityReport


class ExportRequest(BaseModel):
    """Request model for report export"""
    report_type: str = Field(description="Report type: DAILY, WEEKLY, or CUSTOM")
    format: str = Field(description="Export format: json, csv, or pdf")
    date: Optional[str] = Field(None, description="Date for daily report (ISO format, YYYY-MM-DD)")
    start_date: Optional[str] = Field(None, description="Start date for weekly/custom report (ISO format)")
    end_date: Optional[str] = Field(None, description="End date for custom report (ISO format)")


class ExportResponse(BaseModel):
    """Response model for report export"""
    format: str
    filename: str
    content: str = Field(description="Base64 encoded content for binary formats, or plain text for text formats")
    content_type: str = Field(description="MIME type of the exported content")

