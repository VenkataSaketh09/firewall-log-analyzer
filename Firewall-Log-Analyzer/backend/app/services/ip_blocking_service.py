"""
IP Blocking Service
Handles blocking and unblocking IP addresses using UFW firewall
"""
import subprocess
import logging
import os
import shlex
from datetime import datetime, timezone
from typing import Optional, Dict, List
from bson import ObjectId
from app.db.mongo import blacklisted_ips_collection

logger = logging.getLogger(__name__)

# Get sudo password from environment variable (if set)
SUDO_PASSWORD = os.getenv("SUDO_PASSWORD", None)


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
            # UFW always requires root, so we always use sudo
            if not SUDO_PASSWORD:
                error_msg = "Sudo password required but SUDO_PASSWORD environment variable is not set."
                error_msg += "\n\nSOLUTION: Add SUDO_PASSWORD=your_password to your .env file"
                error_msg += "\nor configure passwordless sudo for UFW commands (see SUDO_PASSWORD_SETUP.md)"
                logger.error(error_msg)
                raise Exception(error_msg)
            
            # Run sudo with password from environment
            # Use echo to pipe password to sudo -S (more reliable than input parameter)
            # This prevents hanging on password prompts
            try:
                # Escape special characters in password and IP address for shell safety
                escaped_password = shlex.quote(SUDO_PASSWORD)
                escaped_ip = shlex.quote(ip_address)
                
                # Use echo to pipe password (most reliable method)
                echo_cmd = f"echo {escaped_password} | sudo -S ufw deny from {escaped_ip}"
                result = subprocess.run(
                    echo_cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=15,  # Increased timeout slightly
                    env=os.environ.copy()  # Preserve environment
                )
                
                ufw_output = result.stdout + result.stderr if result.stdout or result.stderr else None
                
                # Check for authentication failure
                if result.returncode != 0:
                    error_lower = (result.stderr + result.stdout).lower()
                    if "password" in error_lower or "authentication failure" in error_lower or "incorrect password" in error_lower or "sorry" in error_lower or "try again" in error_lower:
                        logger.error(f"Invalid sudo password for blocking IP {ip_address}")
                        raise Exception("Invalid sudo password. Please check SUDO_PASSWORD environment variable.")
                    elif "already exists" in error_lower or "existing rule" in error_lower:
                        logger.warning(f"UFW rule for {ip_address} already exists")
                        # Rule exists in UFW, but we still update our database
                    elif "need to be root" in error_lower or "root" in error_lower:
                        logger.error(f"UFW requires root privileges: {result.stderr}")
                        raise Exception(f"UFW command requires root: {result.stderr}")
                    else:
                        logger.error(f"UFW command failed for {ip_address}. stdout: {result.stdout}, stderr: {result.stderr}")
                        raise Exception(f"UFW command failed: {result.stderr or result.stdout}")
                        
            except subprocess.TimeoutExpired:
                logger.error(f"Timeout executing sudo UFW command for {ip_address}")
                raise Exception("Timeout executing UFW command. This usually means:\n1. SUDO_PASSWORD is incorrect\n2. Sudo is waiting for password input\n3. UFW command is hanging")
            except Exception as e:
                if "Timeout" in str(e):
                    raise
                logger.error(f"Error executing UFW command for {ip_address}: {e}")
                raise Exception(f"Error executing UFW command: {str(e)}")
            
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
            # UFW always requires root, so we always use sudo
            cmd = ["sudo", "-S", "ufw", "delete", "deny", "from", ip_address]
            
            if not SUDO_PASSWORD:
                logger.warning(f"Sudo password required but SUDO_PASSWORD not set. Skipping UFW command for {ip_address}")
                logger.warning("Database will still be updated. Set SUDO_PASSWORD environment variable to enable UFW commands.")
                ufw_output = None
            else:
                try:
                    # Escape special characters for shell safety
                    escaped_password = shlex.quote(SUDO_PASSWORD)
                    escaped_ip = shlex.quote(ip_address)
                    
                    # Use echo to pipe password (more reliable)
                    echo_cmd = f"echo {escaped_password} | sudo -S ufw delete deny from {escaped_ip}"
                    result = subprocess.run(
                        echo_cmd,
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=15,  # Increased timeout slightly
                        env=os.environ.copy()
                    )
                    ufw_output = result.stdout + result.stderr if result.stdout or result.stderr else None
                    
                    if result.returncode != 0:
                        error_lower = (result.stderr + result.stdout).lower()
                        if "not found" in error_lower or "no matching rule" in error_lower:
                            logger.warning(f"UFW rule for {ip_address} not found, updating database anyway")
                        elif "password" in error_lower or "authentication failure" in error_lower or "incorrect password" in error_lower or "sorry" in error_lower or "try again" in error_lower:
                            logger.warning(f"Invalid sudo password for unblocking IP {ip_address}")
                        else:
                            logger.warning(f"UFW delete command failed for {ip_address}: {result.stderr}")
                        # Still update database even if UFW command fails
                except subprocess.TimeoutExpired:
                    logger.warning(f"Timeout executing sudo UFW delete command for {ip_address}")
                    # Still update database
                    ufw_output = None
                except Exception as e:
                    logger.warning(f"Error executing UFW delete command for {ip_address}: {e}")
                    ufw_output = None
            
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

