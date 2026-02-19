from app.core.celery import celery_app
from app.core.config import get_settings

settings = get_settings()


@celery_app.task(bind=True, max_retries=3)
def send_email_task(self, to_email: str, subject: str, body: str):
    """Send email asynchronously."""
    try:
        # In production, integrate with actual email service
        # For now, just log the email
        print(f"Sending email to {to_email}")
        print(f"Subject: {subject}")
        print(f"Body: {body}")
        return {"status": "sent", "to": to_email}
    except Exception as exc:
        self.retry(exc=exc, countdown=60)


@celery_app.task
def process_file_task(file_path: str, user_id: int):
    """Process uploaded file asynchronously."""
    print(f"Processing file {file_path} for user {user_id}")
    # Add file processing logic here (resize images, convert formats, etc.)
    return {"status": "processed", "file": file_path}


@celery_app.task
def cleanup_old_tasks_task():
    """Cleanup old completed tasks."""
    print("Running cleanup of old tasks")
    # Add cleanup logic here
    return {"status": "cleaned"}
