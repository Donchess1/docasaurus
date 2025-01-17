from celery import shared_task

from core.resources.email_service_v2 import EmailClientV2


@shared_task
def send_wallet_withdrawal_confirmation_via_merchant_platform_email(email, values):
    """
    this method sends an email when there is an intent to withdraw funds from a merchant's wallet
    or customer's wallet (either through widget or via merchant API)
    """
    EmailClientV2.send_wallet_withdrawal_confirmation_via_merchant_platform_email(
        email, values
    )


@shared_task
def send_unlock_funds_merchant_buyer_email(email, values):
    EmailClientV2.send_unlock_funds_merchant_buyer_email(email, values)


@shared_task
def send_unlock_funds_merchant_seller_email(email, values):
    EmailClientV2.send_unlock_funds_merchant_seller_email(email, values)


@shared_task
def send_unlock_funds_merchant_email(email, values):
    EmailClientV2.send_unlock_funds_merchant_email(email, values)
