"""
IP Blocking API Routes
Endpoints for blocking and unblocking IP addresses
"""
from fastapi import APIRouter, HTTPException, Body, Query, Security
from typing import Optional
from app.services.ip_blocking_service import IPBlockingService
from app.middleware.auth_middleware import verify_api_key
from app.schemas.ip_blocking_schema import (
    BlockIPRequest,
    UnblockIPRequest,
    BlockIPResponse,
    UnblockIPResponse,
    BlockedIPsListResponse,
    BlockedIPResponse,
    IPStatusResponse
)

router = APIRouter(prefix="/api/ip-blocking", tags=["ip-blocking"])


@router.post("/block", response_model=BlockIPResponse)
def block_ip_endpoint(
    request: BlockIPRequest = Body(...),
    api_key: str = Security(verify_api_key)
):
    """
    Block an IP address using UFW firewall.
    
    This endpoint will:
    1. Add a UFW deny rule for the specified IP address
    2. Store the blocked IP in the database
    3. Return the blocking status
    
    Requires API key authentication via X-API-Key header.
    """
    try:
        result = IPBlockingService.block_ip(
            ip_address=request.ip_address,
            reason=request.reason,
            blocked_by="api_user"
        )
        return BlockIPResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error blocking IP: {str(e)}")


@router.post("/unblock", response_model=UnblockIPResponse)
def unblock_ip_endpoint(
    request: UnblockIPRequest = Body(...),
    api_key: str = Security(verify_api_key)
):
    """
    Unblock an IP address by removing the UFW deny rule.
    
    This endpoint will:
    1. Remove the UFW deny rule for the specified IP address
    2. Update the database record to mark the IP as unblocked
    3. Return the unblocking status
    
    Requires API key authentication via X-API-Key header.
    """
    try:
        result = IPBlockingService.unblock_ip(
            ip_address=request.ip_address,
            unblocked_by="api_user"
        )
        return UnblockIPResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error unblocking IP: {str(e)}")


@router.get("/list", response_model=BlockedIPsListResponse)
def get_blocked_ips_endpoint(
    active_only: bool = Query(True, description="Show only actively blocked IPs")
):
    """
    Get list of blocked IP addresses.
    
    Returns a list of all blocked IPs (or only active ones if active_only=True)
    with details such as blocking timestamp, reason, and status.
    """
    try:
        blocked_ips_data = IPBlockingService.get_blocked_ips(active_only=active_only)
        blocked_ips = [BlockedIPResponse(**item) for item in blocked_ips_data]
        return BlockedIPsListResponse(
            blocked_ips=blocked_ips,
            total=len(blocked_ips)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving blocked IPs: {str(e)}")


@router.get("/check/{ip_address}", response_model=IPStatusResponse)
def check_ip_status_endpoint(ip_address: str):
    """
    Check if an IP address is currently blocked.
    
    Returns the blocking status for the specified IP address.
    """
    try:
        is_blocked = IPBlockingService.is_blocked(ip_address)
        return IPStatusResponse(
            ip_address=ip_address,
            is_blocked=is_blocked
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking IP status: {str(e)}")

