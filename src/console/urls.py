from django.urls import path
from rest_framework.routers import DefaultRouter

from console.views.base import CheckUserByEmailView, CheckUserByPhoneView, UserViewSet
from console.views.dispute import DisputeDetailView, DisputeListView
from console.views.webhook import FlwPayoutWebhookView
from transaction.views.transaction import TransactionListView
from transaction.views.user import TransactionDetailView

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="users")

urlpatterns = [
    path("webhook/flw", FlwPayoutWebhookView.as_view(), name="payout-webhook"),
    path("transactions", TransactionListView.as_view(), name="transactions"),
    path(
        "transactions/<str:id>",
        TransactionDetailView.as_view(),
        name="transaction-detail-view",
    ),
    path("disputes", DisputeListView.as_view(), name="disputes"),
    path(
        "disputes/<uuid:id>",
        DisputeDetailView.as_view(),
        name="dispute-detail-view",
    ),
    path(
        "check-email",
        CheckUserByEmailView.as_view(),
        name="user-detail-email-view",
    ),
    path(
        "check-phone-number",
        CheckUserByPhoneView.as_view(),
        name="user-detail-phone-view",
    ),
] + router.urls
