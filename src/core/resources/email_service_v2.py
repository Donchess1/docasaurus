import logging
from datetime import datetime

from django.conf import settings
from django.core.mail import send_mail as django_send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


class EmailClient:
    FROM_EMAIL = f"MyBalance <mybalance@oinvent.com>"

    @classmethod
    def send_account_verification_email(cls, email: str, context: dict):
        template_name = "registration/verification_email.html"
        html_content = render_to_string(template_name=template_name, context=context)
        subject = "Verify Your Account"
        return cls.send_email(email, subject, html_content)

    @classmethod
    def send_welcome_email(cls, email: str, context: dict):
        template_name = "registration/welcome_email.html"
        html_content = render_to_string(template_name=template_name, context=context)
        subject = "Welcome to MyBalance 🎉"
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
