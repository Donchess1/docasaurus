import logging
import uuid
from functools import wraps

from django.contrib.auth import get_user_model
from rest_framework import status

from core.resources.jwt_client import JWTClient
from merchant.models.base import ApiKey, Merchant
from merchant.utils import verify_api_key
from utils.response import Response
from utils.utils import unflatten_uuid

User = get_user_model()
logger = logging.getLogger(__name__)


def authorized_api_call(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        req = request.request
        logger.debug("Starting authorization process for request.")

        api_key_or_token = req.headers.get("Authorization")
        if not api_key_or_token:
            logger.error("Authorization header missing in request.")
            return Response(
                success=False,
                status_code=status.HTTP_401_UNAUTHORIZED,
                message="Unauthorized request. Provide API key or token.",
            )

        logger.info("Authorization header detected.")

        try:
            if api_key_or_token.startswith("Bearer "):
                logger.debug("Processing Bearer token.")
                token = api_key_or_token.split(" ")[1]
                logger.debug(
                    "Extracted Bearer token (partially shown): %s", token[:10] + "..."
                )
                user_id = JWTClient.authenticate_token(token)

                if not user_id:
                    logger.error("Token authentication failed.")
                    return Response(
                        success=False,
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        message="Invalid or expired token.",
                    )

                logger.info("Token authentication successful for User ID: %s", user_id)
                user = User.objects.filter(id=user_id).first()
                if not user:
                    logger.error("User not found for User ID: %s", user_id)
                    return Response(
                        success=False,
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        message="User does not exist.",
                    )

                merchant = Merchant.objects.filter(user_id=user).first()
                if not merchant:
                    logger.error("Merchant not found for User ID: %s", user_id)
                    return Response(
                        success=False,
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        message="Merchant does not exist.",
                    )
                logger.info("Authenticated Merchant ID: %s", merchant.id)

            elif api_key_or_token.startswith("MYB") and len(api_key_or_token) == 110:
                logger.debug("Processing API key.")
                scrambled_identity = api_key_or_token[14:46]
                logger.debug(
                    "Extracted scrambled identity (partially shown): %s",
                    scrambled_identity[:8] + "...",
                )
                identity = unflatten_uuid(scrambled_identity)

                api_key_obj = ApiKey.objects.filter(id=identity).first()
                if not api_key_obj:
                    logger.error("API key object not found for identity: %s", identity)
                    return Response(
                        success=False,
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        message="API key does not exist.",
                    )

                raw_api_key = api_key_or_token[46:]
                logger.debug(
                    "Raw API key (partially shown): %s", raw_api_key[:6] + "..."
                )
                if not verify_api_key(raw_api_key, api_key_obj.key):
                    logger.error(
                        "API key verification failed for identity: %s", identity
                    )
                    return Response(
                        success=False,
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        message="Invalid API key.",
                    )

                merchant = api_key_obj.merchant
                logger.info("Authenticated Merchant ID via API key: %s", merchant.id)
            else:
                logger.error("Invalid Authorization header format.")
                return Response(
                    success=False,
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    message="Invalid Authorization header.",
                )

        except Exception as e:
            logger.exception("Error occurred during authorization.")
            return Response(
                success=False,
                status_code=status.HTTP_401_UNAUTHORIZED,
                message="An error occurred during authorization.",
            )

        logger.debug("Setting merchant attribute in request: %s", merchant.id)
        setattr(req, "merchant", merchant)
        setattr(
            req,
            "authorization_channel",
            "API_KEY" if api_key_or_token.startswith("MYB") else "AUTH_TOKEN",
        )

        logger.info("Authorization successful. Proceeding to view function.")
        return view_func(request, *args, **kwargs)

    return wrapper
