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
from console.views.entity_schema import DisputeSchemaView, TransactionSchemaView
from console.views.event import EventViewSet
from console.views.overview import (
    DisputeOverviewView,
    EmailLogOverviewView,
    TransactionChartView,
    TransactionOverviewView,
    UserOverviewView,
)
from console.views.product import ProductViewSet
from console.views.provider import EmailProviderSwitchView
from merchant.views.base import (
    ConsoleMerchantCustomerView,
    ConsoleGenerateMerchantApiKeyView,
    MerchantCreateView,
    MerchantDetailView,
    MerchantListView,
)
from transaction.views.activity_log import TransactionActivityLogListView
from transaction.views.transaction import TransactionListView
from transaction.views.user import TransactionDetailView

# fmt: off
router = DefaultRouter()
router.register(r"users", UserViewSet, basename="users")
router.register(r"events", EventViewSet, basename="events")
router.register(r"products", ProductViewSet, basename="products")

urlpatterns = [
    path("overview/users", UserOverviewView.as_view(), name="users-overview"),
    path("overview/emails", EmailLogOverviewView.as_view(), name="email-log-overview"),
    path("overview/transactions", TransactionOverviewView.as_view(), name="transactions-overview",),
    path("chart/transactions", TransactionChartView.as_view(), name="transactions-chart",),
    path("schema/transactions", TransactionSchemaView.as_view(), name="transactions-schema",),
    path("transactions", TransactionListView.as_view(), name="transactions"),
    path("transactions/<str:id>", TransactionDetailView.as_view(), name="transaction-detail-view",),
    path("transactions/<str:id>/activity-logs", TransactionActivityLogListView.as_view(), name="transaction-activity-logs",),
    path("overview/disputes", DisputeOverviewView.as_view(), name="disputes-overview"),
    path("schema/disputes", DisputeSchemaView.as_view(), name="disputes-schema",),
    path("disputes", DisputeListView.as_view(), name="disputes"),
    path("disputes/<uuid:id>", DisputeDetailView.as_view(), name="dispute-detail-view",),
    path("merchants", MerchantListView.as_view(), name="list-merchants",),
    path("merchants/create", MerchantCreateView.as_view(), name="create-merchants",),
    path("merchants/<uuid:id>", MerchantDetailView.as_view(), name="merchant-detail-view",),
    path("merchants/<uuid:id>/customers", ConsoleMerchantCustomerView.as_view(), name="merchant-detail-customers",),
    path("merchants/<uuid:id>/api-key", ConsoleGenerateMerchantApiKeyView.as_view(), name="generate-merchant-api-key",),
    path("check-email", CheckUserByEmailView.as_view(), name="user-detail-email-view",),
    path("check-phone-number", CheckUserByPhoneView.as_view(), name="user-detail-phone-view",),
    path("get-user-wallet", CheckUserWalletInfoByEmailView.as_view(), name="user-wallet-info-view",),
    path("switch-email-provider", EmailProviderSwitchView.as_view(), name="toggle-email-provider",),
    path("registration-metrics", UserRegistrationMetricsView.as_view(), name="console-metrics",),
] + router.urls
# fmt: on
