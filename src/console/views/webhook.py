from django.contrib.auth import get_user_model
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny

from console import tasks
from console.serializers.flutterwave import FlwBankTransferSerializer
from users.models import UserProfile
from utils.html import generate_flw_payment_webhook_html
from utils.response import Response

User = get_user_model()


class FlwBankTransferWebhookView(GenericAPIView):
    serializer_class = FlwBankTransferSerializer
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Webhook for Fluttterwave to send BankTransfer Updates",
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors,
            )

        data = serializer.validated_data
        event = data.get("event", None)
        data = data.get("data", None)

        amount_charged = data["amount"]
        customer_email = data["customer"]["email"]

        html_content = generate_flw_payment_webhook_html(event, data)

        # tracking webhook payload
        dev_email = "devtosxn@gmail.com"
        values = {
            "webhook_html_content": html_content,
        }
        tasks.send_webhook_notification_email(dev_email, values)

        # update user wallet
        if data["status"] == "failed":
            return Response(
                success=True,
                message="Webhook sent successfully: Failed Bank Transfer",
                status_code=status.HTTP_200_OK,
            )

        try:
            user = User.objects.get(email=customer_email)
            profile = UserProfile.objects.get(user_id=user)
            profile.wallet_balance += int(amount_charged)
            profile.save()
        except User.DoesNotExist:
            return Response(
                success=False,
                message="User not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        except UserProfile.DoesNotExist:
            return Response(
                success=False,
                message="Profile not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            success=True,
            message="Webhook sent successfully: Successful Bank Transfer",
            status_code=status.HTTP_200_OK,
        )
