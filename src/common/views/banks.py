from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny

from common.serializers.banks import (
    BankAccountPayloadSerializer,
    BankListSerializer,
    ValidateBankAccountSerializer,
)
from core.resources.cache import Cache
from core.resources.third_party.main import ThirdPartyAPI
from users.models.bank_account import BankAccount
from utils.response import Response


class ListBanksView(GenericAPIView):
    serializer_class = BankListSerializer
    permission_classes = [AllowAny]
    third_party = ThirdPartyAPI
    cache = Cache()

    @swagger_auto_schema(
        operation_description="Retrieve list of banks",
    )
    def get(self, request):
        banks = None
        banks = self.cache.get("banks")
        if banks is None:
            banks = self.third_party.list_banks()
            if not banks:
                return Response(
                    success=False,
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message="ERR005: Error occured while listing banks",
                )

        serializer = self.serializer_class(banks["sorted_banks"], many=True)
        return Response(
            success=True,
            message="Banks fetched successfully",
            status_code=status.HTTP_200_OK,
            data=serializer.data,
            meta={"count": len(serializer.data)},
        )


class ValidateBankAccountView(GenericAPIView):
    serializer_class = ValidateBankAccountSerializer
    permission_classes = [AllowAny]
    third_party = ThirdPartyAPI

    @swagger_auto_schema(
        operation_description="Verify Bank Account",
        responses={
            200: BankAccountPayloadSerializer,
        },
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors,
            )

        data = serializer.validated_data
        bank_code = data.get("bank_code")
        account_number = data.get("account_number")

        obj = self.third_party.validate_bank_account(bank_code, account_number)
        if obj["status"] == "error" or not obj["status"]:
            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                message=obj["message"],
            )
        return Response(
            success=True,
            message=obj["message"],
            status_code=status.HTTP_200_OK,
            data=obj["data"],
        )
