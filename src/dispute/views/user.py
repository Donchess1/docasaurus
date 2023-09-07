from django.contrib.auth import get_user_model
from django.db.models import Q
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated

from console import tasks
from console.models.dispute import Dispute
from console.models.transaction import Transaction
from dispute.serializers.dispute import DisputeSerializer
from utils.pagination import CustomPagination
from utils.response import Response

User = get_user_model()


class UserDisputeView(generics.ListCreateAPIView):
    serializer_class = DisputeSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user
        queryset = Dispute.objects.filter(Q(buyer=user) | Q(seller=user)).order_by(
            "created_at"
        )
        return queryset

    @swagger_auto_schema(
        operation_description="List all disputes for an Authenticated User",
        responses={
            200: DisputeSerializer,
        },
    )
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        qs = self.paginate_queryset(queryset)
        serializer = self.get_serializer(qs, many=True)
        self.pagination_class.message = "User's disputes retrieved successfully"
        response = self.get_paginated_response(
            serializer.data,
        )
        return response

    @swagger_auto_schema(
        operation_description="Create a new dispute for an Authenticated User",
        request_body=DisputeSerializer,
        responses={
            201: DisputeSerializer,
        },
    )
    def create(self, request, *args, **kwargs):
        user = request.user
        serializer = self.get_serializer(
            data=request.data, context={"user": request.user}
        )
        if not serializer.is_valid():
            return Response(
                success=False,
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        transaction_id = serializer.validated_data.get("transaction")
        transaction = Transaction.objects.filter(id=str(transaction_id)).first()
        escrow_meta = transaction.escrowmeta
        locked_amount = transaction.lockedamount
        buyer = (
            transaction.user_id
            if escrow_meta.author == "BUYER"
            else User.objects.filter(email=escrow_meta.partner_email).first()
        )
        seller = User.objects.filter(email=locked_amount.seller_email).first()
        author = "BUYER" if user.is_buyer else "SELLER"
        priority = serializer.validated_data.get("priority")
        reason = serializer.validated_data.get("reason")
        description = serializer.validated_data.get("description")
        dispute = Dispute.objects.create(
            buyer=buyer,
            seller=seller,
            author=author,
            status="PENDING",
            transaction=transaction,
            priority=priority,
            description=description,
            reason=reason,
        )

        # TODO: Send appropriate notification to the seller and buyer

        return Response(
            success=True,
            message="Dispute created successfully",
            status_code=status.HTTP_201_CREATED,
            data=serializer.data,
        )
