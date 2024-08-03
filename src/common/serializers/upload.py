from rest_framework import serializers


class UploadMediaSerializer(serializers.Serializer):
    image = serializers.FileField()
