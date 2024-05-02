import uuid
from functools import wraps

from rest_framework import status

from merchant.models.base import ApiKey, Merchant
from merchant.utils import verify_api_key
from utils.response import Response
from utils.utils import unflatten_uuid


def authorized_api_call(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        req = request.request
        api_key = req.headers.get("Authorization")
        if not api_key:
            return Response(
                success=False,
                status_code=status.HTTP_401_UNAUTHORIZED,
                message="Invalid header. Provide API key",
            )
        # test_env_sample_key = "MYBTSTSECK-" + random_text(3) + reversed_and_flattened_api_key_id + raw_api_key"
        if len(api_key) != 110:
            return Response(
                success=False,
                status_code=status.HTTP_401_UNAUTHORIZED,
                message="Invalid API key lenght",
            )
        scrambled_identity = api_key[14:46]
        identity = unflatten_uuid(scrambled_identity)
        api_key_obj = ApiKey.objects.filter(id=identity).first()
        if not api_key_obj:
            return Response(
                success=False,
                status_code=status.HTTP_401_UNAUTHORIZED,
                message="API key does not exist",
            )
        api_key = api_key[46:]
        if not verify_api_key(api_key, api_key_obj.key):
            return Response(
                success=False,
                status_code=status.HTTP_401_UNAUTHORIZED,
                message="Invalid API Key",
            )
        setattr(req, "merchant", api_key_obj.merchant)
        return view_func(request, *args, **kwargs)

    return wrapper
