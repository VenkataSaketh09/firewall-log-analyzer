from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Query, HTTPException, Body
from app.services.brute_force_detection import detect_brute_force, get_brute_force_timeline
from app.services.ddos_detection import detect_ddos
from app.services.virustotal_service import get_multiple_ip_reputations, enhance_severity_with_reputation
from app.schemas.threat_schema import (
    BruteForceDetectionsResponse,
    BruteForceDetection,
    BruteForceTimelineResponse,
    AttackWindow,
    BruteForceConfig,
    DDoSDetectionsResponse,
    DDoSDetection,
    DDoSAttackWindow
)
from app.schemas.log_schema import VirusTotalReputation

router = APIRouter(prefix="/api/threats", tags=["threats"])


@router.get("/brute-force", response_model=BruteForceDetectionsResponse)
def get_brute_force_detections(
    time_window_minutes: int = Query(15, ge=1, le=1440, description="Time window in minutes to check for failed attempts"),
    threshold: int = Query(5, ge=1, le=1000, description="Number of failed attempts to trigger detection"),
    start_date: Optional[datetime] = Query(None, description="Start date for analysis (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date for analysis (ISO format)"),
    source_ip: Optional[str] = Query(None, description="Optional specific IP to check"),
    include_reputation: bool = Query(False, description="Include VirusTotal IP reputation data")
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
        
        # Get reputation data for all detected IPs if requested
        reputation_data = {}
        if include_reputation:
            unique_ips = [detection.get("source_ip") for detection in detections if detection.get("source_ip")]
            if unique_ips:
                reputation_data = get_multiple_ip_reputations(unique_ips)
        
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
            
            # Get reputation for this IP
            ip_reputation = None
            detected_ip = detection.get("source_ip")
            severity = detection.get("severity", "LOW")
            
            if include_reputation and detected_ip and detected_ip in reputation_data:
                rep_data = reputation_data[detected_ip]
                if rep_data:
                    ip_reputation = VirusTotalReputation(**rep_data)
                    # Enhance severity based on reputation
                    severity = enhance_severity_with_reputation(severity, rep_data)
            
            detection_models.append(
                BruteForceDetection(
                    source_ip=detected_ip,
                    total_attempts=detection["total_attempts"],
                    unique_usernames_attempted=detection["unique_usernames_attempted"],
                    usernames_attempted=detection["usernames_attempted"],
                    first_attempt=detection["first_attempt"],
                    last_attempt=detection["last_attempt"],
                    attack_windows=attack_windows,
                    severity=severity,
                    virustotal=ip_reputation
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
    config: BruteForceConfig = Body(..., description="Brute force detection configuration"),
    include_reputation: bool = Query(False, description="Include VirusTotal IP reputation data")
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
        
        # Get reputation data for all detected IPs if requested
        reputation_data = {}
        if include_reputation:
            unique_ips = [detection.get("source_ip") for detection in detections if detection.get("source_ip")]
            if unique_ips:
                reputation_data = get_multiple_ip_reputations(unique_ips)
        
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
            
            # Get reputation for this IP
            ip_reputation = None
            detected_ip = detection.get("source_ip")
            severity = detection.get("severity", "LOW")
            
            if include_reputation and detected_ip and detected_ip in reputation_data:
                rep_data = reputation_data[detected_ip]
                if rep_data:
                    ip_reputation = VirusTotalReputation(**rep_data)
                    # Enhance severity based on reputation
                    severity = enhance_severity_with_reputation(severity, rep_data)
            
            detection_models.append(
                BruteForceDetection(
                    source_ip=detected_ip,
                    total_attempts=detection["total_attempts"],
                    unique_usernames_attempted=detection["unique_usernames_attempted"],
                    usernames_attempted=detection["usernames_attempted"],
                    first_attempt=detection["first_attempt"],
                    last_attempt=detection["last_attempt"],
                    attack_windows=attack_windows,
                    severity=severity,
                    virustotal=ip_reputation
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


@router.get("/ddos", response_model=DDoSDetectionsResponse)
def get_ddos_detections(
    time_window_seconds: int = Query(60, ge=1, le=3600, description="Time window in seconds for rate calculation"),
    single_ip_threshold: int = Query(100, ge=1, le=100000, description="Minimum requests per window to flag single IP flood"),
    distributed_ip_count: int = Query(10, ge=2, le=1000, description="Minimum unique IPs to consider distributed attack"),
    distributed_request_threshold: int = Query(500, ge=1, le=1000000, description="Total requests threshold for distributed attack"),
    start_date: Optional[datetime] = Query(None, description="Start date for analysis (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date for analysis (ISO format)"),
    destination_port: Optional[int] = Query(None, description="Optional destination port to filter by"),
    protocol: Optional[str] = Query(None, description="Optional protocol to filter by (TCP, UDP, etc.)"),
    include_reputation: bool = Query(False, description="Include VirusTotal IP reputation data")
):
    """
    Detect DDoS/Flood attacks based on traffic patterns.
    
    Detects two types of attacks:
    1. Single IP Floods - High request rate from a single source IP (rate-based anomaly detection)
    2. Distributed Floods - Multiple IPs targeting same destination/port simultaneously (distributed attack pattern recognition)
    
    Uses sliding window analysis to identify traffic floods and calculates request rates
    to detect anomalies in network traffic patterns.
    
    Returns a list of detected DDoS/flood attacks with detailed analysis including:
    - Attack type (single IP or distributed)
    - Request rates and patterns
    - Target information (ports, protocols)
    - Attack time windows
    - Severity assessment
    """
    try:
        detections = detect_ddos(
            time_window_seconds=time_window_seconds,
            single_ip_threshold=single_ip_threshold,
            distributed_ip_count=distributed_ip_count,
            distributed_request_threshold=distributed_request_threshold,
            start_date=start_date,
            end_date=end_date,
            destination_port=destination_port,
            protocol=protocol
        )
        
        # Get reputation data for all detected IPs if requested
        reputation_data = {}
        if include_reputation:
            all_source_ips = []
            for detection in detections:
                source_ips = detection.get("source_ips", [])
                all_source_ips.extend(source_ips)
            
            if all_source_ips:
                unique_ips = list(set(all_source_ips))
                reputation_data = get_multiple_ip_reputations(unique_ips)
        
        # Convert to response models
        detection_models = []
        for detection in detections:
            attack_windows = [
                DDoSAttackWindow(
                    window_start=win["window_start"],
                    window_end=win["window_end"],
                    request_count=win["request_count"],
                    request_rate_per_min=win["request_rate_per_min"],
                    target_ports=win.get("target_ports"),
                    protocols=win.get("protocols"),
                    unique_ip_count=win.get("unique_ip_count"),
                    top_attacking_ips=win.get("top_attacking_ips")
                )
                for win in detection["attack_windows"]
            ]
            
            detection_models.append(
                DDoSDetection(
                    attack_type=detection["attack_type"],
                    source_ips=detection["source_ips"],
                    source_ip_count=detection["source_ip_count"],
                    total_requests=detection["total_requests"],
                    peak_request_rate=detection["peak_request_rate"],
                    avg_request_rate=detection["avg_request_rate"],
                    target_ports=detection.get("target_ports"),
                    target_protocols=detection.get("target_protocols"),
                    target_port=detection.get("target_port"),
                    target_protocol=detection.get("target_protocol"),
                    peak_unique_ips=detection.get("peak_unique_ips"),
                    first_request=detection["first_request"],
                    last_request=detection["last_request"],
                    attack_windows=attack_windows,
                    top_attacking_ips=detection.get("top_attacking_ips"),
                    severity=detection["severity"],
                    source_ip_reputations={
                        ip: VirusTotalReputation(**rep_data)
                        for ip, rep_data in reputation_data.items()
                        if ip in detection.get("source_ips", []) and rep_data
                    } if include_reputation and reputation_data else None
                )
            )
        
        # Determine time range for response
        if end_date is None:
            end_date = datetime.utcnow()
        if start_date is None:
            start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        return DDoSDetectionsResponse(
            detections=detection_models,
            total_detections=len(detection_models),
            time_window_seconds=time_window_seconds,
            single_ip_threshold=single_ip_threshold,
            distributed_ip_count=distributed_ip_count,
            distributed_request_threshold=distributed_request_threshold,
            time_range={
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error detecting DDoS/flood attacks: {str(e)}")

