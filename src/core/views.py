import os

from django.http import HttpResponse
from rest_framework import generics, permissions, serializers, status

from utils.response import Response


def api_ok(request):
    hostname = os.uname().nodename
    return HttpResponse(f"<h1>Server is Now Running on 1-{hostname}</h1>")


class HealthCheckSerializer(serializers.Serializer):
    status = serializers.CharField()


class HealthCheckView(generics.GenericAPIView):
    serializer_class = HealthCheckSerializer
    permission_classes = (permissions.AllowAny,)

    def get(self, request, *args, **kwargs):
        return Response(
            success=True,
            message="Health Check OK. Server is running.",
            status_code=status.HTTP_200_OK,
            data={"status": "Server is running"},
        )
