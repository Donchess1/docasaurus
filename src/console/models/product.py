import uuid

from django.db import models
from django.utils.text import slugify

from console.models.event import Event
from users.models import CustomUser


class Product(models.Model):
    CURRENCY = (
        ("NGN", "NGN"),
        ("USD", "USD"),
    )
    CATEGORY = (
        ("SERVICE", "SERVICE"),
        ("ITEM", "ITEM"),
        ("EVENT_TICKET", "EVENT_TICKET"),
    )
    id = models.UUIDField(
        unique=True, primary_key=True, default=uuid.uuid4, editable=False
    )
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    reference = models.CharField(max_length=255, unique=True)
    description = models.TextField(null=True, blank=True)
    price = models.IntegerField(default=0)
    currency = models.CharField(
        max_length=3, choices=CURRENCY, default="NGN", db_index=True
    )
    owner = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="products"
    )
    category = models.CharField(max_length=255, choices=CATEGORY, db_index=True)
    quantity = models.IntegerField(default=0)
    event = models.ForeignKey(
        Event,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    tier = models.CharField(max_length=255, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    meta = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.reference} - {self.name}"

    def save(self, *args, **kwargs):
        if not self.slug or self.name != Product.objects.get(pk=self.pk).name:
            self.slug = slugify(self.name)
            # Ensure slug uniqueness
            if Product.objects.filter(slug=self.slug).exists():
                unique_suffix = 1
                original_slug = self.slug
                while Product.objects.filter(slug=self.slug).exists():
                    self.slug = f"{original_slug}-{unique_suffix}"
                    unique_suffix += 1

        super().save(*args, **kwargs)
