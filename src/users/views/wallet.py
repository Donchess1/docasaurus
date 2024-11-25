from rest_framework import generics, permissions, status

from users.models.wallet import Wallet
from users.serializers.wallet import UserWalletSerializer
from utils.response import Response


class UserWalletListView(generics.ListAPIView):
    serializer_class = UserWalletSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        wallets = Wallet.objects.filter(user=self.request.user).order_by(
            "-currency"
        )  # ["USD", "NGN"]
        return wallets

    def get(self, request, *args, **kwargs):
        data = self.get_queryset()
        serializer = UserWalletSerializer(data, many=True)
        return Response(
            success=True,
            status_code=status.HTTP_200_OK,
            message="Wallets retrieved successfully",
            data=serializer.data,
        )
