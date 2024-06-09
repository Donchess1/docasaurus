from celery import shared_task

from core.resources.email_service import EmailClient
from core.resources.email_service_v2 import EmailClientV2


@shared_task
def send_lock_funds_buyer_email(email, values):
    EmailClient.send_lock_funds_buyer_email(email, values)


@shared_task
def send_lock_funds_merchant_buyer_email(email, values):
    EmailClient.send_lock_funds_merchant_buyer_email(email, values)


@shared_task
def send_lock_funds_seller_email(email, values):
    EmailClient.send_lock_funds_seller_email(email, values)


@shared_task
def send_lock_funds_merchant_seller_email(email, values):
    EmailClient.send_lock_funds_merchant_seller_email(email, values)


@shared_task
def send_lock_funds_merchant_email(email, values):
    EmailClient.send_lock_funds_merchant_email(email, values)


@shared_task
def send_unlock_funds_buyer_email(email, values):
    EmailClient.send_unlock_funds_buyer_email(email, values)


@shared_task
def send_unlock_funds_seller_email(email, values):
    EmailClient.send_unlock_funds_seller_email(email, values)


@shared_task
def send_rejected_escrow_transaction_email(email, values):
    EmailClientV2.send_rejected_escrow_transaction_email(email, values)


@shared_task
def send_approved_escrow_transaction_email(email, values):
    EmailClientV2.send_approved_escrow_transaction_email(email, values)
