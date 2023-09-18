from django.http import HttpResponse


def api_ok(request):
    return HttpResponse("API OK")
