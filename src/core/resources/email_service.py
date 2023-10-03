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


class EmailClient:
    SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY", None)
    FROM_EMAIL = os.environ.get("FROM_EMAIL", None)
    ENVIRONMENT = os.environ.get("ENVIRONMENT", None)
    # use_live_email_server = True if ENVIRONMENT == "production" else False
    use_live_email_server = False
    sg_client = SendGridAPIClient(SENDGRID_API_KEY)

    @classmethod
    def send_account_verification_email(cls, email: str, values: dict):
        template_id = (
            TemplateId("d-c7705c480c644ef69c2599b70f80a796")
            if cls.use_live_email_server
            else TemplateId("d-4487d3c426ac451ea4107d4622fe5a0f")
        )
        dynamic_template_data = DynamicTemplateData(values)
        return cls.send_email(email, template_id, dynamic_template_data)

    @classmethod
    def send_welcome_email(cls, email: str, values: dict):
        template_id = (
            TemplateId("d-8b52dcaa981245ad87f3b736ebf2c47")
            if cls.use_live_email_server
            else TemplateId("d-e045a73225224c4c83b59ffe6d565bb6")
        )
        dynamic_template_data = DynamicTemplateData(values)
        return cls.send_email(email, template_id, dynamic_template_data)

    @classmethod
    def send_reset_password_request_email(cls, email: str, values: dict):
        template_id = (
            TemplateId("d-926d624f4ae64585833eda41e0ee1c8c")
            if cls.use_live_email_server
            else TemplateId("d-6562061135c44c959c43c08e5bc9cc7d")
        )
        dynamic_template_data = DynamicTemplateData(values)
        return cls.send_email(email, template_id, dynamic_template_data)

    @classmethod
    def send_reset_password_success_email(cls, email: str, values: dict):
        template_id = (
            TemplateId("d-60b626bd4fb44d509c19e3621956111c")
            if cls.use_live_email_server
            else TemplateId("d-506c4b99dde94ee7a58d28cf7ba166d3")
        )
        dynamic_template_data = DynamicTemplateData(values)
        return cls.send_email(email, template_id, dynamic_template_data)

    @classmethod
    def send_wallet_withdrawal_email(cls, email: str, values: dict):
        template_id = TemplateId("d-abcbf3f7f9da4a689bc23d04bb25d617")
        dynamic_template_data = DynamicTemplateData(values)
        return cls.send_email(email, template_id, dynamic_template_data)

    @classmethod
    def send_wallet_funding_email(cls, email: str, values: dict):
        template_id = TemplateId("d-125b68d79ed148ae84281f37d7cafbf1")
        dynamic_template_data = DynamicTemplateData(values)
        return cls.send_email(email, template_id, dynamic_template_data)

    @classmethod
    def send_lock_funds_buyer_email(cls, email: str, values: dict):
        template_id = TemplateId("d-1840ebd4e7ee4281bc18dd8f2b00731e")
        dynamic_template_data = DynamicTemplateData(values)
        return cls.send_email(email, template_id, dynamic_template_data)

    @classmethod
    def send_lock_funds_seller_email(cls, email: str, values: dict):
        template_id = TemplateId("d-0fba8d742e884212ad73b35ed81b9c95")
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
            return response.status_code == 202
        except Exception as e:
            print(e)
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
