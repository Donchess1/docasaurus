import uuid

from django.db import models


class Event(models.Model):
    id = models.UUIDField(
        unique=True, primary_key=True, default=uuid.uuid4, editable=False
    )
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    venue = models.CharField(max_length=255, null=True, blank=True)
    date = models.DateTimeField(null=True, blank=True)
    convener = models.CharField(max_length=255, null=True, blank=True)
    meta = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.id}"
