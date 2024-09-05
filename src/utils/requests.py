import json

import requests
from django.utils import timezone
from rest_framework import status

from utils.response import Response
from utils.utils import APP_ENV, convert_to_camel


class Requests:
    @classmethod
    def make_get_request(
        cls, url, flw_headers=None, zha_headers=None, terraswitch_headers=None
    ):
        if flw_headers:
            response = requests.get(url, headers=flw_headers)
        elif zha_headers:
            response = requests.get(url, headers=zha_headers)
        elif terraswitch_headers:
            response = requests.get(url, headers=terraswitch_headers)
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
        cls,
        url,
        data=None,
        camelize=True,
        flw_headers=None,
        zha_headers=None,
        terraswitch_headers=None,
    ):
        if data and camelize:
            json_data = {convert_to_camel(k): v for k, v in data.items()}
            response = requests.post(url, json=json_data)
        elif not camelize and flw_headers:
            response = requests.post(url, json=data, headers=flw_headers)
        elif not camelize and zha_headers:
            response = requests.post(url, json=data, headers=zha_headers)
        elif not camelize and terraswitch_headers:
            response = requests.post(url, json=data, headers=terraswitch_headers)
        elif not camelize:
            response = requests.post(url, data)
        else:
            response = requests.post(url)

        if response.status_code in [503, 500]:
            cls.send_slack_alert(url, data, response)
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
        print("=====================================")
        print("status_code", response.status_code)
        print("=====================================")
        print("response_content==>", response.content)
        print("=====================================")
        try:
            res_data = response.json()
            res_data["status_code"] = response.status_code
            return res_data
        except requests.exceptions.JSONDecodeError:
            # logging.error(f"Failed to decode JSON: {response.text}")
            cls.send_slack_alert(url, data, response)
            print("================================================")
            print(f"Failed to decode JSON: {response.text}")
            print("================================================")
            return {
                "message": "An error occurred while processing the request. Please try again later or contact support.",
                "success": False,
                "status": "error",
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            }

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

    @classmethod
    def send_slack_alert(cls, url, data, response):
        webhook_url = "https://hooks.slack.com/services/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"
        utc_now = timezone.now()
        wat_now = utc_now + timedelta(hours=1)  # Apply the UTC+1 offset for WAT
        timestamp = wat_now.strftime("%Y-%m-%d %H:%M:%S %Z")

        payload = {
            "text": "🚨 *API Alert: Third Party Service Unavailable* 🚨",
            "attachments": [
                {
                    "color": "danger",
                    "fields": [
                        {"title": "Endpoint", "value": url, "short": False},
                        {"title": "Environment", "value": APP_ENV, "short": False},
                        {
                            "title": "Status Code",
                            "value": response.status_code,
                            "short": True,
                        },
                        {"title": "Timestamp", "value": timestamp, "short": True},
                        {
                            "title": "Request Payload",
                            "value": json.dumps(data, indent=2),
                            "short": False,
                        },
                        {
                            "title": "Response Content",
                            "value": response.text,
                            "short": False,
                        },
                    ],
                }
            ],
        }

        headers = {"Content-Type": "application/json"}
        requests.post(webhook_url, data=json.dumps(payload), headers=headers)
