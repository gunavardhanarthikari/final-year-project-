"""
Notification Manager for TrueFace AI
Handles email alerts for face detection matches
"""
import smtplib
import logging
import os
from email.message import EmailMessage
from pathlib import Path

logger = logging.getLogger(__name__)

class NotificationManager:
    def __init__(self, config):
        self.enabled = config.get('ENABLE_ALERTS', False)
        self.smtp_server = config.get('MAIL_SERVER')
        self.smtp_port = config.get('MAIL_PORT', 587)
        self.smtp_user = config.get('MAIL_USERNAME')
        self.smtp_pass = config.get('MAIL_PASSWORD')
        self.recipients = config.get('ALERT_RECIPIENTS', [])
        
        if self.enabled and not (self.smtp_server and self.smtp_user):
            logger.warning("Alerts enabled but SMTP settings are incomplete. Alerts will be logged only.")

    def send_match_alert(self, person_name, confidence, image_path=None, recipients=None):
        """Send an email alert for a face match to one or more recipients"""
        if not self.enabled:
            return False

        subject = f"🚨 Alert: {person_name} Detected"
        body = (
            f"TrueFace AI System Alert\n"
            f"----------------------\n"
            f"Target: {person_name}\n"
            f"Confidence: {confidence:.2f}%\n"
            f"Timestamp: {os.path.basename(image_path) if image_path else 'N/A'}\n"
        )

        logger.info(f"Triggering alert for: {person_name} ({confidence:.2f}%)")

        if not self.smtp_server or not self.smtp_user or not self.recipients:
            logger.info("SMTP not configured. Alert would be sent here.")
            return True

        try:
            msg = EmailMessage()
            msg.set_content(body)
            msg['Subject'] = subject
            msg['From'] = f"TrueFace AI <{self.smtp_user}>"
            
            # Use provided recipients or default list
            target_recipients = recipients if recipients else self.recipients
            msg['To'] = ", ".join(target_recipients)

            # Add HTML version
            html_content = f"""
            <html>
                <body style="font-family: Arial, sans-serif; color: #333;">
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px;">
                        <h2 style="margin: 0;">🚨 Security Alert: Match Found</h2>
                    </div>
                    <div style="padding: 20px; border: 1px solid #ddd; border-top: none; border-radius: 0 0 8px 8px;">
                        <p>A face match has been identified by the <strong>TrueFace AI</strong> system.</p>
                        <table style="width: 100%;">
                            <tr><td><strong>Individual:</strong></td><td>{person_name}</td></tr>
                            <tr><td><strong>Confidence:</strong></td><td>{confidence:.2f}%</td></tr>
                        </table>
                        <p style="font-size: 12px; color: #666; margin-top: 20px;">
                            This is an automated notification from your security dashboard.
                        </p>
                    </div>
                </body>
            </html>
            """
            msg.add_alternative(html_content, subtype='html')

            # Attach image if available
            if image_path and os.path.exists(image_path):
                with open(image_path, 'rb') as f:
                    file_data = f.read()
                    file_name = os.path.basename(image_path)
                    msg.add_attachment(file_data, maintype='image', subtype='jpeg', filename=file_name)

            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                if self.smtp_pass:
                    server.login(self.smtp_user, self.smtp_pass)
                server.send_message(msg)
            
            logger.info(f"Email alert sent to {len(self.recipients)} recipients")
            return True

        except Exception as e:
            logger.error(f"Failed to send email alert: {str(e)}")
            return False
