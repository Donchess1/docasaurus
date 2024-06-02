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
from utils.html import generate_flw_payment_webhook_html
from utils.response import Response
from utils.text import notifications
from utils.utils import (
    add_commas_to_transaction_amount,
    calculate_payment_amount_to_charge,
    generate_txn_reference,
    get_withdrawal_fee,
    parse_datetime,
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
                message=f"FLW Err: {msg}",
            )

        if obj["data"]["status"] == "failed":
            msg = obj["data"]["processor_response"]
            txn.meta.update({"description": f"FLW Transaction {msg}"})
            txn.save()
            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                message=f"FLW Failed: {msg}",
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
                profile.wallet_balance += int(txn.amount)
                profile.save()

                email = user.email
                values = {
                    "first_name": user.name.split(" ")[0],
                    "recipient": email,
                    "date": parse_datetime(txn.created_at),
                    "amount_funded": f"NGN {add_commas_to_transaction_amount(txn.amount)}",
                    "wallet_balance": f"NGN {add_commas_to_transaction_amount(str(profile.wallet_balance))}",
                    "transaction_reference": f"{(txn.reference).upper()}",
                }
                console_tasks.send_fund_wallet_email.delay(email, values)
                # Create Notification
                UserNotification.objects.create(
                    user=user,
                    category="DEPOSIT",
                    title=notifications.WalletDepositNotification(txn.amount).TITLE,
                    content=notifications.WalletDepositNotification(txn.amount).CONTENT,
                    action_url=f"{BACKEND_BASE_URL}/v1/transaction/link/{tx_ref}",
                )

                # TODO: Send real-time Notification
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


class FundEscrowTransactionRedirectView(GenericAPIView):
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
            txn.meta.update({"description": f"FLW Escrow Transaction cancelled"})
            txn.save()
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
        print("FLW TRANSACTION VALIDATION VIA API ----->", obj)

        if obj["status"] == "error":
            msg = obj["message"]
            txn.meta.update({"description": f"FLW Escrow Transaction {msg}"})
            txn.save()
            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                message=f"{msg}[]",
            )

        if obj["data"]["status"] == "failed":
            msg = obj["data"]["processor_response"]
            txn.meta.update({"description": f"FLW Escrow Transaction {msg}"})
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
            txn.meta.update(
                {
                    "payment_method": obj["data"]["payment_type"],
                    "provider_txn_id": obj["data"]["id"],
                    "description": f"FLW Escrow Transaction {narration}_{flw_ref}",
                }
            )
            txn.save()

            customer_email = obj["data"]["customer"]["email"]
            amount_charged = obj["data"]["charged_amount"]

            try:
                user = User.objects.get(email=customer_email)
                profile = UserProfile.objects.get(user_id=user)
                profile.wallet_balance += int(amount_charged)
                profile.locked_amount += int(escrow_txn.amount)
                profile.save()
                profile.wallet_balance -= Decimal(str(escrow_amount_to_charge))
                profile.save()

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
                instance.save()
                escrow_amount = add_commas_to_transaction_amount(escrow_txn.amount)
                buyer_values = {
                    "first_name": user.name.split(" ")[0],
                    "recipient": user.email,
                    "date": parse_datetime(escrow_txn.updated_at),
                    "amount_funded": f"NGN {escrow_amount}",
                    "transaction_id": escrow_txn.reference,
                    "item_name": escrow_txn.meta["title"],
                    # "seller_name": seller.name,
                }

                if escrow_txn.escrowmeta.author == "SELLER":
                    seller = escrow_txn.user_id
                    seller_values = {
                        "first_name": seller.name.split(" ")[0],
                        "recipient": seller.email,
                        "date": parse_datetime(escrow_txn.updated_at),
                        "amount_funded": f"NGN {escrow_amount}",
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
                            escrow_amount
                        ).TITLE,
                        content=notifications.FundsLockedSellerNotification(
                            escrow_amount
                        ).CONTENT,
                        action_url=f"{BACKEND_BASE_URL}/v1/transaction/link/{escrow_txn_ref}",
                    )

                    txn_tasks.send_lock_funds_buyer_email.delay(
                        user.email, buyer_values
                    )
                else:
                    txn_tasks.send_lock_funds_buyer_email.delay(
                        user.email, buyer_values
                    )

                #  Create Notification for Buyer
                UserNotification.objects.create(
                    user=user,
                    category="FUNDS_LOCKED_BUYER",
                    title=notifications.FundsLockedBuyerNotification(
                        escrow_amount
                    ).TITLE,
                    content=notifications.FundsLockedBuyerNotification(
                        escrow_amount
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
            except UserProfile.DoesNotExist:
                return Response(
                    success=False,
                    message="Profile not found",
                    status_code=status.HTTP_404_NOT_FOUND,
                )
            retry_validation = self.flw_api.verify_transaction(flw_transaction_id)
            print("FLW TRANSACTION VALIDATION VIA API ----->", retry_validation)
            return Response(
                success=True,
                status_code=status.HTTP_200_OK,
                data={
                    "transaction_reference": escrow_txn_ref,
                    "amount": escrow_amount_to_charge,
                },
                message="Transaction verified.",
            )

        return Response(
            success=True,
            message="Payment successfully verified",
            status_code=status.HTTP_200_OK,
            data={"transaction_reference": tx_ref},
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

        if total_amount > profile.wallet_balance:
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
            # "callback_url": f"{BACKEND_BASE_URL}/v1/shared/withdraw-callback",
        }

        obj = self.flw_api.initiate_payout(tx_data)
        print("PAYOUT INIT OBJ:", obj)
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

        print("DATA FOR WALLET DEBIT:", obj["data"])

        return Response(
            success=True,
            message="Withdrawal is currently being processed",
            status_code=status.HTTP_200_OK,
            # data=obj["data"],
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
        print("WITHDRAW CALLBACK FUNCTION CALLED")
        print("REQUEST DATA---->", request.data)
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
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Withdrawal transaction already verified",
            )

        # TODO: LOG EVENT
        print("================================================")
        print("FLW WITHDRAWAL CALLBACK DATA", data)
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
                message="Callback processed successfully.",
                status_code=status.HTTP_200_OK,
            )

        try:
            user = User.objects.get(email=customer_email)
            profile = UserProfile.objects.get(user_id=user)
            profile.wallet_balance -= Decimal(str(amount_to_debit))
            profile.withdrawn_amount += int(txn.amount)
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

            email = user.email
            values = {
                "first_name": user.name.split(" ")[0],
                "recipient": email,
                "transaction_reference": (txn.reference).upper(),
                "amount_withdrawn": f"NGN {add_commas_to_transaction_amount(txn.amount)}",
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
                title=notifications.WalletWithdrawalNotification(txn.amount).TITLE,
                content=notifications.WalletWithdrawalNotification(txn.amount).CONTENT,
                action_url=f"{BACKEND_BASE_URL}/v1/transaction/link/{tx_ref}",
            )
            # TODO: Send real-time Notification
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
