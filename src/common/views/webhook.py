import os

from rest_framework import generics, permissions, status

from common.serializers.webhook import FlwWebhookSerializer
from common.services import handle_deposit, handle_withdrawal
from core.resources.sockets.pusher import PusherSocket
from utils.activity_log import extract_api_request_metadata
from utils.response import Response

ENVIRONMENT = os.environ.get("ENVIRONMENT", None)
env = "live" if ENVIRONMENT == "production" else "test"


class FlwWebhookView(generics.GenericAPIView):
    serializer_class = FlwWebhookSerializer
    permission_classes = [permissions.AllowAny]
    pusher = PusherSocket()

    def post(self, request):
        request_meta = extract_api_request_metadata(request)
        secret_hash = os.environ.get("FLW_SECRET_HASH")
        verif_hash = request.headers.get("verif-hash", None)

        if not verif_hash or verif_hash != secret_hash:
            return Response(
                success=False,
                message="Invalid authorization token.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        print("================================================================")
        print("================================================================")
        print("FLUTTTERWAVE WEBHOOK CALLED")
        print("================================================================")
        print("REQUEST DATA---->", request.data)
        print("================================================================")
        print("================================================================")

        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors,
            )

        event = serializer.validated_data.get("event")
        data = serializer.validated_data.get("data")

        # if event not in [
        #     "transfer.completed",
        #     "charge.completed",
        # ]:  # Valid events from Flutterwave for inflows and outflows
        #     return Response(
        #         success=False,
        #         message="Invalid webhook event does not exist",
        #         status_code=status.HTTP_400_BAD_REQUEST,
        #     )

        event_type = request.data.get("event.type")
        withdrawal_data = request.data.get("transfer") if env == "test" else data
        result = (
            handle_withdrawal(withdrawal_data, request_meta, self.pusher)
            if event_type.upper() == "TRANSFER"
            else handle_deposit(request.data, request_meta, self.pusher)
        )
        return Response(**result)
