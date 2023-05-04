import uuid

from django.contrib.auth import get_user_model
from django.db import models

from users.models.user import CustomUser

# from .kyc import BusinessKYC
# from .category import BusinessCategory

# User = get_user_model()


class Business(models.Model):
    id = models.UUIDField(
        unique=True, primary_key=True, default=uuid.uuid4, editable=False
    )
    user_id = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    # category_id = models.ForeignKey(BusinessCategory, on_delete=models.CASCADE)
    # kyc_id = models.ForeignKey(BusinessKYC, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = models.TextField()
    address = models.CharField(max_length=255)
    phone = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.id
