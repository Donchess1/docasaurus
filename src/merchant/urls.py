from django.urls import path

from merchant.views.base import (
    MerchantCreateView,
    MerchantCustomerView,
    MerchantListView,
    MerchantProfileView,
    MerchantResetKeyView,
)
from merchant.views.customer import (
    CustomerTransactionDetailView,
    CustomerTransactionListView,
    CustomerWidgetSessionView,
)
from merchant.views.transaction import (
    InitiateMerchantEscrowTransactionView,
    MerchantEscrowTransactionRedirectView,
    MerchantTransactionListView,
    UnlockEscrowFundsView,
)

urlpatterns = [
    path("list", MerchantListView.as_view(), name="list-merchants"),
    path("profile", MerchantProfileView.as_view(), name="merchant-profile"),
    path("create", MerchantCreateView.as_view(), name="create-merchants"),
    path("reset-api-key", MerchantResetKeyView.as_view(), name="reset-api-key"),
    path(
        "customers", MerchantCustomerView.as_view(), name="register-merchant-customer"
    ),
    # path(
    #     "customers/unlock-funds",
    #     UnlockEscrowFundsView.as_view(),
    #     name="unlock-customer-escrow-funds",
    # ),
    path(
        "transactions",
        MerchantTransactionListView.as_view(),
        name="merchant-transactions",
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
