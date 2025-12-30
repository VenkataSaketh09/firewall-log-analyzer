import os
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import ipaddress
from dotenv import load_dotenv
from app.db.mongo import db

load_dotenv()

VIRUS_TOTAL_API_KEY = os.getenv("VIRUS_TOTAL_API_KEY")
VIRUS_TOTAL_API_URL = "https://www.virustotal.com/api/v3"

# Cache collection for IP reputation (TTL: 24 hours)
ip_reputation_cache = db.ip_reputation_cache


def _normalize_reputation_fields(rep: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize reputation fields for consistent API responses.
    - Convert empty strings to None for optional text fields
    """
    if not rep:
        return rep
    # Some cached / upstream responses may store empty strings; treat as missing.
    if not rep.get("country"):
        rep["country"] = None
    if not rep.get("as_owner"):
        rep["as_owner"] = None
    return rep


def get_ip_reputation(ip_address: str, use_cache: bool = True) -> Optional[Dict[str, Any]]:
    """
    Get IP address reputation from VirusTotal API.
    Uses caching to avoid excessive API calls.
    
    Args:
        ip_address: IP address to check
        use_cache: Whether to use cached results (default: True)
    
    Returns:
        Dictionary with IP reputation data or None if error
    """
    # VirusTotal won't have enrichment for private/reserved IPs; avoid wasting API calls.
    try:
        ip_obj = ipaddress.ip_address(ip_address)
        if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local or ip_obj.is_reserved or ip_obj.is_multicast:
            return {
                "detected": False,
                "reputation_score": 0,
                "threat_level": "UNKNOWN",
                "malicious_count": 0,
                "suspicious_count": 0,
                "total_engines": 0,
                "last_analysis_date": None,
                "country": None,
                "asn": None,
                "as_owner": None,
                "categories": [],
                "detection_names": [],
                "virustotal_url": None,
            }
    except ValueError:
        # Not a valid IP string; let downstream handle.
        pass

    if not VIRUS_TOTAL_API_KEY:
        return None
    
    # Check cache first
    if use_cache:
        cached_result = ip_reputation_cache.find_one({"ip": ip_address})
        if cached_result:
            # Check if cache is still valid (24 hours)
            cached_time = cached_result.get("cached_at")
            if cached_time:
                if isinstance(cached_time, datetime):
                    cache_age = datetime.utcnow() - cached_time
                    if cache_age < timedelta(hours=24):
                        # Return cached result without API call
                        cached_result.pop("_id", None)
                        cached_result.pop("cached_at", None)
                        return _normalize_reputation_fields(cached_result)
    
    # Make API request to VirusTotal
    try:
        headers = {
            "x-apikey": VIRUS_TOTAL_API_KEY
        }
        
        response = requests.get(
            f"{VIRUS_TOTAL_API_URL}/ip_addresses/{ip_address}",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            reputation_data = _parse_virustotal_response(data)
            reputation_data = _normalize_reputation_fields(reputation_data)
            
            # Cache the result
            # Always write-through cache on successful fetch, even if caller bypassed cache reads.
            ip_reputation_cache.update_one(
                {"ip": ip_address},
                {
                    "$set": {
                        **reputation_data,
                        "ip": ip_address,
                        "cached_at": datetime.utcnow()
                    }
                },
                upsert=True
            )
            
            return reputation_data
        
        elif response.status_code == 404:
            # IP not found in VirusTotal (clean/unknown)
            reputation_data = {
                "detected": False,
                "reputation_score": 0,
                "threat_level": "UNKNOWN",
                "last_analysis_date": None,
                "country": None,
                "asn": None,
                "as_owner": None,
                "categories": [],
                "detection_names": []
            }
            
            # Cache the result
            ip_reputation_cache.update_one(
                {"ip": ip_address},
                {
                    "$set": {
                        **reputation_data,
                        "ip": ip_address,
                        "cached_at": datetime.utcnow()
                    }
                },
                upsert=True
            )
            
            return reputation_data
        
        else:
            # API error - return None or use cache if available
            if use_cache:
                cached_result = ip_reputation_cache.find_one({"ip": ip_address})
                if cached_result:
                    cached_result.pop("_id", None)
                    cached_result.pop("cached_at", None)
                    return _normalize_reputation_fields(cached_result)
            return None
    
    except Exception as e:
        print(f"Error fetching IP reputation from VirusTotal: {str(e)}")
        # Return cached result if available
        if use_cache:
            cached_result = ip_reputation_cache.find_one({"ip": ip_address})
            if cached_result:
                cached_result.pop("_id", None)
                cached_result.pop("cached_at", None)
                return _normalize_reputation_fields(cached_result)
        return None


def _parse_virustotal_response(data: Dict) -> Dict[str, Any]:
    """
    Parse VirusTotal API response into standardized format.
    """
    attributes = data.get("data", {}).get("attributes", {})
    
    # Get reputation stats
    last_analysis_stats = attributes.get("last_analysis_stats", {})
    malicious_count = last_analysis_stats.get("malicious", 0)
    suspicious_count = last_analysis_stats.get("suspicious", 0)
    undetected_count = last_analysis_stats.get("undetected", 0)
    total_engines = malicious_count + suspicious_count + undetected_count
    
    # Calculate reputation score (0-100, higher = more malicious)
    if total_engines > 0:
        reputation_score = int((malicious_count / total_engines) * 100)
    else:
        reputation_score = 0
    
    # Determine threat level
    if malicious_count >= 10:
        threat_level = "CRITICAL"
    elif malicious_count >= 5:
        threat_level = "HIGH"
    elif malicious_count >= 2 or suspicious_count >= 5:
        threat_level = "MEDIUM"
    elif malicious_count >= 1 or suspicious_count >= 1:
        threat_level = "LOW"
    else:
        threat_level = "CLEAN"
    
    # Get categories
    categories = attributes.get("categories", {})
    category_list = list(categories.values()) if categories else []
    
    # Get detection names
    last_analysis_results = attributes.get("last_analysis_results", {})
    detection_names = []
    for engine, result in last_analysis_results.items():
        if result.get("category") == "malicious":
            detection_names.append(result.get("result", "Malicious"))
    
    # Get location data
    # VirusTotal may omit these fields; avoid storing empty strings so clients can display "N/A" consistently.
    country = attributes.get("country") or None
    asn = attributes.get("asn", None)
    as_owner = attributes.get("as_owner") or None
    
    # Last analysis date
    last_analysis_date = attributes.get("last_analysis_date", None)
    if last_analysis_date:
        last_analysis_date = datetime.fromtimestamp(last_analysis_date).isoformat()
    
    return {
        "detected": malicious_count > 0,
        "reputation_score": reputation_score,
        "threat_level": threat_level,
        "malicious_count": malicious_count,
        "suspicious_count": suspicious_count,
        "total_engines": total_engines,
        "last_analysis_date": last_analysis_date,
        "country": country,
        "asn": asn,
        "as_owner": as_owner,
        "categories": list(set(category_list)),  # Remove duplicates
        "detection_names": detection_names[:10],  # Limit to top 10
        "virustotal_url": f"https://www.virustotal.com/gui/ip-address/{data.get('data', {}).get('id', '')}"
    }


def get_multiple_ip_reputations(ip_addresses: list[str], use_cache: bool = True) -> Dict[str, Dict[str, Any]]:
    """
    Get reputation for multiple IP addresses.
    Returns a dictionary mapping IP -> reputation data.
    
    Args:
        ip_addresses: List of IP addresses to check
        use_cache: Whether to use cached results
    
    Returns:
        Dictionary mapping IP addresses to their reputation data
    """
    results = {}
    
    for ip in ip_addresses:
        if ip:  # Skip None or empty IPs
            reputation = get_ip_reputation(ip, use_cache=use_cache)
            if reputation:
                results[ip] = reputation
            else:
                results[ip] = {
                    "detected": False,
                    "reputation_score": 0,
                    "threat_level": "UNKNOWN",
                    "error": "Unable to fetch reputation"
                }
    
    return results


def enhance_severity_with_reputation(severity: str, reputation: Optional[Dict[str, Any]]) -> str:
    """
    Enhance log severity based on VirusTotal reputation.
    
    Args:
        severity: Original severity level
        reputation: VirusTotal reputation data
    
    Returns:
        Enhanced severity level
    """
    if not reputation:
        return severity
    
    threat_level = reputation.get("threat_level", "UNKNOWN")
    detected = reputation.get("detected", False)
    
    if not detected:
        return severity
    
    # Upgrade severity based on threat level
    severity_levels = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
    current_level = severity_levels.get(severity, 1)
    
    if threat_level == "CRITICAL":
        return "CRITICAL"
    elif threat_level == "HIGH" and current_level < 3:
        return "HIGH"
    elif threat_level == "MEDIUM" and current_level < 2:
        return "MEDIUM"
    
    return severity

