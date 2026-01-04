"""
Email Notification Service using SendGrid
Handles sending email alerts for detected threats.
"""
import os
from typing import List, Optional
from datetime import datetime
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending email notifications via SendGrid"""
    
    def __init__(self):
        self.enabled = os.getenv("EMAIL_ENABLED", "false").lower() == "true"
        self.api_key = os.getenv("SENDGRID_API_KEY", "")
        self.from_email = os.getenv("EMAIL_FROM_ADDRESS", "alerts@firewall-analyzer.com")
        self.from_name = os.getenv("EMAIL_FROM_NAME", "Firewall Log Analyzer")
        self.recipients = self._parse_recipients(os.getenv("EMAIL_RECIPIENTS", ""))
        
        if self.enabled and not self.api_key:
            logger.warning("EMAIL_ENABLED=true but SENDGRID_API_KEY not set. Email notifications disabled.")
            self.enabled = False
        
        if self.enabled:
            try:
                self.client = SendGridAPIClient(self.api_key)
                logger.info(f"✓ Email service initialized. Recipients: {len(self.recipients)}")
                if self.recipients:
                    logger.info(f"  Recipient emails: {', '.join(self.recipients)}")
            except Exception as e:
                logger.error(f"✗ Failed to initialize SendGrid client: {e}")
                self.enabled = False
        else:
            logger.info("Email service disabled (EMAIL_ENABLED=false)")
    
    def _parse_recipients(self, recipients_str: str) -> List[str]:
        """Parse comma-separated email recipients"""
        if not recipients_str:
            return []
        return [email.strip() for email in recipients_str.split(",") if email.strip()]
    
    def send_alert_email(
        self,
        alert_type: str,
        severity: str,
        source_ip: str,
        description: str,
        ml_risk_score: Optional[float] = None,
        ml_anomaly_score: Optional[float] = None,
        ml_confidence: Optional[float] = None,
        count: Optional[int] = None,
        first_seen: Optional[datetime] = None,
        last_seen: Optional[datetime] = None,
        details: Optional[dict] = None,
    ) -> bool:
        """
        Send email notification for an alert.
        
        Returns True if email sent successfully, False otherwise.
        """
        if not self.enabled:
            logger.debug("Email service disabled. Skipping email send.")
            return False
        
        if not self.recipients:
            logger.warning("No email recipients configured. Skipping email send.")
            return False
        
        try:
            subject = self._generate_subject(alert_type, severity, source_ip)
            html_content = self._generate_html_email(
                alert_type=alert_type,
                severity=severity,
                source_ip=source_ip,
                description=description,
                ml_risk_score=ml_risk_score,
                ml_anomaly_score=ml_anomaly_score,
                ml_confidence=ml_confidence,
                count=count,
                first_seen=first_seen,
                last_seen=last_seen,
                details=details,
            )
            text_content = self._generate_text_email(
                alert_type=alert_type,
                severity=severity,
                source_ip=source_ip,
                description=description,
                ml_risk_score=ml_risk_score,
                ml_anomaly_score=ml_anomaly_score,
                ml_confidence=ml_confidence,
                count=count,
                first_seen=first_seen,
                last_seen=last_seen,
            )
            
            # Send to all recipients
            for recipient in self.recipients:
                try:
                    message = Mail(
                        from_email=Email(self.from_email, self.from_name),
                        to_emails=To(recipient),
                        subject=subject,
                        plain_text_content=text_content,
                        html_content=html_content,
                    )
                    
                    response = self.client.send(message)
                    
                    if response.status_code in [200, 201, 202]:
                        logger.info(f"✓ Alert email sent to {recipient} for {alert_type} from {source_ip} (Status: {response.status_code})")
                    else:
                        # Get error details from response
                        error_body = ""
                        try:
                            error_body = response.body.decode('utf-8') if response.body else "No error body"
                        except:
                            error_body = str(response.body)
                        
                        logger.error(f"✗ Failed to send email to {recipient}. Status: {response.status_code}")
                        logger.error(f"  Error details: {error_body}")
                        logger.error(f"  Headers: {response.headers}")
                        
                        # Provide helpful error messages
                        if response.status_code == 403:
                            logger.error("  → 403 Forbidden: Check if sender email is verified in SendGrid dashboard")
                            logger.error("  → Go to SendGrid → Settings → Sender Authentication → Verify Single Sender")
                        elif response.status_code == 401:
                            logger.error("  → 401 Unauthorized: Check if SendGrid API key is valid and has Mail Send permissions")
                        elif response.status_code == 400:
                            logger.error("  → 400 Bad Request: Check email address format and SendGrid API key permissions")
                        
                        return False
                
                except Exception as e:
                    logger.error(f"✗ Error sending email to {recipient}: {e}")
                    import traceback
                    logger.error(f"  Traceback: {traceback.format_exc()}")
                    return False
            
            return True
        
        except Exception as e:
            logger.error(f"✗ Error in send_alert_email: {e}")
            return False
    
    def _generate_subject(self, alert_type: str, severity: str, source_ip: str) -> str:
        """Generate email subject line"""
        return f"[ALERT] {severity} {alert_type} detected from {source_ip}"
    
    def _generate_html_email(
        self,
        alert_type: str,
        severity: str,
        source_ip: str,
        description: str,
        ml_risk_score: Optional[float],
        ml_anomaly_score: Optional[float],
        ml_confidence: Optional[float],
        count: Optional[int],
        first_seen: Optional[datetime],
        last_seen: Optional[datetime],
        details: Optional[dict],
    ) -> str:
        """Generate HTML email content"""
        severity_color = {
            "CRITICAL": "#DC2626",  # Red
            "HIGH": "#EA580C",      # Orange
            "MEDIUM": "#F59E0B",    # Yellow
            "LOW": "#10B981",       # Green
        }.get(severity.upper(), "#6B7280")
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: {severity_color}; color: white; padding: 20px; border-radius: 5px 5px 0 0; }}
                .content {{ background-color: #f9fafb; padding: 20px; border: 1px solid #e5e7eb; }}
                .alert-box {{ background-color: white; padding: 15px; margin: 15px 0; border-left: 4px solid {severity_color}; }}
                .label {{ font-weight: bold; color: #6B7280; }}
                .value {{ color: #111827; margin-bottom: 10px; }}
                .ml-section {{ background-color: #EFF6FF; padding: 15px; margin: 15px 0; border-radius: 5px; }}
                .footer {{ text-align: center; color: #6B7280; font-size: 12px; margin-top: 20px; }}
                .button {{ display: inline-block; padding: 10px 20px; background-color: #3B82F6; color: white; text-decoration: none; border-radius: 5px; margin-top: 15px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>🚨 Security Alert</h2>
                </div>
                <div class="content">
                    <div class="alert-box">
                        <div class="label">Alert Type:</div>
                        <div class="value"><strong>{alert_type.replace('_', ' ').title()}</strong></div>
                        
                        <div class="label">Severity:</div>
                        <div class="value" style="color: {severity_color};"><strong>{severity}</strong></div>
                        
                        <div class="label">Source IP:</div>
                        <div class="value"><strong>{source_ip}</strong></div>
                        
                        <div class="label">Description:</div>
                        <div class="value">{description}</div>
                        
                        {f'<div class="label">Event Count:</div><div class="value">{count}</div>' if count else ''}
                        
                        {f'<div class="label">First Detected:</div><div class="value">{first_seen.strftime("%Y-%m-%d %H:%M:%S UTC") if first_seen else "N/A"}</div>' if first_seen else ''}
                        
                        {f'<div class="label">Last Detected:</div><div class="value">{last_seen.strftime("%Y-%m-%d %H:%M:%S UTC") if last_seen else "N/A"}</div>' if last_seen else ''}
                    </div>
        """
        
        # Add ML Analysis section if available
        if ml_risk_score is not None or ml_anomaly_score is not None:
            html += """
                    <div class="ml-section">
                        <h3>🤖 ML Analysis</h3>
            """
            if ml_risk_score is not None:
                risk_color = "#DC2626" if ml_risk_score >= 80 else "#EA580C" if ml_risk_score >= 60 else "#F59E0B"
                html += f"""
                        <div class="label">Risk Score:</div>
                        <div class="value" style="color: {risk_color};"><strong>{ml_risk_score:.1f}/100</strong></div>
                """
            if ml_anomaly_score is not None:
                html += f"""
                        <div class="label">Anomaly Score:</div>
                        <div class="value"><strong>{ml_anomaly_score:.3f}</strong></div>
                """
            if ml_confidence is not None:
                html += f"""
                        <div class="label">Confidence:</div>
                        <div class="value"><strong>{ml_confidence:.1%}</strong></div>
                """
            html += """
                    </div>
            """
        
        html += f"""
                    <div style="text-align: center; margin-top: 20px;">
                        <a href="http://localhost:3000/threats" class="button">View Dashboard</a>
                    </div>
                </div>
                <div class="footer">
                    <p>This is an automated alert from Firewall Log Analyzer</p>
                    <p>Generated at {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}</p>
                </div>
            </div>
        </body>
        </html>
        """
        return html
    
    def _generate_text_email(
        self,
        alert_type: str,
        severity: str,
        source_ip: str,
        description: str,
        ml_risk_score: Optional[float],
        ml_anomaly_score: Optional[float],
        ml_confidence: Optional[float],
        count: Optional[int],
        first_seen: Optional[datetime],
        last_seen: Optional[datetime],
    ) -> str:
        """Generate plain text email content"""
        text = f"""
SECURITY ALERT
==============

Alert Type: {alert_type.replace('_', ' ').title()}
Severity: {severity}
Source IP: {source_ip}
Description: {description}
"""
        if count:
            text += f"Event Count: {count}\n"
        if first_seen:
            text += f"First Detected: {first_seen.strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
        if last_seen:
            text += f"Last Detected: {last_seen.strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
        
        if ml_risk_score is not None or ml_anomaly_score is not None:
            text += "\nML Analysis:\n"
            if ml_risk_score is not None:
                text += f"  Risk Score: {ml_risk_score:.1f}/100\n"
            if ml_anomaly_score is not None:
                text += f"  Anomaly Score: {ml_anomaly_score:.3f}\n"
            if ml_confidence is not None:
                text += f"  Confidence: {ml_confidence:.1%}\n"
        
        text += f"\nView Dashboard: http://localhost:3000/threats\n"
        text += f"\nGenerated at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
        
        return text


# Global singleton instance
email_service = EmailService()

