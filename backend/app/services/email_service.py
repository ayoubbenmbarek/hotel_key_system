# backend/app/services/email_service.py
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from datetime import datetime
import os
import time
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
import qrcode
from io import BytesIO
import base64

from app.config import settings

# Configure logging
logger = logging.getLogger(__name__)

# Set up Jinja2 environment for email templates
templates_dir = Path(__file__).parent.parent.parent / "templates"
env = Environment(loader=FileSystemLoader(templates_dir))


def format_datetime(dt_str):
    """Format ISO datetime string to human-readable format"""
    dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
    return dt.strftime("%A, %B %d, %Y at %I:%M %p")


def generate_qr_code(url):
    """Generate QR code for the wallet pass URL"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert PIL image to bytes for email embedding
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return buffered.getvalue()


def send_key_email(recipient_email, guest_name, pass_url, key_id, pass_data, max_retries=3):
    """Send email with digital key information to guest"""
    try:
        # Create message
        msg = MIMEMultipart('related')
        msg['Subject'] = f"Your Digital Room Key - {settings.HOTEL_NAME}"
        msg['From'] = f"{settings.EMAILS_FROM_NAME} <{settings.EMAILS_FROM_EMAIL}>"
        msg['To'] = recipient_email
        
        # Generate QR code for pass URL
        qr_code_bytes = generate_qr_code(pass_url)
        
        # Load email template
        template = env.get_template('email_key.html')
        
        # Render HTML content with template
        html_content = template.render(
            hotel_name=settings.HOTEL_NAME,
            hotel_logo_url=settings.HOTEL_LOGO_URL,
            hotel_website=settings.FRONTEND_URL,
            guest_name=guest_name,
            room_number=pass_data["room_number"],
            check_in=format_datetime(pass_data["check_in"]),
            check_out=format_datetime(pass_data["check_out"]),
            pass_url=pass_url,
            current_year=datetime.now().year
        )
        
        # Create alternative part for email (plain text and HTML)
        msg_alternative = MIMEMultipart('alternative')
        msg.attach(msg_alternative)
        
        # Create plain text version
        text_content = f"""
            Welcome to {settings.HOTEL_NAME}!

            Hello {guest_name},

            Your digital room key is ready. Here are your reservation details:

            Room: {pass_data["room_number"]}
            Check-in: {format_datetime(pass_data["check_in"])}
            Check-out: {format_datetime(pass_data["check_out"])}

            To add your key to your wallet, visit: {pass_url}

            We hope you enjoy your stay!

            Best regards,
            The {settings.HOTEL_NAME} Team
                    """
        
        # Attach text and HTML versions
        msg_alternative.attach(MIMEText(text_content, 'plain'))
        msg_alternative.attach(MIMEText(html_content, 'html'))
        
        # Attach QR code image
        qr_image = MIMEImage(qr_code_bytes)
        qr_image.add_header('Content-ID', '<qr_code>')
        msg.attach(qr_image)
        
        # Connect to SMTP server and send email
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.send_message(msg)
        # In production we will use this
        # for attempt in range(max_retries):
        #     try:
        #         with smtplib.SMTP("smtp.gmail.com", 587) as server:
        #             server.starttls()
        #             server.login("ayoubenmbarek@gmail.com", "uojt dktu yfrw vrdn")
        #             server.send_message(msg)
        #         # with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        #         # # Use port 465 with SMTP_SSL (no starttls() needed)
        #         #     if settings.SMTP_TLS:
        #         #         server.starttls()
        #         #     if settings.SMTP_USER and settings.SMTP_PASSWORD:
        #         #         server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        #         #     server.send_message(msg)
                
        #         logger.info(f"Digital key email sent successfully to {recipient_email}")
        #         return True
        #     except Exception as e:
        #         logger.warning(f"Email sending attempt {attempt+1} failed: {str(e)}")
        #         time.sleep(2 ** attempt)  # Exponential backoff
    # Use a more robust email sending service:
    # Consider using a third-party email service like SendGrid, Mailgun, or Amazon SES that has built-in 
    # retries and better reliability than direct SMTP connections
    except Exception as e:
        logger.error(f"Failed to send digital key email: {str(e)}")
        return False


def send_key_download_link(recipient_email, guest_name, key_id):
    """Send email with a download link for the digital key"""
    try:
        # Create message
        msg = MIMEMultipart()
        msg['Subject'] = f"Your Digital Room Key Download Link - {settings.HOTEL_NAME}"
        msg['From'] = f"{settings.EMAILS_FROM_NAME} <{settings.EMAILS_FROM_EMAIL}>"
        msg['To'] = recipient_email
        
        # Generate download link
        download_url = f"{settings.FRONTEND_URL}/download-key/{key_id}"
        
        # Load email template
        template = env.get_template('email_download.html')
        
        # Render HTML content with template
        html_content = template.render(
            hotel_name=settings.HOTEL_NAME,
            hotel_logo_url=settings.HOTEL_LOGO_URL,
            hotel_website=settings.FRONTEND_URL,
            guest_name=guest_name,
            download_url=download_url,
            current_year=datetime.now().year
        )
        
        # Create plain text version
        text_content = f"""
            Hello {guest_name},

            You can download your digital room key by visiting this link:
            {download_url}

            Best regards,
            The {settings.HOTEL_NAME} Team
                    """
        
        # Attach text and HTML versions
        msg.attach(MIMEText(text_content, 'plain'))
        msg.attach(MIMEText(html_content, 'html'))
        
        # Connect to SMTP server and send email
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            if settings.SMTP_TLS:
                server.starttls()
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
        
        logger.info(f"Digital key download link sent successfully to {recipient_email}")
        return True
    
    except Exception as e:
        logger.error(f"Failed to send digital key download link: {str(e)}")
        return False
