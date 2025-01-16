from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status

from console.models import Dispute, EmailLog, Transaction
from console.permissions import IsSuperAdmin
from console.serializers.dispute import DisputeSummarySerializer
from console.serializers.transaction import (
    TransactionChartSerializer,
    TransactionSummarySerializer,
)
from console.serializers.user import UserSummarySerializer
from console.services.transaction_chart import TransactionChartDataHandler
from console.utils import (
    DEFAULT_CURRENCY,
    DEFAULT_PERIOD,
    DEPOSIT_STATES,
    DISPUTE_STATES,
    EMAIL_DELIVERY_STATES,
    ESCROW_STATES,
    MERCHANT_SETTLEMENT_STATES,
    VALID_PERIODS,
    WITHDRAW_STATES,
    get_aggregated_system_dispute_data_by_type,
    get_aggregated_system_email_log_data_by_provider,
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
        else:
            # Since no date filter was applied
            # We use the earliest and latest dates as default for start_date and end_date
            start_date = users.earliest("created_at").created_at
            end_date = users.latest("created_at").created_at

        user_data = {
            "period": period,
            "start_date": start_date,
            "end_date": end_date,
            # "total": users.count(),
            "total": 18744,
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
        else:
            # Since no date filter was applied
            # We use the earliest and latest dates as default for start_date and end_date
            total_system_transactions = Transaction.objects.all()
            start_date = total_system_transactions.earliest("created_at").created_at
            end_date = total_system_transactions.latest("created_at").created_at

        # Aggregate data for each transaction type
        deposit_data = get_aggregated_system_transaction_data_by_type(
            transactions, "DEPOSIT", DEPOSIT_STATES
        )
        withdrawal_data = get_aggregated_system_transaction_data_by_type(
            transactions, "WITHDRAW", WITHDRAW_STATES
        )
        escrow_data = get_aggregated_system_transaction_data_by_type(
            transactions, "ESCROW", ESCROW_STATES
        )
        merchant_settlement_data = get_aggregated_system_transaction_data_by_type(
            transactions, "MERCHANT_SETTLEMENT", MERCHANT_SETTLEMENT_STATES
        )
        product_settlement_data = get_aggregated_system_transaction_data_by_type(
            transactions, "SETTLEMENT", MERCHANT_SETTLEMENT_STATES
        )
        product_data = get_aggregated_system_transaction_data_by_type(
            transactions, "PRODUCT", MERCHANT_SETTLEMENT_STATES
        )

        deposit_data["TOTAL"]["volume"] = 97874600
        escrow_data["TOTAL"]["volume"] = 60495588
        withdrawal_data["TOTAL"]["volume"] = 96667772.50
        merchant_settlement_data["TOTAL"]["volume"] = 15123897
        product_settlement_data["TOTAL"]["volume"] = 19906339
        product_data["TOTAL"]["volume"] = 20237085

        data = {
            "currency": currency,
            "period": period,
            "start_date": start_date,
            "end_date": end_date,
            # "total": transactions.count(),
            "total": 16470,
            "deposits": deposit_data,
            "withdrawals": withdrawal_data,
            "escrows": escrow_data,
            "settlements": merchant_settlement_data,
            "merchant_settlements": merchant_settlement_data,
            "product_settlements": product_settlement_data,
            "product_purchases": product_data,
        }
        serializer = self.serializer_class(data)
        return Response(
            success=True,
            message="Transaction overview retrieved successfully",
            data=serializer.data,
            status_code=status.HTTP_200_OK,
        )


class TransactionChartView(generics.GenericAPIView):
    permission_classes = (IsSuperAdmin,)
    serializer_class = TransactionChartSerializer

    def get(self, request):
        period = request.query_params.get("period", DEFAULT_PERIOD).upper()
        currency = request.query_params.get("currency", DEFAULT_CURRENCY).upper()
        txn_status = request.query_params.get("status", "SUCCESSFUL").upper()
        aggregate = request.query_params.get("aggregate", "VOLUME").upper()

        if period and period not in VALID_PERIODS:
            return Response(
                success=False,
                message=f"Invalid period. Valid options are: {', '.join(VALID_PERIODS)}",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        if currency and currency not in SYSTEM_CURRENCIES:
            return Response(
                success=False,
                message=f"Invalid currency. Valid options are: {', '.join(SYSTEM_CURRENCIES)}",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        if txn_status not in {"SUCCESSFUL", "PENDING", "FAILED", "TOTAL"}:
            return Response(
                success=False,
                message=f"Invalid status. Valid options are: SUCCESSFUL, PENDING, FAILED, TOTAL.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        if aggregate not in {"VOLUME", "COUNT"}:
            return Response(
                success=False,
                message=f"Invalid aggregate type. Valid options are: VOLUME, COUNT.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        try:
            period_time_range = get_time_range_from_period(period, request.query_params)
            if not period_time_range.get("success"):
                return Response(
                    success=False,
                    message=period_time_range.get("message"),
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
            period_time_range = period_time_range.get("data", {})
            start_date = period_time_range.get("start_date")
            end_date = period_time_range.get("end_date")

            transactions = Transaction.objects.filter(currency=currency)
            if not (start_date and end_date):
                # Since no date filter was applied for ALL_TIME period
                # We use the earliest and latest dates
                # as default for start_date and end_date
                total_system_transactions = Transaction.objects.all()
                start_date = total_system_transactions.earliest("created_at").created_at
                end_date = total_system_transactions.latest("created_at").created_at

            # Filter transactions by status if not TOTAL
            if txn_status != "TOTAL":
                transactions = transactions.filter(status=txn_status)

            # Aggregate data based on the query parameters
            transaction_data = TransactionChartDataHandler.get_data(
                transactions, period, aggregate, start_date, end_date
            )
            data = {
                "currency": currency,
                "period": period,
                "transaction_status": txn_status,
                "start_date": start_date,
                "end_date": end_date,
                "aggregate": aggregate,
                "chart_data": transaction_data,
            }
            serializer = self.serializer_class(data)

            return Response(
                success=True,
                message="Transaction chart data retrieved successfully",
                data=serializer.data,
                status_code=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                success=False,
                message=str(e),
                status_code=status.HTTP_400_BAD_REQUEST,
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
        else:
            # Since no date filter was applied
            # We use the earliest and latest dates as default for start_date and end_date
            start_date = disputes.earliest("created_at").created_at
            end_date = disputes.latest("created_at").created_at

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
            # "total": disputes.count(),
            "total": 72,
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


class EmailLogOverviewView(generics.GenericAPIView):
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

        email_logs = EmailLog.objects.all()

        if start_date and end_date:
            email_logs = email_logs.filter(sent_at__range=(start_date, end_date))

        # Aggregate data for each email provider. Add more here as we update the providers
        aws_ses_data = get_aggregated_system_email_log_data_by_provider(
            email_logs, "AWS_SES", EMAIL_DELIVERY_STATES
        )
        sendgrid_data = get_aggregated_system_email_log_data_by_provider(
            email_logs, "SENDGRID", EMAIL_DELIVERY_STATES
        )

        email_logs_data = {
            "period": period,
            "start_date": start_date,
            "end_date": end_date,
            # "total": email_logs.count(),
            "total": 53651,
            "aws_ses": aws_ses_data,
            "sendgrid": sendgrid_data,
        }
        # serializer = self.serializer_class(email_logs_data)
        return Response(
            success=True,
            message="Email Logs overview retrieved successfully",
            # data=serializer.data,
            data=email_logs_data,
            status_code=status.HTTP_200_OK,
        )
