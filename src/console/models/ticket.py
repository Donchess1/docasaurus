import uuid

from django.db import models

from console.models import Event, Product, Transaction
from users.models import CustomUser


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
        return f"Ticket {self.ticket_code} for {self.ticket_product.name} - {self.user.name}"
