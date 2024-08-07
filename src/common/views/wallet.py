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
from console import tasks as console_tasks
from console.models.transaction import LockedAmount, Transaction
from console.serializers.flutterwave import FlwTransferCallbackSerializer
from core.resources.flutterwave import FlwAPI
from core.resources.sockets.pusher import PusherSocket
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


class FundWalletView(GenericAPIView):
    serializer_class = WalletAmountSerializer
    permission_classes = [IsAuthenticated]
    flw_api = FlwAPI

    @swagger_auto_schema(
        operation_description="Fund user wallet",
    )
    def post(self, request):
        request_meta = extract_api_request_metadata(request)
        user = request.user
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

        description = f"{(user.name).upper()} initiated deposit of {currency} {add_commas_to_transaction_amount(amount)} to fund wallet."
        log_transaction_activity(txn, description, request_meta)

        tx_data = {
            "tx_ref": tx_ref,
            "amount": amount,
            "currency": currency,
            # "redirect_url": f"{BACKEND_BASE_URL}/v1/shared/payment-redirect",
            "redirect_url": f"{FRONTEND_BASE_URL}/buyer/payment-callback",
            "customer": {
                "email": user.email,
                "phone_number": user.phone,
                "name": user.name,
            },
            "customizations": {
                "title": "MyBalance",
                "logo": "https://res.cloudinary.com/devtosxn/image/upload/v1686595168/197x43_mzt3hc.png",
            },
            "configurations": {
                "session_duration": 10,  # Session timeout in minutes (maxValue: 1440 minutes)
                "max_retry_attempt": 3,  # Max retry (int)
            },
            "meta": {
                "action": "FUND_WALLET",
                "platform": "WEB",
            },
        }

        obj = self.flw_api.initiate_payment_link(tx_data)
        if obj["status"] == "error":
            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                message=obj["message"],
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


class FundWalletRedirectView(GenericAPIView):
    serializer_class = WalletAmountSerializer  # Placeholder Serializer
    permission_classes = [AllowAny]
    flw_api = FlwAPI

    def get(self, request):
        request_meta = extract_api_request_metadata(request)
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
                success=True,
                status_code=status.HTTP_200_OK,
                message="Payment already verified.",
            )

        if flw_status == "cancelled":
            txn.verified = True
            txn.status = "CANCELLED"
            txn.meta.update({"description": f"FLW Transaction cancelled"})
            txn.save()

            description = f"Payment was cancelled."
            log_transaction_activity(txn, description, request_meta)

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

            description = f"Payment failed."
            log_transaction_activity(txn, description, request_meta)

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

            description = (
                f"Error occurred while verifying transaction. Description: {msg}"
            )
            log_transaction_activity(txn, description, request_meta)

            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                message=msg,
            )

        if obj["data"]["status"] == "failed":
            msg = obj["data"]["processor_response"]
            txn.meta.update({"description": f"FLW Transaction {msg}"})
            txn.save()

            description = f"Transaction failed. Description: {msg}"
            log_transaction_activity(txn, description, request_meta)

            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                message=msg,
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
            payment_type = obj["data"]["payment_type"]
            txn.meta.update(
                {
                    "payment_method": payment_type,
                    "provider_txn_id": obj["data"]["id"],
                    "description": f"FLW Transaction {narration}_{flw_ref}",
                }
            )
            txn.save()

            customer_email = obj["data"]["customer"]["email"]
            amount_charged = obj["data"]["charged_amount"]

            description = f"Payment received via {payment_type} channel. Transaction verified via REDIRECT URL."
            log_transaction_activity(txn, description, request_meta)

            try:
                user = User.objects.filter(email=customer_email).first()
                wallet_exists, wallet = user.get_currency_wallet(txn.currency)

                description = f"Previous User Balance: {txn.currency} {add_commas_to_transaction_amount(wallet.balance)}"
                log_transaction_activity(txn, description, request_meta)

                user.credit_wallet(txn.amount, txn.currency)
                wallet_exists, wallet = user.get_currency_wallet(txn.currency)

                description = f"New User Balance: {txn.currency} {add_commas_to_transaction_amount(wallet.balance)}"
                log_transaction_activity(txn, description, request_meta)

                email = user.email
                values = {
                    "first_name": user.name.split(" ")[0],
                    "recipient": email,
                    "date": parse_datetime(txn.created_at),
                    "amount_funded": f"{txn.currency} {add_commas_to_transaction_amount(txn.amount)}",
                    "wallet_balance": f"{txn.currency} {add_commas_to_transaction_amount(wallet.balance)}",
                    "transaction_reference": f"{(txn.reference).upper()}",
                }
                console_tasks.send_fund_wallet_email.delay(email, values)
                # Create Notification
                UserNotification.objects.create(
                    user=user,
                    category="DEPOSIT",
                    title=notifications.WalletDepositNotification(
                        txn.amount, txn.currency
                    ).TITLE,
                    content=notifications.WalletDepositNotification(
                        txn.amount, txn.currency
                    ).CONTENT,
                    action_url=f"{BACKEND_BASE_URL}/v1/transaction/link/{tx_ref}",
                )

                # TODO: Send real-time Notification
            except User.DoesNotExist:
                return Response(
                    success=False,
                    message="User not found",
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


class FundEscrowTransactionRedirectView(GenericAPIView):
    serializer_class = WalletAmountSerializer  # Placeholder Serializer class
    permission_classes = [AllowAny]
    flw_api = FlwAPI

    def get(self, request):
        request_meta = extract_api_request_metadata(request)
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
                success=True,
                status_code=status.HTTP_200_OK,
                message="Payment already verified.",
                data={
                    "transaction_reference": txn.reference,
                    "amount": txn.amount,
                    "currency": txn.currency,
                },
            )

        if flw_status == "cancelled":
            txn.verified = True
            txn.status = "CANCELLED"
            txn.meta.update({"description": f"FLW Escrow Transaction cancelled"})
            txn.save()

            description = f"Payment was cancelled."
            log_transaction_activity(txn, description, request_meta)

            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Payment was cancelled.",
            )

        if flw_status == "failed":
            txn.verified = True
            txn.status = "FAILED"
            txn.meta.update({"description": f"FLW Escrow Transaction failed"})
            txn.save()

            description = f"Payment failed."
            log_transaction_activity(txn, description, request_meta)

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
            txn.meta.update({"description": f"FLW Escrow Transaction {msg}"})
            txn.save()

            description = f"Error occurred while verifying escrow deposit transaction. Description: {msg}"
            log_transaction_activity(txn, description, request_meta)

            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                message=msg,
            )

        if obj["data"]["status"] == "failed":
            msg = obj["data"]["processor_response"]
            txn.meta.update({"description": f"FLW Escrow Transaction {msg}"})
            txn.save()

            description = f"Transaction failed. Description: {msg}"
            log_transaction_activity(txn, description, request_meta)

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
            escrow_txn_ref = obj["data"]["meta"]["escrow_transaction_reference"]
            escrow_txn = Transaction.objects.filter(reference=escrow_txn_ref).first()
            escrow_txn.verified = True
            escrow_txn.status = "SUCCESSFUL"
            escrow_txn.save()
            escrow_amount_to_charge = int(escrow_txn.amount + escrow_txn.charge)

            flw_ref = obj["data"]["flw_ref"]
            narration = obj["data"]["narration"]
            txn.verified = True
            txn.status = "SUCCESSFUL"
            txn.mode = obj["data"]["auth_model"]
            txn.charge = obj["data"]["app_fee"]
            txn.remitted_amount = obj["data"]["amount_settled"]
            txn.provider_tx_reference = flw_ref
            txn.narration = narration
            payment_type = obj["data"]["payment_type"]
            txn.meta.update(
                {
                    "payment_method": payment_type,
                    "provider_txn_id": obj["data"]["id"],
                    "description": f"FLW Escrow Transaction {narration}_{flw_ref}",
                }
            )
            txn.save()

            customer_email = obj["data"]["customer"]["email"]
            amount_charged = obj["data"]["charged_amount"]

            description = f"Payment received via {payment_type} channel. Escrow deposit transaction verified via REDIRECT URL."
            log_transaction_activity(txn, description, request_meta)

            try:
                user = User.objects.filter(email=customer_email).first()
                _, wallet = user.get_currency_wallet(txn.currency)

                description = f"Previous User Balance: {txn.currency} {add_commas_to_transaction_amount(wallet.balance)}"
                log_transaction_activity(txn, description, request_meta)

                profile = user.userprofile
                buyer_free_escrow_credits = int(profile.free_escrow_transactions)
                escrow_credits_used = False
                if buyer_free_escrow_credits > 0:
                    # deplete free credits and make transaction free
                    profile.free_escrow_transactions -= 1
                    profile.save()
                    escrow_amount_to_charge = escrow_txn.amount
                    escrow_credits_used = True

                user.credit_wallet(amount_charged, txn.currency)

                _, wallet = user.get_currency_wallet(txn.currency)
                description = f"User Balance after topup: {txn.currency} {add_commas_to_transaction_amount(wallet.balance)}"
                log_transaction_activity(txn, description, request_meta)

                user.debit_wallet(escrow_amount_to_charge, txn.currency)

                _, wallet = user.get_currency_wallet(txn.currency)
                description = f"New User Balance after final debit: {txn.currency} {add_commas_to_transaction_amount(wallet.balance)}"
                log_transaction_activity(txn, description, request_meta)

                # =================================================================
                # ESCROW TRANSACTION ACTIVITY
                escrow_credits_message = " " if escrow_credits_used else " not "
                description = (
                    f"{escrow_txn.currency} {add_commas_to_transaction_amount(escrow_txn.amount)} was locked successfully by buyer: {(user.name).upper()} <{user.email}> via direct wallet debit. Escrow credit was"
                    + escrow_credits_message
                    + f"used by buyer."
                )
                log_transaction_activity(escrow_txn, description, request_meta)
                # ESCROW TRANSACTION ACTIVITY
                # =================================================================

                user.update_locked_amount(
                    amount=escrow_txn.amount,
                    currency=txn.currency,
                    mode="OUTWARD",
                    type="CREDIT",
                )

                instance = LockedAmount.objects.create(
                    transaction=escrow_txn,
                    user=user,
                    seller_email=(
                        escrow_txn.escrowmeta.partner_email
                        if escrow_txn.escrowmeta.author == "BUYER"
                        else escrow_txn.user_id.email
                    ),
                    amount=escrow_txn.amount,
                    status="ESCROW",
                )
                escrow_amount = add_commas_to_transaction_amount(escrow_txn.amount)
                buyer_values = {
                    "first_name": user.name.split(" ")[0],
                    "recipient": user.email,
                    "date": parse_datetime(escrow_txn.updated_at),
                    "amount_funded": f"{txn.currency} {escrow_amount}",
                    "transaction_id": escrow_txn.reference,
                    "item_name": escrow_txn.meta["title"],
                    # "seller_name": seller.name,
                }
                # Only notify seller at this point if they initiated the transaction.
                # If the buyer initiated, then the seller will be notified when they approve the transaction.
                # This may not be immediate. Seller may take a while to approve the transaction.
                # So we just default to use the created_at timestamp on LockedAmount instance above as time to avoid incorrect timestamps when email is sent out
                if escrow_txn.escrowmeta.author == "SELLER":
                    seller = escrow_txn.user_id
                    # seller.userprofile.locked_amount += int(escrow_txn.amount)
                    # seller.userprofile.save()
                    seller.update_locked_amount(
                        amount=escrow_txn.amount,
                        currency=escrow_txn.currency,
                        mode="INWARD",
                        type="CREDIT",
                    )

                    seller_values = {
                        "first_name": seller.name.split(" ")[0],
                        "recipient": seller.email,
                        "date": parse_datetime(escrow_txn.updated_at),
                        "amount_funded": f"{escrow_txn.currency} {escrow_amount}",
                        "transaction_id": escrow_txn.reference,
                        "item_name": escrow_txn.meta["title"],
                        "buyer_name": user.name,
                    }
                    txn_tasks.send_lock_funds_seller_email.delay(
                        seller.email, seller_values
                    )
                    # Create Notification for Seller
                    UserNotification.objects.create(
                        user=seller,
                        category="FUNDS_LOCKED_SELLER",
                        title=notifications.FundsLockedSellerNotification(
                            escrow_amount, escrow_txn.currency
                        ).TITLE,
                        content=notifications.FundsLockedSellerNotification(
                            escrow_amount, escrow_txn.currency
                        ).CONTENT,
                        action_url=f"{BACKEND_BASE_URL}/v1/transaction/link/{escrow_txn_ref}",
                    )

                txn_tasks.send_lock_funds_buyer_email.delay(user.email, buyer_values)
                #  Create Notification for Buyer
                UserNotification.objects.create(
                    user=user,
                    category="FUNDS_LOCKED_BUYER",
                    title=notifications.FundsLockedBuyerNotification(
                        escrow_amount, escrow_txn.currency
                    ).TITLE,
                    content=notifications.FundsLockedBuyerNotification(
                        escrow_amount, escrow_txn.currency
                    ).CONTENT,
                    action_url=f"{BACKEND_BASE_URL}/v1/transaction/link/{escrow_txn_ref}",
                )
            # TODO: Send real-time Notification
            except User.DoesNotExist:
                return Response(
                    success=False,
                    message="User not found",
                    status_code=status.HTTP_404_NOT_FOUND,
                )
            return Response(
                success=True,
                status_code=status.HTTP_200_OK,
                data={
                    "transaction_reference": escrow_txn_ref,
                    "amount": escrow_amount_to_charge,
                    "currency": txn.currency,
                },
                message="Transaction verified.",
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
        user = request.user
        request_meta = extract_api_request_metadata(request)
        profile = user.userprofile
        if profile.is_flagged or profile.is_deactivated:
            return Response(
                success=False,
                status_code=status.HTTP_403_FORBIDDEN,
                message="Account restricted.",
            )
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
        currency = data.get("currency", "NGN")

        charge, total_amount = get_withdrawal_fee(int(amount))

        valid, message = user.validate_wallet_withdrawal_amount(total_amount, currency)
        if not valid:
            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                message=message,
            )

        tx_ref = (
            f"{generate_txn_reference()}_PMCKDU_1"
            if env == "test"
            else f"{generate_txn_reference()}_TRF"
        )
        email = user.email

        txn = Transaction.objects.create(
            user_id=request.user,
            type="WITHDRAW",
            amount=amount,
            charge=charge,
            status="PENDING",
            reference=tx_ref,
            currency=currency,
            provider="FLUTTERWAVE",
            meta={"title": "Wallet debit"},
        )

        description = f"{(user.name).upper()} initiated withdrawal of {currency} {add_commas_to_transaction_amount(amount)} from wallet."
        log_transaction_activity(txn, description, request_meta)

        # https://developer.flutterwave.com/docs/making-payments/transfers/overview/
        tx_data = {
            "account_bank": bank_code,
            "account_number": account_number,
            "amount": int(amount),
            "narration": description if description else "MyBalance TRF",
            "reference": tx_ref,
            "currency": currency,
            "meta": {
                "amount_to_debit": total_amount,
                "customer_email": user.email,
                "tx_ref": tx_ref,
            },
            # "callback_url": f"{BACKEND_BASE_URL}/v1/shared/withdraw-callback",
        }

        obj = self.flw_api.initiate_payout(tx_data)
        print("================================================================")
        print("================================================================")
        print("FLUTTTERWAVE TRANSFER API CALLED")
        print("Response DATA---->", obj)
        print("================================================================")
        print("================================================================")
        if obj["status"] == "error":
            msg = obj["message"]
            txn.meta.update({"description": f"FLW Transaction: {tx_ref}", "note": msg})
            txn.save()

            description = f"Withdrawal initiation failed. Description: {msg}"
            log_transaction_activity(txn, description, request_meta)

            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                message=msg,
            )
        msg = obj["message"]
        txn.meta.update({"description": f"FLW Transaction {tx_ref}", "note": msg})
        txn.save()

        description = f"Withdrawal successfully queued on {PAYMENT_GATEWAY_PROVIDER}."
        log_transaction_activity(txn, description, request_meta)

        return Response(
            success=True,
            message="Withdrawal is currently being processed",
            status_code=status.HTTP_200_OK,
            data={"transaction_reference": tx_ref},
        )


class WalletWithdrawalCallbackView(GenericAPIView):
    serializer_class = FlwTransferCallbackSerializer
    permission_classes = [AllowAny]
    pusher = PusherSocket()

    @swagger_auto_schema(
        operation_description="Callback for FLW PAYOUT to Bank Account",
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
        print("================================================================")
        print("FLUTTERWAVE WEBHOOK/CALLBACK V1 FUNCTION CALLED")
        print("REQUEST DATA=========>", request.data)
        print("================================================================")
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors,
            )
        transfer_data = serializer.validated_data.get("transfer")
        data_data = serializer.validated_data.get("data")

        if transfer_data is not None:
            # 'transfer' field was provided in the request
            data = transfer_data
        elif data_data is not None:
            # 'data' field was provided in the request
            data = data_data
        else:
            # Both fields were provided, choose one (here, 'transfer' is chosen)
            data = transfer_data

        amount_charged = data.get("amount")
        msg = data.get("complete_message")
        amount_to_debit = data["meta"].get("amount_to_debit")
        customer_email = data["meta"].get("customer_email")
        tx_ref = data["meta"].get("tx_ref")

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
                success=True,
                status_code=status.HTTP_200_OK,
                message="Transfer already verified",
            )

        if data["status"] == "FAILED":
            txn.status = "FAILED"
            txn.meta.update({"note": msg})
            txn.verified = True
            txn.save()

            self.pusher.trigger(
                f"WALLET_WITHDRAWAL_{tx_ref}",
                "WALLET_WITHDRAWAL_FAILURE",
                {
                    "status": "FAILED",
                    "message": msg,
                    "amount": txn.amount,
                    "currency": txn.currency,
                },
            )

            return Response(
                success=True,
                message="Callback processed successfully.",
                status_code=status.HTTP_200_OK,
            )

        try:
            user = User.objects.get(email=customer_email)
            user.debit_wallet(amount_to_debit, txn.currency)
            user.update_withdrawn_amount(
                amount=txn.amount,
                currency=txn.currency,
            )

            self.pusher.trigger(
                f"WALLET_WITHDRAWAL_{tx_ref}",
                "WALLET_WITHDRAWAL_SUCCESS",
                {
                    "status": "SUCCESSFUL",
                    "message": msg,
                    "amount": txn.amount,
                    "currency": txn.currency,
                },
            )

            txn.status = "SUCCESSFUL"
            txn.meta.update({"note": msg})
            txn.verified = True
            txn.save()

            email = user.email
            values = {
                "first_name": user.name.split(" ")[0],
                "recipient": email,
                "transaction_reference": (txn.reference).upper(),
                "amount_withdrawn": f"{txn.currency} {add_commas_to_transaction_amount(txn.amount)}",
                "date": parse_datetime(txn.created_at),
                "bank_name": data.get("bank_name"),
                "account_name": data.get("fullname"),
                "account_number": data.get("account_number"),
            }
            console_tasks.send_wallet_withdrawal_email.delay(email, values)

            # Create Notification
            UserNotification.objects.create(
                user=user,
                category="WITHDRAWAL",
                title=notifications.WalletWithdrawalNotification(
                    txn.amount, txn.currency
                ).TITLE,
                content=notifications.WalletWithdrawalNotification(
                    txn.amount, txn.currency
                ).CONTENT,
                action_url=f"{BACKEND_BASE_URL}/v1/transaction/link/{tx_ref}",
            )
            # TODO: Send real-time Notification
        except User.DoesNotExist:
            return Response(
                success=False,
                message="User not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return Response(
            success=True,
            message="Withdrawal callback processed successfully.",
            status_code=status.HTTP_200_OK,
        )
