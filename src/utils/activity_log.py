from typing import Any, Dict
from uuid import UUID

import geocoder
from django.http import HttpRequest

from console.models.transaction import Transaction
from transaction.models import TransactionActivityLog


def get_client_ip(request: HttpRequest) -> str:
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]  # Take the first IP in the list
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


def get_user_agent(request: HttpRequest) -> str:
    return request.META.get("HTTP_USER_AGENT", "")


def get_geo_location(ip: str) -> Dict[str, str]:
    if not ip:  # Check if IP is None or an empty string
        return {}

    # Use geocoder to get the city and country from the IP address.
    g = geocoder.ip(ip)
    if g.ok:
        return {
            "city": g.city,
            "country": g.country,
        }
    return {}


def extract_api_request_metadata(request: HttpRequest) -> Dict[str, str]:
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)
    geo_location = get_geo_location(ip_address)

    meta = {
        "ip_address": ip_address,
        "user_agent": user_agent,
        "city": geo_location.get("city") if geo_location else None,
        "country": geo_location.get("country") if geo_location else None,
    }
    return meta


def log_transaction_activity(
    transaction: Transaction, description: str, request_meta: dict
) -> TransactionActivityLog:
    """
    Logs a transaction activity with the given description and metadata.

    Args:
        transaction (Transaction): The transaction instance.
        description (str): A description template with placeholders.
        request (HttpRequest): The HTTP request object.
        **kwargs: Additional metadata to be included in the description.
    """
    return TransactionActivityLog.objects.create(
        transaction=transaction,
        description=description,
        meta=request_meta,
    )
