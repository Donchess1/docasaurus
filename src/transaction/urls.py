from django.urls import path

from transaction.views.user import (
    FundEscrowTransactionView,
    InitiateEscrowTransactionView,
    LockEscrowFundsView,
    UnlockEscrowFundsView,
    UserLockedEscrowTransactionListView,
    UserTransactionDetailView,
    UserTransactionListView,
)

urlpatterns = [
    path("", UserTransactionListView.as_view(), name="user-transactions"),
    path(
        "locked-escrows",
        UserLockedEscrowTransactionListView.as_view(),
        name="user-locked-escrow-transactions",
    ),
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
        "fund-escrow",
        FundEscrowTransactionView.as_view(),
        name="fund-escrow",
    ),
    path(
        "unlock-funds",
        UnlockEscrowFundsView.as_view(),
        name="lock-escrow-funds",
    ),
    path(
        "link/<str:id>",
        UserTransactionDetailView.as_view(),
        name="user-transaction-detail-view",
    ),
]
