"""
Notification Service - Sahool Agricultural Platform
Handles email, SMS, and push notifications
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
from datetime import datetime
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class NotificationType(str, Enum):
    """Notification type enumeration"""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"


class NotificationPriority(str, Enum):
    """Notification priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class EmailService:
    """Email notification service"""
    
    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("FROM_EMAIL", "noreply@sahool.com")
        self.from_name = os.getenv("FROM_NAME", "Sahool Platform")
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ) -> bool:
        """
        Send an email
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Plain text body
            html_body: HTML body (optional)
            cc: CC recipients (optional)
            bcc: BCC recipients (optional)
        
        Returns:
            bool: True if sent successfully
        """
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            if cc:
                msg['Cc'] = ', '.join(cc)
            if bcc:
                msg['Bcc'] = ', '.join(bcc)
            
            # Attach plain text
            msg.attach(MIMEText(body, 'plain'))
            
            # Attach HTML if provided
            if html_body:
                msg.attach(MIMEText(html_body, 'html'))
            
            # Connect and send
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                
                recipients = [to_email]
                if cc:
                    recipients.extend(cc)
                if bcc:
                    recipients.extend(bcc)
                
                server.sendmail(self.from_email, recipients, msg.as_string())
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
    
    def send_verification_email(self, to_email: str, verification_link: str) -> bool:
        """Send email verification"""
        subject = "Verify your Sahool account"
        body = f"""
        Welcome to Sahool!
        
        Please verify your email address by clicking the link below:
        {verification_link}
        
        This link will expire in 24 hours.
        
        If you didn't create an account, please ignore this email.
        
        Best regards,
        Sahool Team
        """
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6;">
            <h2 style="color: #4CAF50;">Welcome to Sahool!</h2>
            <p>Please verify your email address by clicking the button below:</p>
            <p>
                <a href="{verification_link}" 
                   style="background-color: #4CAF50; color: white; padding: 12px 24px; 
                          text-decoration: none; border-radius: 4px; display: inline-block;">
                    Verify Email
                </a>
            </p>
            <p>Or copy and paste this link in your browser:</p>
            <p><a href="{verification_link}">{verification_link}</a></p>
            <p><small>This link will expire in 24 hours.</small></p>
            <hr>
            <p><small>If you didn't create an account, please ignore this email.</small></p>
        </body>
        </html>
        """
        
        return self.send_email(to_email, subject, body, html_body)
    
    def send_password_reset_email(self, to_email: str, reset_link: str) -> bool:
        """Send password reset email"""
        subject = "Reset your Sahool password"
        body = f"""
        Password Reset Request
        
        We received a request to reset your password. Click the link below to reset it:
        {reset_link}
        
        This link will expire in 1 hour.
        
        If you didn't request this, please ignore this email.
        
        Best regards,
        Sahool Team
        """
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6;">
            <h2 style="color: #4CAF50;">Password Reset Request</h2>
            <p>We received a request to reset your password.</p>
            <p>Click the button below to reset it:</p>
            <p>
                <a href="{reset_link}" 
                   style="background-color: #4CAF50; color: white; padding: 12px 24px; 
                          text-decoration: none; border-radius: 4px; display: inline-block;">
                    Reset Password
                </a>
            </p>
            <p>Or copy and paste this link in your browser:</p>
            <p><a href="{reset_link}">{reset_link}</a></p>
            <p><small>This link will expire in 1 hour.</small></p>
            <hr>
            <p><small>If you didn't request this, please ignore this email.</small></p>
        </body>
        </html>
        """
        
        return self.send_email(to_email, subject, body, html_body)
    
    def send_alert_email(
        self,
        to_email: str,
        alert_type: str,
        field_name: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.MEDIUM
    ) -> bool:
        """Send field alert email"""
        priority_colors = {
            NotificationPriority.LOW: "#2196F3",
            NotificationPriority.MEDIUM: "#FF9800",
            NotificationPriority.HIGH: "#F44336",
            NotificationPriority.URGENT: "#D32F2F"
        }
        
        color = priority_colors.get(priority, "#4CAF50")
        
        subject = f"[{priority.value.upper()}] Alert: {alert_type} - {field_name}"
        body = f"""
        Field Alert
        
        Type: {alert_type}
        Field: {field_name}
        Priority: {priority.value}
        
        {message}
        
        Please check your dashboard for more details.
        
        Sahool Platform
        """
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6;">
            <div style="border-left: 4px solid {color}; padding-left: 16px;">
                <h2 style="color: {color};">Field Alert</h2>
                <p><strong>Type:</strong> {alert_type}</p>
                <p><strong>Field:</strong> {field_name}</p>
                <p><strong>Priority:</strong> <span style="color: {color};">{priority.value.upper()}</span></p>
                <hr>
                <p>{message}</p>
            </div>
            <p>
                <a href="https://sahool.com/dashboard/alerts" 
                   style="background-color: #4CAF50; color: white; padding: 12px 24px; 
                          text-decoration: none; border-radius: 4px; display: inline-block;">
                    View Dashboard
                </a>
            </p>
        </body>
        </html>
        """
        
        return self.send_email(to_email, subject, body, html_body)


class SMSService:
    """SMS notification service (placeholder)"""
    
    def __init__(self):
        self.api_key = os.getenv("SMS_API_KEY", "")
        self.api_url = os.getenv("SMS_API_URL", "")
    
    def send_sms(self, phone: str, message: str) -> bool:
        """Send SMS message"""
        try:
            # Implement SMS sending logic here
            # Example: Twilio, AWS SNS, etc.
            logger.info(f"SMS sent to {phone}: {message}")
            return True
        except Exception as e:
            logger.error(f"Failed to send SMS to {phone}: {e}")
            return False


class PushNotificationService:
    """Push notification service (placeholder)"""
    
    def __init__(self):
        self.fcm_key = os.getenv("FCM_SERVER_KEY", "")
    
    def send_push(self, device_token: str, title: str, body: str, data: dict = None) -> bool:
        """Send push notification"""
        try:
            # Implement push notification logic here
            # Example: Firebase Cloud Messaging
            logger.info(f"Push notification sent: {title}")
            return True
        except Exception as e:
            logger.error(f"Failed to send push notification: {e}")
            return False


class NotificationManager:
    """Main notification manager"""
    
    def __init__(self):
        self.email_service = EmailService()
        self.sms_service = SMSService()
        self.push_service = PushNotificationService()
    
    def send_notification(
        self,
        notification_type: NotificationType,
        recipient: str,
        subject: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        **kwargs
    ) -> bool:
        """
        Send notification based on type
        
        Args:
            notification_type: Type of notification
            recipient: Email, phone, or device token
            subject: Notification subject/title
            message: Notification message
            priority: Priority level
            **kwargs: Additional parameters
        
        Returns:
            bool: True if sent successfully
        """
        try:
            if notification_type == NotificationType.EMAIL:
                return self.email_service.send_email(
                    recipient, subject, message,
                    html_body=kwargs.get('html_body')
                )
            elif notification_type == NotificationType.SMS:
                return self.sms_service.send_sms(recipient, message)
            elif notification_type == NotificationType.PUSH:
                return self.push_service.send_push(
                    recipient, subject, message,
                    data=kwargs.get('data')
                )
            else:
                logger.warning(f"Unsupported notification type: {notification_type}")
                return False
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            return False


# Global notification manager instance
notification_manager = NotificationManager()

__all__ = [
    "NotificationType",
    "NotificationPriority",
    "EmailService",
    "SMSService",
    "PushNotificationService",
    "NotificationManager",
    "notification_manager"
]
