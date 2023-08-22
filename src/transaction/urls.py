from django.urls import path

from transaction.views.user import (
    FundEscrowTransactionView,
    InitiateEscrowTransactionView,
    LockEscrowFundsView,
    TransactionDetailView,
    UserTransactionListView,
)

urlpatterns = [
    path("user", UserTransactionListView.as_view(), name="user-transactions"),
    path(
        "escrow",
        InitiateEscrowTransactionView.as_view(),
        name="initiate-escrow-transaction",
    ),
    path(
        "lock-funds",
        LockEscrowFundsView.as_view(),
        name="lock-escrow-funds",
    ),
    path(
        "fund-escrow",
        FundEscrowTransactionView.as_view(),
        name="fund-escrow",
    ),
    path(
        "link/<str:id>",
        TransactionDetailView.as_view(),
        name="transaction-detail-view",
    ),
]
