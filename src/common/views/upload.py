from rest_framework import generics, permissions, status

from core.resources.upload_client import FileUploadClient
from users.serializers.user import UploadMediaSerializer
from utils.response import Response


class UploadMediaView(generics.GenericAPIView):
    serializer_class = UploadMediaSerializer
    permission_classes = [permissions.IsAuthenticated]
    upload_client = FileUploadClient

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                success=False,
                message="Validation error",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        image = serializer.validated_data.get("image")
        destination = serializer.validated_data.get("destination", None)

        cloudinary_folder = "MYBALANCE"
        if destination == "BLOG":
            cloudinary_folder = f"{cloudinary_folder}/BLOG"
        elif destination == "DISPUTE_RESOLUTION":
            cloudinary_folder = f"{cloudinary_folder}/DISPUTE_RESOLUTION"
        elif destination == "AVATAR":
            cloudinary_folder = f"{cloudinary_folder}/AVATAR"
        obj = self.upload_client.execute(
            file=image, cloudinary_folder=cloudinary_folder
        )

        if not obj["success"]:
            return Response(**obj)

        image_url = obj["data"]["url"]

        return Response(
            success=True,
            message="Image uploaded successfully",
            data=image_url,
            status_code=status.HTTP_200_OK,
        )
