from django.urls import include, path
from rest_framework.routers import DefaultRouter

from merchant.views.payout import PayoutConfigViewSet

router = DefaultRouter()
router.register(r"payout-config", PayoutConfigViewSet)
from merchant.views.base import (
    MerchantApiKeyView,
    MerchantCreateView,
    MerchantCustomerView,
    MerchantListView,
    MerchantProfileView,
)
from merchant.views.customer import (
    ConfirmMerchantWalletWithdrawalView,
    CustomerTransactionDetailView,
    CustomerTransactionListView,
    CustomerWidgetSessionView,
    InitiateMerchantWalletWithdrawalView,
)
from merchant.views.transaction import (
    InitiateMerchantEscrowTransactionView,
    MerchantEscrowTransactionRedirectView,
    MerchantSettlementTransactionListView,
    MerchantTransactionListView,
    UnlockEscrowFundsView,
)

urlpatterns = [
    path("", include(router.urls)),
    path("list", MerchantListView.as_view(), name="list-merchants"),
    path("profile", MerchantProfileView.as_view(), name="merchant-profile"),
    path("create", MerchantCreateView.as_view(), name="create-merchants"),
    path("api-key", MerchantApiKeyView.as_view(), name="merchant-api-key"),
    path(
        "customers", MerchantCustomerView.as_view(), name="register-merchant-customer"
    ),
    path(
        "customers/unlock-funds",
        UnlockEscrowFundsView.as_view(),
        name="unlock-customer-escrow-funds",
    ),
    path(
        "transactions",
        MerchantTransactionListView.as_view(),
        name="merchant-transactions",
    ),
    path(
        "settlements",
        MerchantSettlementTransactionListView.as_view(),
        name="merchant-settlement-transactions",
    ),
    path(
        "customer-transactions",
        CustomerTransactionListView.as_view(),
        name="customer-transactions",
    ),
    path(
        "customer-transactions/<uuid:id>",
        CustomerTransactionDetailView.as_view(),
        name="customer-transaction-detail-view",
    ),
    path(
        "initiate-escrow",
        InitiateMerchantEscrowTransactionView.as_view(),
        name="initiate-merchant-escrow",
    ),
    path(
        "customers/initiate-withdrawal",
        InitiateMerchantWalletWithdrawalView.as_view(),
        name="initiate-wallet-withdrawal",
    ),
    path(
        "customers/confirm-withdrawal",
        ConfirmMerchantWalletWithdrawalView.as_view(),
        name="confirm-wallet-withdrawal",
    ),
    path(
        "escrow-redirect",
        MerchantEscrowTransactionRedirectView.as_view(),
        name="validate-merchant-escrow-payment",
    ),
    path(
        "generate-widget-session",
        CustomerWidgetSessionView.as_view(),
        name="customer-widget-session",
    ),
]
