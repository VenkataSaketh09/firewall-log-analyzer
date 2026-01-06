#!/usr/bin/env python3
"""
Test Script for Email Notifications and Auto-Blocking
Tests both alert notifications and auto-blocking email notifications
"""
import requests
import json
import time
import sys
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
API_KEY = "your-api-key-here"  # Update with your API key if needed

def print_header(text):
    """Print a formatted header"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)

def print_success(text):
    """Print success message"""
    print(f"✓ {text}")

def print_error(text):
    """Print error message"""
    print(f"✗ {text}")

def print_info(text):
    """Print info message"""
    print(f"ℹ {text}")

def test_email_service():
    """Test 1: Basic email service"""
    print_header("TEST 1: Basic Email Service Test")
    
    try:
        response = requests.post(f"{BASE_URL}/test/email")
        data = response.json()
        
        if data.get("success"):
            print_success("Email sent successfully!")
            print_info(f"Recipients: {', '.join(data.get('recipients', []))}")
            return True
        else:
            print_error(f"Failed to send email: {data.get('message', 'Unknown error')}")
            if "error" in data:
                print_error(f"Error details: {data['error']}")
            return False
    except Exception as e:
        print_error(f"Error testing email service: {e}")
        return False

def test_alert_notification():
    """Test 2: Alert notification (threat detection)"""
    print_header("TEST 2: Alert Notification (Threat Detection)")
    
    try:
        response = requests.post(f"{BASE_URL}/test/alert-notification")
        data = response.json()
        
        if data.get("success"):
            print_success("Alert notification processed successfully!")
            result = data.get("result", {})
            print_info(f"Email sent: {result.get('sent', False)}")
            print_info(f"ML scored: {result.get('ml_scored', False)}")
            if result.get("ml_risk_score"):
                print_info(f"ML Risk Score: {result['ml_risk_score']:.1f}")
            if result.get("reason"):
                print_info(f"Reason: {result['reason']}")
            return True
        else:
            print_error(f"Alert notification failed: {data.get('message', 'Unknown error')}")
            if "error" in data:
                print_error(f"Error details: {data['error']}")
            return False
    except Exception as e:
        print_error(f"Error testing alert notification: {e}")
        return False

def test_auto_block_with_notification():
    """Test 3: Auto-blocking with email notification"""
    print_header("TEST 3: Auto-Blocking with Email Notification")
    
    try:
        response = requests.post(f"{BASE_URL}/test/auto-block")
        data = response.json()
        
        if data.get("success"):
            print_success("Auto-blocking test completed!")
            print_info(f"Test IP: {data.get('ip_address')}")
            print_info(f"Blocked: {data.get('is_blocked_verified', False)}")
            print_info(f"Email sent: {data.get('email_sent', False)}")
            
            block_result = data.get("block_result", {})
            print_info(f"Blocking message: {block_result.get('message', 'N/A')}")
            
            if data.get("ip_address"):
                print_info(f"\n⚠️  Note: IP {data['ip_address']} is now blocked for testing.")
                print_info(f"   To unblock, run: python test_email_notifications.py --unblock {data['ip_address']}")
            
            return data.get("ip_address")
        else:
            print_error(f"Auto-blocking test failed: {data.get('message', 'Unknown error')}")
            if "error" in data:
                print_error(f"Error details: {data['error']}")
            return None
    except Exception as e:
        print_error(f"Error testing auto-blocking: {e}")
        return None

def verify_blocked_ip_in_interface(ip_address):
    """Test 4: Verify blocked IP appears in interface"""
    print_header("TEST 4: Verify Blocked IP in Interface")
    
    try:
        # Check if IP is blocked via API
        response = requests.get(f"{BASE_URL}/api/ip-blocking/check/{ip_address}")
        data = response.json()
        
        if data.get("is_blocked"):
            print_success(f"IP {ip_address} is confirmed as blocked in database")
            
            # Get list of blocked IPs
            response = requests.get(f"{BASE_URL}/api/ip-blocking/list?active_only=true")
            list_data = response.json()
            
            blocked_ips = [ip["ip_address"] for ip in list_data.get("blocked_ips", [])]
            if ip_address in blocked_ips:
                print_success(f"IP {ip_address} appears in blocked IPs list")
                print_info(f"Total blocked IPs: {list_data.get('total', 0)}")
                return True
            else:
                print_error(f"IP {ip_address} not found in blocked IPs list")
                return False
        else:
            print_error(f"IP {ip_address} is not marked as blocked")
            return False
    except Exception as e:
        print_error(f"Error verifying blocked IP: {e}")
        return False

def unblock_test_ip(ip_address):
    """Unblock a test IP address"""
    print_header(f"Unblocking Test IP: {ip_address}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/test/auto-block-cleanup/{ip_address}"
        )
        data = response.json()
        
        if data.get("success"):
            print_success(f"IP {ip_address} unblocked successfully")
            return True
        else:
            print_error(f"Failed to unblock IP: {data.get('message', 'Unknown error')}")
            return False
    except Exception as e:
        print_error(f"Error unblocking IP: {e}")
        return False

def check_health():
    """Check system health before testing"""
    print_header("System Health Check")
    
    try:
        # Check notification health
        response = requests.get(f"{BASE_URL}/health/notifications")
        health = response.json()
        
        email_service = health.get("email_service", {})
        if email_service.get("enabled"):
            print_success("Email service is enabled")
            print_info(f"Recipients: {email_service.get('recipients_count', 0)}")
            if email_service.get("recipients"):
                print_info(f"  → {', '.join(email_service['recipients'])}")
        else:
            print_error("Email service is DISABLED")
            print_info("Set EMAIL_ENABLED=true in .env file")
            return False
        
        # Check auto-blocking health
        response = requests.get(f"{BASE_URL}/health/auto-blocking")
        auto_block_health = response.json()
        
        auto_blocking = auto_block_health.get("auto_blocking_service", {})
        if auto_blocking.get("enabled"):
            print_success("Auto-blocking service is enabled")
        else:
            print_error("Auto-blocking service is DISABLED")
            print_info("Set AUTO_IP_BLOCKING_ENABLED=true in .env file")
        
        return True
    except Exception as e:
        print_error(f"Error checking health: {e}")
        print_info("Make sure the backend server is running on http://localhost:8000")
        return False

def main():
    """Main test function"""
    print("\n" + "="*70)
    print("  EMAIL NOTIFICATION & AUTO-BLOCKING TEST SUITE")
    print("="*70)
    
    # Check for unblock command
    if len(sys.argv) > 1 and sys.argv[1] == "--unblock":
        if len(sys.argv) < 3:
            print_error("Please provide an IP address to unblock")
            print_info("Usage: python test_email_notifications.py --unblock <ip_address>")
            return
        ip_to_unblock = sys.argv[2]
        unblock_test_ip(ip_to_unblock)
        return
    
    # Health check
    if not check_health():
        print_error("\nSystem health check failed. Please fix issues before testing.")
        return
    
    # Run tests
    results = {}
    
    # Test 1: Basic email
    results["email"] = test_email_service()
    time.sleep(2)  # Wait between tests
    
    # Test 2: Alert notification
    results["alert"] = test_alert_notification()
    time.sleep(2)
    
    # Test 3: Auto-blocking
    blocked_ip = test_auto_block_with_notification()
    results["auto_block"] = blocked_ip is not None
    time.sleep(2)
    
    # Test 4: Verify in interface
    if blocked_ip:
        results["interface"] = verify_blocked_ip_in_interface(blocked_ip)
    
    # Summary
    print_header("TEST SUMMARY")
    print(f"Basic Email Test:        {'✓ PASS' if results.get('email') else '✗ FAIL'}")
    print(f"Alert Notification:      {'✓ PASS' if results.get('alert') else '✗ FAIL'}")
    print(f"Auto-Blocking:           {'✓ PASS' if results.get('auto_block') else '✗ FAIL'}")
    print(f"Interface Verification:   {'✓ PASS' if results.get('interface') else '✗ FAIL'}")
    
    if blocked_ip:
        print(f"\n⚠️  Test IP {blocked_ip} is still blocked.")
        print(f"   To unblock: python test_email_notifications.py --unblock {blocked_ip}")
    
    all_passed = all(results.values())
    if all_passed:
        print_success("\nAll tests passed! ✓")
    else:
        print_error("\nSome tests failed. Please check the output above.")

if __name__ == "__main__":
    main()

