from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status

from console.models import Dispute, EmailLog, Transaction
from console.permissions import IsSuperAdmin
from console.serializers.dispute import DisputeSummarySerializer
from console.serializers.transaction import TransactionEntitySchemaSerializer, DisputeEntitySchemaSerializer
from console.serializers.user import UserSummarySerializer
from console.services.transaction_chart import TransactionChartDataHandler
from console.utils import (
    DEPOSIT_STATES,
    DISPUTE_STATES,
    ESCROW_STATES,
    MERCHANT_SETTLEMENT_STATES,
    TRANSACTION_TYPES,
    WITHDRAW_STATES,
    get_aggregated_system_dispute_data_by_type,
    get_aggregated_system_email_log_data_by_provider,
    get_aggregated_system_transaction_data_by_type,
    get_time_range_from_period,
)
from utils.response import Response
from utils.utils import SYSTEM_CURRENCIES

User = get_user_model()


class TransactionSchemaView(generics.GenericAPIView):
    permission_classes = (IsSuperAdmin,)
    serializer_class = TransactionEntitySchemaSerializer

    def get(self, request):
        transaction_type_map = {
            "DEPOSIT": DEPOSIT_STATES[:-1],
            "WITHDRAW": WITHDRAW_STATES[:-1],
            "ESCROW": ESCROW_STATES[:-1],
            "MERCHANT_SETTLEMENT": MERCHANT_SETTLEMENT_STATES[:-1],
            "SETTLEMENT": MERCHANT_SETTLEMENT_STATES[:-1],
            "PRODUCT": MERCHANT_SETTLEMENT_STATES[:-1],
        }
        data = {
            "entity": "TRANSACTION",
            "type": [
                "DEPOSIT",
                "WITHDRAW",
                "ESCROW",
                "MERCHANT_SETTLEMENT",
                "SETTLEMENT",
                "PRODUCT",
            ],
            "mode": ["MERCHANT_API", "WEB"],
            "hierarchy_map": {
                "parent_field": "TYPE",
                "child_field": "STATUS",
                "schema": transaction_type_map,
            },
        }
        return Response(
            success=True,
            message="Transaction schema retrieved successfully",
            data=data,
            status_code=status.HTTP_200_OK,
        )


class DisputeSchemaView(generics.GenericAPIView):
    permission_classes = (IsSuperAdmin,)
    serializer_class = DisputeEntitySchemaSerializer

    def get(self, request):
        data = {
            "entity": "DISPUTE",
            "source": ["PLATFORM", "API"],
            "status": ["PENDING", "RESOLVED", "REJECTED", "PROGRESS"],
            "priority": ["HIGH", "MEDIUM", "LOW"],
            "author": ["BUYER", "SELLER"],
        }
        return Response(
            success=True,
            message="Transaction schema retrieved successfully",
            data=data,
            status_code=status.HTTP_200_OK,
        )
