import os
import uuid
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db.models import Q
from drf_yasg.utils import swagger_auto_schema
from rest_framework import filters, generics, status, views
from rest_framework.permissions import AllowAny, BasePermission, IsAuthenticated

from console.models.transaction import LockedAmount, Transaction
from core.resources.flutterwave import FlwAPI
from transaction import tasks
from transaction.permissions import IsBuyer, IsTransactionStakeholder
from transaction.serializers.transaction import (
    EscrowTransactionPaymentSerializer,
    EscrowTransactionSerializer,
    FundEscrowTransactionSerializer,
    UnlockEscrowTransactionSerializer,
)
from transaction.serializers.user import (
    UpdateEscrowTransactionSerializer,
    UserTransactionSerializer,
)
from users.models import UserProfile
from utils.html import generate_flw_payment_webhook_html
from utils.pagination import CustomPagination
from utils.response import Response
from utils.transaction import get_escrow_transaction_stakeholders
from utils.utils import generate_txn_reference, parse_datetime

User = get_user_model()
BACKEND_BASE_URL = os.environ.get("BACKEND_BASE_URL", "")
FRONTEND_BASE_URL = os.environ.get("FRONTEND_BASE_URL", "")


class UserTransactionListView(generics.ListAPIView):
    serializer_class = UserTransactionSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = CustomPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ["reference", "provider", "type"]

    def get_queryset(self):
        user = self.request.user
        # Transactions where user is the main user or user is involved in escrow
        queryset = Transaction.objects.filter(
            Q(user_id=user) | Q(escrowmeta__partner_email=user.email)
        ).order_by("-created_at")
        return queryset

    @swagger_auto_schema(
        operation_description="List all transactions for an Authenticated User",
        responses={
            200: UserTransactionSerializer,
        },
    )
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        qs = self.paginate_queryset(queryset)
        serializer = self.get_serializer(qs, many=True)
        self.pagination_class.message = "User's transactions retrieved successfully"
        response = self.get_paginated_response(serializer.data)
        return response


class UserLockedEscrowTransactionListView(generics.ListAPIView):
    serializer_class = UserTransactionSerializer
    permission_classes = [IsBuyer]
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user
        # Escow Transactions locked by the Buyer
        queryset = Transaction.objects.filter(
            Q(user_id=user) | Q(escrowmeta__partner_email=user.email),
            type="ESCROW",
            status="SUCCESSFUL",
        ).order_by("created_at")

        return queryset

    @swagger_auto_schema(
        operation_description="List all transactions locked in escrow for a Buyer",
        responses={
            200: UserTransactionSerializer,
        },
    )
    def list(self, request, *args, **kwargs):
        if not request.user.is_buyer:
            return Response(
                success=False,
                status_code=status.HTTP_403_FORBIDDEN,
                message="You do not have permission to perform this action",
            )
        queryset = self.filter_queryset(self.get_queryset())
        qs = self.paginate_queryset(queryset)
        serializer = self.get_serializer(qs, many=True)
        self.pagination_class.message = ("User's transactions retrieved successfully",)
        response = self.get_paginated_response(serializer.data)
        return response


class UserTransactionDetailView(generics.GenericAPIView):
    serializer_class = UserTransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self, *args, **kwargs):
        if self.request.method == "PATCH":
            return UpdateEscrowTransactionSerializer
        return self.serializer_class

    def get_queryset(self):
        return Transaction.objects.all()

    def get_transaction_instance(self, ref_or_id):
        instance = self.get_queryset().filter(reference=ref_or_id).first()
        if instance is None:
            try:
                instance = self.get_queryset().filter(id=ref_or_id).first()
            except Exception as e:
                instance = None
        return instance

    @swagger_auto_schema(
        operation_description="Get a transaction detail by ID or Reference",
        responses={
            200: UserTransactionSerializer,
        },
    )
    def get(self, request, id, *args, **kwargs):
        instance = self.get_transaction_instance(id)
        if not instance:
            return Response(
                success=False,
                message="Transaction does not exist",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        if instance.status == "ESCROW":
            stakeholders = get_escrow_transaction_stakeholders(id)
            if request.user.email not in stakeholders.values():
                return Response(
                    success=False,
                    status_code=status.HTTP_403_FORBIDDEN,
                    message="You do not have permission to perform this action",
                )

        serializer = self.get_serializer(instance)
        return Response(
            success=True,
            message="Transaction detail retrieved successfully.",
            status_code=status.HTTP_200_OK,
            data=serializer.data,
        )

    @swagger_auto_schema(
        operation_description="Update ESCROW transaction status to 'APPROVED' or 'REJECTED'",
    )
    def patch(self, request, id, *args, **kwargs):
        instance = self.get_transaction_instance(id)
        if not instance:
            return Response(
                success=False,
                message="Transaction does not exist",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        if instance.type != "ESCROW":
            return Response(
                success=False,
                message=f"{instance.type} transactions cannot be updated",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        if request.user.email != instance.escrowmeta.partner_email:
            return Response(
                success=False,
                status_code=status.HTTP_403_FORBIDDEN,
                message="You do not have permission to update this escrow transaction",
            )
        escrow_action = instance.meta.get("escrow_action", None)
        if escrow_action:
            return Response(
                success=False,
                message=f"Escrow transaction cannot be updated again",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                success=False,
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        new_status = serializer.validated_data.get("status")
        rejected_reason = serializer.validated_data.get("rejected_reason")

        instance.status = new_status
        instance.meta.update(
            {
                "escrow_action": new_status,
                "rejected_reason": list(rejected_reason) if rejected_reason else None,
            }
        )
        instance.save()
        # If status is approved, then
        # If status is REJECTED and the author is buyer, refund the escrow funds to the buyer.
        return Response(
            success=True,
            message=f"Escrow transaction {new_status.lower()}",
            status_code=status.HTTP_200_OK,
        )


class TransactionDetailView(generics.GenericAPIView):
    serializer_class = UserTransactionSerializer
    permission_classes = (AllowAny,)

    def get_queryset(self):
        return Transaction.objects.all()

    def get_transaction_instance(self, ref_or_id):
        instance = self.get_queryset().filter(reference=ref_or_id).first()
        if instance is None:
            try:
                instance = self.get_queryset().filter(id=ref_or_id).first()
            except Exception as e:
                instance = None
        return instance

    @swagger_auto_schema(
        operation_description="Console: Get a transaction detail by ID or Reference",
        responses={
            200: UserTransactionSerializer,
        },
    )
    def get(self, request, id, *args, **kwargs):
        instance = self.get_transaction_instance(id)
        if not instance:
            return Response(
                success=False,
                message="Transaction does not exist",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        serializer = self.get_serializer(instance)
        return Response(
            success=True,
            message="Transaction detail retrieved successfully.",
            status_code=status.HTTP_200_OK,
            data=serializer.data,
        )


class InitiateEscrowTransactionView(generics.CreateAPIView):
    serializer_class = EscrowTransactionSerializer
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(
        operation_description="Initiate Escrow Transaction",
        responses={
            200: UserTransactionSerializer,
        },
    )
    def perform_create(self, serializer):
        return serializer.save()

    def post(self, request):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        if not serializer.is_valid():
            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors,
            )

        instance = self.perform_create(serializer)
        obj = UserTransactionSerializer(instance)
        return Response(
            success=True,
            message="Escrow transaction created successfully.",
            status_code=status.HTTP_200_OK,
            data=obj.data,
        )


class LockEscrowFundsView(generics.CreateAPIView):
    serializer_class = EscrowTransactionPaymentSerializer
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(
        operation_description="Lock funds for escrow transaction as a buyer",
    )
    def post(self, request):
        user = request.user
        try:
            profile = UserProfile.objects.get(user_id=user)
        except UserProfile.DoesNotExist:
            return Response(
                success=False,
                message="User Profile does not exist",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors,
            )
        reference = serializer.validated_data.get("transaction_reference")

        # Validate permissions: Only the associated buyer can lock funds
        stakeholders = get_escrow_transaction_stakeholders(reference)
        if request.user.email != stakeholders["BUYER"]:
            return Response(
                success=False,
                status_code=status.HTTP_403_FORBIDDEN,
                message="You do not have permission to perform this action",
            )

        txn = Transaction.objects.get(reference=reference)
        deficit = (txn.amount + txn.charge) - profile.wallet_balance
        if deficit <= 0:
            txn.status = "SUCCESSFUL"
            txn.verified = True
            txn.save()

            instance = LockedAmount.objects.create(
                transaction=txn,
                user=user,
                seller_email=txn.escrowmeta.partner_email
                if txn.escrowmeta.author == "BUYER"
                else txn.user_id.email,
                amount=txn.amount,
                status="ESCROW",
            )
            instance.save()

            amount_to_debit = int(txn.amount + txn.charge)
            profile.wallet_balance -= Decimal(str(amount_to_debit))
            profile.locked_amount += int(txn.amount)
            profile.save()

            buyer_values = {
                "first_name": user.name.split(" ")[0],
                "recipient": user.email,
                "date": parse_datetime(txn.updated_at),
                "amount_funded": f"N{txn.amount}",
                "transaction_id": reference,
                "item_name": txn.meta["title"],
                # "seller_name": seller.name,
            }

            if txn.escrowmeta.author == "SELLER":
                seller = txn.user_id
                seller_values = {
                    "first_name": seller.name.split(" ")[0],
                    "recipient": seller.email,
                    "date": parse_datetime(txn.updated_at),
                    "amount_funded": f"N{txn.amount}",
                    "transaction_id": reference,
                    "item_name": txn.meta["title"],
                    "buyer_name": user.name,
                }
                # Notify both buyer and seller of payment details
                tasks.send_lock_funds_seller_email(seller.email, seller_values)
                tasks.send_lock_funds_buyer_email(user.email, buyer_values)
            else:
                tasks.send_lock_funds_buyer_email(user.email, buyer_values)
            return Response(
                status=True,
                message="Funds locked successfully",
                status_code=status.HTTP_200_OK,
                data={"transaction_reference": reference},
            )
        return Response(
            success=False,
            message="Insufficient funds in wallet.",
            status_code=status.HTTP_200_OK,
            errors={
                "deficit": abs(deficit),
                "message": "Insufficient funds in wallet.",
            },
        )


class FundEscrowTransactionView(generics.GenericAPIView):
    serializer_class = FundEscrowTransactionSerializer
    permission_classes = (IsAuthenticated,)
    flw_api = FlwAPI

    def get_queryset(self):
        return Transaction.objects.all()

    def get_transaction_instance(self, ref_or_id):
        instance = self.get_queryset().filter(reference=ref_or_id).first()
        if instance is None:
            try:
                instance = self.get_queryset().filter(id=ref_or_id).first()
            except Exception as e:
                instance = None
        return instance

    @swagger_auto_schema(
        operation_description="Fund escrow transaction with Payment Gateway",
    )
    def post(self, request):
        user = request.user
        ref = request.data.get("transaction_reference", None)
        instance = self.get_transaction_instance(ref)
        if not instance:
            return Response(
                success=False,
                message="Transaction does not exist",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        stakeholders = get_escrow_transaction_stakeholders(ref)
        if request.user.email != stakeholders["BUYER"]:
            return Response(
                success=False,
                status_code=status.HTTP_403_FORBIDDEN,
                message="You do not have permission to perform this action",
            )

        serializer = self.serializer_class(data=request.data, context={"user": user})
        if not serializer.is_valid():
            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors,
            )
        data = serializer.validated_data
        amount = data.get("amount_to_charge")
        escrow_transaction_reference = data.get("transaction_reference")

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
            "redirect_url": f"{BACKEND_BASE_URL}/v1/shared/escrow-payment-redirect",
            "customer": {
                "email": user.email,
                "phone_number": user.phone,
                "name": user.name,
            },
            "customizations": {
                "title": "MyBalance",
                "logo": "https://res.cloudinary.com/devtosxn/image/upload/v1686595168/197x43_mzt3hc.png",
            },
            "meta": {
                "escrow_transaction_reference": escrow_transaction_reference,
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
            message="Escrow payment successfully initialized",
            status_code=status.HTTP_200_OK,
            data=payload,
        )


class UnlockEscrowFundsView(generics.CreateAPIView):
    serializer_class = UnlockEscrowTransactionSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return Transaction.objects.all()

    def get_transaction_instance(self, ref_or_id):
        instance = self.get_queryset().filter(reference=ref_or_id).first()
        if instance is None:
            try:
                instance = self.get_queryset().filter(id=ref_or_id).first()
            except Exception as e:
                instance = None
        return instance

    @swagger_auto_schema(
        operation_description="Unlock funds for a Escrow Transaction as a Buyer",
        responses={
            200: UserTransactionSerializer,
        },
    )
    def post(self, request):
        user = request.user
        ref = request.data.get("transaction_reference", None)
        instance = self.get_transaction_instance(ref)
        if not instance:
            return Response(
                success=False,
                message="Transaction does not exist",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        stakeholders = get_escrow_transaction_stakeholders(ref)
        if request.user.email != stakeholders["BUYER"]:
            return Response(
                success=False,
                status_code=status.HTTP_403_FORBIDDEN,
                message="You do not have permission to perform this action",
            )
        try:
            profile = UserProfile.objects.get(user_id=user)
        except UserProfile.DoesNotExist:
            return Response(
                success=False,
                message="User Profile does not exist",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors,
            )
        reference = serializer.validated_data.get("transaction_reference")
        try:
            txn = Transaction.objects.get(reference=reference)
            txn.status = "FUFILLED"
            txn.save()

            # Move amount from Buyer's Locked Balance to Unlocked Balance
            profile.locked_amount -= Decimal(str(txn.amount))
            profile.unlocked_amount += int(txn.amount)
            profile.save()

            instance = LockedAmount.objects.get(transaction=txn)

            # Credit amount to Seller's wallet balance after deducting applicable escrow fees
            seller = User.objects.get(email=instance.seller_email)
            amount_to_credit_seller = int(txn.amount - txn.charge)
            seller_profile = UserProfile.objects.get(user_id=seller)
            seller_profile.wallet_balance += int(amount_to_credit_seller)
            seller_profile.save()

            instance.status = "SETTLED"
            instance.save()

            # TODO: Notify Buyer & Seller that funds has been unlocked from escrow via email.

            return Response(
                status=True,
                message="Funds unlocked successfully",
                status_code=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                status=False,
                message=f"Exception occurred: {str(e)}",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
