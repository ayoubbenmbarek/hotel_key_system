# backend/app/utils/email.py
import logging
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
import smtplib

from app.config import settings

logger = logging.getLogger(__name__)


def render_template(template_name: str, **context) -> str:
    """
    Render a template with the given context
    
    This is a simplified function. In a real application, 
    you'd use a template engine like Jinja2.
    """
    try:
        template_dir = Path(__file__).parent.parent.parent / "templates"
        template_path = template_dir / template_name
        
        if not template_path.exists():
            logger.error(f"Template not found: {template_name}")
            return ""
        
        with open(template_path, "r") as f:
            template_content = f.read()
        
        # Very basic template substitution
        for key, value in context.items():
            placeholder = f"{{{{ {key} }}}}"
            template_content = template_content.replace(placeholder, str(value))
        
        return template_content
    
    except Exception as e:
        logger.error(f"Error rendering template {template_name}: {str(e)}")
        return ""


def send_email(
    email_to: Union[str, List[str]],
    subject: str,
    html_content: str,
    text_content: Optional[str] = None,
    attachments: Optional[List[Dict[str, Any]]] = None,
    cc: Optional[List[str]] = None,
    bcc: Optional[List[str]] = None,
) -> bool:
    """
    Send an email using the configured SMTP server
    """
    try:
        # Create message container
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{settings.EMAILS_FROM_NAME} <{settings.EMAILS_FROM_EMAIL}>"
        
        # Handle single email or list of emails
        if isinstance(email_to, list):
            msg['To'] = ", ".join(email_to)
        else:
            msg['To'] = email_to
        
        # Add CC and BCC if provided
        if cc:
            msg['Cc'] = ", ".join(cc)
        
        if bcc:
            msg['Bcc'] = ", ".join(bcc)
        
        # Set text and HTML content
        if text_content:
            msg.attach(MIMEText(text_content, 'plain'))
        
        if html_content:
            msg.attach(MIMEText(html_content, 'html'))
        
        # Add attachments if provided
        if attachments:
            for attachment in attachments:
                if attachment.get('type') == 'image':
                    image = MIMEImage(attachment['content'])
                    image.add_header('Content-ID', f"<{attachment['content_id']}>")
                    msg.attach(image)
        
        # Connect to SMTP server and send email
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            if settings.SMTP_TLS:
                server.starttls()
            
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            
            # Determine all recipients
            recipients = [email_to] if isinstance(email_to, str) else email_to
            if cc:
                recipients.extend(cc)
            if bcc:
                recipients.extend(bcc)

            server.send_message(msg)

        logger.info(f"Email sent successfully to {msg['To']}")
        return True

    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return False


def send_test_email(email_to: str) -> bool:
    """
    Send a test email to verify the email configuration
    """
    subject = f"Test email from {settings.HOTEL_NAME}"

    html_content = f"""
    <html>
        <body>
            <h1>Test Email</h1>
            <p>This is a test email from the {settings.HOTEL_NAME} Virtual Key System.</p>
            <p>If you received this email, the email configuration is working correctly.</p>
        </body>
    </html>
    """

    text_content = f"""
    Test Email
    
    This is a test email from the {settings.HOTEL_NAME} Virtual Key System.
    If you received this email, the email configuration is working correctly.
    """

    return send_email(
        email_to=email_to,
        subject=subject,
        html_content=html_content,
        text_content=text_content
    )


def send_welcome_email(email_to: str, first_name: str) -> bool:
    """
    Send a welcome email to a new user
    """
    subject = f"Welcome to {settings.HOTEL_NAME}"

    html_content = render_template(
        "welcome_email.html",
        first_name=first_name,
        hotel_name=settings.HOTEL_NAME,
        hotel_logo_url=settings.HOTEL_LOGO_URL,
        hotel_website=settings.FRONTEND_URL,
        current_year=datetime.now().year
    )

    text_content = f"""
    Welcome to {settings.HOTEL_NAME}!
    
    Hello {first_name},
    
    Thank you for registering with {settings.HOTEL_NAME}. We're excited to have you as our guest.
    
    Best regards,
    The {settings.HOTEL_NAME} Team
    """

    return send_email(
        email_to=email_to,
        subject=subject,
        html_content=html_content,
        text_content=text_content
    )
