"""
IP Blocking Service
Handles blocking and unblocking IP addresses using UFW firewall
"""
import subprocess
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, List
from bson import ObjectId
from app.db.mongo import blacklisted_ips_collection

logger = logging.getLogger(__name__)


class IPBlockingService:
    """Service to block and unblock IP addresses using UFW"""
    
    @staticmethod
    def block_ip(ip_address: str, reason: Optional[str] = None, blocked_by: str = "system") -> Dict:
        """
        Block an IP address using UFW
        
        Args:
            ip_address: IP address to block
            reason: Optional reason for blocking
            blocked_by: Who/what blocked the IP (default: "system")
        
        Returns:
            Dict with blocking status and details
        """
        try:
            # Check if already blocked
            existing = blacklisted_ips_collection.find_one({"ip_address": ip_address})
            
            # Execute UFW command to block IP
            # UFW command: sudo ufw deny from <IP>
            cmd = ["sudo", "ufw", "deny", "from", ip_address]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            ufw_output = result.stdout + result.stderr if result.stdout or result.stderr else None
            
            if result.returncode != 0:
                # Check if rule already exists
                error_lower = (result.stderr + result.stdout).lower()
                if "already exists" in error_lower or "existing rule" in error_lower:
                    logger.warning(f"UFW rule for {ip_address} already exists")
                    # Rule exists in UFW, but we still update our database
                else:
                    logger.error(f"UFW command failed for {ip_address}: {result.stderr}")
                    raise Exception(f"UFW command failed: {result.stderr}")
            
            # Store/Update in database
            block_record = {
                "ip_address": ip_address,
                "blocked_at": datetime.now(timezone.utc),
                "is_active": True,
                "reason": reason,
                "blocked_by": blocked_by,
                "unblocked_at": None,
                "unblocked_by": None
            }
            
            if existing:
                # Update existing record
                blacklisted_ips_collection.update_one(
                    {"ip_address": ip_address},
                    {"$set": {
                        "blocked_at": datetime.now(timezone.utc),
                        "is_active": True,
                        "reason": reason,
                        "blocked_by": blocked_by,
                        "unblocked_at": None,
                        "unblocked_by": None
                    }}
                )
            else:
                # Insert new record
                blacklisted_ips_collection.insert_one(block_record)
            
            logger.info(f"Successfully blocked IP: {ip_address}")
            return {
                "success": True,
                "ip_address": ip_address,
                "message": f"IP {ip_address} blocked successfully",
                "ufw_output": ufw_output
            }
            
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout blocking IP: {ip_address}")
            raise Exception("Timeout executing UFW command")
        except Exception as e:
            logger.error(f"Error blocking IP {ip_address}: {e}")
            raise
    
    @staticmethod
    def unblock_ip(ip_address: str, unblocked_by: str = "system") -> Dict:
        """
        Unblock an IP address by removing UFW rule
        
        Args:
            ip_address: IP address to unblock
            unblocked_by: Who/what unblocked the IP
        
        Returns:
            Dict with unblocking status
        """
        try:
            # Execute UFW command to remove block rule
            # UFW command: sudo ufw delete deny from <IP>
            cmd = ["sudo", "ufw", "delete", "deny", "from", ip_address]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            ufw_output = result.stdout + result.stderr if result.stdout or result.stderr else None
            
            if result.returncode != 0:
                # Check if rule doesn't exist
                error_lower = (result.stderr + result.stdout).lower()
                if "not found" in error_lower or "no matching rule" in error_lower:
                    logger.warning(f"UFW rule for {ip_address} not found, updating database anyway")
                    # Rule doesn't exist in UFW, but we update our database
                else:
                    logger.error(f"UFW delete command failed for {ip_address}: {result.stderr}")
                    # Still update database even if UFW command fails
                    # (in case rule was manually removed)
            
            # Update database record
            blacklisted_ips_collection.update_one(
                {"ip_address": ip_address},
                {"$set": {
                    "is_active": False,
                    "unblocked_at": datetime.now(timezone.utc),
                    "unblocked_by": unblocked_by
                }}
            )
            
            logger.info(f"Successfully unblocked IP: {ip_address}")
            return {
                "success": True,
                "ip_address": ip_address,
                "message": f"IP {ip_address} unblocked successfully",
                "ufw_output": ufw_output
            }
            
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout unblocking IP: {ip_address}")
            raise Exception("Timeout executing UFW command")
        except Exception as e:
            logger.error(f"Error unblocking IP {ip_address}: {e}")
            raise
    
    @staticmethod
    def get_blocked_ips(active_only: bool = True) -> List[Dict]:
        """
        Get list of blocked IPs from database
        
        Args:
            active_only: If True, return only actively blocked IPs
        
        Returns:
            List of blocked IP records
        """
        query = {"is_active": True} if active_only else {}
        blocked = list(blacklisted_ips_collection.find(query).sort("blocked_at", -1))
        
        # Convert ObjectId to string for JSON serialization
        for item in blocked:
            if "_id" in item and isinstance(item["_id"], ObjectId):
                item["_id"] = str(item["_id"])
        
        return blocked
    
    @staticmethod
    def is_blocked(ip_address: str) -> bool:
        """
        Check if an IP is currently blocked
        
        Args:
            ip_address: IP address to check
        
        Returns:
            True if IP is blocked, False otherwise
        """
        record = blacklisted_ips_collection.find_one({
            "ip_address": ip_address,
            "is_active": True
        })
        return record is not None

