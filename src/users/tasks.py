from celery import shared_task

from core.resources.email_service import EmailClient
from core.resources.email_service_v2 import EmailClientV2


@shared_task
def send_invitation_email(email, values):
    EmailClientV2.send_account_verification_email(email, values)


@shared_task
def send_onboarding_successful_email(email, values):
    EmailClientV2.send_onboarding_successful_email(email, values)


@shared_task
def send_one_time_login_code_email(email, values):
    EmailClientV2.send_one_time_login_code_email(email, values)


@shared_task
def send_reset_password_request_email(email, values):
    EmailClientV2.send_reset_password_request_email(email, values)


@shared_task
def send_reset_password_success_email(email, values):
    EmailClientV2.send_reset_password_success_email(email, values)
