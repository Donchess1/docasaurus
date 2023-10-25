from common.serializers.bvn import ValidateNINBVNSerializer
from common.serializers.driver_license import ValidateDriverLicenseSerializer
from common.serializers.passport import ValidatePassportSerializer
from common.serializers.voter_card import ValidateVoterCardSerializer
from users.models.kyc import UserKYC

KYC_CHOICES = (
    "NIN",
    "BVN",
    "DL",
    "VC",
    "IP",
)

kyc_meta_map = {
    "NIN": ValidateNINBVNSerializer,
    "BVN": ValidateNINBVNSerializer,
    "DL": ValidateDriverLicenseSerializer,
    "IP": ValidatePassportSerializer,
    "VC": ValidateVoterCardSerializer,
}


def create_user_kyc(user, type, kyc_meta):
    kyc = UserKYC(user_id=user, type=type, status="ACTIVE")

    if type == "NIN":
        kyc.nin_metadata = kyc_meta
    elif type == "BVN":
        kyc.bvn_metadata = kyc_meta
    elif type == "DL":
        kyc.dl_metadata = kyc_meta
    elif type == "VC":
        kyc.vc_metadata = kyc_meta
    elif type == "IP":
        kyc.inp_metadata = kyc_meta

    kyc.save()
    return kyc
