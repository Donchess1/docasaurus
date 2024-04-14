from django.urls import path

from merchant.views.base import (
    MerchantCreateView,
    MerchantCustomerView,
    MerchantListView,
    MerchantProfileView,
    MerchantResetKeyView,
)
from merchant.views.transaction import (
    InitiateMerchantEscrowTransactionView,
    MerchantEscrowTransactionRedirectView,
    MerchantTransactionListView,
)

urlpatterns = [
    path("list", MerchantListView.as_view(), name="list-merchants"),
    path("profile", MerchantProfileView.as_view(), name="merchant-profile"),
    path("create", MerchantCreateView.as_view(), name="create-merchants"),
    path("reset-api-key", MerchantResetKeyView.as_view(), name="reset-api-key"),
    path(
        "customers", MerchantCustomerView.as_view(), name="register-merchant-customer"
    ),
    path(
        "transactions",
        MerchantTransactionListView.as_view(),
        name="merchant-transactions",
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
    # path("transactions/<str:id>",UserTransactionDetailView.as_view(),name="merchant-transaction-detail"),
]
