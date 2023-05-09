from rest_framework import serializers

from common.serializers.bvn import ValidateNINBVNSerializer
from common.serializers.driver_license import ValidateDriverLicenseSerializer
from common.serializers.passport import ValidatePassportSerializer
from common.serializers.voter_card import ValidateVoterCardSerializer
from users.models.kyc import UserKYC

kyc_meta_map = {
    "NIN": ValidateNINBVNSerializer,
    "BVN": ValidateNINBVNSerializer,
    "DL": ValidateDriverLicenseSerializer,
    "IP": ValidatePassportSerializer,
    "VC": ValidateVoterCardSerializer,
}


class UserKYCSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserKYC
        fields = "__all__"
