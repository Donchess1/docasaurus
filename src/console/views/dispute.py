from decimal import Decimal
from datetime import datetime

from django.contrib.auth import get_user_model
from django.db.models import Q
from django_filters import rest_framework as django_filters
from drf_yasg.utils import swagger_auto_schema
from rest_framework import filters, generics, status
from rest_framework.permissions import IsAuthenticated

from console import tasks
from console.models.dispute import Dispute
from console.models.transaction import Transaction
from console.permissions import IsSuperAdmin
from console.serializers.base import EmptySerializer
from dispute import tasks as dispute_tasks
from dispute.filters import DisputeFilter
from dispute.serializers.dispute import DisputeSerializer, ResolveDisputeSerializer
from users.models import UserProfile
from utils.pagination import CustomPagination
from utils.response import Response
from utils.utils import parse_datetime

User = get_user_model()


class DisputeListView(generics.ListAPIView):
    serializer_class = DisputeSerializer
    permission_classes = (IsSuperAdmin,)
    pagination_class = CustomPagination
    filter_backends = [
        django_filters.DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = DisputeFilter
    search_fields = ["status", "reason", "priority", "description"]
    ordering_fields = ["status", "priority", "buyer", "seller", "created_at"]

    def get_queryset(self):
        return Dispute.objects.all().order_by("-created_at")

    @swagger_auto_schema(
        operation_description="List all disputes from DB",
        responses={
            200: DisputeSerializer,
        },
    )
    def get(self, request, *args, **kwargs):
        try:
            queryset = self.filter_queryset(self.get_queryset())
            qs = self.paginate_queryset(queryset)
            serializer = self.get_serializer(qs, many=True)
            self.pagination_class.message = "Disputes retrieved successfully"
            response = self.get_paginated_response(
                serializer.data,
            )
            return response
        except Exception as e:
            return Response(
                success=False,
                message=f"{str(e)}",
                status_code=status.HTTP_400_BAD_REQUEST,
            )


class DisputeDetailView(generics.GenericAPIView):
    serializer_class = DisputeSerializer
    permission_classes = (IsSuperAdmin,)

    def get_serializer_class(self, *args, **kwargs):
        if self.request.method == "PUT":
            return ResolveDisputeSerializer
        elif self.request.method == "PATCH":
            return EmptySerializer
        return self.serializer_class

    @swagger_auto_schema(
        operation_description="Get a dispute detail by ID",
        responses={
            200: DisputeSerializer,
        },
    )
    def get(self, request, id, *args, **kwargs):
        instance = Dispute.objects.filter(id=id).first()
        if not instance:
            return Response(
                success=False,
                message="Dispute does not exist",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        serializer = self.get_serializer(instance)
        return Response(
            success=True,
            message="Dispute retrieved successfully.",
            status_code=status.HTTP_200_OK,
            data=serializer.data,
        )

    @swagger_auto_schema(
        operation_description="Mark dispute as in progress",
    )
    def patch(self, request, id, *args, **kwargs):
        user = request.user
        instance = Dispute.objects.filter(id=id).first()
        if not instance:
            return Response(
                success=False,
                message="Dispute does not exist",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        if instance.status != "PENDING":
            return Response(
                success=False,
                message=f"Dispute with '{(instance.status).title()}' status cannot be marked as in progress.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        instance.status = "PROGRESS"
        instance.meta = {
            "in_progress_actor": request.user.email,
            "in_progress_timestamp": datetime.now().isoformat(),  # Convert datetime to ISO format string
        }
        instance.save()
        return Response(
            success=True,
            message=f"Dispute marked in progress successfuly",
            status_code=status.HTTP_200_OK,
        )

    @swagger_auto_schema(
        operation_description="Resolve dispute to either buyer or seller",
    )
    def put(self, request, id, *args, **kwargs):
        user = request.user
        instance = Dispute.objects.filter(id=id).first()
        if not instance:
            return Response(
                success=False,
                message="Dispute does not exist",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        if instance.status == "PENDING":
            return Response(
                success=False,
                message="Dispute yet to be marked as in progress",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        if instance.status == "RESOLVED":
            return Response(
                success=False,
                message="Dispute already resolved",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                success=False,
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        destination = serializer.validated_data.get("destination")
        transaction_author = instance.transaction.user_id

        seller, buyer = None, None
        if instance.transaction.escrowmeta.author == "BUYER":
            buyer = instance.transaction.user_id
            seller = User.objects.filter(
                email=instance.transaction.escrowmeta.partner_email
            ).first()
        else:
            seller = instance.transaction.user_id
            buyer = User.objects.filter(
                email=instance.transaction.escrowmeta.partner_email
            ).first()
        currency = instance.transaction.currency
        if destination == "BUYER":
            # Revert the transaction plus charges to the buyer wallet.
            # Move amount from locked funds to buyer wallet balance
            # Send email notification to buyer & seller
            amount_to_credit_buyer = int(
                instance.transaction.amount + instance.transaction.charge
            )
            profile = buyer.userprofile
            # profile.wallet_balance += int(amount_to_credit_buyer)
            # profile.locked_amount -= Decimal(str(instance.transaction.amount))
            # profile.save()
            buyer.credit_wallet(amount_to_credit_buyer, currency)
            buyer.update_locked_amount(
                amount=instance.transaction.amount,
                currency=currency,
                mode="OUTWARD",
                type="DEBIT",
            )
            # seller.userprofile.locked_amount -= Decimal(
            #     str(instance.transaction.amount)
            # )
            # seller.userprofile.save()
            seller.update_locked_amount(
                amount=instance.transaction.amount,
                currency=currency,
                mode="INWARD",
                type="DEBIT",
            )
        else:
            # Move amount from buyer Locked amount to unlocked amount
            # Move amount to seller wallet and remove charges only if there are no free transaction credit
            seller_free_escrow_credits = int(
                seller.userprofile.free_escrow_transactions
            )
            amount_to_credit_seller = int(
                instance.transaction.amount - instance.transaction.charge
            )
            if seller_free_escrow_credits > 0:
                seller.userprofile.free_escrow_transactions -= 1
                amount_to_credit_seller = int(instance.transaction.amount)

            # seller.userprofile.wallet_balance += amount_to_credit_seller
            # seller.userprofile.locked_amount -= Decimal(
            #     str(instance.transaction.amount)
            # )
            # seller.userprofile.save()
            seller.credit_wallet(amount_to_credit_seller, currency)
            seller.update_locked_amount(
                amount=instance.transaction.amount,
                currency=currency,
                mode="INWARD",
                type="DEBIT",
            )

            # buyer.userprofile.locked_amount -= int(instance.transaction.amount)
            # buyer.userprofile.unlocked_amount += int(instance.transaction.amount)
            # buyer.userprofile.save()
            buyer.update_locked_amount(
                amount=instance.transaction.amount,
                currency=currency,
                mode="OUTWARD",
                type="DEBIT",
            )
            buyer.update_unlocked_amount(
                amount=instance.transaction.amount,
                currency=currency,
                type="CREDIT",
            )

        instance.status = "RESOLVED"
        instance.meta = {"destination": destination, "admin": request.user.email}
        instance.save()

        return Response(
            success=True,
            message=f"Dispute resolved successfuly for {destination.upper()}",
            status_code=status.HTTP_200_OK,
        )
