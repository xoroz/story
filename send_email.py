#!/usr/bin/env python3
import json
import os
import logging
import re
from pathlib import Path
from dotenv import load_dotenv
from mailersend import emails

# Ensure logs directory exists
os.makedirs('logs', exist_ok=True)

# Setup 
logging.basicConfig(
    #level=logging.INFO, 
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    filename='logs/email_notification.log',
    filemode='a'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configuration
PROCESSED_FOLDER = 'processed'
ERROR_FOLDER = 'error'

# MailerSend settings
MAILERSEND_TOKEN = os.getenv('MAILERSENDTOKEN')
TEMPLATE_ID = os.getenv('MAILERSEND_TEMPLATE_ID', '0r83ql3menxgzw1j')
SENDER_NAME = os.getenv('SENDER_NAME', 'Story Submission System')
SENDER_EMAIL = os.getenv('SENDER_EMAIL', 'info@yourdomain.com')
EMAIL_SUBJECT = os.getenv('EMAIL_SUBJECT', 'Your Story Submission: {{title}}')

# Check if MailerSend token is available
if not MAILERSEND_TOKEN:
    logger.error("Missing MailerSend API token in .env file. Please set MAILERSENDTOKEN")
    exit(1)

def ensure_folders_exist():
    """Create necessary folders if they don't exist"""
    for folder in [PROCESSED_FOLDER, ERROR_FOLDER, 'logs']:
        if not os.path.exists(folder):
            os.makedirs(folder)
            logger.info(f"Created folder: {folder}")

def send_email_with_mailersend(email, name, title, story_about, link):
    """Send email using MailerSend API"""
    try:
        # Initialize the MailerSend instance
        mailer = emails.NewEmail(MAILERSEND_TOKEN)

        # Define an empty dict to populate with mail values
        mail_body = {}

        # Set sender information
        mail_from = {
            "name": SENDER_NAME,
            "email": SENDER_EMAIL,
        }

        # Set recipient information
        recipients = [
            {
                "name": name,
                "email": email,
            }
        ]

        # Set personalization data (the variables in your template)
        personalization = [
            {
                "email": email,
                "data": {
                    "link": link,
                    "title": title,
                    "story_about": story_about
                }
            }
        ]

        # Build the email
        mailer.set_mail_from(mail_from, mail_body)
        mailer.set_mail_to(recipients, mail_body)
        
        # Set subject with personalization if needed
        subject = EMAIL_SUBJECT.replace('{{title}}', title)
        mailer.set_subject(subject, mail_body)
        
        # Set template ID
        mailer.set_template(TEMPLATE_ID, mail_body)
        
        # Apply personalization
        mailer.set_personalization(personalization, mail_body)

        # Debug log the mail_body for troubleshooting
        debug_body = mail_body.copy()
        if 'personalizations' in debug_body:
            debug_body['personalizations'] = "[REDACTED FOR LOG]"
        logger.debug(f"Mail body: {debug_body}")

        # Send the email and capture the response
        response = mailer.send(mail_body)
        
        # Log the response for debugging
        logger.debug(f"MailerSend raw response: {response}")
        
        # The SDK might return different response types, so let's handle them appropriately
        if isinstance(response, str):
            # If it's a string, let's try to see if it's a JSON response string
            logger.info(f"Email response: {response}")
            if "success" in response.lower() or "202" in response or "200" in response:
                logger.info(f"Email successfully sent to {email}")
                return True
            else:
                logger.error(f"Failed to send email: {response}")
                return False
        elif hasattr(response, 'status_code'):
            # If it's a response object with status_code
            if response.status_code in (200, 202):
                logger.info(f"Email successfully sent to {email}")
                return True
            else:
                logger.error(f"Failed to send email: HTTP {response.status_code}")
                if hasattr(response, 'text'):
                    logger.error(f"Response: {response.text}")
                return False
        else:
            # If we can't determine success/failure, assume success and log the response
            logger.warning(f"Unknown response type from MailerSend: {type(response)}")
            logger.info(f"Assuming success. Response: {response}")
            return True
            
    except Exception as e:
        logger.error(f"Error sending email via MailerSend: {str(e)}")
        return False

def send_story_notification(email, name, title, story_about, link):
    """Send a story notification email"""
    if not email or not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        logger.error(f"Invalid email address: {email}")
        return False
        
    logger.info(f"Sending email to {email} with title '{title}'")
    
    try:
        # Send the email
        success = send_email_with_mailersend(email, name, title, story_about, link)
        
        if success:
            logger.info(f"Successfully sent email to {email}")
            return True
        else:
            logger.error(f"Failed to send email to {email}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        return False

def main():
    """Main function for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Send a story notification email')
    parser.add_argument('--email', required=True, help='Recipient email address')
    parser.add_argument('--name', default='Valued Contributor', help='Recipient name')
    parser.add_argument('--title', required=True, help='Story title')
    parser.add_argument('--story_about', default='', help='Brief description of the story')
    parser.add_argument('--link', required=True, help='Link to the story')
    
    args = parser.parse_args()
    
    logger.info("Starting Email Notification Service with MailerSend")
    logger.info(f"Using template ID: {TEMPLATE_ID}")
    logger.info(f"Sender: {SENDER_NAME} <{SENDER_EMAIL}>")
    ensure_folders_exist()
    
    success = send_story_notification(
        args.email, 
        args.name, 
        args.title, 
        args.story_about, 
        args.link
    )
    
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
