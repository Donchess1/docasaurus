from celery import shared_task

from core.resources.email_service import EmailClient


@shared_task
def send_dispute_raised_author_email(email, values):
    EmailClient.send_dispute_raised_author_email(email, values)


@shared_task
def send_dispute_raised_via_merchant_widget_author_email(email, values):
    EmailClient.send_dispute_raised_via_merchant_widget_author_email(email, values)


@shared_task
def send_dispute_raised_receiver_email(email, values):
    EmailClient.send_dispute_raised_receiver_email(email, values)


@shared_task
def send_dispute_raised_via_merchant_widget_receiver_email(email, values):
    EmailClient.send_dispute_raised_via_merchant_widget_receiver_email(email, values)
