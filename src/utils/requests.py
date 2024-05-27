import requests
from rest_framework import status

from utils.response import Response
from utils.utils import convert_to_camel


class Requests:
    @classmethod
    def make_get_request(cls, url, flw_headers=None, zha_headers=None):
        if flw_headers:
            response = requests.get(url, headers=flw_headers)
        elif zha_headers:
            response = requests.get(url, headers=zha_headers)
        else:
            response = requests.get(url)

        if response.status_code in [503, 500]:
            print("THIRD PARTY SERVICE NOT AVAILABLE!")
            print("THIRD PARTY STATUS CODE:", response.status_code)
            return {
                "message": "Third party service unavailable. Please try again later.",
                "success": False,
                "status": "error",
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            }
            # return Response(
            #     message="Third Party Service not available.",
            #     success=False,
            #     status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            # )

        data = response.json()
        data["status_code"] = response.status_code
        return data

    @classmethod
    def make_post_request(
        cls, url, data=None, camelize=True, flw_headers=None, zha_headers=None
    ):
        if data and camelize:
            json_data = {convert_to_camel(k): v for k, v in data.items()}
            response = requests.post(url, json=json_data)
        elif not camelize and flw_headers:
            response = requests.post(url, json=data, headers=flw_headers)
        elif not camelize and zha_headers:
            response = requests.post(url, json=data, headers=zha_headers)
        elif not camelize:
            response = requests.post(url, data)
        else:
            response = requests.post(url)

        if response.status_code in [503, 500]:
            print("THIRD PARTY SERVICE NOT AVAILABLE!")
            print("THIRD PARTY STATUS CODE:", response.status_code)
            return {
                "message": "Third party service unavailable. Please try again later.",
                "success": False,
                "status": "error",
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            }
            # return Response(
            #     message="Third Party Service not available.",
            #     success=False,
            #     status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            # )

        data = response.json()
        data["status_code"] = response.status_code
        return data

    @classmethod
    def make_put_request(cls, url, data):
        json_data = {convert_to_camel(k): v for k, v in data.items()}
        response = requests.put(url, json=json_data)
        if response.status_code in [503, 500]:
            return Response(
                message="Service not available.",
                success=False,
                status_code=503,
            )

        data = response.json()
        data["status_code"] = response.status_code
        return data

    @classmethod
    def make_delete_request(cls, url):
        response = requests.delete(url)
        if response.status_code in [503, 500]:
            return Response(
                message="Service not available.",
                success=False,
                status_code=503,
            )

        data = response.json()
        data["status_code"] = response.status_code
        return data
