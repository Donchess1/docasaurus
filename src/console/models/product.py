import uuid

from django.db import models
from users.models import CustomUser
from console.models import Transaction, Product, Event


class Product(models.Model):
    CURRENCY = (
        ("NGN", "NGN"),
        ("USD", "USD"),
    )
    CATEGORY = (("SERVICE", "SERVICE"), ("ITEM", "ITEM"), ("EVENT_TICKET", "EVENT_TICKET"))
    id = models.UUIDField(
        unique=True, primary_key=True, default=uuid.uuid4, editable=False
    )
    name = models.CharField(max_length=255)
    reference = models.CharField(max_length=255, unique=True)
    description = models.TextField(null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(
        max_length=3, choices=CURRENCY, default="NGN", db_index=True
    )
    owner = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="products"
    )
    category = models.CharField(max_length=255, choices=CATEGORY, db_index=True)
    quantity = models.IntegerField(default=0)
    event = models.ForeignKey(Event, on_delete=models.SET_NULL, null=True, blank=True,)
    tier = models.CharField(max_length=255, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    meta = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.reference} - {self.name}"


class TicketPurchase(models.Model):
    id = models.UUIDField(
        unique=True, primary_key=True, default=uuid.uuid4, editable=False
    )
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="ticket_purchases"
    )
    ticket_product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="purchases"
    )
    transaction = models.ForeignKey(
        Transaction, on_delete=models.CASCADE, related_name="ticket_purchases"
    )
    ticket_code = models.CharField(max_length=255, unique=True)
    purchase_date = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Ticket {self.ticket_code} for {self.ticket_product.event_name} - {self.user.username}"

