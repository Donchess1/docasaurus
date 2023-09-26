from django.http import HttpResponse


def api_ok(request):
    return HttpResponse("<h1>Server Running</h1>")
