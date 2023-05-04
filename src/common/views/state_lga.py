from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny

from common.serializers.state_lga import StateLGAListSerializer, StatesListSerializer
from core.resources.third_party.main import ThirdPartyAPI
from utils.response import Response


class ListNGNStatesView(GenericAPIView):
    serializer_class = StatesListSerializer
    permission_classes = [AllowAny]
    third_party = ThirdPartyAPI

    @swagger_auto_schema(
        operation_description="Retrieve Nigerian States",
    )
    def get(self, request):
        states = self.third_party.list_states()
        serializer = self.serializer_class(states["payload"], many=True)
        states["payload"] = serializer.data

        return Response(
            success=True,
            message=states["message"],
            status_code=status.HTTP_200_OK,
            data=serializer.data,
            meta={"count": len(serializer.data)},
        )


class ListLGAByStateAliasView(GenericAPIView):
    serializer_class = StateLGAListSerializer
    permission_classes = [AllowAny]
    third_party = ThirdPartyAPI

    @swagger_auto_schema(
        operation_description="Retrieve Local Government Areas (LGA) by State Alias",
    )
    def get(self, request, alias):
        states = self.third_party.list_lgas_by_state_alias(alias)
        if not states["status"]:
            return Response(
                success=False,
                status_code=status.HTTP_404_NOT_FOUND,
                message=states["message"],
            )
        data = {"lgas": states["payload"]}

        return Response(
            success=True,
            message=states["message"],
            status_code=status.HTTP_200_OK,
            data=data,
            meta={"count": len(states["payload"])},
        )
