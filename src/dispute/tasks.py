from celery import shared_task

from core.resources.email_service import EmailClient
from core.resources.email_service_v2 import EmailClientV2


@shared_task
def send_dispute_raised_author_email(email, values):
    EmailClientV2.send_dispute_raised_author_email(email, values)


@shared_task
def send_dispute_raised_via_merchant_widget_author_email(email, values):
    EmailClient.send_dispute_raised_via_merchant_widget_author_email(email, values)


@shared_task
def send_dispute_raised_receiver_email(email, values):
    EmailClientV2.send_dispute_raised_receiver_email(email, values)


@shared_task
def send_dispute_raised_via_merchant_widget_receiver_email(email, values):
    EmailClient.send_dispute_raised_via_merchant_widget_receiver_email(email, values)
