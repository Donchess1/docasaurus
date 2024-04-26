import os
import uuid

from django.db import models
from rest_framework import serializers

from users.models.user import CustomUser
from utils.utils import get_priv_key


class Merchant(models.Model):
    id = models.UUIDField(
        unique=True, primary_key=True, default=uuid.uuid4, editable=False
    )
    user_id = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = models.TextField()
    address = models.CharField(max_length=255)
    enable_payout_splitting = models.BooleanField(default=False)
    payout_splitting_ratio = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )  # --> 0.20
    metadata = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name}"


class Customer(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    merchants = models.ManyToManyField(Merchant, through="CustomerMerchant")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class CustomerMerchant(models.Model):
    USER_TYPE_CHOICES = (
        ("BUYER", "BUYER"),
        ("SELLER", "SELLER"),
    )
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    merchant = models.ForeignKey(Merchant, on_delete=models.CASCADE)
    alternate_phone_number = models.CharField(max_length=20, null=True, blank=True)
    phone_number_match = models.BooleanField(default=True)
    alternate_email = models.EmailField(max_length=20, null=True, blank=True)
    alternate_name = models.CharField(max_length=255, null=True, blank=True)
    name_match = models.BooleanField(default=True)
    user_type = models.CharField(max_length=255, choices=USER_TYPE_CHOICES)
    user_type_match = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class ApiKey(models.Model):
    id = models.UUIDField(
        unique=True, primary_key=True, default=uuid.uuid4, editable=False
    )
    name = models.CharField(max_length=255)
    key = models.CharField(max_length=255, null=True, blank=True)
    merchant = models.ForeignKey(
        Merchant, on_delete=models.CASCADE, null=True, blank=True
    )
    buyer_redirect_url = models.CharField(max_length=255, null=True, blank=True)
    seller_redirect_url = models.CharField(max_length=255, null=True, blank=True)
    webhook_url = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name}"
