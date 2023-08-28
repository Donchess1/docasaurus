from django.contrib.auth import get_user_model
from django.db.models import Q
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated

from console import tasks
from console.models.dispute import Dispute
from dispute.serializers.dispute import DisputeSerializer
from transaction.pagination import LargeResultsSetPagination
from utils.response import Response

User = get_user_model()


class UserDisputeView(generics.ListCreateAPIView):
    serializer_class = DisputeSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = LargeResultsSetPagination

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
        response = self.get_paginated_response(serializer.data)
        return Response(
            success=True,
            message="User's disputes retrieved successfully",
            status_code=status.HTTP_200_OK,
            data=response.data,
        )

    @swagger_auto_schema(
        operation_description="Create a new dispute for an Authenticated User",
        request_body=DisputeSerializer,
        responses={
            201: DisputeSerializer,
        },
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data, context={"user": request.user}
        )
        if not serializer.is_valid():
            return Response(
                success=False,
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        dispute = serializer.save()
        # TODO: Send appropriate notification to the seller and buyer

        return Response(
            success=True,
            message="Dispute created successfully",
            status_code=status.HTTP_201_CREATED,
            data=serializer.data,
        )
