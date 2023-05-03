from celery import shared_task

from core.resources.email_service import EmailClient


@shared_task
def send_invitation_email(email, values):
    EmailClient.send_account_verification_email(email, values)


@shared_task
def send_welcome_email(email, values):
    EmailClient.send_welcome_email(email, values)
