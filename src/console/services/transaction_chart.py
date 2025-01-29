# from datetime import timedelta
import datetime

from django.db.models import Count, DateField, F, QuerySet, Sum
from django.db.models.functions import (
    Coalesce,
    TruncDay,
    TruncHour,
    TruncMonth,
    TruncWeek,
    TruncYear,
)
from django.utils import timezone


class TransactionChartDataHandler:
    TRANSACTION_TYPES = ["deposit", "escrow", "withdraw", "merchant_settlement"]

    @classmethod
    def get_data(cls, transactions, period, aggregate, start_date, end_date):
        transactions = transactions.filter(created_at__range=(start_date, end_date))
        grouped_transactions = cls._group_by_period(
            transactions, period, start_date, end_date
        )
        grouped_transactions = cls._aggregate_data(grouped_transactions, aggregate)
        data = cls._format_data(grouped_transactions, period, start_date, end_date)
        return data

    @classmethod
    def _group_by_period(cls, transactions, period, start_date=None, end_date=None):
        if period == "TODAY":
            today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
            transactions = transactions.filter(created_at__gte=today).annotate(
                hour=TruncHour("created_at")
            )
            return transactions.values("hour", "type")

        elif period == "DAY":  # 24 hours
            day_ago = timezone.now() - datetime.timedelta(days=1)
            transactions = transactions.filter(created_at__gte=day_ago).annotate(
                hour=TruncHour("created_at")
            )
            return transactions.values("hour", "type")

        elif period == "WEEK":
            transactions = transactions.annotate(
                day_of_week=TruncWeek("created_at", output_field=DateField())
            )
            return transactions.values("day_of_week", "type")

        elif period == "MONTH":
            transactions = transactions.annotate(day_of_month=TruncDay("created_at"))
            return transactions.values("day_of_month", "type")

        elif period in {"3_MONTHS", "6_MONTHS"}:
            start_date = timezone.now() - datetime.timedelta(
                days=90 if period == "3_MONTHS" else 180
            )
            transactions = transactions.filter(created_at__gte=start_date).annotate(
                month_of_year=TruncMonth("created_at")
            )
            return transactions.values("month_of_year", "type")

        elif period == "YEAR":
            transactions = transactions.annotate(month_of_year=TruncMonth("created_at"))
            return transactions.values("month_of_year", "type")

        elif period in ("ALL_TIME", "CUSTOM"):
            time_delta = (end_date - start_date).days

            if time_delta <= 1:  # Up to 1 day
                transactions = transactions.filter(
                    created_at__range=(start_date, end_date)
                ).annotate(hour=TruncHour("created_at"))
                return transactions.values("hour", "type")

            elif time_delta <= 31:  # Between 1 day and 1 month
                transactions = transactions.filter(
                    created_at__range=(start_date, end_date)
                ).annotate(day_of_month=TruncDay("created_at"))
                return transactions.values("day_of_month", "type")

            elif time_delta <= 365:  # Between 1 month and 1 year
                transactions = transactions.filter(
                    created_at__range=(start_date, end_date)
                ).annotate(month_of_year=TruncMonth("created_at"))
                return transactions.values("month_of_year", "type")

            else:  # Over 1 year
                transactions = transactions.filter(
                    created_at__range=(start_date, end_date)
                ).annotate(year=TruncYear("created_at"))
                return transactions.values("year", "type")

        return transactions

    @classmethod
    def _aggregate_data(cls, grouped_transactions, aggregate):
        if aggregate == "VOLUME":
            return grouped_transactions.annotate(total=Sum("amount"))
        else:  # aggregate == "COUNT"
            return grouped_transactions.annotate(total=Count("id"))

    @staticmethod
    def _initialize_data(period, start_date, end_date):
        data = {}
        if period == "TODAY":
            current_time = datetime.datetime.now()
            for hour in range(24):
                time_key = current_time.replace(
                    minute=0, second=0, microsecond=0
                ) - datetime.timedelta(hours=(23 - hour))
                data[time_key.strftime("%I:%M%p")] = {
                    t: 0 for t in TransactionChartDataHandler.TRANSACTION_TYPES
                }

        elif period == "DAY":
            current_time = datetime.datetime.now()
            for hour in range(24):
                time_key = current_time - datetime.timedelta(hours=(23 - hour))
                data[time_key.strftime("%b %d %Y %I:%M%p")] = {
                    t: 0 for t in TransactionChartDataHandler.TRANSACTION_TYPES
                }

        elif period == "WEEK":
            for i in range(7):
                day_key = (start_date + datetime.timedelta(days=i)).strftime("%b %d")
                data[day_key] = {
                    t: 0 for t in TransactionChartDataHandler.TRANSACTION_TYPES
                }

        elif period == "MONTH":
            for i in range(31):
                day_key = (start_date + datetime.timedelta(days=i)).strftime("%b %d")
                data[day_key] = {
                    t: 0 for t in TransactionChartDataHandler.TRANSACTION_TYPES
                }

        elif period == "3_MONTHS":
            for i in range(3):
                month_key = (start_date + datetime.timedelta(days=i * 30)).strftime(
                    "%B %Y"
                )
                data[month_key] = {
                    t: 0 for t in TransactionChartDataHandler.TRANSACTION_TYPES
                }

        elif period == "6_MONTHS":
            for i in range(6):
                month_key = (start_date + datetime.timedelta(days=i * 30)).strftime(
                    "%B %Y"
                )
                data[month_key] = {
                    t: 0 for t in TransactionChartDataHandler.TRANSACTION_TYPES
                }

        elif period == "YEAR":
            for i in range(12):
                month_key = (start_date + datetime.timedelta(days=i * 30)).strftime(
                    "%B %Y"
                )
                data[month_key] = {
                    t: 0 for t in TransactionChartDataHandler.TRANSACTION_TYPES
                }

        elif period in ("ALL_TIME", "CUSTOM"):
            current = start_date
            time_delta = (end_date - start_date).days
            while current <= end_date:
                if time_delta < 31:
                    day_key = current.strftime("%b %d")
                elif time_delta < 365:
                    day_key = current.strftime("%B %Y")
                else:
                    day_key = current.strftime("%Y-%m")
                data[day_key] = {
                    t: 0 for t in TransactionChartDataHandler.TRANSACTION_TYPES
                }
                current += datetime.timedelta(days=1)

        return data

    @classmethod
    def _format_data(cls, grouped_transactions, period, start_date, end_date):
        # Initialize data dictionary with default transaction types
        data = cls._initialize_data(period, start_date, end_date)
        for group in grouped_transactions:
            key = cls._format_data_key(period, group)
            transaction_type = group["type"].lower()

            if key not in data:
                data[key] = {
                    "deposit": 0,
                    "escrow": 0,
                    "withdraw": 0,
                    "merchant_settlement": 0,
                }

            data[key][transaction_type] = group["total"]
        return data

    @classmethod
    def _format_data_key(cls, period, group):
        if period == "WEEK":
            return group["day_of_week"].strftime("%b %d")
        elif period == "MONTH":
            return group["day_of_month"].strftime("%b %d")
        elif period in {"3_MONTHS", "6_MONTHS", "YEAR"}:
            return group["month_of_year"].strftime("%B %Y")
        elif period == "TODAY":
            return group["hour"].strftime("%I:%M %p")
        elif period == "DAY":
            return group["hour"].strftime("%b %d %Y %I:%M %p")
        elif period in {"ALL_TIME", "CUSTOM"}:
            dynamic_data_key = next(
                key for key in group if key not in {"type", "total"}
            )
            if dynamic_data_key == "hour":
                return group[dynamic_data_key].strftime("%b %d %Y %I:%M %p")
            elif dynamic_data_key == "day_of_month":
                return group[dynamic_data_key].strftime("%b %d")
            elif dynamic_data_key == "month_of_year":
                return group[dynamic_data_key].strftime("%B %Y")
            elif dynamic_data_key == "year":
                return group[dynamic_data_key].strftime("%Y")
            else:
                raise ValueError(f"Unexpected dynamic key: {dynamic_data_key}")
        else:
            raise ValueError(f"Unsupported period: {period}")


def get_transaction_chart_data(transactions, period, aggregate, start_date, end_date):
    grouped_transactions = None
    today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)

    if period == "WEEK":
        transactions = transactions.annotate(
            day_of_week=TruncWeek("created_at", output_field=DateField())
        )
        grouped_transactions = transactions.values("day_of_week", "type")

    elif period == "MONTH":
        transactions = transactions.annotate(day_of_month=TruncDay("created_at"))
        grouped_transactions = transactions.values("day_of_month", "type")

    elif period == "YEAR":
        transactions = transactions.annotate(month_of_year=TruncMonth("created_at"))
        grouped_transactions = transactions.values("month_of_year", "type")

    elif period == "TODAY":
        transactions = transactions.filter(created_at__gte=today)
        transactions = transactions.annotate(hour=TruncHour("created_at"))
        grouped_transactions = transactions.values("hour", "type")

    elif period == "DAY":
        day_ago = timezone.now() - timedelta(days=1)
        transactions = transactions.filter(created_at__gte=day_ago)
        transactions = transactions.annotate(hour=TruncHour("created_at"))
        grouped_transactions = transactions.values("hour", "type")

    # Define the aggregation type
    if aggregate == "VOLUME":
        grouped_transactions = grouped_transactions.annotate(total=Sum("amount"))
    else:  # aggregate == "COUNT"
        grouped_transactions = grouped_transactions.annotate(total=Count("id"))

    # Reshape the data into the desired format
    data = {}
    for group in grouped_transactions:
        if period == "WEEK":
            key = group["day_of_week"].strftime("%A")  # E.g., "Monday", "Tuesday"
        elif period == "MONTH":
            key = group["day_of_month"].strftime("%Y-%m-%d")  # E.g., "2024-08-26"
        elif period == "YEAR":
            key = group["month_of_year"].strftime("%B")  # E.g., "January", "February"
        else:  # period == "TODAY" or "DAY"
            key = group["hour"].strftime("%H:%M")  # E.g., "13:00", "14:00"

        transaction_type = group["type"].lower()

        if key not in data:
            data[key] = {"deposit": 0, "escrow": 0, "withdraw": 0}

        data[key][transaction_type] = group["total"]

    return data
