from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from app.schemas.log_schema import VirusTotalReputation


class AttackWindow(BaseModel):
    """Model for an attack time window"""
    window_start: datetime
    window_end: datetime
    attempt_count: int
    attempts: List[dict]  # List of attempt details with timestamp, username, log_id


class BruteForceDetection(BaseModel):
    """Response model for a brute force detection"""
    source_ip: str
    total_attempts: int
    unique_usernames_attempted: int
    usernames_attempted: List[str]
    first_attempt: datetime
    last_attempt: datetime
    attack_windows: List[AttackWindow]
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    virustotal: Optional[VirusTotalReputation] = None
    # ML enrichment (optional)
    ml_anomaly_score: Optional[float] = None
    ml_predicted_label: Optional[str] = None
    ml_confidence: Optional[float] = None
    ml_risk_score: Optional[float] = None  # 0-100
    ml_reasoning: Optional[list[str]] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class BruteForceDetectionsResponse(BaseModel):
    """Response model for brute force detections list"""
    detections: List[BruteForceDetection]
    total_detections: int
    time_window_minutes: int
    threshold: int
    time_range: dict  # {"start": datetime, "end": datetime}


class BruteForceTimelineResponse(BaseModel):
    """Response model for brute force timeline"""
    source_ip: str
    total_attempts: int
    timeline: List[dict]  # List of attempts with timestamp, username, log_id
    time_range: dict  # {"start": datetime, "end": datetime}

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class BruteForceConfig(BaseModel):
    """Request model for configuring brute force detection"""
    time_window_minutes: int = Field(15, ge=1, le=1440, description="Time window in minutes")
    threshold: int = Field(5, ge=1, le=1000, description="Number of failed attempts to trigger detection")
    start_date: Optional[datetime] = Field(None, description="Start date for analysis (ISO format)")
    end_date: Optional[datetime] = Field(None, description="End date for analysis (ISO format)")
    source_ip: Optional[str] = Field(None, description="Optional specific IP to check")


class DDoSAttackWindow(BaseModel):
    """Model for a DDoS attack time window"""
    window_start: datetime
    window_end: datetime
    request_count: int
    request_rate_per_min: float
    target_ports: Optional[dict] = None
    protocols: Optional[dict] = None
    unique_ip_count: Optional[int] = None  # For distributed attacks
    top_attacking_ips: Optional[dict] = None  # For distributed attacks


class DDoSDetection(BaseModel):
    """Response model for a DDoS/flood detection"""
    attack_type: str  # SINGLE_IP_FLOOD or DISTRIBUTED_FLOOD
    source_ips: List[str]
    source_ip_count: int
    total_requests: int
    peak_request_rate: float  # requests per minute
    avg_request_rate: float  # requests per minute
    target_ports: Optional[List[int]] = None  # For single IP attacks
    target_protocols: Optional[List[str]] = None  # For single IP attacks
    target_port: Optional[int] = None  # For distributed attacks
    target_protocol: Optional[str] = None  # For distributed attacks
    peak_unique_ips: Optional[int] = None  # For distributed attacks
    first_request: datetime
    last_request: datetime
    attack_windows: List[DDoSAttackWindow]
    top_attacking_ips: Optional[dict] = None  # For distributed attacks: {ip: request_count}
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    source_ip_reputations: Optional[dict[str, VirusTotalReputation]] = None  # Map of IP -> reputation
    # ML enrichment (optional)
    ml_anomaly_score: Optional[float] = None
    ml_predicted_label: Optional[str] = None
    ml_confidence: Optional[float] = None
    ml_risk_score: Optional[float] = None  # 0-100
    ml_reasoning: Optional[list[str]] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class DDoSDetectionsResponse(BaseModel):
    """Response model for DDoS detections list"""
    detections: List[DDoSDetection]
    total_detections: int
    time_window_seconds: int
    single_ip_threshold: int
    distributed_ip_count: int
    distributed_request_threshold: int
    time_range: dict  # {"start": datetime, "end": datetime}


class PortScanAttackWindow(BaseModel):
    """Model for a port scan time window"""
    window_start: datetime
    window_end: datetime
    attempt_count: int
    unique_ports: int
    ports: List[int]
    attempts: List[dict]  # {timestamp, destination_port, protocol, log_id}


class PortScanDetection(BaseModel):
    """Response model for a port scan detection"""
    source_ip: str
    total_attempts: int
    unique_ports_attempted: int
    ports_attempted: List[int]
    first_attempt: datetime
    last_attempt: datetime
    attack_windows: List[PortScanAttackWindow]
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    virustotal: Optional[VirusTotalReputation] = None
    # ML enrichment (optional)
    ml_anomaly_score: Optional[float] = None
    ml_predicted_label: Optional[str] = None
    ml_confidence: Optional[float] = None
    ml_risk_score: Optional[float] = None  # 0-100
    ml_reasoning: Optional[list[str]] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PortScanDetectionsResponse(BaseModel):
    """Response model for port scan detections list"""
    detections: List[PortScanDetection]
    total_detections: int
    time_window_minutes: int
    unique_ports_threshold: int
    min_total_attempts: int
    time_range: dict  # {"start": datetime, "end": datetime}


class PortScanConfig(BaseModel):
    """Request model for configuring port scan detection"""
    time_window_minutes: int = Field(10, ge=1, le=1440, description="Sliding window size in minutes")
    unique_ports_threshold: int = Field(10, ge=2, le=65535, description="Minimum unique destination ports in a window")
    min_total_attempts: int = Field(20, ge=1, le=1000000, description="Minimum total attempts from IP in period")
    start_date: Optional[datetime] = Field(None, description="Start date for analysis (ISO format)")
    end_date: Optional[datetime] = Field(None, description="End date for analysis (ISO format)")
    source_ip: Optional[str] = Field(None, description="Optional specific IP to check")
    protocol: Optional[str] = Field(None, description="Optional protocol filter (TCP/UDP)")

