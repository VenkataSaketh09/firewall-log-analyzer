from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ThreatSummary(BaseModel):
    """Model for threat summary statistics"""
    total_brute_force_attacks: int
    total_ddos_attacks: int
    total_port_scan_attacks: int = 0
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


class PortScanAttackSummary(BaseModel):
    """Summary of port scan for reports"""
    source_ip: str
    total_attempts: int
    unique_ports_attempted: int
    severity: str
    first_attempt: Optional[str] = None
    last_attempt: Optional[str] = None


class ThreatDetections(BaseModel):
    """Model for threat detections in reports"""
    brute_force_attacks: List[BruteForceAttackSummary]
    ddos_attacks: List[DDoSAttackSummary]
    port_scan_attacks: List[PortScanAttackSummary] = Field(default_factory=list)


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
    # These are optional so include_* toggles can omit sections cleanly.
    summary: Optional[ReportSummary] = None
    log_statistics: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Log statistics including distributions, top IPs, ports, etc."
    )
    threat_detections: Optional[ThreatDetections] = None
    top_threat_sources: Optional[List[ThreatSourceSummary]] = None
    recommendations: Optional[List[str]] = None
    time_breakdown: Optional[List[Dict[str, Any]]] = None
    detailed_logs: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Optional detailed logs included when include_logs=true (may be truncated)"
    )

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
    include_charts: Optional[bool] = Field(None, description="Include chart/statistics sections")
    include_summary: Optional[bool] = Field(None, description="Include executive summary section")
    include_threats: Optional[bool] = Field(None, description="Include threats sections")
    include_logs: Optional[bool] = Field(None, description="Include detailed logs section (may be truncated)")


class ExportResponse(BaseModel):
    """Response model for report export"""
    format: str
    filename: str
    content: str = Field(description="Base64 encoded content for binary formats, or plain text for text formats")
    content_type: str = Field(description="MIME type of the exported content")


class SavedReport(BaseModel):
    """Model for a saved report in the database"""
    id: Optional[str] = Field(None, alias="_id", description="MongoDB document ID")
    report_name: Optional[str] = Field(None, description="User-provided name for the report")
    report: SecurityReport = Field(description="The actual report data")
    created_at: str = Field(description="When the report was saved (ISO format)")
    notes: Optional[str] = Field(None, description="Optional user notes")


class SaveReportRequest(BaseModel):
    """Request model for saving a report"""
    report: SecurityReport = Field(description="The report to save")
    report_name: Optional[str] = Field(None, description="Optional name for the report")
    notes: Optional[str] = Field(None, description="Optional notes about the report")


class SaveReportResponse(BaseModel):
    """Response model for saving a report"""
    id: str = Field(description="ID of the saved report")
    message: str = Field(description="Success message")


class SavedReportListItem(BaseModel):
    """Model for a saved report in the list (summary only)"""
    id: str = Field(description="MongoDB document ID")
    report_name: Optional[str] = None
    report_type: str
    report_date: str
    period: ReportPeriod
    summary: ReportSummary
    created_at: str
    notes: Optional[str] = None

    class Config:
        populate_by_name = True


class ReportHistoryResponse(BaseModel):
    """Response model for report history list"""
    reports: List[SavedReportListItem]
    total: int = Field(description="Total number of saved reports")

