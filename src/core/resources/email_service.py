import os

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    DynamicTemplateData,
    Email,
    Mail,
    Substitution,
    TemplateId,
    To,
)

from .email_templates import EmailTemplate


class EmailClient:
    SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY", None)
    from_email = os.environ.get("FROM_EMAIL", None)
    FROM_EMAIL = f"MyBalance <{from_email}>"
    ENVIRONMENT = os.environ.get("ENVIRONMENT", None)
    env = "live" if ENVIRONMENT == "production" else "test"
    template_handler = EmailTemplate(env)
    sg_client = SendGridAPIClient(SENDGRID_API_KEY)

    @classmethod
    def send_account_verification_email(cls, email: str, values: dict):
        template_id = cls.template_handler.get_template("ACCOUNT_VERIFICATION")
        dynamic_template_data = DynamicTemplateData(values)
        return cls.send_email(email, template_id, dynamic_template_data)

    @classmethod
    def send_welcome_email(cls, email: str, values: dict):
        template_id = cls.template_handler.get_template("ONBOARDING_SUCCESSFUL")
        dynamic_template_data = DynamicTemplateData(values)
        return cls.send_email(email, template_id, dynamic_template_data)

    @classmethod
    def send_reset_password_request_email(cls, email: str, values: dict):
        template_id = cls.template_handler.get_template("RESET_PASSWORD")
        dynamic_template_data = DynamicTemplateData(values)
        return cls.send_email(email, template_id, dynamic_template_data)

    @classmethod
    def send_reset_password_success_email(cls, email: str, values: dict):
        template_id = cls.template_handler.get_template("RESET_PASSWORD_SUCCESSFUL")
        dynamic_template_data = DynamicTemplateData(values)
        return cls.send_email(email, template_id, dynamic_template_data)

    @classmethod
    def send_wallet_withdrawal_email(cls, email: str, values: dict):
        template_id = cls.template_handler.get_template("WALLET_WITHDRAWAL_SUCCESSFUL")
        dynamic_template_data = DynamicTemplateData(values)
        return cls.send_email(email, template_id, dynamic_template_data)

    @classmethod
    def send_wallet_funding_email(cls, email: str, values: dict):
        template_id = cls.template_handler.get_template("WALLET_FUNDING_SUCCESSFUL")
        dynamic_template_data = DynamicTemplateData(values)
        return cls.send_email(email, template_id, dynamic_template_data)

    @classmethod
    def send_approved_escrow_transaction_email(cls, email: str, values: dict):
        template_id = cls.template_handler.get_template("ESCROW_TRANSACTION_APPROVED")
        dynamic_template_data = DynamicTemplateData(values)
        return cls.send_email(email, template_id, dynamic_template_data)

    @classmethod
    def send_rejected_escrow_transaction_email(cls, email: str, values: dict):
        template_id = cls.template_handler.get_template("ESCROW_TRANSACTION_REJECTED")
        dynamic_template_data = DynamicTemplateData(values)
        return cls.send_email(email, template_id, dynamic_template_data)

    @classmethod
    def send_lock_funds_buyer_email(cls, email: str, values: dict):
        template_id = cls.template_handler.get_template("LOCK_FUNDS_BUYER")
        dynamic_template_data = DynamicTemplateData(values)
        return cls.send_email(email, template_id, dynamic_template_data)

    @classmethod
    def send_lock_funds_seller_email(cls, email: str, values: dict):
        template_id = cls.template_handler.get_template("LOCK_FUNDS_SELLER")
        dynamic_template_data = DynamicTemplateData(values)
        return cls.send_email(email, template_id, dynamic_template_data)

    @classmethod
    def send_unlock_funds_buyer_email(cls, email: str, values: dict):
        template_id = cls.template_handler.get_template("UNLOCK_FUNDS_BUYER")
        dynamic_template_data = DynamicTemplateData(values)
        return cls.send_email(email, template_id, dynamic_template_data)

    @classmethod
    def send_unlock_funds_seller_email(cls, email: str, values: dict):
        template_id = cls.template_handler.get_template("UNLOCK_FUNDS_SELLER")
        dynamic_template_data = DynamicTemplateData(values)
        return cls.send_email(email, template_id, dynamic_template_data)

    @classmethod
    def send_dispute_raised_author_email(cls, email: str, values: dict):
        template_id = cls.template_handler.get_template("DISPUTE_RAISED_AUTHOR")
        dynamic_template_data = DynamicTemplateData(values)
        return cls.send_email(email, template_id, dynamic_template_data)

    @classmethod
    def send_dispute_raised_receiver_email(cls, email: str, values: dict):
        template_id = cls.template_handler.get_template("DISPUTE_RAISED_RECIPIENT")
        dynamic_template_data = DynamicTemplateData(values)
        return cls.send_email(email, template_id, dynamic_template_data)

    @classmethod
    def send_one_time_login_code_email(cls, email: str, values: dict):
        template_id = cls.template_handler.get_template("VERIFY_ONE_TIME_LOGIN_CODE")
        dynamic_template_data = DynamicTemplateData(values)
        return cls.send_email(email, template_id, dynamic_template_data)

    @classmethod
    def send_webhook_notification_email_plain(cls, email: str, values: dict):
        subject = "Webhook Notification"
        webhook_html_content = values.get("webhook_html_content", None)
        html_content = webhook_html_content
        return cls.send_plain_email(email, subject, html_content)

    # BASE HANDLERS
    @classmethod
    def send_email(cls, email: str, template_id: str, dynamic_template_data: dict):
        to_email = To(email)
        mail = Mail(cls.FROM_EMAIL, to_email)
        mail.template_id = template_id
        mail.dynamic_template_data = dynamic_template_data
        try:
            response = cls.sg_client.send(mail)
            print("SUCCESSFUL -->", response.status_code == 202)
            # TODO: Log Email Message and Status
            return response.status_code == 202
        except Exception as e:
            print(e)
            # TODO: Log Email Message and Status
            return False

    @classmethod
    def send_plain_email(cls, email: str, subject: str, html_content: str):
        message = Mail(
            from_email=cls.FROM_EMAIL,
            to_emails=email,
            subject=subject,
            html_content=html_content,
        )
        try:
            response = cls.sg_client.send(message)
            print("SUCCESSFUL -->", response.status_code == 202)
            return response.status_code == 202
        except Exception as e:
            print(e)
            return False
