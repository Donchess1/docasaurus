from django.contrib.auth import get_user_model
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated

from business.serializers.business import BusinessSerializer
from core.resources.model_retriever import ModelRetriever
from users.models.profile import UserProfile
from users.serializers.bank_account import BankAccountSerializer
from users.serializers.kyc import UserKYCSerializer
from users.serializers.profile import UserProfileSerializer
from utils.response import Response

User = get_user_model()


class UserProfileView(GenericAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    mr = ModelRetriever

    @swagger_auto_schema(
        operation_description="Retrieve Profile for Authenticated User",
    )
    def get(self, request):
        user_id = request.user.id
        try:
            profile = UserProfile.objects.get(user_id=user_id)
        except UserProfile.DoesNotExist:
            return Response(
                success=False,
                message="Profile not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.serializer_class(profile)

        bank_account_id = serializer.data.get("bank_account_id", None)
        kyc_id = serializer.data.get("kyc_id", None)
        business_id = serializer.data.get("business_id", None)

        bank_account = self.mr.get_object("BankAccount", bank_account_id)
        kyc = self.mr.get_object("UserKYC", kyc_id)
        business = self.mr.get_object("Business", business_id)

        ser_data = dict(serializer.data)
        del ser_data["bank_account_id"]
        del ser_data["kyc_id"]
        del ser_data["business_id"]

        data = {
            **ser_data,
            "bank_account": BankAccountSerializer(bank_account).data
            if bank_account
            else None,
            "kyc": UserKYCSerializer(kyc).data if kyc else None,
            "business": BusinessSerializer(business).data if business else None,
        }

        return Response(
            success=True,
            message="Profile retrieved successfully",
            status_code=status.HTTP_200_OK,
            data=data,
        )
