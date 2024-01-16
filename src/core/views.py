import os

from django.http import HttpResponse


def api_ok(request):
    hostname = os.uname().nodename
    return HttpResponse(f"<h1>Server Running</h1> - HostName: {hostname}")
