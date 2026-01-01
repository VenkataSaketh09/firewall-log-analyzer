from datetime import datetime, timezone
from typing import Optional, Literal
import csv
import io
import json

from fastapi import APIRouter, Query, HTTPException, Body
from fastapi.encoders import jsonable_encoder
from fastapi.responses import Response, StreamingResponse
from app.services.brute_force_detection import detect_brute_force, get_brute_force_timeline
from app.services.ddos_detection import detect_ddos
from app.services.port_scan_detection import detect_port_scan
from app.services.virustotal_service import get_multiple_ip_reputations, enhance_severity_with_reputation
from app.schemas.threat_schema import (
    BruteForceDetectionsResponse,
    BruteForceDetection,
    BruteForceTimelineResponse,
    AttackWindow,
    BruteForceConfig,
    DDoSDetectionsResponse,
    DDoSDetection,
    DDoSAttackWindow,
    PortScanDetectionsResponse,
    PortScanDetection,
    PortScanAttackWindow,
    PortScanConfig
)
from app.schemas.log_schema import VirusTotalReputation

router = APIRouter(prefix="/api/threats", tags=["threats"])

ThreatExportFormat = Optional[Literal["csv", "json"]]


def _normalize_severity_filter(severity: Optional[str]) -> Optional[str]:
    if not severity:
        return None
    s = severity.strip().upper()
    return s or None


def _filter_by_severity(items, severity: Optional[str]):
    sev = _normalize_severity_filter(severity)
    if not sev:
        return items
    return [i for i in items if (getattr(i, "severity", None) or "").upper() == sev]


def _csv_download(csv_text: str, filename: str) -> Response:
    # Use UTF-8 with BOM for Excel-friendliness.
    payload = ("\ufeff" + csv_text).encode("utf-8")
    return Response(
        content=payload,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _json_download(data, filename: str) -> Response:
    payload = json.dumps(jsonable_encoder(data), indent=2).encode("utf-8")
    return Response(
        content=payload,
        media_type="application/json; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _downgrade_severity(sev: str) -> str:
    s = (sev or "").strip().upper()
    order = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    if s not in order:
        return sev
    idx = order.index(s)
    return order[max(0, idx - 1)]


@router.get("/brute-force", response_model=BruteForceDetectionsResponse)
def get_brute_force_detections(
    time_window_minutes: int = Query(15, ge=1, le=1440, description="Time window in minutes to check for failed attempts"),
    threshold: int = Query(5, ge=1, le=1000, description="Number of failed attempts to trigger detection"),
    start_date: Optional[datetime] = Query(None, description="Start date for analysis (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date for analysis (ISO format)"),
    source_ip: Optional[str] = Query(None, description="Optional specific IP to check"),
    severity: Optional[str] = Query(None, description="Optional severity filter (CRITICAL/HIGH/MEDIUM/LOW)"),
    include_reputation: bool = Query(False, description="Include VirusTotal IP reputation data"),
    include_ml: bool = Query(True, description="Include ML anomaly/classification/risk scoring if available"),
    format: ThreatExportFormat = Query(None, description="Optional export format (csv/json)")
):
    """
    Detect brute force attacks based on failed login attempts.
    
    Analyzes SSH_FAILED_LOGIN events to identify IPs that have exceeded
    the threshold number of failed attempts within the specified time window.
    
    Returns a list of IPs flagged as potential brute force attacks with
    detailed attack timeline information.
    """
    try:
        # Initialize ML service only if needed
        ml_service_available = False
        ml_service = None
        if include_ml:
            try:
                from app.services.ml_service import ml_service
                # Initialize ML service (will use cache if already initialized)
                # Wrap in try-except to prevent hanging if models are missing
                ml_service.initialize()
                # Check if ML is actually available (initialized and no errors)
                ml_service_available = (
                    hasattr(ml_service, '_initialized') and 
                    ml_service._initialized and 
                    (not hasattr(ml_service, '_last_error') or ml_service._last_error is None)
                )
            except Exception as e:
                # If ML initialization fails, continue without ML
                ml_service_available = False
                ml_service = None

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
            
            model = BruteForceDetection(
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

            if include_ml:
                try:
                    # Representative log: we only have log_id list in windows; use a synthetic log line hinting the behavior.
                    raw_hint = detection.get("sample_raw_log") or f"SSH failed login brute force suspected from {detected_ip}"
                    ml = ml_service.score(
                        source_ip=detected_ip,
                        threat_type_hint="BRUTE_FORCE",
                        severity_hint=severity,
                        timestamp=detection.get("last_attempt"),
                        log_source=detection.get("sample_log_source") or "auth.log",
                        event_type=detection.get("sample_event_type") or "SSH_FAILED_LOGIN",
                        raw_log=raw_hint,
                        context={"threat": "brute_force", "source_ip": detected_ip},
                    )
                    # Always attach ML data, even if ml_available is False (partial failure)
                    model.ml_anomaly_score = ml.anomaly_score
                    model.ml_predicted_label = ml.predicted_label
                    model.ml_confidence = ml.confidence
                    model.ml_risk_score = ml.risk_score
                    model.ml_reasoning = ml.reasoning or []

                    # Reduce false positives conservatively: if ML is strongly NORMAL and low anomaly, downgrade severity
                    if (
                        ml.ml_available
                        and (ml.predicted_label or "").upper() == "NORMAL"
                        and (ml.confidence or 0.0) >= 0.80
                        and (ml.anomaly_score or 0.0) <= 0.30
                    ):
                        model.severity = _downgrade_severity(model.severity)
                        model.ml_reasoning.append(f"severity_downgraded_to={model.severity}")
                except Exception as ml_error:
                    # If ML scoring fails completely, still attach error info for debugging
                    model.ml_reasoning = [f"ML scoring error: {str(ml_error)}"]
                    # Compute a basic fallback risk score using severity
                    severity_map = {"CRITICAL": 0.95, "HIGH": 0.85, "MEDIUM": 0.70, "LOW": 0.55}
                    fallback_conf = severity_map.get((severity or "").upper(), 0.50)
                    label_weight = 0.80  # BRUTE_FORCE weight
                    model.ml_risk_score = 100.0 * max(0.0, min(1.0, 0.45 * fallback_conf * label_weight))
                    model.ml_predicted_label = "BRUTE_FORCE"
                    model.ml_confidence = fallback_conf

            detection_models.append(model)
        
        # Determine time range for response
        if end_date is None:
            end_date = datetime.now(timezone.utc)
        if start_date is None:
            start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        detection_models = _filter_by_severity(detection_models, severity)

        response_model = BruteForceDetectionsResponse(
            detections=detection_models,
            total_detections=len(detection_models),
            time_window_minutes=time_window_minutes,
            threshold=threshold,
            time_range={
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            }
        )
        if format == "json":
            return _json_download(
                response_model.model_dump(),
                filename=f"brute_force_threats_{datetime.now(timezone.utc).date().isoformat()}.json",
            )
        if format == "csv":
            output = io.StringIO()
            writer = csv.DictWriter(
                output,
                fieldnames=[
                    "source_ip",
                    "severity",
                    "total_attempts",
                    "unique_usernames_attempted",
                    "first_attempt",
                    "last_attempt",
                ],
            )
            writer.writeheader()
            for d in detection_models:
                writer.writerow(
                    {
                        "source_ip": d.source_ip,
                        "severity": d.severity,
                        "total_attempts": d.total_attempts,
                        "unique_usernames_attempted": d.unique_usernames_attempted,
                        "first_attempt": d.first_attempt,
                        "last_attempt": d.last_attempt,
                    }
                )
            return _csv_download(
                output.getvalue(),
                filename=f"brute_force_threats_{datetime.now(timezone.utc).date().isoformat()}.csv",
            )

        return response_model
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error detecting brute force attacks: {str(e)}")


@router.post("/brute-force", response_model=BruteForceDetectionsResponse)
def detect_brute_force_post(
    config: BruteForceConfig = Body(..., description="Brute force detection configuration"),
    include_reputation: bool = Query(False, description="Include VirusTotal IP reputation data"),
    include_ml: bool = Query(True, description="Include ML anomaly/classification/risk scoring if available")
):
    """
    Detect brute force attacks using POST method with configuration in request body.
    
    This endpoint allows more complex configurations to be sent in the request body.
    """
    try:
        from app.services.ml_service import ml_service
        ml_service.initialize()

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
            
            model = BruteForceDetection(
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

            if include_ml:
                raw_hint = detection.get("sample_raw_log") or f"SSH failed login brute force suspected from {detected_ip}"
                ml = ml_service.score(
                    source_ip=detected_ip,
                    threat_type_hint="BRUTE_FORCE",
                    severity_hint=severity,
                    timestamp=detection.get("last_attempt"),
                    log_source=detection.get("sample_log_source") or "auth.log",
                    event_type=detection.get("sample_event_type") or "SSH_FAILED_LOGIN",
                    raw_log=raw_hint,
                    context={"threat": "brute_force", "source_ip": detected_ip},
                )
                model.ml_anomaly_score = ml.anomaly_score
                model.ml_predicted_label = ml.predicted_label
                model.ml_confidence = ml.confidence
                model.ml_risk_score = ml.risk_score
                model.ml_reasoning = ml.reasoning or []

                if (
                    (ml.predicted_label or "").upper() == "NORMAL"
                    and (ml.confidence or 0.0) >= 0.80
                    and (ml.anomaly_score or 0.0) <= 0.30
                ):
                    model.severity = _downgrade_severity(model.severity)
                    model.ml_reasoning.append(f"severity_downgraded_to={model.severity}")

            detection_models.append(model)
        
        # Determine time range for response
        end_date = config.end_date if config.end_date else datetime.now(timezone.utc)
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
    severity: Optional[str] = Query(None, description="Optional severity filter (CRITICAL/HIGH/MEDIUM/LOW)"),
    include_reputation: bool = Query(False, description="Include VirusTotal IP reputation data"),
    include_ml: bool = Query(True, description="Include ML anomaly/classification/risk scoring if available"),
    format: ThreatExportFormat = Query(None, description="Optional export format (csv/json)")
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
        from app.services.ml_service import ml_service
        ml_service.initialize()

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
            
            model = DDoSDetection(
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

            if include_ml:
                try:
                    sample_ip = (detection.get("source_ips") or [None])[0]
                    # DDoS detection is aggregate; use a generic hint (or later we can sample a real raw log)
                    raw_hint = f"Traffic flood suspected from {sample_ip or 'unknown'}"
                    ml = ml_service.score(
                        source_ip=sample_ip,
                        threat_type_hint="DDOS",
                        severity_hint=model.severity,
                        timestamp=detection.get("last_request"),
                        log_source="ufw.log",
                        event_type="DDOS_FLOOD",
                        raw_log=raw_hint,
                        context={"threat": "ddos", "source_ip": sample_ip, "attack_type": model.attack_type},
                    )
                    # Always attach ML data, even if ml_available is False (partial failure)
                    model.ml_anomaly_score = ml.anomaly_score
                    model.ml_predicted_label = ml.predicted_label
                    model.ml_confidence = ml.confidence
                    model.ml_risk_score = ml.risk_score
                    model.ml_reasoning = ml.reasoning or []
                except Exception as ml_error:
                    # If ML scoring fails completely, still attach error info for debugging
                    model.ml_reasoning = [f"ML scoring error: {str(ml_error)}"]
                    # Compute a basic fallback risk score using severity
                    severity_map = {"CRITICAL": 0.95, "HIGH": 0.85, "MEDIUM": 0.70, "LOW": 0.55}
                    fallback_conf = severity_map.get((model.severity or "").upper(), 0.50)
                    label_weight = 0.90  # DDOS weight
                    model.ml_risk_score = 100.0 * max(0.0, min(1.0, 0.45 * fallback_conf * label_weight))
                    model.ml_predicted_label = "DDOS"
                    model.ml_confidence = fallback_conf

            detection_models.append(model)
        
        # Determine time range for response
        if end_date is None:
            end_date = datetime.now(timezone.utc)
        if start_date is None:
            start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        detection_models = _filter_by_severity(detection_models, severity)

        response_model = DDoSDetectionsResponse(
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
        if format == "json":
            return _json_download(
                response_model.model_dump(),
                filename=f"ddos_threats_{datetime.now(timezone.utc).date().isoformat()}.json",
            )
        if format == "csv":
            output = io.StringIO()
            writer = csv.DictWriter(
                output,
                fieldnames=[
                    "attack_type",
                    "severity",
                    "total_requests",
                    "peak_request_rate",
                    "avg_request_rate",
                    "source_ip_count",
                    "target_port",
                    "target_protocol",
                    "first_request",
                    "last_request",
                ],
            )
            writer.writeheader()
            for d in detection_models:
                writer.writerow(
                    {
                        "attack_type": d.attack_type,
                        "severity": d.severity,
                        "total_requests": d.total_requests,
                        "peak_request_rate": d.peak_request_rate,
                        "avg_request_rate": d.avg_request_rate,
                        "source_ip_count": d.source_ip_count,
                        "target_port": d.target_port,
                        "target_protocol": d.target_protocol,
                        "first_request": d.first_request,
                        "last_request": d.last_request,
                    }
                )
            return _csv_download(
                output.getvalue(),
                filename=f"ddos_threats_{datetime.now(timezone.utc).date().isoformat()}.csv",
            )

        return response_model
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error detecting DDoS/flood attacks: {str(e)}")


@router.get("/port-scan", response_model=PortScanDetectionsResponse)
def get_port_scan_detections(
    time_window_minutes: int = Query(10, ge=1, le=1440, description="Sliding window size in minutes"),
    unique_ports_threshold: int = Query(10, ge=2, le=65535, description="Minimum unique ports in window to flag scan"),
    min_total_attempts: int = Query(20, ge=1, le=1000000, description="Minimum total attempts from IP in period"),
    start_date: Optional[datetime] = Query(None, description="Start date for analysis (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date for analysis (ISO format)"),
    source_ip: Optional[str] = Query(None, description="Optional specific IP to check"),
    protocol: Optional[str] = Query(None, description="Optional protocol filter (TCP/UDP)"),
    severity: Optional[str] = Query(None, description="Optional severity filter (CRITICAL/HIGH/MEDIUM/LOW)"),
    include_reputation: bool = Query(False, description="Include VirusTotal IP reputation data"),
    include_ml: bool = Query(True, description="Include ML anomaly/classification/risk scoring if available"),
    format: ThreatExportFormat = Query(None, description="Optional export format (csv/json)")
):
    """
    Detect port scanning based on a single source IP probing many destination ports
    in a short time window.
    """
    try:
        from app.services.ml_service import ml_service
        ml_service.initialize()

        detections = detect_port_scan(
            time_window_minutes=time_window_minutes,
            unique_ports_threshold=unique_ports_threshold,
            min_total_attempts=min_total_attempts,
            start_date=start_date,
            end_date=end_date,
            source_ip=source_ip,
            protocol=protocol
        )

        reputation_data = {}
        if include_reputation:
            unique_ips = [d.get("source_ip") for d in detections if d.get("source_ip")]
            if unique_ips:
                reputation_data = get_multiple_ip_reputations(unique_ips)

        detection_models = []
        for detection in detections:
            detected_ip = detection.get("source_ip")
            severity = detection.get("severity", "LOW")
            ip_reputation = None

            if include_reputation and detected_ip and detected_ip in reputation_data:
                rep_data = reputation_data[detected_ip]
                if rep_data:
                    ip_reputation = VirusTotalReputation(**rep_data)
                    severity = enhance_severity_with_reputation(severity, rep_data)

            windows = [
                PortScanAttackWindow(
                    window_start=w["window_start"],
                    window_end=w["window_end"],
                    attempt_count=w["attempt_count"],
                    unique_ports=w["unique_ports"],
                    ports=w.get("ports", []),
                    attempts=w.get("attempts", []),
                )
                for w in detection.get("attack_windows", [])
            ]

            model = PortScanDetection(
                    source_ip=detected_ip,
                    total_attempts=detection.get("total_attempts", 0),
                    unique_ports_attempted=detection.get("unique_ports_attempted", 0),
                    ports_attempted=detection.get("ports_attempted", []),
                    first_attempt=detection.get("first_attempt"),
                    last_attempt=detection.get("last_attempt"),
                    attack_windows=windows,
                    severity=severity,
                    virustotal=ip_reputation
            )

            if include_ml:
                try:
                    raw_hint = f"Port scan suspected from {detected_ip} against {model.unique_ports_attempted} ports"
                    ml = ml_service.score(
                        source_ip=detected_ip,
                        threat_type_hint="PORT_SCAN",
                        severity_hint=model.severity,
                        timestamp=detection.get("last_attempt"),
                        log_source="ufw.log",
                        event_type="PORT_SCAN",
                        raw_log=raw_hint,
                        context={"threat": "port_scan", "source_ip": detected_ip},
                    )
                    # Always attach ML data, even if ml_available is False (partial failure)
                    model.ml_anomaly_score = ml.anomaly_score
                    model.ml_predicted_label = ml.predicted_label
                    model.ml_confidence = ml.confidence
                    model.ml_risk_score = ml.risk_score
                    model.ml_reasoning = ml.reasoning or []
                except Exception as ml_error:
                    # If ML scoring fails completely, still attach error info for debugging
                    model.ml_reasoning = [f"ML scoring error: {str(ml_error)}"]
                    # Compute a basic fallback risk score using severity
                    severity_map = {"CRITICAL": 0.95, "HIGH": 0.85, "MEDIUM": 0.70, "LOW": 0.55}
                    fallback_conf = severity_map.get((model.severity or "").upper(), 0.50)
                    label_weight = 0.90  # PORT_SCAN weight
                    model.ml_risk_score = 100.0 * max(0.0, min(1.0, 0.45 * fallback_conf * label_weight))
                    model.ml_predicted_label = "PORT_SCAN"
                    model.ml_confidence = fallback_conf

            detection_models.append(model)

        # Determine time range for response
        if end_date is None:
            end_date = datetime.now(timezone.utc)
        if start_date is None:
            start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)

        detection_models = _filter_by_severity(detection_models, severity)

        response_model = PortScanDetectionsResponse(
            detections=detection_models,
            total_detections=len(detection_models),
            time_window_minutes=time_window_minutes,
            unique_ports_threshold=unique_ports_threshold,
            min_total_attempts=min_total_attempts,
            time_range={"start": start_date.isoformat(), "end": end_date.isoformat()}
        )
        if format == "json":
            return _json_download(
                response_model.model_dump(),
                filename=f"port_scan_threats_{datetime.now(timezone.utc).date().isoformat()}.json",
            )
        if format == "csv":
            output = io.StringIO()
            writer = csv.DictWriter(
                output,
                fieldnames=[
                    "source_ip",
                    "severity",
                    "total_attempts",
                    "unique_ports_attempted",
                    "first_attempt",
                    "last_attempt",
                ],
            )
            writer.writeheader()
            for d in detection_models:
                writer.writerow(
                    {
                        "source_ip": d.source_ip,
                        "severity": d.severity,
                        "total_attempts": d.total_attempts,
                        "unique_ports_attempted": d.unique_ports_attempted,
                        "first_attempt": d.first_attempt,
                        "last_attempt": d.last_attempt,
                    }
                )
            return _csv_download(
                output.getvalue(),
                filename=f"port_scan_threats_{datetime.now(timezone.utc).date().isoformat()}.csv",
            )

        return response_model
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error detecting port scans: {str(e)}")


@router.post("/port-scan", response_model=PortScanDetectionsResponse)
def detect_port_scan_post(
    config: PortScanConfig = Body(..., description="Port scan detection configuration"),
    include_reputation: bool = Query(False, description="Include VirusTotal IP reputation data")
):
    """
    Detect port scans using POST method with configuration in request body.
    """
    return get_port_scan_detections(
        time_window_minutes=config.time_window_minutes,
        unique_ports_threshold=config.unique_ports_threshold,
        min_total_attempts=config.min_total_attempts,
        start_date=config.start_date,
        end_date=config.end_date,
        source_ip=config.source_ip,
        protocol=config.protocol,
        include_reputation=include_reputation
    )

