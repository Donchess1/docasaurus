from datetime import date, datetime, timedelta
from typing import Optional, Tuple

from django.contrib.auth import get_user_model
from django.db.models import Count, Sum
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, mixins, permissions, status, viewsets
from rest_framework.decorators import action

from console.models import Dispute, EscrowMeta, Transaction
from console.permissions import IsSuperAdmin
from console.utils import (
    DEPOSIT_STATES,
    ESCROW_STATES,
    WITHDRAWAL_STATES,
    get_transaction_data,
)
from users.services import get_user_profile_data
from utils.pagination import CustomPagination
from utils.response import Response

User = get_user_model()


class ConsoleOverviewView(generics.GenericAPIView):
    permission_classes = (IsSuperAdmin,)
    DEFAULT_PERIOD = "TODAY"
    VALID_PERIODS = {
        "TODAY",
        "DAY",
        "WEEK",
        "MONTH",
        "3_MONTHS",
        "6_MONTHS",
        "YEAR",
        "CUSTOM",
    }

    def get_time_range(
        self,
        period: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Tuple[Optional[date], Optional[date]]:
        """
        Get the time range based on the specified period.

        Args:
            period (str): The period for which the time range is calculated. Options are "DAY", "WEEK", "MONTH", "CUSTOM".
            start_date (Optional[date]): The start date for a custom period (only applicable if period is "CUSTOM").
            end_date (Optional[date]): The end date for a custom period (only applicable if period is "CUSTOM").

        Returns:
            Tuple[Optional[date], Optional[date]]: A tuple containing the start date and end date for the time range.
                                                   If no filtering is applied, both values will be None.
        """
        if period not in self.VALID_PERIODS:
            period = self.DEFAULT_PERIOD

        today = timezone.now()
        start_of_today = today.replace(hour=0, minute=0, second=0, microsecond=0)

        if period == "TODAY":
            return start_of_today, today
        elif period == "DAY":
            return today, today + timedelta(days=1)
        elif period == "WEEK":
            return today - timedelta(days=7), today
        elif period == "MONTH":
            return today - timedelta(days=30), today
        elif period == "3_MONTHS":
            return today - timedelta(days=90), today
        elif period == "6_MONTHS":
            return today - timedelta(days=180), today
        elif period == "YEAR":
            return today - timedelta(days=365), today
        elif period == "CUSTOM" and start_date and end_date:
            # Convert date objects to datetime objects, setting time to start of the day
            start_date = datetime.combine(start_date, datetime.min.time())
            end_date = datetime.combine(end_date, datetime.max.time())
            # Ensure timezone awareness
            if timezone.is_naive(start_date):
                start_date = timezone.make_aware(start_date)
            if timezone.is_naive(end_date):
                end_date = timezone.make_aware(end_date)
            return start_date, end_date
        return None, None

    def get(self, request):
        period = request.query_params.get("period", self.DEFAULT_PERIOD).upper()
        if period and period not in self.VALID_PERIODS:
            return Response(
                success=False,
                message=f"Invalid period. Valid options are: {', '.join(self.VALID_PERIODS)}",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        if period == "CUSTOM":
            start_date_str = request.query_params.get("start_date")
            end_date_str = request.query_params.get("end_date")

            if not start_date_str or not end_date_str:
                return Response(
                    success=False,
                    message="start_date and end_date must be provided for CUSTOM period.",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            # Validate the date format
            try:
                start_date_str = datetime.strptime(start_date_str, "%Y-%m-%d").date()
                end_date_str = datetime.strptime(end_date_str, "%Y-%m-%d").date()
            except ValueError:
                return Response(
                    success=False,
                    message="start_date and end_date must be in the format YYYY-MM-DD.",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
            start_date, end_date = self.get_time_range(
                period, start_date_str, end_date_str
            )
        else:
            start_date, end_date = self.get_time_range(period)

        users = User.objects.all()
        transactions = Transaction.objects.all()
        disputes = Dispute.objects.all()

        if start_date and end_date:
            users = users.filter(created_at__range=(start_date, end_date))
            transactions = transactions.filter(created_at__range=(start_date, end_date))
            disputes = disputes.filter(created_at__range=(start_date, end_date))

        # Aggregate data for each transaction type
        deposit_data = get_transaction_data(transactions, "DEPOSIT", DEPOSIT_STATES)
        withdrawal_data = get_transaction_data(
            transactions, "WITHDRAW", WITHDRAWAL_STATES
        )
        escrow_data = get_transaction_data(transactions, "ESCROW", ESCROW_STATES)

        data = {
            "period": period if period in self.VALID_PERIODS else self.DEFAULT_PERIOD,
            "start_date": start_date,
            "end_date": end_date,
            "total_users": users.count(),
            "total_transactions": transactions.count(),
            "total_disputes": disputes.count(),
            "deposits": deposit_data,
            "withdrawals": withdrawal_data,
            "escrows": escrow_data,
        }

        return Response(
            success=True,
            message="Overview data retrieved successfully",
            data=data,
            status_code=status.HTTP_200_OK,
        )
