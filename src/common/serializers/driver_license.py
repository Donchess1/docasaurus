from rest_framework import serializers

from utils.utils import CUSTOM_DATE_REGEX


class ValidateDriverLicenseSerializer(serializers.Serializer):
    card_number = serializers.CharField()
    dob = serializers.CharField()

    def validate_dob(self, value):
        if not CUSTOM_DATE_REGEX.match(value):
            raise serializers.ValidationError(
                "Invalid date format. Date must be in the format YYYY-MM-DD."
            )
        return value


class ValidatedDriverLicensePayloadSerializer(serializers.Serializer):
    license_no = serializers.CharField()
    gender = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    middle_name = serializers.CharField()
    issued_date = serializers.CharField()
    expiry_date = serializers.CharField()
    state_of_issue = serializers.CharField()
    birth_date = serializers.CharField()
