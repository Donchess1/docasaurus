from rest_framework import serializers

from business.models.business import Business
from utils.utils import PHONE_NUMBER_SERIALIZER_REGEX_NGN


class BusinessSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(
        validators=[PHONE_NUMBER_SERIALIZER_REGEX_NGN], required=False
    )

    class Meta:
        model = Business
        fields = (
            "id",
            "name",
            "address",
            "user_id",
            "description",
            "phone",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "user_id",
            "created_at",
            "updated_at",
        )
