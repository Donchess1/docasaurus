from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status

from console.models import Dispute, Transaction
from console.permissions import IsSuperAdmin
from console.serializers.dispute import DisputeSummarySerializer
from console.serializers.transaction import TransactionSummarySerializer
from console.serializers.user import UserSummarySerializer
from console.utils import (
    DEFAULT_CURRENCY,
    DEFAULT_PERIOD,
    DEPOSIT_STATES,
    DISPUTE_STATES,
    ESCROW_STATES,
    MERCHANT_SETTLEMENT_STATES,
    VALID_PERIODS,
    WITHDRAWAL_STATES,
    get_aggregated_system_dispute_data_by_type,
    get_aggregated_system_transaction_data_by_type,
    get_time_range_from_period,
)
from utils.response import Response
from utils.utils import SYSTEM_CURRENCIES

User = get_user_model()


class UserOverviewView(generics.GenericAPIView):
    permission_classes = (IsSuperAdmin,)
    serializer_class = UserSummarySerializer

    def get(self, request):
        period = request.query_params.get("period", DEFAULT_PERIOD).upper()
        if period and period not in VALID_PERIODS:
            return Response(
                success=False,
                message=f"Invalid period. Valid options are: {', '.join(VALID_PERIODS)}",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        period_time_range = get_time_range_from_period(period, request.query_params)
        if not period_time_range.get("success"):
            return Response(
                success=False,
                message=period_time_range.get("message"),
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        period_time_range = period_time_range.get("data", {})
        start_date = period_time_range.get("start_date", None)
        end_date = period_time_range.get("end_date", None)

        users = User.objects.all()

        if start_date and end_date:
            users = users.filter(created_at__range=(start_date, end_date))

        user_data = {
            "period": period,
            "start_date": start_date,
            "end_date": end_date,
            "total": users.count(),
            "buyers": users.filter(is_buyer=True).count(),
            "sellers": users.filter(is_seller=True).count(),
            "merchants": users.filter(is_merchant=True).count(),
            "admins": users.filter(is_admin=True).count(),
        }
        serializer = self.serializer_class(user_data)
        return Response(
            success=True,
            message="Users overview retrieved successfully",
            data=serializer.data,
            status_code=status.HTTP_200_OK,
        )


class TransactionOverviewView(generics.GenericAPIView):
    permission_classes = (IsSuperAdmin,)
    serializer_class = TransactionSummarySerializer

    def get(self, request):
        period = request.query_params.get("period", DEFAULT_PERIOD).upper()
        currency = request.query_params.get("currency", DEFAULT_CURRENCY).upper()
        if currency and currency not in SYSTEM_CURRENCIES:
            return Response(
                success=False,
                message=f"Invalid currency. Valid options are: {', '.join(SYSTEM_CURRENCIES)}",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        if period and period not in VALID_PERIODS:
            return Response(
                success=False,
                message=f"Invalid period. Valid options are: {', '.join(VALID_PERIODS)}",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        period_time_range = get_time_range_from_period(period, request.query_params)
        if not period_time_range.get("success"):
            return Response(
                success=False,
                message=period_time_range.get("message"),
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        period_time_range = period_time_range.get("data", {})
        start_date = period_time_range.get("start_date", None)
        end_date = period_time_range.get("end_date", None)

        transactions = Transaction.objects.filter(currency=currency)

        if start_date and end_date:
            transactions = transactions.filter(created_at__range=(start_date, end_date))

        # Aggregate data for each transaction type
        deposit_data = get_aggregated_system_transaction_data_by_type(
            transactions, "DEPOSIT", DEPOSIT_STATES
        )
        withdrawal_data = get_aggregated_system_transaction_data_by_type(
            transactions, "WITHDRAW", WITHDRAWAL_STATES
        )
        escrow_data = get_aggregated_system_transaction_data_by_type(
            transactions, "ESCROW", ESCROW_STATES
        )
        merchant_settlement_data = get_aggregated_system_transaction_data_by_type(
            transactions, "MERCHANT_SETTLEMENT", MERCHANT_SETTLEMENT_STATES
        )

        data = {
            "currency": currency,
            "period": period,
            "start_date": start_date,
            "end_date": end_date,
            "total": transactions.count(),
            "deposits": deposit_data,
            "withdrawals": withdrawal_data,
            "escrows": escrow_data,
            "settlements": merchant_settlement_data,
        }
        serializer = self.serializer_class(data)
        return Response(
            success=True,
            message="Transaction overview retrieved successfully",
            data=serializer.data,
            status_code=status.HTTP_200_OK,
        )


class DisputeOverviewView(generics.GenericAPIView):
    permission_classes = (IsSuperAdmin,)
    serializer_class = DisputeSummarySerializer

    def get(self, request):
        period = request.query_params.get("period", DEFAULT_PERIOD).upper()
        if period and period not in VALID_PERIODS:
            return Response(
                success=False,
                message=f"Invalid period. Valid options are: {', '.join(VALID_PERIODS)}",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        period_data = get_time_range_from_period(period, request.query_params)
        if not period_data.get("success"):
            return Response(
                success=False,
                message=period_data.get("message"),
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        period_data = period_data.get("data", {})
        start_date = period_data.get("start_date", None)
        end_date = period_data.get("end_date", None)

        disputes = Dispute.objects.all()

        if start_date and end_date:
            disputes = disputes.filter(created_at__range=(start_date, end_date))

        low_priority_dispute_data = get_aggregated_system_dispute_data_by_type(
            disputes, "LOW", DISPUTE_STATES
        )
        medium_priority_dispute_data = get_aggregated_system_dispute_data_by_type(
            disputes, "MEDIUM", DISPUTE_STATES
        )
        high_priority_dispute_data = get_aggregated_system_dispute_data_by_type(
            disputes, "HIGH", DISPUTE_STATES
        )

        data = {
            "period": period,
            "start_date": start_date,
            "end_date": end_date,
            "total": disputes.count(),
            "low": low_priority_dispute_data,
            "medium": medium_priority_dispute_data,
            "high": high_priority_dispute_data,
        }
        serializer = self.serializer_class(data)
        return Response(
            success=True,
            message="Disputes data retrieved successfully",
            data=serializer.data,
            status_code=status.HTTP_200_OK,
        )
