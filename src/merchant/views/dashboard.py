from rest_framework import generics, permissions, status

from console.models import Transaction
from console.serializers.transaction import TransactionChartSerializer
from console.services.transaction_chart import TransactionChartDataHandler
from console.utils import (
    DEFAULT_CURRENCY,
    DEFAULT_PERIOD,
    VALID_PERIODS,
    get_time_range_from_period,
)
from merchant.decorators import authorized_merchant_apikey_or_token_call
from utils.response import Response
from utils.utils import SYSTEM_CURRENCIES


class MerchantTransactionChartView(generics.GenericAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = TransactionChartSerializer

    @authorized_merchant_apikey_or_token_call
    def get(self, request):
        merchant = request.merchant
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

            transactions = Transaction.objects.filter(
                currency=currency, merchant=merchant
            )
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
