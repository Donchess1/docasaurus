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

    sg_client = SendGridAPIClient(SENDGRID_API_KEY)

    @classmethod
    def send_account_verification_email(cls, email: str, values: dict):
        template_id = TemplateId("d-4487d3c426ac451ea4107d4622fe5a0f")
        dynamic_template_data = DynamicTemplateData(values)
        return cls.send_email(email, template_id, dynamic_template_data)

    @classmethod
    def send_welcome_email(cls, email: str, values: dict):
        template_id = TemplateId("d-e045a73225224c4c83b59ffe6d565bb6")
        dynamic_template_data = DynamicTemplateData(values)
        return cls.send_email(email, template_id, dynamic_template_data)

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
