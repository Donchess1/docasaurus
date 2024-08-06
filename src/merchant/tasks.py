from celery import shared_task

from core.resources.email_service_v2 import EmailClientV2


@shared_task
def send_merchant_wallet_withdrawal_confirmation_email(email, values):
    EmailClientV2.send_merchant_wallet_withdrawal_confirmation_email(email, values)


@shared_task
def send_unlock_funds_merchant_buyer_email(email, values):
    EmailClientV2.send_unlock_funds_merchant_buyer_email(email, values)


@shared_task
def send_unlock_funds_merchant_seller_email(email, values):
    EmailClientV2.send_unlock_funds_merchant_seller_email(email, values)


@shared_task
def send_unlock_funds_merchant_email(email, values):
    EmailClientV2.send_unlock_funds_merchant_email(email, values)
