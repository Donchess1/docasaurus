import logging
from datetime import datetime

from django.conf import settings
from django.core.mail import send_mail as django_send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


class EmailClientV2:
    FROM_EMAIL = f"MyBalance <mybalance@oinvent.com>"

    @classmethod
    def send_account_verification_email(cls, email: str, context: dict):
        template_name = "account_verification.html"
        html_content = render_to_string(template_name=template_name, context=context)
        subject = "Verify Your Account"
        return cls.send_email(email, subject, html_content)

    @classmethod
    def send_onboarding_successful_email(cls, email: str, context: dict):
        template_name = "welcome_onboard.html"
        html_content = render_to_string(template_name=template_name, context=context)
        subject = "Welcome to MyBalance 🎉"
        return cls.send_email(email, subject, html_content)

    @classmethod
    def send_one_time_login_code_email(cls, email: str, context: dict):
        template_name = "one_time_login.html"
        html_content = render_to_string(template_name=template_name, context=context)
        subject = "One-Time Login Code 🔐"
        return cls.send_email(email, subject, html_content)

    @classmethod
    def send_reset_password_request_email(cls, email: str, context: dict):
        template_name = "reset_password_request.html"
        html_content = render_to_string(template_name=template_name, context=context)
        subject = "Reset MyBalance Password 🛠️🔐"
        return cls.send_email(email, subject, html_content)

    @classmethod
    def send_reset_password_success_email(cls, email: str, context: dict):
        template_name = "reset_password_successful.html"
        html_content = render_to_string(template_name=template_name, context=context)
        subject = "MyBalance Password Reset Successful 🎉"
        return cls.send_email(email, subject, html_content)

    @classmethod
    def send_fund_wallet_email(cls, email: str, context: dict):
        template_name = "wallet_funded.html"
        html_content = render_to_string(template_name=template_name, context=context)
        subject = "Wallet Funded 🎉"
        return cls.send_email(email, subject, html_content)

    @classmethod
    def send_wallet_withdrawal_email(cls, email: str, context: dict):
        template_name = "wallet_withdrawal.html"
        html_content = render_to_string(template_name=template_name, context=context)
        subject = "Wallet Withdrawal 🎉"
        return cls.send_email(email, subject, html_content)

    @classmethod
    def send_approved_escrow_transaction_email(cls, email: str, context: dict):
        template_name = "escrow_transaction_approved.html"
        html_content = render_to_string(template_name=template_name, context=context)
        subject = "Escrow Offer Approved 🎉"
        return cls.send_email(email, subject, html_content)

    @classmethod
    def send_rejected_escrow_transaction_email(cls, email: str, context: dict):
        template_name = "escrow_transaction_rejected.html"
        html_content = render_to_string(template_name=template_name, context=context)
        subject = "Escrow Offer Rejected 😩"
        return cls.send_email(email, subject, html_content)

    # ENTRY POINT
    @classmethod
    def send_email(cls, email: str, subject: str, html_body: dict):
        plain_message = strip_tags(html_body)
        try:
            response = django_send_mail(
                subject=subject,
                message=plain_message,
                from_email=cls.FROM_EMAIL,
                recipient_list=[email],
                html_message=html_body,
                fail_silently=False,
            )
            print("SUCCESSFUL -->", response == 1)
            logger.info(f"{subject.upper()} - EMAIL SUCCESSFUL ✅")
            # TODO: Log Email Message and Status
            return True
        except Exception as e:
            err = str(e)
            print(err)
            logger.error(f"{subject.upper()} - EMAIL FAILED ❌")
            logger.error(f"Error: {err}")
            # TODO: Log Email Message and Status
            return False
