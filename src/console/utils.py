from typing import Any, Dict, List, Optional

from django.db.models import Count, QuerySet, Sum
from django.db.models.functions import Coalesce

from console.models import Transaction

DEPOSIT_STATES = ["PENDING", "SUCCESSFUL", "FAILED", "CANCELLED", "TOTAL"]
WITHDRAWAL_STATES = ["PENDING", "SUCCESSFUL", "FAILED", "TOTAL"]
ESCROW_STATES = [
    "PENDING",
    "SUCCESSFUL",
    "REJECTED",
    "FUFILLED",
    "REVOKED",
    "TOTAL",
]


def get_transaction_data(
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
    return format_data(data, statuses)


def format_data(
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
