from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from django.contrib.auth import get_user_model
from django.db.models import Count, QuerySet, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone

from console.models import Dispute, EmailLog, Transaction
from dispute.services import get_user_owned_dispute_queryset
from transaction.services import get_user_owned_transaction_queryset

User = get_user_model()

EMAIL_DELIVERY_STATES = ["FAILED", "SUCCESSFUL", "TOTAL"]
DISPUTE_STATES = ["PENDING", "PROGRESS", "RESOLVED", "TOTAL"]

TRANSACTION_TYPES = [
    "DEPOSIT",
    "WITHDRAW",
    "ESCROW",
    "MERCHANT_SETTLEMENT",
    "SETTLEMENT",
    "PRODUCT",
]
DEPOSIT_STATES = ["PENDING", "SUCCESSFUL", "FAILED", "CANCELLED", "TOTAL"]
WITHDRAW_STATES = ["PENDING", "SUCCESSFUL", "FAILED", "TOTAL"]
MERCHANT_SETTLEMENT_STATES = ["PENDING", "SUCCESSFUL", "FAILED", "TOTAL"]
ESCROW_STATES = [
    "PENDING",
    "SUCCESSFUL",
    "REJECTED",
    "FUFILLED",
    "REVOKED",
    "TOTAL",
]
VALID_PERIODS = {
    "ALL_TIME",
    "TODAY",
    "DAY",
    "WEEK",
    "MONTH",
    "3_MONTHS",
    "6_MONTHS",
    "YEAR",
    "CUSTOM",
}
DEFAULT_PERIOD = "ALL_TIME"
DEFAULT_CURRENCY = "NGN"
TRANSACTION_CHART_STATUS = ("SUCCESSFUL", "PENDING", "FAILED", "TOTAL")
IBTE2024_TICKET_TIERS = ("BASIC-DEFAULT", "VIP-DEFAULT", "VVIP-DEFAULT")


def get_aggregated_system_transaction_data_by_type(
    transactions: QuerySet[Transaction], txn_type: str, statuses: List[str]
) -> Dict[str, Dict[str, Any]]:
    """
    Aggregate transaction data by type and status, including a total summary.

    Args:
        transactions (QuerySet[Transaction]): The QuerySet containing transaction data specific to the Transaction model.
        txn_type (str): The type of transactions to filter by (e.g., "DEPOSIT", "WITHDRAW", "ESCROW").
        statuses (List[str]): A list of status strings to be used in formatting the final output.

    Returns:
        Dict[str, Dict[str, Any]]: A dictionary where the keys are status values and the values
                                   are dictionaries containing 'volume' and 'count' data.
    """
    data = (
        transactions.filter(type=txn_type)
        .values("status")
        .annotate(volume=Coalesce(Sum("amount"), 0), count=Coalesce(Count("id"), 0))
    )
    total = transactions.filter(type=txn_type).aggregate(
        volume=Coalesce(Sum("amount"), 0), count=Coalesce(Count("id"), 0)
    )
    data = list(data) + [
        {"status": "TOTAL", "volume": total["volume"], "count": total["count"]}
    ]
    return format_system_aggregated_transaction_data(data, statuses)


def format_system_aggregated_transaction_data(
    queryset: List[Dict[str, Any]], statuses: List[str]
) -> Dict[str, Dict[str, int]]:
    """
    Format transaction data by initializing volumes and counts for each status.

    Args:
        queryset (List[Dict[str, Any]]): A list of dictionaries where each dictionary contains transaction data.
        statuses (List[str]): A list of status strings to initialize the output dictionary.

    Returns:
        Dict[str, Dict[str, int]]: A dictionary where the keys are status values and the values
                                   are dictionaries containing 'volume' and 'count' data.
    """
    data = {status: {"volume": 0, "count": 0} for status in statuses}
    for entry in queryset:
        status = entry["status"]
        if status in data:
            data[status]["volume"] = entry.get("volume", 0)
            data[status]["count"] = entry.get("count", 0)
    return data


def get_aggregated_system_email_log_data_by_provider(
    email_logs: QuerySet[EmailLog], provider: str, statuses: List[str]
) -> Dict[str, Dict[str, Any]]:
    data = (
        email_logs.filter(provider=provider)
        .values("status")
        .annotate(count=Coalesce(Count("id"), 0))
    )
    total = email_logs.filter(provider=provider).aggregate(
        count=Coalesce(Count("id"), 0)
    )
    data = list(data) + [{"status": "TOTAL", "count": total["count"]}]
    return format_system_aggregated_email_log_data(data, statuses)


def format_system_aggregated_email_log_data(
    queryset: List[Dict[str, Any]], statuses: List[str]
) -> Dict[str, Dict[str, int]]:
    data = {status: {"count": 0} for status in statuses}
    for entry in queryset:
        status = entry["status"]
        if status in data:
            data[status]["count"] = entry.get("count", 0)
    return data


def get_aggregated_system_dispute_data_by_type(
    disputes: QuerySet[Dispute], priority: str, statuses: List[str]
) -> Dict[str, Dict[str, Any]]:
    """
    Aggregate transaction data by type and status, including a total summary.

    Args:
        disputes (QuerySet[Disptue]): The QuerySet containing dispute data specific to the Dispute model.
        priority (str): The type of disputes to filter by (e.g., "LOW", "MEDIUM", "HIGH").
        statuses (List[str]): A list of status strings to be used in formatting the final output.

    Returns:
        Dict[str, Dict[str, Any]]: A dictionary where the keys are status values and the values
                                   are dictionaries containing 'volume' and 'count' data.
    """
    data = (
        disputes.filter(priority=priority)
        .values("status")
        .annotate(count=Coalesce(Count("id"), 0))
    )
    total = disputes.filter(priority=priority).aggregate(count=Coalesce(Count("id"), 0))
    data = list(data) + [{"status": "TOTAL", "count": total["count"]}]
    return format_system_aggregated_dispute_data(data, statuses)


def format_system_aggregated_dispute_data(
    queryset: List[Dict[str, Any]], statuses: List[str]
) -> Dict[str, Dict[str, int]]:
    """
    Format dispute data by initializing counts for each status.

    Args:
        queryset (List[Dict[str, Any]]): A list of dictionaries where each dictionary contains dispute data.
        statuses (List[str]): A list of status strings to initialize the output dictionary.

    Returns:
        Dict[str, Dict[str, int]]: A dictionary where the keys are status values and the values
                                   are dictionaries containing 'count' data.
    """
    data = {status: {"count": 0} for status in statuses}
    for entry in queryset:
        status = entry["status"]
        if status in data:
            data[status]["count"] = entry.get("count", 0)
    return data


def compute_start_end_end_date_from_filter_period(
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
    if period not in VALID_PERIODS:
        period = DEFAULT_PERIOD

    today = timezone.now()
    start_of_today = today.replace(hour=0, minute=0, second=0, microsecond=0)

    if period == "TODAY":
        return start_of_today, today
    elif period == "DAY":
        return today - timedelta(hours=24), today
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
    return None, None  # period = ALL_TIME


def get_time_range_from_period(period: str, params: dict):
    """
    Returns the time range for a given period.

    Args:
        period (str): The period for which to get the time range.
        params (dict): A dictionary containing additional parameters for the CUSTOM period.

    Returns:
        dict: A dictionary containing the success status, a message, and the time range data.
    """
    if period == "CUSTOM":
        start_date_str = params.get("start_date", None)
        end_date_str = params.get("end_date", None)

        if not start_date_str or not end_date_str:
            return {
                "success": False,
                "message": "start_date and end_date must be provided for CUSTOM period.",
                "data": None,
            }
        try:
            start_date_str = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date_str = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError:
            return {
                "success": False,
                "message": "start_date and end_date must be in the format YYYY-MM-DD.",
                "data": None,
            }
        if start_date_str > end_date_str:
            return {
                "success": False,
                "message": "start_date cannot be later than end_date.",
                "data": None,
            }
        start_date, end_date = compute_start_end_end_date_from_filter_period(
            period, start_date_str, end_date_str
        )
        return {
            "success": True,
            "message": "",
            "data": {"start_date": start_date, "end_date": end_date},
        }
    else:
        start_date, end_date = compute_start_end_end_date_from_filter_period(period)
        return {
            "success": True,
            "message": "",
            "data": {"start_date": start_date, "end_date": end_date},
        }


def get_user_system_metrics(user: User, currency: str = "NGN") -> dict:
    transactions = get_user_owned_transaction_queryset(user, currency)
    disputes = get_user_owned_dispute_queryset(user)
    total = transactions.count()
    deposits = transactions.filter(type="DEPOSIT").count()
    withdrawals = transactions.filter(type="WITHDRAW").count()
    escrows = transactions.filter(type="ESCROW").count()
    disputes = disputes.count()
    return {
        "total_transactions": total,
        "deposits": deposits,
        "withdrawals": withdrawals,
        "escrows": escrows,
        "disputes": disputes,
    }
