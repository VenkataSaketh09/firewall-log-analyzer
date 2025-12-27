from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Query, HTTPException, Body
from app.services.brute_force_detection import detect_brute_force, get_brute_force_timeline
from app.schemas.threat_schema import (
    BruteForceDetectionsResponse,
    BruteForceDetection,
    BruteForceTimelineResponse,
    AttackWindow,
    BruteForceConfig
)

router = APIRouter(prefix="/api/threats", tags=["threats"])


@router.get("/brute-force", response_model=BruteForceDetectionsResponse)
def get_brute_force_detections(
    time_window_minutes: int = Query(15, ge=1, le=1440, description="Time window in minutes to check for failed attempts"),
    threshold: int = Query(5, ge=1, le=1000, description="Number of failed attempts to trigger detection"),
    start_date: Optional[datetime] = Query(None, description="Start date for analysis (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date for analysis (ISO format)"),
    source_ip: Optional[str] = Query(None, description="Optional specific IP to check")
):
    """
    Detect brute force attacks based on failed login attempts.
    
    Analyzes SSH_FAILED_LOGIN events to identify IPs that have exceeded
    the threshold number of failed attempts within the specified time window.
    
    Returns a list of IPs flagged as potential brute force attacks with
    detailed attack timeline information.
    """
    try:
        detections = detect_brute_force(
            time_window_minutes=time_window_minutes,
            threshold=threshold,
            start_date=start_date,
            end_date=end_date,
            source_ip=source_ip
        )
        
        # Convert to response models
        detection_models = []
        for detection in detections:
            attack_windows = [
                AttackWindow(
                    window_start=win["window_start"],
                    window_end=win["window_end"],
                    attempt_count=win["attempt_count"],
                    attempts=win["attempts"]
                )
                for win in detection["attack_windows"]
            ]
            
            detection_models.append(
                BruteForceDetection(
                    source_ip=detection["source_ip"],
                    total_attempts=detection["total_attempts"],
                    unique_usernames_attempted=detection["unique_usernames_attempted"],
                    usernames_attempted=detection["usernames_attempted"],
                    first_attempt=detection["first_attempt"],
                    last_attempt=detection["last_attempt"],
                    attack_windows=attack_windows,
                    severity=detection["severity"]
                )
            )
        
        # Determine time range for response
        if end_date is None:
            end_date = datetime.utcnow()
        if start_date is None:
            start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        return BruteForceDetectionsResponse(
            detections=detection_models,
            total_detections=len(detection_models),
            time_window_minutes=time_window_minutes,
            threshold=threshold,
            time_range={
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error detecting brute force attacks: {str(e)}")


@router.post("/brute-force", response_model=BruteForceDetectionsResponse)
def detect_brute_force_post(
    config: BruteForceConfig = Body(..., description="Brute force detection configuration")
):
    """
    Detect brute force attacks using POST method with configuration in request body.
    
    This endpoint allows more complex configurations to be sent in the request body.
    """
    try:
        detections = detect_brute_force(
            time_window_minutes=config.time_window_minutes,
            threshold=config.threshold,
            start_date=config.start_date,
            end_date=config.end_date,
            source_ip=config.source_ip
        )
        
        # Convert to response models
        detection_models = []
        for detection in detections:
            attack_windows = [
                AttackWindow(
                    window_start=win["window_start"],
                    window_end=win["window_end"],
                    attempt_count=win["attempt_count"],
                    attempts=win["attempts"]
                )
                for win in detection["attack_windows"]
            ]
            
            detection_models.append(
                BruteForceDetection(
                    source_ip=detection["source_ip"],
                    total_attempts=detection["total_attempts"],
                    unique_usernames_attempted=detection["unique_usernames_attempted"],
                    usernames_attempted=detection["usernames_attempted"],
                    first_attempt=detection["first_attempt"],
                    last_attempt=detection["last_attempt"],
                    attack_windows=attack_windows,
                    severity=detection["severity"]
                )
            )
        
        # Determine time range for response
        end_date = config.end_date if config.end_date else datetime.utcnow()
        start_date = config.start_date if config.start_date else end_date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        return BruteForceDetectionsResponse(
            detections=detection_models,
            total_detections=len(detection_models),
            time_window_minutes=config.time_window_minutes,
            threshold=config.threshold,
            time_range={
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error detecting brute force attacks: {str(e)}")


@router.get("/brute-force/{ip}/timeline", response_model=BruteForceTimelineResponse)
def get_brute_force_ip_timeline(
    ip: str,
    start_date: Optional[datetime] = Query(None, description="Start date for timeline (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date for timeline (ISO format)")
):
    """
    Get detailed timeline of brute force attempts for a specific IP address.
    
    Returns a chronological list of all failed login attempts from the specified IP.
    """
    try:
        timeline_data = get_brute_force_timeline(
            ip=ip,
            start_date=start_date,
            end_date=end_date
        )
        
        return BruteForceTimelineResponse(
            source_ip=timeline_data["source_ip"],
            total_attempts=timeline_data["total_attempts"],
            timeline=timeline_data["timeline"],
            time_range={
                "start": timeline_data["time_range"]["start"].isoformat(),
                "end": timeline_data["time_range"]["end"].isoformat()
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving brute force timeline: {str(e)}")

