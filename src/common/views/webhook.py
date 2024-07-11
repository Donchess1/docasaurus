import os

from rest_framework import generics, permissions, status

from common.serializers.webhook import FlwWebhookSerializer
from common.services import handle_deposit, handle_withdrawal
from core.resources.sockets.pusher import PusherSocket
from utils.response import Response


class FlwWebhookView(generics.GenericAPIView):
    serializer_class = FlwWebhookSerializer
    permission_classes = [permissions.AllowAny]
    pusher = PusherSocket()

    def post(self, request):
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

        if event not in [
            "transfer.completed",
            "charge.completed",
        ]:  # Valid events from Flutterwave for inflows and outflows
            return Response(
                success=False,
                message="Invalid webhook event does not exist",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        result = (
            handle_withdrawal(data, self.pusher)
            if event == "transfer.completed"
            else handle_deposit(data, self.pusher)
        )
        return Response(**result)
