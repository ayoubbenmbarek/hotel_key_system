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
        # ERROR - Failed to send email: [Errno 111] Connection refused
        # with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        #     if settings.SMTP_TLS:
        #         server.starttls()
            
        #     if settings.SMTP_USER and settings.SMTP_PASSWORD:
        #         server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login("ayoubenmbarek@gmail.com", "uojt dktu yfrw vrdn")
            # server.send_message(msg)
            
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


def send_password_reset_email(email_to: str, first_name: str, reset_token: str) -> bool:
    """
    Send a password reset email with a link containing the reset token.
    
    Args:
        email_to: The recipient's email address
        first_name: The recipient's first name
        reset_token: The password reset token
        
    Returns:
        bool: Whether the email was sent successfully
    """
    # Build the reset link
    reset_link = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
    
    subject = f"Reset Your Password - {settings.HOTEL_NAME}"
    
    # Set a default logo URL if none is configured
    hotel_logo_url = settings.HOTEL_LOGO_URL or ""
    
    # Try to use a template if available
    html_content = render_template(
        "password_reset_email.html",
        first_name=first_name,
        reset_link=reset_link,
        hotel_name=settings.HOTEL_NAME,
        hotel_logo_url=hotel_logo_url,
        expiry_hours=24,
        current_year=datetime.now().year
    )
    
    # If template rendering failed, use this fallback HTML
    if not html_content:
        html_content = f"""
        <html>
            <body>
                <h1>Hello, {first_name}!</h1>
                <p>We received a request to reset your password for the {settings.HOTEL_NAME} Virtual Key System.</p>
                <p>To reset your password, please click on the link below:</p>
                <p><a href="{reset_link}">Reset Password</a></p>
                <p>This link will expire in 24 hours.</p>
                <p>If you did not request a password reset, please ignore this email or contact support if you have concerns.</p>
                <p>Best regards,<br>The {settings.HOTEL_NAME} Team</p>
            </body>
        </html>
        """

    text_content = f"""
    Password Reset - {settings.HOTEL_NAME}

    Hello {first_name},

    We received a request to reset your password for the {settings.HOTEL_NAME} Virtual Key System.

    To reset your password, please visit this link:
    {reset_link}

    This link will expire in 24 hours.

    If you did not request a password reset, please ignore this email or contact support if you have concerns.

    Best regards,
    The {settings.HOTEL_NAME} Team
    """

    return send_email(
        email_to=email_to,
        subject=subject,
        html_content=html_content,
        text_content=text_content
    )
