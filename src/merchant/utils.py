from merchant.models import Merchant


def validate_request(request):
    api_key = request.headers.get("API-KEY")
    if not api_key:
        return [False, "Request Forbidden. API Key missing"]
    try:
        merchant = Merchant.objects.get(api_key=api_key)
        return [True, merchant]
    except Merchant.DoesNotExist:
        return [False, "Request Forbidden. Invalid API Key"]
