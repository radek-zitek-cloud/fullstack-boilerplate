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
