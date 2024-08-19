import os

import stripe
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status

from common.serializers.webhook import FlwWebhookSerializer, StripeWebhookSerializer
from common.services import handle_deposit, handle_withdrawal
from console.models import Transaction
from core.resources.sockets.pusher import PusherSocket
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
        # Beware that there is a currently disparity between the data sent from Flutterwave in test and live environments
        # Observation date: Sunday, July 14th, 2024
        #  =================================================================
        #  =================================================================
        event_type = request.data.get("event.type")
        withdrawal_data = request.data.get("transfer") if env == "test" else data
        deposit_data = request.data if env == "test" else data
        result = (
            handle_withdrawal(withdrawal_data, request_meta, self.pusher)
            if event_type.upper() == "TRANSFER"
            else handle_deposit(deposit_data, request_meta, self.pusher)
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
        # endpoint_secret = (
        #     "whsec_e75999dec7f8a9ba7a042e78dcd9cdb85779f9059c1780b8171e5ddae2046f5e"
        # )

        try:
            print("===============================================================")
            print("SIG_HEADER --->", signature_header)
            print("===============================================================")
            print("ENDPOINT SECRET --->", endpoint_secret)
            print("===============================================================")
            print("PAYLOAD --->", payload)
            print("===============================================================")
            event = stripe.Webhook.construct_event(
                payload, signature_header, endpoint_secret
            )
            print("===============================================================")
            print("EVENT --->", event)
            print("===============================================================")
        except ValueError as e:
            print("===============================================================")
            print("Invalid payload", str(e))
            print("===============================================================")
            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Invalid payload",
            )
        except stripe.error.SignatureVerificationError as e:
            print("===============================================================")
            print("Invalid signature", str(e))
            print("===============================================================")
            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Invalid signature",
            )

        # Handle the event
        event_type = event["type"]
        data = event["data"]["object"]

        print("===============================================================")
        print("===============================================================")
        print("STRIPE WEBHOOK CALLED")
        print("===============================================================")
        print("EVENT TYPE---->", event_type)
        print("===============================================================")
        print("===============================================================")

        # Handle the event types you care about
        if event_type == "checkout.session.completed":
            print("===============================================================")
            print("CHECKOUT SESSION COMPLETED")
            print("===============================================================")
            result = self.handle_payment_succeeded(data, request_meta)
        elif event_type == "payment_intent.payment_failed":
            print("===============================================================")
            print("PAYMENT INTENT PAYMENT FAILED")
            print("===============================================================")
            result = self.handle_payment_failed(data, request_meta)
        elif event_type == "payout.paid":
            print("===============================================================")
            print("PAYOUT PAID")
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
            print("TXN DOES NOT EXIST")
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

        description = f"Payment verified via Stripe WEBHOOK."
        log_transaction_activity(txn, description, request_meta)

        # Additional logic like crediting user's wallet, updating locked amounts, sending notifications, etc.

        description = f"Payment received via {payment_type} channel. Transaction verified via WEBHOOK."
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
