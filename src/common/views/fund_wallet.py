import os

from django.contrib.auth import get_user_model
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated

from common.serializers.wallet import (
    FundWalletBankTransferPayloadSerializer,
    FundWalletSerializer,
)
from console.models import Transaction
from core.resources.flutterwave import FlwAPI
from users.models import UserProfile
from utils.response import Response
from utils.utils import calculate_payment_amount_to_charge, generate_txn_reference

User = get_user_model()
BACKEND_BASE_URL = os.environ.get("BACKEND_BASE_URL", "")


class FundWalletView(GenericAPIView):
    serializer_class = FundWalletSerializer
    permission_classes = [IsAuthenticated]
    flw_api = FlwAPI

    @swagger_auto_schema(
        operation_description="Fund user wallet",
    )
    def post(self, request):
        user_id = request.user.id
        user = User.objects.get(id=user_id)

        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors,
            )
        data = serializer.validated_data
        amount = data.get("amount", None)

        tx_ref = generate_txn_reference()
        email = user.email

        txn = Transaction.objects.create(
            user_id=request.user,
            type="DEPOSIT",
            amount=amount,
            status="PENDING",
            reference=tx_ref,
            currency="NGN",
            provider="FLUTTERWAVE",
        )
        txn.save()

        tx_data = {
            "tx_ref": tx_ref,
            "amount": amount,
            "currency": "NGN",
            "redirect_url": f"{BACKEND_BASE_URL}/v1/shared/payment-callback",
            "customer": {
                "email": user.email,
                "phone_number": user.phone,
                "name": user.name,
            },
            "customizations": {
                "title": "MyBalance",
                "logo": "https://res.cloudinary.com/devtosxn/image/upload/v1686595168/197x43_mzt3hc.png",
            },
        }

        obj = self.flw_api.initiate_payment_link(tx_data)
        if obj["status"] == "error":
            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                message=obj["message"],
            )

        payload = {"link": obj["data"]["link"]}

        return Response(
            success=True,
            message="Payment successfully initialized",
            status_code=status.HTTP_200_OK,
            data=payload,
        )


class FundWalletCallbackView(GenericAPIView):
    serializer_class = FundWalletSerializer
    permission_classes = [AllowAny]
    flw_api = FlwAPI

    def get(self, request):
        flw_status = request.query_params.get("status", None)
        tx_ref = request.query_params.get("tx_ref", None)
        flw_transaction_id = request.query_params.get("transaction_id", None)

        try:
            txn = Transaction.objects.get(reference=tx_ref)
        except Transaction.DoesNotExist:
            return Response(
                success=False,
                message="Transaction not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        if txn.verified:
            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Transaction already verified",
            )

        if flw_status == "cancelled":
            txn.verified = True
            txn.status = "CANCELLED"
            txn.save()
            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Payment was cancelled.",
            )

        if flw_status == "failed":
            txn.verified = True
            txn.status = "FAILED"
            txn.save()
            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Payment failed",
            )

        obj = self.flw_api.verify_transaction(flw_transaction_id)

        if obj["status"] == "error":
            msg = obj["message"]
            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                message=f"{msg}[]",
            )

        if obj["data"]["status"] == "failed":
            msg = obj["data"]["processor_response"]
            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                message=f"{msg}",
            )

        if (
            obj["data"]["tx_ref"] == txn.reference
            and obj["data"]["status"] == "successful"
            and obj["data"]["currency"] == txn.currency
            and obj["data"]["charged_amount"] >= txn.amount
        ):
            txn.verified = True
            txn.status = "SUCCESSFUL"
            txn.mode = obj["data"]["auth_model"]
            txn.charge = obj["data"]["app_fee"]
            txn.remitted_amount = obj["data"]["amount_settled"]
            txn.provider_tx_reference = obj["data"]["flw_ref"]
            txn.narration = obj["data"]["narration"]
            txn.meta = {
                "payment_method": obj["data"]["payment_type"],
                "provider_txn_id": obj["data"]["id"],
            }
            txn.save()

            customer_email = obj["data"]["customer"]["email"]
            amount_charged = obj["data"]["charged_amount"]

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
                status_code=status.HTTP_200_OK,
                message="Transaction verified.",
            )

        return Response(
            success=True,
            message="Payment successfully verified",
            status_code=status.HTTP_200_OK,
        )
