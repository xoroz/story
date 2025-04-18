import os
import re
from mailersend import emails
from config_loader import load_config
from utils.logging_config import get_logger

# Get logger for this component
logger = get_logger("email")

# Load configuration
config = load_config()

# MailerSend settings
MAILERSEND_TOKEN = os.getenv('MAILERSENDTOKEN')
STORY_TEMPLATE_ID = os.getenv('MAILERSEND_TEMPLATE_ID', '0r83ql3menxgzw1j')
WELCOME_TEMPLATE_ID = os.getenv('MAILERSEND_WELCOME_TEMPLATE_ID', '3zxk54vv70x4jy6v')  # Hardcoded template ID for welcome emails
SENDER_NAME = os.getenv('SENDER_NAME', 'Story Submission System')
SENDER_EMAIL = os.getenv('SENDER_EMAIL', 'info@yourdomain.com')
STORY_EMAIL_SUBJECT = os.getenv('EMAIL_SUBJECT', 'Your Story Submission: {{title}}')
WELCOME_EMAIL_SUBJECT = 'Welcome to StoryMagic!'
CONTACT_EMAIL_SUBJECT = 'New Contact Form Submission'

def send_email_with_mailersend(email, name, template_id, subject, personalization_data):
    """
    Send email using MailerSend API
    
    Args:
        email: Recipient email address
        name: Recipient name
        template_id: MailerSend template ID
        subject: Email subject
        personalization_data: Dictionary of personalization data for the template
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not MAILERSEND_TOKEN:
        logger.error("Missing MailerSend API token in .env file. Please set MAILERSENDTOKEN")
        return False
        
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
                "data": personalization_data
            }
        ]

        # Build the email
        mailer.set_mail_from(mail_from, mail_body)
        mailer.set_mail_to(recipients, mail_body)
        
        # Set subject
        mailer.set_subject(subject, mail_body)
        
        # Set template ID
        mailer.set_template(template_id, mail_body)
        
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
    """
    Send a story notification email
    
    Args:
        email: Recipient email address
        name: Recipient name
        title: Story title
        story_about: Brief description of the story
        link: Link to the story
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not email or not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        logger.error(f"Invalid email address: {email}")
        return False
        
    logger.info(f"Sending story notification email to {email} with title '{title}'")
    
    # Prepare personalization data
    personalization_data = {
        "link": link,
        "title": title,
        "story_about": story_about
    }
    
    # Set subject with personalization if needed
    subject = STORY_EMAIL_SUBJECT.replace('{{title}}', title)
    
    # Send the email
    return send_email_with_mailersend(
        email=email,
        name=name,
        template_id=STORY_TEMPLATE_ID,
        subject=subject,
        personalization_data=personalization_data
    )

def send_welcome_email(email, username, verification_url=None):
    """
    Send a welcome email to a new user with optional verification link
    
    Args:
        email: User's email address
        username: User's username
        verification_url: URL for email verification (optional)
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not email or not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        logger.error(f"Invalid email address: {email}")
        return False
        
    logger.info(f"Sending welcome email to {email}")
    
    # Prepare personalization data
    personalization_data = {
        "username": username
    }
    
    # Add verification URL if provided
    if verification_url:
        personalization_data["validate_link"] = verification_url
        logger.info(f"Including verification link: {verification_url}")
    
    # Send the email
    return send_email_with_mailersend(
        email=email,
        name=username,
        template_id=WELCOME_TEMPLATE_ID,
        subject=WELCOME_EMAIL_SUBJECT,
        personalization_data=personalization_data
    )

def send_plain_email(to_email, to_name, subject, html_content, text_content=None):
    """
    Send a plain email without using a template
    
    Args:
        to_email: Recipient email address
        to_name: Recipient name
        subject: Email subject
        html_content: HTML content of the email
        text_content: Plain text content (optional)
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not MAILERSEND_TOKEN:
        logger.error("Missing MailerSend API token in .env file. Please set MAILERSENDTOKEN")
        return False
        
    if not to_email or not re.match(r"[^@]+@[^@]+\.[^@]+", to_email):
        logger.error(f"Invalid email address: {to_email}")
        return False
        
    logger.info(f"Sending plain email to {to_email} with subject '{subject}'")
    
    try:
        # Set up mail data
        mail_body = {
            "from": {
                "email": SENDER_EMAIL,
                "name": SENDER_NAME
            },
            "to": [
                {
                    "email": to_email,
                    "name": to_name
                }
            ],
            "subject": subject,
            "html": html_content,
        }
        
        # Add text version if provided
        if text_content:
            mail_body["text"] = text_content
        
        # Initialize the MailerSend instance
        mailer = emails.NewEmail(MAILERSEND_TOKEN)
        
        # Send the email directly with the mail_body
        response = mailer.send(mail_body)
        
        # Log the response for debugging
        logger.debug(f"MailerSend raw response: {response}")
        
        # The SDK might return different response types, so let's handle them appropriately
        if isinstance(response, str):
            # If it's a string, let's try to see if it's a JSON response string
            logger.info(f"Email response: {response}")
            if "success" in response.lower() or "202" in response or "200" in response:
                logger.info(f"Email successfully sent to {to_email}")
                return True
            else:
                logger.error(f"Failed to send email: {response}")
                return False
        elif hasattr(response, 'status_code'):
            # If it's a response object with status_code
            if response.status_code in (200, 202):
                logger.info(f"Email successfully sent to {to_email}")
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
        logger.error(f"Error sending plain email via MailerSend: {str(e)}")
        return False

def send_contact_form_email(name, email, message, verification_answer):
    """
    Send a contact form submission email
    
    Args:
        name: Sender's name
        email: Sender's email address
        message: Message content
        verification_answer: Answer to the human verification question
        
    Returns:
        bool: True if successful, False otherwise
    """
    logger.info(f"Sending contact form submission from {email}")
    
    # Create HTML content
    html_content = f"""
    <html>
    <body>
        <h2>New Contact Form Submission</h2>
        <p><strong>From:</strong> {name} ({email})</p>
        <p><strong>Verification Answer:</strong> {verification_answer}</p>
        <h3>Message:</h3>
        <p>{message}</p>
    </body>
    </html>
    """
    
    # Create plain text content
    text_content = f"""
    New Contact Form Submission
    
    From: {name} ({email})
    Verification Answer: {verification_answer}
    
    Message:
    {message}
    """
    
    # Send the email to the site admin
    return send_plain_email(
        to_email="storymagictex@gmail.com",
        to_name="StoryMagic Admin",
        subject=CONTACT_EMAIL_SUBJECT,
        html_content=html_content,
        text_content=text_content
    )
