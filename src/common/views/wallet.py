import os
from decimal import Decimal

from django.contrib.auth import get_user_model
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated

from common.serializers.wallet import (
    FundWalletBankTransferPayloadSerializer,
    WalletAmountSerializer,
    WalletWithdrawalAmountSerializer,
)
from console.models import Transaction
from console.serializers.flutterwave import FlwTransferCallbackSerializer
from core.resources.flutterwave import FlwAPI
from users.models import UserProfile
from utils.html import generate_flw_payment_webhook_html
from utils.response import Response
from utils.utils import (
    calculate_payment_amount_to_charge,
    generate_txn_reference,
    get_withdrawal_fee,
)

User = get_user_model()
BACKEND_BASE_URL = os.environ.get("BACKEND_BASE_URL", "")
FRONTEND_BASE_URL = os.environ.get("FRONTEND_BASE_URL", "")


class FundWalletView(GenericAPIView):
    serializer_class = WalletAmountSerializer
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
            meta={"title": "Wallet credit"},
        )
        txn.save()

        tx_data = {
            "tx_ref": tx_ref,
            "amount": amount,
            "currency": "NGN",
            "redirect_url": f"{BACKEND_BASE_URL}/v1/shared/payment-redirect",
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


class FundWalletRedirectView(GenericAPIView):
    serializer_class = WalletAmountSerializer
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
                message="Transaction does not exist",
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
            txn.meta.update({"description": f"FLW Transaction cancelled"})
            txn.save()
            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Payment was cancelled.",
            )

        if flw_status == "failed":
            txn.verified = True
            txn.status = "FAILED"
            txn.meta.update({"description": f"FLW Transaction failed"})
            txn.save()
            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Payment failed",
            )
        if flw_status not in ["completed", "successful"]:
            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Invalid payment status",
            )

        obj = self.flw_api.verify_transaction(flw_transaction_id)

        if obj["status"] == "error":
            msg = obj["message"]
            txn.meta.update({"description": f"FLW Transaction {msg}"})
            txn.save()
            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                message=f"{msg}[]",
            )

        if obj["data"]["status"] == "failed":
            msg = obj["data"]["processor_response"]
            txn.meta.update({"description": f"FLW Transaction {msg}"})
            txn.save()
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
            flw_ref = obj["data"]["flw_ref"]
            narration = obj["data"]["narration"]
            txn.verified = True
            txn.status = "SUCCESSFUL"
            txn.mode = obj["data"]["auth_model"]
            txn.charge = obj["data"]["app_fee"]
            txn.remitted_amount = obj["data"]["amount_settled"]
            txn.provider_tx_reference = flw_ref
            txn.narration = narration
            txn.meta.update(
                {
                    "payment_method": obj["data"]["payment_type"],
                    "provider_txn_id": obj["data"]["id"],
                    "description": f"FLW Transaction {narration}_{flw_ref}",
                }
            )
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


class WalletWithdrawalFeeView(GenericAPIView):
    serializer_class = WalletAmountSerializer
    permission_classes = [IsAuthenticated]
    flw_api = FlwAPI

    @swagger_auto_schema(
        operation_description="Get fees for withdrawal",
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
        temp_amount = data.get("amount", None)
        amount = get_withdrawal_fee(temp_amount)

        # obj = self.flw_api.get_transfer_fee(amount)
        # if obj["status"] == "error":
        #     return Response(
        #         success=False,
        #         status_code=status.HTTP_400_BAD_REQUEST,
        #         message=obj["message"],
        #     )
        # {
        #     "status": "success",
        #     "message": "Transfer fee fetched",
        #     "data": [{"currency": "NGN", "fee_type": "value", "fee": 10.75}],
        #     "status_code": 200,
        # }
        # payload = {
        #     "currency": obj["data"][0]["currency"],
        #     "fee": obj["data"][0]["fee"],
        # }
        payload = {"currency": "NGN", "fee": amount[0], "total": amount[1]}
        # TODO: Send email notification

        return Response(
            success=True,
            message="Withdrawal fee retrieved successfully.",
            status_code=status.HTTP_200_OK,
            data=payload,
        )


class WalletWithdrawalView(GenericAPIView):
    serializer_class = WalletWithdrawalAmountSerializer
    permission_classes = [IsAuthenticated]
    flw_api = FlwAPI

    @swagger_auto_schema(
        operation_description="Initiate withdrawal from user wallet",
    )
    def post(self, request):
        user_id = request.user.id
        user = User.objects.get(id=user_id)
        profile = UserProfile.objects.get(user_id=user)

        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors,
            )
        data = serializer.validated_data
        amount = data.get("amount", None)
        bank_code = data.get("bank_code", None)
        account_number = data.get("account_number", None)
        description = data.get("description", None)

        charge, total_amount = get_withdrawal_fee(int(amount))

        if total_amount >= profile.wallet_balance:
            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Insufficient funds.",
            )

        tx_ref = f"{generate_txn_reference()}_PMCKDU_1"
        email = user.email

        txn = Transaction.objects.create(
            user_id=request.user,
            type="WITHDRAW",
            amount=amount,
            charge=charge,
            status="PENDING",
            reference=tx_ref,
            currency="NGN",
            provider="FLUTTERWAVE",
            meta={"title": "Wallet debit"},
        )
        txn.save()
        # https://developer.flutterwave.com/docs/making-payments/transfers/overview/
        tx_data = {
            "account_bank": bank_code,
            "account_number": account_number,
            "amount": int(amount),
            "narration": description,
            "reference": tx_ref,
            "currency": "NGN",
            "meta": {
                "amount_to_debit": total_amount,
                "customer_email": user.email,
                "tx_ref": tx_ref,
            },
            "callback_url": f"{BACKEND_BASE_URL}/v1/shared/withdraw-callback",
        }

        obj = self.flw_api.initiate_payout(tx_data)
        if obj["status"] == "error":
            msg = obj["message"]
            txn.meta.update({"description": f"FLW Transaction: {tx_ref}", "note": msg})
            txn.save()
            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                message=msg,
            )
        msg = obj["message"]
        txn.meta.update({"description": f"FLW Transaction {tx_ref}", "note": msg})
        txn.save()

        # TODO: Send email notification
        print("DATA FOR WALLET DEBIT:", obj["data"])

        return Response(
            success=True,
            message="Withdrawal is currently being processed",
            status_code=status.HTTP_200_OK,
            # data=obj["data"],
        )


class WalletWithdrawalCallbackView(GenericAPIView):
    serializer_class = FlwTransferCallbackSerializer
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Callback for FLW Transfer to Bank Account",
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
        data = data.get("transfer", None)

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
        print("DATA", data)
        print("================================================")

        if data["status"] == "FAILED":
            txn.status = "FAILED"
            txn.meta.update({"note": msg})
            txn.verified = True
            txn.save()
            return Response(
                success=True,
                message="Callback processed successfully.",
                status_code=status.HTTP_200_OK,
            )

        try:
            user = User.objects.get(email=customer_email)
            profile = UserProfile.objects.get(user_id=user)
            # profile.wallet_balance -= int(amount_to_debit)
            profile.wallet_balance -= Decimal(str(amount_to_debit))
            profile.save()

            txn.status = "SUCCESSFUL"
            txn.meta.update({"note": msg})
            txn.verified = True
            txn.save()
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
            message="Withdrawal callback processed successfully.",
            status_code=status.HTTP_200_OK,
        )
