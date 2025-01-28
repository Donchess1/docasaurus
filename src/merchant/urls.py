from django.urls import include, path
from rest_framework.routers import DefaultRouter

from merchant.views.base import (
    ConfirmMerchantWalletWithdrawalView,
    InitiateMerchantWalletWithdrawalView,
    MerchantApiKeyView,
    MerchantCustomerDetailView,
    MerchantCustomerView,
    MerchantProfileByAPIKeyView,
    MerchantProfileView,
    MerchantWalletsView,
)
from merchant.views.customer import (
    ConfirmCustomerWalletWithdrawalByMerchantView,
    ConfirmCustomerWidgetWalletWithdrawalView,
    CustomerTransactionDetailView,
    CustomerTransactionListView,
    CustomerWidgetSessionView,
    InitiateCustomerWalletWithdrawalByMerchantView,
    InitiateCustomerWidgetWalletWithdrawalView,
    MerchantDashboardCustomerTransactionDetailView,
    MerchantDashboardCustomerTransactionListByUserIdView,
)
from merchant.views.dispute import (
    MerchantDashboardCustomerDisputeDetailView,
    MerchantDashboardCustomerDisputeListView,
    MerchantDisputeDetailView,
    MerchantDisputeListView,
)
from merchant.views.payout import PayoutConfigViewSet
from merchant.views.transaction import (
    InitiateMerchantEscrowTransactionView,
    MandateFundsReleaseView,
    MerchantEscrowTransactionRedirectView,
    MerchantSettlementTransactionListView,
    MerchantTransactionActivityLogView,
    MerchantTransactionDetailView,
    MerchantTransactionListView,
    ReleaseEscrowFundsByMerchantView,
    UnlockEscrowFundsByBuyerView,
)

# fmt: off
router = DefaultRouter()
router.register(r"payout-config", PayoutConfigViewSet)
urlpatterns = [
    path("api-key", MerchantApiKeyView.as_view(), name="merchant-api-key"),
    path("profile-info", MerchantProfileView.as_view(), name="merchant-profile"),
    # =================================================================
    # MERCHANT AUTHORIZED CALLS VIA API KEY or JWT TOKEN
    # =================================================================
    path("", include(router.urls)),  # payout config
    path("profile", MerchantProfileByAPIKeyView.as_view(), name="merchant-profile-by-api-key"),
    path("wallets", MerchantWalletsView.as_view(), name="merchant-wallets"),
    path("initiate-withdrawal", InitiateMerchantWalletWithdrawalView.as_view(), name="initiate-merchant-wallet-withdrawal",),
    path("confirm-withdrawal", ConfirmMerchantWalletWithdrawalView.as_view(), name="confirm-merchant-wallet-withdrawal",),
    path("customers", MerchantCustomerView.as_view(), name="register-merchant-customer"),
    path("customers/<int:id>", MerchantCustomerDetailView.as_view(), name="merchant-customer-user-detail",),
    path("transactions", MerchantTransactionListView.as_view(), name="merchant-transactions",),
    path("transactions/<str:id>", MerchantTransactionDetailView.as_view(), name="merchant-transaction-detail",),
    path("transactions/<str:id>/activity-logs", MerchantTransactionActivityLogView.as_view(), name="merchant-transaction-detail-activity-logs",),
    path("settlements", MerchantSettlementTransactionListView.as_view(), name="merchant-settlement-transactions",),
    path("disputes", MerchantDisputeListView.as_view(), name="merchant-disputes",),
    path("disputes/<uuid:id>", MerchantDisputeDetailView.as_view(), name="merchant-dispute-detail",),
    path("customer-transactions/<str:id>/mandate-release", MandateFundsReleaseView.as_view(), name="consent-funds-release",),
    path("customer-transactions/<str:id>/release-funds", ReleaseEscrowFundsByMerchantView.as_view(), name="unlock-customer-escrow-funds-merchant",),
    path("initiate-customer-withdrawal", InitiateCustomerWalletWithdrawalByMerchantView.as_view(), name="initiate-customer-wallet-withdrawal",),
    path("confirm-customer-withdrawal", ConfirmCustomerWalletWithdrawalByMerchantView.as_view(), name="confirm-customer-wallet-withdrawal",),
    # DASHBOARD x CUSTOMER MANAGEMENT
    path("dashboard/customer-transactions", MerchantDashboardCustomerTransactionListByUserIdView.as_view(), name="dasboard-customer-transactions",),
    path("dashboard/customer-transactions/<uuid:id>", MerchantDashboardCustomerTransactionDetailView.as_view(), name="dasboard-customer-transaction-detail",),
    path("dashboard/customer-disputes", MerchantDashboardCustomerDisputeListView.as_view(), name="dasboard-customer-disputes",),
    path("dashboard/customer-disputes/<uuid:id>", MerchantDashboardCustomerDisputeDetailView.as_view(), name="dasboard-customer-dispute-detail",),
    # path("dashboard/disputes", CustomerTransactionListByUserIdView.as_view(), name="dasboard-customer-transactions",),
    # =================================================================
    # ESCROW INITIALIZATION & VERIFICATION
    # =================================================================
    path("initiate-escrow", InitiateMerchantEscrowTransactionView.as_view(), name="initiate-merchant-escrow",),
    path("escrow-redirect", MerchantEscrowTransactionRedirectView.as_view(), name="validate-merchant-escrow-payment",),
    # =================================================================
    # MERCHANT WIDGET API
    # =================================================================
    path("generate-widget-session", CustomerWidgetSessionView.as_view(), name="customer-widget-session",),
    path("customer-transactions", CustomerTransactionListView.as_view(), name="customer-transactions",),
    # this next endpoint is used to retrieve an escrow transaction and also create a dispute if needed
    path("customer-transactions/<uuid:id>", CustomerTransactionDetailView.as_view(), name="customer-transaction-detail-view",),
    path("customers/unlock-funds", UnlockEscrowFundsByBuyerView.as_view(), name="unlock-customer-escrow-funds-buyer",),
    path("customers/initiate-withdrawal", InitiateCustomerWidgetWalletWithdrawalView.as_view(), name="initiate-customer-widget-wallet-withdrawal",),
    path("customers/confirm-withdrawal", ConfirmCustomerWidgetWalletWithdrawalView.as_view(), name="confirm-customer-widget-wallet-withdrawal",
    ),
    # =================================================================
    # =================================================================
]
# fmt: on
