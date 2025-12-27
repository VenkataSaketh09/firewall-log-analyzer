from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


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

