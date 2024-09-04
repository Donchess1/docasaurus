from celery import shared_task

from core.resources.email_service_v2 import EmailClientV2


@shared_task
def send_wallet_withdrawal_email(email, values):
    EmailClientV2.send_wallet_withdrawal_email(email, values)


@shared_task
def send_fund_wallet_email(email, values):
    EmailClientV2.send_fund_wallet_email(email, values)


@shared_task
def send_product_ticket_successful_payment_email(email, values):
    EmailClientV2.send_product_ticket_successful_payment_email(email, values)
