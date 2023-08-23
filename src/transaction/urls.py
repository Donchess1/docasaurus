from django.urls import path

from transaction.views.transaction import TransactionListView
from transaction.views.user import (
    FundEscrowTransactionView,
    InitiateEscrowTransactionView,
    LockEscrowFundsView,
    TransactionDetailView,
    UnlockEscrowFundsView,
    UserTransactionListView,
)

urlpatterns = [
    path("", TransactionListView.as_view(), name="transactions"),
    path("user", UserTransactionListView.as_view(), name="user-transactions"),
    path(
        "initiate-escrow",
        InitiateEscrowTransactionView.as_view(),
        name="initiate-escrow-transaction",
    ),
    path(
        "lock-funds",
        LockEscrowFundsView.as_view(),
        name="lock-escrow-funds",
    ),
    path(
        "unlock-funds",
        UnlockEscrowFundsView.as_view(),
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
