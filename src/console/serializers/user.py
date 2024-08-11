from rest_framework import serializers

from console.serializers.overview import BaseSummarySerializer


class UserSummarySerializer(BaseSummarySerializer):
    buyers = serializers.IntegerField()
    sellers = serializers.IntegerField()
    merchants = serializers.IntegerField()
    admins = serializers.IntegerField()
