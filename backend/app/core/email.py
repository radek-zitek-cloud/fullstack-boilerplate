from pathlib import Path
from typing import Optional

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from app.core.config import get_settings
from app.core.tasks import send_email_task

settings = get_settings()

# Configure FastMail
conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
)

fastmail = FastMail(conf)


async def send_email_async(to_email: str, subject: str, body: str, use_celery: bool = True):
    """Send email - async or via Celery background task."""
    if use_celery:
        # Queue email in background
        send_email_task.delay(to_email, subject, body)
    else:
        # Send immediately
        message = MessageSchema(
            subject=subject,
            recipients=[to_email],
            body=body,
            subtype=MessageType.plain,
        )
        await fastmail.send_message(message)


async def send_password_reset_email(to_email: str, first_name: Optional[str], reset_url: str) -> None:
    """Send password reset email with HTML template.
    
    Args:
        to_email: Recipient email address
        first_name: User's first name (optional)
        reset_url: The password reset URL
    """
    # Load HTML template
    template_path = Path(__file__).parent.parent / "templates" / "email" / "reset_password.html"
    
    try:
        template_content = template_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        # Fallback to plain text if template not found
        await send_email_async(
            to_email,
            "Password Reset Request",
            f"Click this link to reset your password: {reset_url}",
            use_celery=False
        )
        return
    
    # Simple template rendering
    html_content = template_content.replace("{{ first_name }}", first_name or "")
    html_content = html_content.replace("{{ email }}", to_email)
    html_content = html_content.replace("{{ reset_url }}", reset_url)
    
    message = MessageSchema(
        subject="Password Reset Request",
        recipients=[to_email],
        body=html_content,
        subtype=MessageType.html,
    )
    
    await fastmail.send_message(message)
