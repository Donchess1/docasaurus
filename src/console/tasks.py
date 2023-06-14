from celery import shared_task

from core.resources.email_service import EmailClient


@shared_task
def send_webhook_notification_email(email, values):
    EmailClient.send_webhook_notification_email_plain(email, values)
