import uuid
from functools import wraps

from rest_framework import status

from merchant.models.base import ApiKey, Merchant
from merchant.utils import verify_api_key
from utils.response import Response


def authorized_api_call(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        req = request.request
        api_key = req.headers.get("X-API-KEY")
        identity = req.headers.get("X-IDENTITY")

        if not all([api_key, identity]):
            return Response(
                success=False,
                status_code=status.HTTP_401_UNAUTHORIZED,
                message="Invalid headers. Pass Identity and API key",
            )
        try:
            uuid.UUID(identity)
        except ValueError:
            return Response(
                success=False,
                status_code=status.HTTP_401_UNAUTHORIZED,
                message="Invalid Identity",
            )

        api_key_obj = ApiKey.objects.filter(merchant__id=identity).first()
        if not api_key_obj:
            return Response(
                success=False,
                status_code=status.HTTP_401_UNAUTHORIZED,
                message="Invalid API Key",
            )

        if not verify_api_key(api_key, api_key_obj.key):
            return Response(
                success=False,
                status_code=status.HTTP_401_UNAUTHORIZED,
                message="Invalid API Key",
            )

        return view_func(request, *args, **kwargs)

    return wrapper
