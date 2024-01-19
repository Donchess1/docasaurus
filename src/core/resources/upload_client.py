import os

import cloudinary
from cloudinary.exceptions import Error as CloudinaryError
from cloudinary.uploader import upload

from utils.utils import replace_space


class FileUploadClient:
    CLOUDINARY_CLOUD_NAME = os.environ.get("CLOUDINARY_CLOUD_NAME")
    CLOUDINARY_API_KEY = os.environ.get("CLOUDINARY_API_KEY")
    CLOUDINARY_API_SECRET = os.environ.get("CLOUDINARY_API_SECRET")
    MAX_IMAGE_SIZE_BYTES = 1024 * 1024  # 1MB in bytes
    ALLOWED_IMAGE_FORMATS = ["jpg", "jpeg"]

    @classmethod
    def initialize_cloudinary(cls):
        cloudinary.config(
            cloud_name=cls.CLOUDINARY_CLOUD_NAME,
            api_key=cls.CLOUDINARY_API_KEY,
            api_secret=cls.CLOUDINARY_API_SECRET,
        )

    @classmethod
    def is_image(cls, uploaded_file):
        original_file_name = uploaded_file.name
        file_extension = original_file_name.split(".")[-1].lower()
        return file_extension in cls.ALLOWED_IMAGE_FORMATS

    @classmethod
    def is_valid_size(cls, uploaded_file):
        return uploaded_file.size <= cls.MAX_IMAGE_SIZE_BYTES

    @classmethod
    def execute(cls, file):
        if not cls.is_image(file):
            return {
                "message": "Invalid file format. Only image (JPG) are allowed",
                "success": False,
                "status_code": 400,
            }
        if not cls.is_valid_size(file):
            return {
                "message": "Image size must be 1MB or less",
                "success": False,
                "status_code": 400,
            }
        cls.initialize_cloudinary()
        try:
            result = upload(file, folder="MYBALANCE")
            file_url = result["secure_url"]
            return {
                "message": "Upload Successful",
                "success": True,
                "status_code": 200,
                "data": {"url": file_url},
            }
        except CloudinaryError as e:
            return {
                "message": f"Cloudinary Error: {str(e)}",
                "success": False,
                "status_code": 500,
            }
        except Exception as e:
            return {
                "message": f"Error: {str(e)}",
                "success": False,
                "status_code": 500,
            }
