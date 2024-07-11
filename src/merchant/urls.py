from django.urls import include, path
from rest_framework.routers import DefaultRouter

from merchant.views.base import (
    MerchantApiKeyView,
    MerchantCreateView,
    MerchantCustomerDetailView,
    MerchantCustomerView,
    MerchantListView,
    MerchantProfileView,
    MerchantWalletsView,
)
from merchant.views.customer import (
    ConfirmMerchantWalletWithdrawalByMerchantView,
    ConfirmMerchantWalletWithdrawalView,
    CustomerTransactionDetailView,
    CustomerTransactionListView,
    CustomerWidgetSessionView,
    InitiateMerchantWalletWithdrawalByMerchantView,
    InitiateMerchantWalletWithdrawalView,
)
from merchant.views.payout import PayoutConfigViewSet
from merchant.views.transaction import (
    InitiateMerchantEscrowTransactionView,
    MandateFundsReleaseView,
    MerchantEscrowTransactionRedirectView,
    MerchantSettlementTransactionListView,
    MerchantTransactionListView,
    ReleaseEscrowFundsByMerchantView,
    UnlockEscrowFundsByBuyerView,
)

router = DefaultRouter()
router.register(r"payout-config", PayoutConfigViewSet)
urlpatterns = [
    path("list", MerchantListView.as_view(), name="list-merchants"),
    path("create", MerchantCreateView.as_view(), name="create-merchants"),
    path("api-key", MerchantApiKeyView.as_view(), name="merchant-api-key"),
    # =================================================================
    # MERCHANT AUTHORIZED CALLS VIA API KEY
    # =================================================================
    path("", include(router.urls)),  # payout config
    path("profile", MerchantProfileView.as_view(), name="merchant-profile"),
    path("wallets", MerchantWalletsView.as_view(), name="merchant-wallets"),
    path(
        "customers", MerchantCustomerView.as_view(), name="register-merchant-customer"
    ),
    path(
        "customers/<int:id>",
        MerchantCustomerDetailView.as_view(),
        name="merchant-customer-user-detail",
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
        "customer-transactions/<uuid:id>/mandate-release",
        MandateFundsReleaseView.as_view(),
        name="consent-funds-release",
    ),
    path(
        "customer-transactions/<uuid:id>/release-funds",
        ReleaseEscrowFundsByMerchantView.as_view(),
        name="unlock-customer-escrow-funds-merchant",
    ),
    path(
        "initiate-customer-withdrawal",
        InitiateMerchantWalletWithdrawalByMerchantView.as_view(),
        name="initiate-customer-wallet-withdrawal",
    ),
    path(
        "confirm-customer-withdrawal",
        ConfirmMerchantWalletWithdrawalByMerchantView.as_view(),
        name="confirm-customer-wallet-withdrawal",
    ),
    # =================================================================
    # ESCROW INITIALIZATION & VERIFICATION
    # =================================================================
    path(
        "initiate-escrow",
        InitiateMerchantEscrowTransactionView.as_view(),
        name="initiate-merchant-escrow",
    ),
    path(
        "escrow-redirect",
        MerchantEscrowTransactionRedirectView.as_view(),
        name="validate-merchant-escrow-payment",
    ),
    # =================================================================
    # MERCHANT WIDGET API
    # =================================================================
    path(
        "generate-widget-session",
        CustomerWidgetSessionView.as_view(),
        name="customer-widget-session",
    ),
    path(
        "customer-transactions",
        CustomerTransactionListView.as_view(),
        name="customer-transactions",
    ),
    path(
        "customers/unlock-funds",
        UnlockEscrowFundsByBuyerView.as_view(),
        name="unlock-customer-escrow-funds-buyer",
    ),
    path(
        "customer-transactions/<uuid:id>",
        CustomerTransactionDetailView.as_view(),
        name="customer-transaction-detail-view",
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
    # =================================================================
    # =================================================================
]
