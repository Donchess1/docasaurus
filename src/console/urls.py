from django.urls import path
from rest_framework.routers import DefaultRouter

from console.views.base import UserViewSet
from console.views.webhook import FlwBankTransferWebhookView

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="users")

urlpatterns = [
    path(
        "webhook/flw", FlwBankTransferWebhookView.as_view(), name="verify-bank-transfer"
    ),
] + router.urls
