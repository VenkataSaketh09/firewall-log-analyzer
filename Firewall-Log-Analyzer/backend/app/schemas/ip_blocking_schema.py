from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, validator

class BlockIPRequest(BaseModel):
    """Request model for blocking an IP address"""
    ip_address: str = Field(..., description="IP address to block (IPv4)")
    reason: Optional[str] = Field(None, description="Reason for blocking")
    
    @validator('ip_address')
    def validate_ip_address(cls, v):
        """Validate IPv4 address format"""
        parts = v.split('.')
        if len(parts) != 4:
            raise ValueError('Invalid IP address format. Must be IPv4 (e.g., 192.168.1.1)')
        for part in parts:
            if not part.isdigit():
                raise ValueError('Invalid IP address format. All parts must be numbers')
            num = int(part)
            if not (0 <= num <= 255):
                raise ValueError('Invalid IP address format. Each part must be between 0 and 255')
        return v


class UnblockIPRequest(BaseModel):
    """Request model for unblocking an IP address"""
    ip_address: str = Field(..., description="IP address to unblock (IPv4)")
    
    @validator('ip_address')
    def validate_ip_address(cls, v):
        """Validate IPv4 address format"""
        parts = v.split('.')
        if len(parts) != 4:
            raise ValueError('Invalid IP address format. Must be IPv4 (e.g., 192.168.1.1)')
        for part in parts:
            if not part.isdigit():
                raise ValueError('Invalid IP address format. All parts must be numbers')
            num = int(part)
            if not (0 <= num <= 255):
                raise ValueError('Invalid IP address format. Each part must be between 0 and 255')
        return v


class BlockedIPResponse(BaseModel):
    """Response model for a blocked IP address"""
    ip_address: str
    blocked_at: datetime
    is_active: bool
    reason: Optional[str] = None
    blocked_by: str
    unblocked_at: Optional[datetime] = None
    unblocked_by: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class BlockIPResponse(BaseModel):
    """Response model for block IP operation"""
    success: bool
    ip_address: str
    message: str
    ufw_output: Optional[str] = None


class UnblockIPResponse(BaseModel):
    """Response model for unblock IP operation"""
    success: bool
    ip_address: str
    message: str
    ufw_output: Optional[str] = None


class BlockedIPsListResponse(BaseModel):
    """Response model for list of blocked IPs"""
    blocked_ips: List[BlockedIPResponse]
    total: int


class IPStatusResponse(BaseModel):
    """Response model for IP status check"""
    ip_address: str
    is_blocked: bool

