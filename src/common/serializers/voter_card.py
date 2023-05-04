from rest_framework import serializers

from utils.utils import CUSTOM_DATE_REGEX


class ValidateVoterCardSerializer(serializers.Serializer):
    number = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    state = serializers.CharField()
    lga = serializers.CharField()
    dob = serializers.CharField()

    def validate_dob(self, value):
        if not CUSTOM_DATE_REGEX.match(value):
            raise serializers.ValidationError(
                "Invalid date format. Date must be in the format YYYY-MM-DD."
            )
        return value


class ValidateVoterCardPayloadSerializer(serializers.Serializer):
    vin = serializers.CharField()
    full_name = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    polling_unit = serializers.CharField()
    date_of_birth = serializers.CharField()
    state = serializers.CharField()
    lga = serializers.CharField()
    polling_unit_code = serializers.CharField()
