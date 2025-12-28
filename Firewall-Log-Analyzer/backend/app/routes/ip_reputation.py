from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from app.services.virustotal_service import get_ip_reputation, get_multiple_ip_reputations
from app.schemas.log_schema import VirusTotalReputation
from pydantic import BaseModel

router = APIRouter(prefix="/api/ip-reputation", tags=["ip-reputation"])


class IPReputationResponse(BaseModel):
    """Response model for IP reputation lookup"""
    ip: str
    reputation: Optional[VirusTotalReputation] = None


class MultipleIPReputationResponse(BaseModel):
    """Response model for multiple IP reputation lookup"""
    reputations: dict[str, Optional[VirusTotalReputation]]


@router.get("/{ip_address}", response_model=IPReputationResponse)
def get_ip_reputation_endpoint(
    ip_address: str,
    use_cache: bool = Query(True, description="Use cached results if available")
):
    """
    Get VirusTotal reputation for a specific IP address.
    
    Returns detailed threat intelligence including:
    - Reputation score (0-100)
    - Threat level (CRITICAL, HIGH, MEDIUM, LOW, CLEAN, UNKNOWN)
    - Detection counts from security engines
    - Geographic information (country, ASN)
    - Categories and detection names
    - Link to VirusTotal report
    """
    try:
        reputation = get_ip_reputation(ip_address, use_cache=use_cache)
        
        if reputation is None:
            raise HTTPException(
                status_code=503,
                detail="Unable to fetch IP reputation. VirusTotal API may be unavailable."
            )
        
        return IPReputationResponse(
            ip=ip_address,
            reputation=VirusTotalReputation(**reputation) if reputation else None
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching IP reputation: {str(e)}")


@router.post("/batch", response_model=MultipleIPReputationResponse)
def get_multiple_ip_reputation_endpoint(ips: list[str]):
    """
    Get VirusTotal reputation for multiple IP addresses.
    
    Accepts a list of IP addresses and returns reputation data for each.
    Useful for bulk reputation lookups.
    
    Request body:
    ```json
    ["192.168.1.1", "10.0.0.1", "172.16.0.1"]
    ```
    """
    try:
        if not ips or len(ips) == 0:
            raise HTTPException(status_code=400, detail="IP addresses list cannot be empty")
        
        if len(ips) > 100:
            raise HTTPException(status_code=400, detail="Maximum 100 IP addresses allowed per request")
        
        reputation_data = get_multiple_ip_reputations(ips)
        
        # Convert to response format
        reputations = {}
        for ip, rep_data in reputation_data.items():
            if rep_data:
                reputations[ip] = VirusTotalReputation(**rep_data)
            else:
                reputations[ip] = None
        
        return MultipleIPReputationResponse(reputations=reputations)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching IP reputations: {str(e)}")

