from celery import shared_task

from core.resources.email_service import EmailClient


@shared_task
def send_lock_funds_buyer_email(email, values):
    EmailClient.send_lock_funds_buyer_email(email, values)


@shared_task
def send_lock_funds_seller_email(email, values):
    EmailClient.send_lock_funds_seller_email(email, values)


@shared_task
def send_unlock_funds_buyer_email(email, values):
    EmailClient.send_unlock_funds_buyer_email(email, values)


@shared_task
def send_unlock_funds_seller_email(email, values):
    EmailClient.send_unlock_funds_seller_email(email, values)


@shared_task
def send_rejected_escrow_transaction_email(email, values):
    EmailClient.send_rejected_escrow_transaction_email(email, values)


@shared_task
def send_approved_escrow_transaction_email(email, values):
    EmailClient.send_approved_escrow_transaction_email(email, values)
