import hashlib
import hmac
import os

import stripe
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status

from common.constants import (
    TERRASWITCH_PAYIN_LINK_FAILED,
    TERRASWITCH_PAYIN_LINK_SUCCESS,
    TERRASWITCH_PAYOUT_FAILED,
    TERRASWITCH_PAYOUT_SUCCESS,
)
from common.serializers.webhook import (
    FlwWebhookSerializer,
    GenericWebhookSerializer,
    StripeWebhookSerializer,
)
from common.services import (
    handle_flutterwave_deposit_webhook,
    handle_flutterwave_withdrawal_webhook,
    handle_terraswitch_deposit_webhook,
    handle_terraswitch_withdrawal_webhook,
)
from console.models import Transaction
from core.resources.sockets.pusher import PusherSocket
from core.resources.terraswitch import TerraSwitchAPI
from transaction import tasks as txn_tasks
from utils.activity_log import extract_api_request_metadata, log_transaction_activity
from utils.response import Response
from utils.utils import add_commas_to_transaction_amount

ENVIRONMENT = os.environ.get("ENVIRONMENT", None)
env = "live" if ENVIRONMENT == "production" else "test"

User = get_user_model()
stripe.api_key = settings.STRIPE_SECRET_KEY


class FlwWebhookView(generics.GenericAPIView):
    serializer_class = FlwWebhookSerializer
    permission_classes = [permissions.AllowAny]
    pusher = PusherSocket()

    def post(self, request):
        request_meta = extract_api_request_metadata(request)
        secret_hash = os.environ.get("FLW_SECRET_HASH")
        verif_hash = request.headers.get("verif-hash", None)

        if not verif_hash or verif_hash != secret_hash:
            return Response(
                success=False,
                message="Invalid authorization token.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        print("================================================================")
        print("================================================================")
        print("FLUTTTERWAVE WEBHOOK CALLED")
        print("================================================================")
        print("REQUEST DATA---->", request.data)
        print("================================================================")
        print("================================================================")

        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors,
            )

        event = serializer.validated_data.get("event")
        data = serializer.validated_data.get("data")

        #  =================================================================
        #  =================================================================
        # if event not in [
        #     "transfer.completed",
        #     "charge.completed",
        # ]:  # Valid events from Flutterwave for inflows and outflows
        #     return Response(
        #         success=False,
        #         message="Invalid webhook event does not exist",
        #         status_code=status.HTTP_400_BAD_REQUEST,
        #     )
        #  =================================================================
        # Beware that there is a disparity between the webhook data sent from Flutterwave in test and live environments
        # Observation date: Sunday, July 14th, 2024
        #  =================================================================
        #  =================================================================
        event_type = request.data.get("event.type")
        withdrawal_data = request.data.get("transfer") if env == "test" else data
        deposit_data = request.data if env == "test" else data
        result = (
            handle_flutterwave_withdrawal_webhook(
                withdrawal_data, request_meta, self.pusher
            )
            if event_type.upper() == "TRANSFER"
            else handle_flutterwave_deposit_webhook(
                deposit_data, request_meta, self.pusher
            )
        )
        return Response(**result)


class StripeWebhookView(generics.GenericAPIView):
    serializer_class = StripeWebhookSerializer
    permission_classes = [permissions.AllowAny]
    pusher = PusherSocket()

    def post(self, request, *args, **kwargs):
        request_meta = extract_api_request_metadata(request)
        payload = request.body
        signature_header = request.META["HTTP_STRIPE_SIGNATURE"]
        endpoint_secret = settings.STRIPE_WEBHOOK_SECRET
        try:
            event = stripe.Webhook.construct_event(
                payload, signature_header, endpoint_secret
            )
        except ValueError as e:
            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Invalid payload",
            )
        except stripe.error.SignatureVerificationError as e:
            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Invalid signature",
            )
        event_type = event["type"]
        data = event["data"]["object"]
        print("===============================================================")
        print("===============================================================")
        print("STRIPE WEBHOOK CALLED!!!!!")
        print("===============================================================")
        print("EVENT TYPE---->", event_type)
        print("===============================================================")
        print("===============================================================")

        # Handle the event types you care about
        if event_type == "checkout.session.completed":
            print("===============================================================")
            print("CHECKOUT SESSION COMPLETED - EVENT TYPE")
            print("===============================================================")
            result = self.handle_payment_succeeded(data, request_meta)
        elif event_type == "payment_intent.payment_failed":
            print("===============================================================")
            print("PAYMENT INTENT PAYMENT FAILED - EVENT TYPE")
            print("===============================================================")
            result = self.handle_payment_failed(data, request_meta)
        elif event_type == "payout.paid":
            print("===============================================================")
            print("PAYOUT PAID - EVENT TYPE")
            print("===============================================================")
            result = self.handle_payout_paid(data, request_meta)
        else:
            print("===============================================================")
            print("UNHANDLED EVENT TYPE", event_type)
            print("===============================================================")
            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Unhandled event type",
            )

        return Response(**result)

    def handle_payment_succeeded(self, data, request_meta):
        metadata = data.get("metadata", {})
        tx_ref = metadata.get("transaction_ref", None)
        stripe_transaction_id = data.get("id")
        customer_details = data.get("customer_details")
        print("TX_REF---->", tx_ref)
        print("STRIPE_TXN_ID---->", stripe_transaction_id)
        # print("DATA received", data)
        print("CUSTOMER", customer_details)
        customer_email = customer_details.get("email", None)
        try:
            txn = Transaction.objects.get(reference=tx_ref)
        except Transaction.DoesNotExist:
            return {
                "success": False,
                "message": "Transaction does not exist",
                "status_code": status.HTTP_404_NOT_FOUND,
            }

        if txn.verified:
            return {
                "success": False,
                "message": "Transaction already verified",
                "status_code": status.HTTP_200_OK,
            }

        payment_type = "CARD"
        txn.verified = True
        txn.status = "SUCCESSFUL"
        txn.meta.update(
            {
                "payment_method": payment_type,
            }
        )
        txn.save()

        description = f"Payment received via {payment_type} channel. Transaction verified via Stripe WEBHOOK."
        log_transaction_activity(txn, description, request_meta)

        try:
            user = User.objects.filter(email=customer_email).first()
        except User.DoesNotExist:
            return {
                "success": False,
                "message": "User does not exist.",
                "status_code": status.HTTP_404_NOT_FOUND,
            }

        wallet_exists, wallet = user.get_currency_wallet(txn.currency)
        description = f"Previous User Balance: {txn.currency} {add_commas_to_transaction_amount(wallet.balance)}"
        log_transaction_activity(txn, description, request_meta)

        user.credit_wallet(txn.amount, txn.currency)

        _, wallet = user.get_currency_wallet(txn.currency)
        description = f"New User Balance: {txn.currency} {add_commas_to_transaction_amount(wallet.balance)}"
        log_transaction_activity(txn, description, request_meta)

        return {
            "success": True,
            "status_code": status.HTTP_200_OK,
            "message": "Payment succeeded webhook processed successfully.",
        }

    def handle_payment_failed(self, data, request_meta):
        # Handle payment failure logic
        return {
            "success": False,
            "message": "Payment failed webhook processed.",
            "status_code": status.HTTP_200_OK,
        }

    def handle_payout_paid(self, data, request_meta):
        # Handle payout paid logic
        return {
            "success": True,
            "message": "Payout paid webhook processed.",
            "status_code": status.HTTP_200_OK,
        }


class TerraSwitchWebhookView(generics.GenericAPIView):
    serializer_class = GenericWebhookSerializer
    permission_classes = [permissions.AllowAny]
    pusher = PusherSocket()

    def post(self, request):
        request_meta = extract_api_request_metadata(request)
        terraswitch_signature = request.headers.get("x-terraswitch-signature", None)
        api_key = os.environ.get("TERRASWITCH_SECRET_KEY")
        payload = request.body

        computed_hash = hmac.new(
            key=api_key.encode("utf-8"), msg=payload, digestmod=hashlib.sha512
        ).hexdigest()
        if computed_hash != terraswitch_signature:
            return Response(
                success=False,
                message="Invalid signature.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        print("================================================================")
        print("TERRASWITCH WEBHOOK CALLED")
        print("================================================================")
        print("REQUEST DATA---->", request.data)
        print("================================================================")

        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors,
            )

        event = serializer.validated_data.get("event")
        data = serializer.validated_data.get("data")

        if event and event not in (
            TERRASWITCH_PAYIN_LINK_SUCCESS,
            TERRASWITCH_PAYIN_LINK_FAILED,
            TERRASWITCH_PAYOUT_SUCCESS,
            TERRASWITCH_PAYOUT_FAILED,
        ):
            return Response(
                success=False,
                message="Invalid webhook event type.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        if event in (TERRASWITCH_PAYOUT_SUCCESS, TERRASWITCH_PAYOUT_FAILED):
            result = handle_terraswitch_withdrawal_webhook(
                data, request_meta, self.pusher
            )
        elif event in (TERRASWITCH_PAYIN_LINK_SUCCESS, TERRASWITCH_PAYIN_LINK_FAILED):
            result = handle_terraswitch_deposit_webhook(data, request_meta, self.pusher)
        else:
            result = {
                "success": True,
                "message": f"Terra Switch Webhook processed successfully without valid event: {event}",
                "status_code": status.HTTP_200_OK,
            }
        return Response(**result)


class TestTerraSwitchAPIView(generics.GenericAPIView):
    serializer_class = FlwWebhookSerializer
    permission_classes = [permissions.IsAuthenticated]
    pusher = PusherSocket()

    def post(self, request):
        user = request.user
        request_meta = extract_api_request_metadata(request)
        print("================================================================")
        print("TESTING TERRA!!! --->")
        print("================================================================")
        # obj = TerraSwitchAPI.get_wallet_details()
        payout_data = {
            "type": "account",
            "amount": 2000,
            "reference": "RVFGHYU8334OP",
            "bank": {"accountNo": "0252872743", "bankCode": "4061"},
        }
        obj = TerraSwitchAPI.initiate_payout(payout_data)
        print(obj)
        print("================================================================")
        print("TESTING TERRA!!! --->")
        print("================================================================")

        return Response(
            success=True,
            message="API Called.",
            status_code=status.HTTP_200_OK,
            data=obj,
        )
