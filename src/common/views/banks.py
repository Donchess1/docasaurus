from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny

from common.serializers.banks import (BankAccountPayloadSerializer,
                                      BankListSerializer,
                                      ValidateBankAccountSerializer)
from core.resources.cache import Cache
from core.resources.third_party.main import ThirdPartyAPI
from utils.response import Response
from utils.utils import hours_to_seconds


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
            banks = self.third_party.list_banks(read_from_file=True)
            if not banks["status"]:
                return Response(**banks)

        cache_exp = hours_to_seconds(6)
        self.cache.set("banks", banks, cache_exp)

        serializer = self.serializer_class(banks["payload"], many=True)
        banks["payload"] = serializer.data

        return Response(
            success=True,
            message="List of banks retrieved successfully",
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

        obj = self.third_party.validate_bank_account(data)
        if not obj["status"]:
            return Response(
                success=False,
                status_code=status.HTTP_404_NOT_FOUND,
                message=obj["message"],
            )

        return Response(
            success=True,
            message=obj["message"],
            status_code=status.HTTP_200_OK,
            data=obj["payload"],
        )
