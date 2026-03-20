"""Email delivery using aiosmtplib."""
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from typing import List, Optional
import os
from intelligence.schemas import MeetingIntelligence


class EmailSender:
    """Send meeting follow-up emails."""
    
    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        username: str,
        password: str,
        from_address: str
    ):
        """
        Initialize email sender.
        
        Args:
            smtp_host: SMTP server hostname
            smtp_port: SMTP server port
            username: SMTP username
            password: SMTP password (app password for Gmail)
            from_address: From email address
        """
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_address = from_address
        
        # Setup Jinja2 for templates
        template_dir = Path(__file__).parent / "templates"
        self.jinja_env = Environment(loader=FileSystemLoader(str(template_dir)))
    
    async def send_followup(
        self,
        intelligence: MeetingIntelligence,
        recipients: List[str],
        subject: Optional[str] = None
    ):
        """
        Send meeting follow-up email.
        
        Args:
            intelligence: Meeting intelligence data
            recipients: List of recipient email addresses
            subject: Email subject (auto-generated if None)
        """
        print(f"📧 Preparing email to {len(recipients)} recipients...")
        
        # Generate subject if not provided
        if subject is None:
            subject = f"Meeting Follow-up: {intelligence.summary.title}"
        
        # Render HTML template
        template = self.jinja_env.get_template("followup.html")
        html_content = template.render(
            title=intelligence.summary.title,
            date=intelligence.processed_at.strftime("%Y-%m-%d"),
            duration=intelligence.summary.duration_minutes or "N/A",
            participants=intelligence.summary.participants,
            summary=intelligence.summary.summary,
            key_points=intelligence.summary.key_points,
            action_items=[item.dict() for item in intelligence.action_items],
            decisions=[dec.dict() for dec in intelligence.decisions],
            processed_at=intelligence.processed_at.strftime("%Y-%m-%d %H:%M")
        )
        
        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = self.from_address
        message["To"] = ", ".join(recipients)
        
        # Add HTML part
        html_part = MIMEText(html_content, "html")
        message.attach(html_part)
        
        # Send email
        async with aiosmtplib.SMTP(hostname=self.smtp_host, port=self.smtp_port) as smtp:
            await smtp.starttls()
            await smtp.login(self.username, self.password)
            await smtp.send_message(message)
        
        print(f"✅ Email sent successfully to {len(recipients)} recipients")
    
    def send_followup_sync(
        self,
        intelligence: MeetingIntelligence,
        recipients: List[str],
        subject: Optional[str] = None
    ):
        """Synchronous wrapper for send_followup."""
        import asyncio
        return asyncio.run(self.send_followup(intelligence, recipients, subject))


def create_email_sender_from_config(config_path: str = "config.yaml") -> EmailSender:
    """Create EmailSender from config file."""
    import yaml
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    email_config = config['integrations']['email']
    
    return EmailSender(
        smtp_host=email_config['smtp_host'],
        smtp_port=email_config['smtp_port'],
        username=os.getenv('EMAIL_USERNAME') or email_config['username'],
        password=os.getenv('EMAIL_APP_PASSWORD') or email_config['password'],
        from_address=os.getenv('EMAIL_FROM') or email_config['from_address']
    )
