import uuid

from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class UserKYC(models.Model):
    KYC_CHOICES = (
        ("NIN", "NATIONAL_IDENTIFICATION_NUMBER"),
        ("BVN", "BANK_VERIFICATION_NUMBER"),
        ("DL", "DRIVER_LICENSE"),
        ("VC", "VOTER_CARD"),
        ("IP", "INTERNATIONAL_PASSPORT"),
    )
    STATUS_CHOICES = (
        ("ACTIVE", "ACTIVE"),
        ("INACTIVE", "INACTIVE"),
    )
    id = models.UUIDField(
        unique=True, primary_key=True, default=uuid.uuid4, editable=False
    )
    user_id = user_id = models.OneToOneField(User, on_delete=models.CASCADE)
    type = models.CharField(max_length=255, choices=KYC_CHOICES)
    status = models.CharField(
        max_length=255, choices=STATUS_CHOICES, default="INACTIVE"
    )
    nin = models.CharField(max_length=11, null=True, blank=True)
    bvn = models.CharField(max_length=11, null=True, blank=True)
    dl_metadata = models.JSONField(null=True, blank=True)
    vc_metadata = models.JSONField(null=True, blank=True)
    inp_metadata = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.id}"
