from django.urls import path
from rest_framework.routers import DefaultRouter

from console.views.base import (
    CheckUserByEmailView,
    CheckUserByPhoneView,
    CheckUserWalletInfoByEmailView,
    UserRegistrationMetricsView,
    UserViewSet,
)
from console.views.dispute import DisputeDetailView, DisputeListView
from transaction.views.transaction import TransactionListView
from transaction.views.user import TransactionDetailView

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="users")

urlpatterns = [
    path(
        "registration-metrics",
        UserRegistrationMetricsView.as_view(),
        name="console-metrics",
    ),
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
    path(
        "get-user-wallet",
        CheckUserWalletInfoByEmailView.as_view(),
        name="user-wallet-info-view",
    ),
] + router.urls
