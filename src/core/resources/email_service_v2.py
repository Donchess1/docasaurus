import logging
from datetime import datetime

from django.conf import settings
from django.core.mail import get_connection
from django.core.mail import send_mail as django_send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags

from console.models.providers import EmailLog
from utils.utils import EMAIL_SMTP_PROVIDERS

logger = logging.getLogger(__name__)


class EmailClientV2:
    FROM_EMAIL = settings.FROM_EMAIL
    PROVIDER = "AWS_SES"  # Default provider
    # TODO: Read provider from database or cache

    @classmethod
    def set_provider(cls, provider: str):
        if provider.upper() in EMAIL_SMTP_PROVIDERS:
            cls.PROVIDER = provider.upper()
        else:
            raise ValueError("Invalid email provider")

    @classmethod
    def get_connection(cls):
        """
        Get the appropriate connection based on the PROVIDER attribute.
        """
        provider = cls.PROVIDER
        if provider and provider in settings.EMAIL_BACKENDS:
            backend_config = settings.EMAIL_BACKENDS[provider]
            return get_connection(
                backend=backend_config["BACKEND"],
                host=backend_config["HOST"],
                port=backend_config["PORT"],
                username=backend_config["USERNAME"],
                password=backend_config["PASSWORD"],
                use_tls=backend_config["USE_TLS"],
            )
        else:
            raise ValueError(
                f"Provider {provider} is not configured in EMAIL_BACKENDS."
            )

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

    @classmethod
    def send_revoked_escrow_transaction_email(cls, email: str, context: dict):
        template_name = "escrow_transaction_revoked.html"
        html_content = render_to_string(template_name=template_name, context=context)
        subject = "Escrow Offer Revoked ❌"
        return cls.send_email(email, subject, html_content)

    @classmethod
    def send_lock_funds_buyer_email(cls, email: str, context: dict):
        template_name = "escrow_funds_locked_buyer.html"
        html_content = render_to_string(template_name=template_name, context=context)
        subject = "Escrow Funds Locked 🎉"
        return cls.send_email(email, subject, html_content)

    @classmethod
    def send_lock_funds_seller_email(cls, email: str, context: dict):
        template_name = "escrow_funds_locked_seller.html"
        html_content = render_to_string(template_name=template_name, context=context)
        subject = "Escrow Funds Locked 🎉"
        return cls.send_email(email, subject, html_content)

    @classmethod
    def send_unlock_funds_buyer_email(cls, email: str, context: dict):
        template_name = "escrow_funds_unlocked_buyer.html"
        html_content = render_to_string(template_name=template_name, context=context)
        subject = "Escrow Funds Unlocked 🎉"
        return cls.send_email(email, subject, html_content)

    @classmethod
    def send_unlock_funds_seller_email(cls, email: str, context: dict):
        template_name = "escrow_funds_unlocked_seller.html"
        html_content = render_to_string(template_name=template_name, context=context)
        subject = "Escrow Funds Unlocked 🎉"
        return cls.send_email(email, subject, html_content)

    @classmethod
    def send_dispute_raised_author_email(cls, email: str, context: dict):
        template_name = "dispute_raised_author.html"
        html_content = render_to_string(template_name=template_name, context=context)
        subject = "Dispute Raised 🎉"
        return cls.send_email(email, subject, html_content)

    @classmethod
    def send_dispute_raised_receiver_email(cls, email: str, context: dict):
        template_name = "dispute_raised_recipient.html"
        html_content = render_to_string(template_name=template_name, context=context)
        subject = "Escrow Transaction Disputed 🎉"
        return cls.send_email(email, subject, html_content)

    @classmethod
    def send_lock_funds_merchant_buyer_email(cls, email: str, context: dict):
        template_name = "merchant/escrow_funds_locked_buyer.html"
        html_content = render_to_string(template_name=template_name, context=context)
        subject = "Escrow Funds Locked 🎉"
        return cls.send_email(email, subject, html_content)

    @classmethod
    def send_lock_funds_merchant_seller_email(cls, email: str, context: dict):
        template_name = "merchant/escrow_funds_locked_seller.html"
        html_content = render_to_string(template_name=template_name, context=context)
        subject = "Escrow Funds Locked 🎉"
        return cls.send_email(email, subject, html_content)

    @classmethod
    def send_lock_funds_merchant_email(cls, email: str, context: dict):
        template_name = "merchant/escrow_funds_locked_merchant.html"
        html_content = render_to_string(template_name=template_name, context=context)
        subject = "Escrow Funds Locked 🎉"
        return cls.send_email(email, subject, html_content)

    @classmethod
    def send_unlock_funds_merchant_buyer_email(cls, email: str, context: dict):
        template_name = "merchant/escrow_funds_unlocked_buyer.html"
        html_content = render_to_string(template_name=template_name, context=context)
        subject = "Escrow Funds Unlocked 🎉"
        return cls.send_email(email, subject, html_content)

    @classmethod
    def send_unlock_funds_merchant_seller_email(cls, email: str, context: dict):
        template_name = "merchant/escrow_funds_unlocked_seller.html"
        html_content = render_to_string(template_name=template_name, context=context)
        subject = "Escrow Funds Unlocked 🎉"
        return cls.send_email(email, subject, html_content)

    @classmethod
    def send_unlock_funds_merchant_email(cls, email: str, context: dict):
        template_name = "merchant/escrow_funds_unlocked_merchant.html"
        html_content = render_to_string(template_name=template_name, context=context)
        subject = "Escrow Settlement 🎉"
        return cls.send_email(email, subject, html_content)

    @classmethod
    def send_merchant_wallet_withdrawal_confirmation_email(
        cls, email: str, context: dict
    ):
        template_name = "merchant/merchant_wallet_withdrawal_confirmation_code.html"
        html_content = render_to_string(template_name=template_name, context=context)
        subject = "MyBalance Confirmation Code 🔐"
        return cls.send_email(email, subject, html_content)

    @classmethod
    def send_dispute_raised_via_merchant_widget_author_email(
        cls, email: str, context: dict
    ):
        template_name = "merchant/dispute_raised_author.html"
        html_content = render_to_string(template_name=template_name, context=context)
        subject = "Dispute Raised"
        return cls.send_email(email, subject, html_content)

    @classmethod
    def send_dispute_raised_via_merchant_widget_receiver_email(
        cls, email: str, context: dict
    ):
        template_name = "merchant/dispute_raised_receipient.html"
        html_content = render_to_string(template_name=template_name, context=context)
        subject = "Escrow Transaction Disputed"
        return cls.send_email(email, subject, html_content)

    @classmethod
    def send_product_ticket_successful_payment_email(cls, email: str, context: dict):
        template_name = "product_ticket_successful_payment.html"
        html_content = render_to_string(template_name=template_name, context=context)
        subject = "Ticket Payment Complete 🎉"
        return cls.send_email(email, subject, html_content)

    # ENTRY POINT
    @classmethod
    def send_email(cls, email: str, subject: str, html_body: dict):
        plain_message = strip_tags(html_body)
        try:
            connection = cls.get_connection()
            response = django_send_mail(
                subject=subject,
                message=plain_message,
                from_email=cls.FROM_EMAIL,
                recipient_list=[email],
                html_message=html_body,
                fail_silently=False,
                connection=connection,
            )
            print("SUCCESSFUL -->", response == 1)
            logger.info(f"{subject.upper()} - EMAIL SUCCESSFUL ✅")
            EmailLog.objects.create(
                recipient=email,
                subject=subject,
                body=html_body if html_body else plain_message,
                sent_at=timezone.now(),
                status="SUCCESSFUL",
                smtp_server=connection.host,
                provider=cls.PROVIDER,
            )
        except Exception as e:
            err = str(e)
            print(err)
            logger.error(f"{subject.upper()} - EMAIL FAILED ❌")
            logger.error(f"Error: {err}")
            EmailLog.objects.create(
                recipient=email,
                subject=subject,
                body=html_body if html_body else plain_message,
                sent_at=timezone.now(),
                status="FAILED",
                error_message=str(e),
                provider=cls.PROVIDER,
            )
