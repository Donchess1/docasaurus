from rest_framework import generics, status

from console.models import Dispute, Transaction
from console.permissions import IsSuperAdmin
from console.serializers.dispute import DisputeSummarySerializer
from console.serializers.transaction import (
    DisputeEntitySchemaSerializer,
    TransactionEntitySchemaSerializer,
)
from console.utils import (
    DEPOSIT_STATES,
    DISPUTE_STATES,
    ESCROW_STATES,
    MERCHANT_SETTLEMENT_STATES,
    TRANSACTION_FILTER_FIELDS,
    TRANSACTION_STATUS,
    TRANSACTION_TYPES,
    WITHDRAW_STATES,
)
from utils.response import Response
from utils.utils import SYSTEM_CURRENCIES


class TransactionSchemaView(generics.GenericAPIView):
    permission_classes = (IsSuperAdmin,)
    serializer_class = TransactionEntitySchemaSerializer

    def get(self, request):
        transaction_type_map = {
            "DEPOSIT": {
                "status": DEPOSIT_STATES[:-1],
                "actions": {"view": DEPOSIT_STATES[:-1], "verify": ["PENDING"]},
            },
            "WITHDRAW": {
                "status": WITHDRAW_STATES[:-1],
                "actions": {
                    "view": WITHDRAW_STATES[:-1],
                },
            },
            "ESCROW": {
                "status": ESCROW_STATES[:-1],
                "actions": {"view": ESCROW_STATES[:-1], "revoke": ["SUCCESSFUL"]},
            },
            "MERCHANT_SETTLEMENT": {
                "status": MERCHANT_SETTLEMENT_STATES[:-1],
                "actions": {
                    "view": MERCHANT_SETTLEMENT_STATES[:-1],
                },
            },
            "SETTLEMENT": {
                "status": MERCHANT_SETTLEMENT_STATES[:-1],
                "actions": {
                    "view": MERCHANT_SETTLEMENT_STATES[:-1],
                },
            },
            "PRODUCT": {
                "status": MERCHANT_SETTLEMENT_STATES[:-1],
                "actions": {
                    "view": MERCHANT_SETTLEMENT_STATES[:-1],
                    "verify": ["PENDING"],
                },
            },
        }
        data = {
            "entity": "TRANSACTION",
            "type": TRANSACTION_TYPES,
            "mode": ["MERCHANT_API", "WEB"],
            "currency": SYSTEM_CURRENCIES,
            "filter_fields": TRANSACTION_FILTER_FIELDS,
            "schema": transaction_type_map,
            "obtainable_status": TRANSACTION_STATUS,
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
            "status": DISPUTE_STATES[:-1],
            "priority": ["HIGH", "MEDIUM", "LOW"],
            "currency": SYSTEM_CURRENCIES,
            "author": ["BUYER", "SELLER"],
            "actions": ["VIEW", "MARK_IN_PROGRESS", "RESOLVE"],
        }
        return Response(
            success=True,
            message="Transaction schema retrieved successfully",
            data=data,
            status_code=status.HTTP_200_OK,
        )
