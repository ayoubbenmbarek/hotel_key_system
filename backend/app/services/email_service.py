# backend/app/services/email_service.py
import logging
import smtplib
import re
import dns.resolver
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
from app.utils.date_formatting import format_datetime
from app.db.session import get_db_context
from app.services.hotel_service import get_hotel_name
from app.models.digital_key import DigitalKey
from app.models.reservation import Reservation
from app.models.room import Room

# Configure logging
logger = logging.getLogger(__name__)

# Set up Jinja2 environment for email templates
templates_dir = Path(__file__).parent.parent.parent / "templates"
env = Environment(loader=FileSystemLoader(templates_dir))


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


def validate_email(email):
    """Basic email validation including domain check"""
    # Check format
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    if not re.match(email_regex, email):
        return False, "Invalid email format"
    
    # Check if domain exists and has MX records
    domain = email.split('@')[1]
    try:
        mx_records = dns.resolver.resolve(domain, 'MX')
        if not mx_records:
            return False, "Domain doesn't have mail exchange servers"
        return True, "Valid email"
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.NoNameservers):
        return False, "Domain doesn't exist or can't receive emails"
    except Exception as e:
        return False, f"Error checking domain: {str(e)}"


def send_key_email(recipient_email, guest_name, pass_url, key_id, pass_data, max_retries=3):
    """Send email with digital key information to guest"""
     # First validate the email
    is_valid, validation_message = validate_email(recipient_email)
    if not is_valid:
        logger.error(f"Invalid email address: {recipient_email}. {validation_message}")
        return False, validation_message
    try:
        # Get hotel name from database
        with get_db_context() as db:
            # Get the digital key
            key = db.query(DigitalKey).filter(DigitalKey.id == key_id).first()
            if not key:
                logger.error(f"Key not found: {key_id}")
                return False
                
            # Get the reservation
            reservation = db.query(Reservation).filter(Reservation.id == key.reservation_id).first()
            if not reservation:
                logger.error(f"Reservation not found for key: {key_id}")
                return False
                
            # Get the room
            room = db.query(Room).filter(Room.id == reservation.room_id).first()
            if not room:
                logger.error(f"Room not found for reservation: {reservation.id}")
                return False
                
            # Now that we have the hotel_id, use your existing function
            hotel_id = room.hotel_id
            hotel_name = get_hotel_name(db, hotel_id)
            
            # Fallback if no hotel name is found
            if not hotel_name:
                hotel_name = settings.HOTEL_NAME
        
        # Create message
        msg = MIMEMultipart('related')
        msg['Subject'] = f"Your Digital Room Key - {hotel_name}"
        msg['From'] = f"{settings.EMAILS_FROM_NAME} <{settings.EMAILS_FROM_EMAIL}>"
        msg['To'] = recipient_email
        
        # Generate QR code for pass URL
        qr_code_bytes = generate_qr_code(pass_url)
        
        # Load email template
        template = env.get_template('email_key.html')
        
        # Render HTML content with template
        html_content = template.render(
            hotel_name=hotel_name,
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
            Welcome to {hotel_name}!

            Hello {guest_name},

            Your digital room key is ready. Here are your reservation details:

            Room: {pass_data["room_number"]}
            Check-in: {format_datetime(pass_data["check_in"])}
            Check-out: {format_datetime(pass_data["check_out"])}

            To add your key to your wallet, visit: {pass_url}

            We hope you enjoy your stay!

            Best regards,
            The {hotel_name} Team
                    """
        
        # Attach text and HTML versions
        msg_alternative.attach(MIMEText(text_content, 'plain'))
        msg_alternative.attach(MIMEText(html_content, 'html'))
        
        # Attach QR code image
        qr_image = MIMEImage(qr_code_bytes)
        qr_image.add_header('Content-ID', '<qr_code>')
        msg.attach(qr_image)
        
        # Connect to SMTP server and send email
        # with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        #     server.send_message(msg)
        # In production we will use this
        for attempt in range(max_retries):
            try:
                with smtplib.SMTP("smtp.gmail.com", 587) as server:
                    server.starttls()
                    server.login("ayoubenmbarek@gmail.com", "uojt dktu yfrw vrdn")
                    server.send_message(msg)
                # with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                # # Use port 465 with SMTP_SSL (no starttls() needed)
                #     if settings.SMTP_TLS:
                #         server.starttls()
                #     if settings.SMTP_USER and settings.SMTP_PASSWORD:
                #         server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                #     server.send_message(msg)
                
                logger.info(f"Digital key email sent successfully to {recipient_email}")
                return True, "Email sent successfully"
            except Exception as e:
                logger.warning(f"Email sending attempt {attempt+1} failed: {str(e)}")
                time.sleep(2 ** attempt)  # Exponential backoff
    # Use a more robust email sending service:
    # Consider using a third-party email service like SendGrid, Mailgun, or Amazon SES that has built-in 
    # retries and better reliability than direct SMTP connections
    except Exception as e:
        logger.error(f"Failed to send digital key email: {str(e)}")
        return False


def send_key_download_link(recipient_email, guest_name, key_id):
    """Send email with a download link for the digital key"""
    try:
        # Get hotel name from database using key_id
        with get_db_context() as db:
            # Get the digital key
            key = db.query(DigitalKey).filter(DigitalKey.id == key_id).first()
            if not key:
                logger.error(f"Key not found: {key_id}")
                return False
                
            # Get the reservation
            reservation = db.query(Reservation).filter(Reservation.id == key.reservation_id).first()
            if not reservation:
                logger.error(f"Reservation not found for key: {key_id}")
                return False
                
            # Get the room
            room = db.query(Room).filter(Room.id == reservation.room_id).first()
            if not room:
                logger.error(f"Room not found for reservation: {reservation.id}")
                return False
                
            # Now that we have the hotel_id, use your existing function
            hotel_id = room.hotel_id
            hotel_name = get_hotel_name(db, hotel_id)
            
            # Fallback if no hotel name is found
            if not hotel_name:
                hotel_name = settings.HOTEL_NAME
        # Create message
        msg = MIMEMultipart()
        msg['Subject'] = f"Your Digital Room Key Download Link - {hotel_name}"
        msg['From'] = f"{settings.EMAILS_FROM_NAME} <{settings.EMAILS_FROM_EMAIL}>"
        msg['To'] = recipient_email
        
        # Generate download link
        download_url = f"{settings.FRONTEND_URL}/download-key/{key_id}"
        
        # Load email template
        template = env.get_template('email_download.html')
        
        # Render HTML content with template
        html_content = template.render(
            hotel_name=hotel_name,
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
            The {hotel_name} Team
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
