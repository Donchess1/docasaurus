from .base import ZeehAfricaServiceBaseService


class ZeehAfricaService(ZeehAfricaServiceBaseService):
    @classmethod
    def validate_nin(cls, number):
        url = f"{cls.ZEEHAFRICA_BASE_URL}/nigeria_kyc/lookup_nin"
        data = {"nin": number}
        return cls.make_post_request(
            url, data, camelize=False, zha_headers=cls.ZEEHAFRICA_HEADERS
        )
