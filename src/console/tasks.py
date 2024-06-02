from celery import shared_task

from core.resources.email_service import EmailClient
from core.resources.email_service_v2 import EmailClient as EmailClientV2


@shared_task
def send_wallet_withdrawal_email(email, values):
    EmailClient.send_wallet_withdrawal_email(email, values)


@shared_task
def send_wallet_funding_email(email, values):
    EmailClientV2.send_wallet_funding_email(email, values)
