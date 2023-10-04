from .base import ZeehAfricaServiceBaseService


class ZeehAfricaService(ZeehAfricaServiceBaseService):
    @classmethod
    def validate_nin(cls, number):
        url = f"{cls.ZEEHAFRICA_BASE_URL}/nin/live/lookup/{cls.ZEEHAFRICA_PUBLIC_KEY}?nin={number}"
        return cls.make_get_request(url, zha_headers=cls.ZEEHAFRICA_HEADERS)
