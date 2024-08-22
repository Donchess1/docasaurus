from rest_framework import serializers

from utils.utils import EMAIL_SMTP_PROVIDERS


class EmailProviderSwitchSerializer(serializers.Serializer):
    provider = serializers.ChoiceField(
        choices=EMAIL_SMTP_PROVIDERS,
    )
