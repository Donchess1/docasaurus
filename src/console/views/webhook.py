import os

from django.contrib.auth import get_user_model
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny

from console import tasks
from console.serializers.flutterwave import FlwPayoutSerializer, FlwWebhookSerializer
from core.resources.sockets.pusher import PusherSocket
from users.models import UserProfile
from utils.html import generate_flw_payment_webhook_html
from utils.response import Response

User = get_user_model()


class FlwBankTransferWebhookView(GenericAPIView):
    serializer_class = FlwWebhookSerializer
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Webhook for FLW Updates",
    )
    def post(self, request):
        secret_hash = os.environ.get("FLW_SECRET_HASH")
        verif_hash = request.headers.get("verif-hash", None)

        if not verif_hash or verif_hash != secret_hash:
            return Response(
                success=False,
                message="Invalid authorization token.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

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

        html_content = generate_flw_payment_webhook_html(event, data)

        amount_charged = data["amount"]
        customer_email = data["customer"]["email"]

        # LOG EVENT

        # tracking webhook payload
        dev_email = "devtosxn@gmail.com"
        values = {
            "webhook_html_content": html_content,
        }
        tasks.send_webhook_notification_email(dev_email, values)

        if data["status"] == "failed":
            return Response(
                success=True,
                message="Webhook processed successfully.",
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
            message="Webhook processed successfully.",
            status_code=status.HTTP_200_OK,
        )


class FlwPayoutWebhookView(GenericAPIView):
    serializer_class = FlwPayoutSerializer
    permission_classes = [AllowAny]
    pusher = PusherSocket()

    @swagger_auto_schema(
        operation_description="Webhook for FLW Updates: Payout v1",
    )
    def post(self, request):
        secret_hash = os.environ.get("FLW_SECRET_HASH")
        verif_hash = request.headers.get("verif-hash", None)

        if not verif_hash or verif_hash != secret_hash:
            return Response(
                success=False,
                message="Invalid authorization token.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors,
            )

        data = serializer.validated_data
        # event = data.get("event", None)
        data = data.get("transfer")

        # html_content = generate_flw_payment_webhook_html(event, data)

        amount_charged = data["amount"]
        msg = data["complete_message"]
        amount_to_debit = data["meta"]["amount_to_debit"]
        customer_email = data["meta"]["customer_email"]
        tx_ref = data["meta"]["tx_ref"]

        try:
            txn = Transaction.objects.get(reference=tx_ref)
        except Transaction.DoesNotExist:
            return Response(
                success=False,
                message="Transaction does not exist",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        if txn.verified:
            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Withdrawal transaction already verified",
            )

        # TODO: LOG EVENT
        print("================================================")
        print("FLW WEBHOOK WITHDRAWAL DATA", data)
        print("================================================")

        if data["status"] == "FAILED":
            txn.status = "FAILED"
            txn.meta.update({"note": msg})
            txn.verified = True
            txn.save()

            self.pusher.trigger(
                f"WALLET_WITHDRAWAL_{tx_ref}",
                "WALLET_WITHDRAWAL_FAILURE",
                {"status": "FAILED", "message": msg, "amount": txn.amount},
            )

            return Response(
                success=True,
                message="Webhook processed successfully.",
                status_code=status.HTTP_200_OK,
            )

        try:
            user = User.objects.get(email=customer_email)
            profile = UserProfile.objects.get(user_id=user)
            profile.wallet_balance -= Decimal(str(amount_to_debit))
            profile.save()

            self.pusher.trigger(
                f"WALLET_WITHDRAWAL_{tx_ref}",
                "WALLET_WITHDRAWAL_SUCCESS",
                {"status": "SUCCESSFUL", "message": msg, "amount": txn.amount},
            )

            txn.status = "SUCCESSFUL"
            txn.meta.update({"note": msg})
            txn.verified = True
            txn.save()
            # TODO: Send email to User Account of Wallet Withdrawal
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
            message="Withdrawal webhook processed successfully.",
            status_code=status.HTTP_200_OK,
        )
