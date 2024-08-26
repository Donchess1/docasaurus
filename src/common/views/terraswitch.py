import os
from decimal import Decimal

import stripe
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
from console import tasks as console_tasks
from console.models.transaction import LockedAmount, Transaction
from console.serializers.flutterwave import FlwTransferCallbackSerializer
from core.resources.flutterwave import FlwAPI
from core.resources.sockets.pusher import PusherSocket
from core.resources.stripe import StripeAPI
from core.resources.terraswitch import TerraSwitchAPI
from notifications.models.notification import UserNotification
from transaction import tasks as txn_tasks
from users.models import UserProfile
from users.models.wallet import Wallet
from utils.activity_log import extract_api_request_metadata, log_transaction_activity
from utils.response import Response
from utils.text import notifications
from utils.utils import (
    PAYMENT_GATEWAY_PROVIDER,
    add_commas_to_transaction_amount,
    calculate_payment_amount_to_charge,
    generate_txn_reference,
    get_withdrawal_fee,
    parse_datetime,
)

User = get_user_model()
BACKEND_BASE_URL = os.environ.get("BACKEND_BASE_URL", "")
FRONTEND_BASE_URL = os.environ.get("FRONTEND_BASE_URL", "")
ENVIRONMENT = os.environ.get("ENVIRONMENT", None)
env = "live" if ENVIRONMENT == "production" else "test"


class FundWalletTerraSwitchView(GenericAPIView):
    serializer_class = WalletAmountSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Fund user wallet via TerraSwitch",
    )
    def post(self, request):
        request_meta = extract_api_request_metadata(request)
        user = request.user
        PAYMENT_GATEWAY_PROVIDER = "TERRASWITCH"
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors,
            )
        data = serializer.validated_data
        amount = data.get("amount", None)
        currency = data.get("currency")

        tx_ref = generate_txn_reference()
        email = user.email
        txn = Transaction.objects.create(
            user_id=user,
            type="DEPOSIT",
            amount=amount,
            status="PENDING",
            reference=tx_ref,
            currency=currency,
            provider=PAYMENT_GATEWAY_PROVIDER,
            meta={"title": "Wallet credit"},
        )

        description = f"{(user.name).upper()} initiated deposit of {currency} {add_commas_to_transaction_amount(amount)} to fund wallet. Payment Provider: {txn.provider}"
        log_transaction_activity(txn, description, request_meta)

        tx_data = {
            "type": "fixed",
            "reuseable": False,
            "amount": amount,
            "reference": tx_ref,
            "currency": currency,
            "redirectUrl": f"{FRONTEND_BASE_URL}/buyer/payment-callback",
            "message": "Thank you for your payment. Please wait for a response shortly.",  # Success message after a successful payment.
            "customer": {
                "email": user.email,
                "firstName": user.name.split(" ")[0],
                "lastName": user.name.split(" ")[1]
                if len(user.name.split()) > 1
                else "",
                "phoneNumber": user.phone,
                "phoneCode": "+234",
            },
            "metadata": [  # TerraSwitch Constructive Structure
                {
                    "displayName": "Merchant Reference",
                    "variableName": "merchant_reference",
                    "value": tx_ref,
                },
                {
                    "displayName": "Merchant Action",
                    "variableName": "action",
                    "value": "FUND_WALLET",  # ["FUND_ESCROW", "FUND_MERCHANT_ESCROW", "FUND_WALLET"]
                },
                {
                    "displayName": "Merchant Platform",
                    "variableName": "platform",
                    "value": "WEB",  # ["WEB", "MERCHANT_API"]
                },
            ],
        }

        obj = TerraSwitchAPI.initiate_payment_link(tx_data)
        if obj["error"]:
            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                message=obj["errors"][0],
            )

        link = obj["data"]["link"]
        payload = {"link": link}

        description = f"Payment link: {link} successfully generated on {PAYMENT_GATEWAY_PROVIDER}."
        log_transaction_activity(txn, description, request_meta)

        return Response(
            success=True,
            message="Payment successfully initialized",
            status_code=status.HTTP_200_OK,
            data=payload,
        )
