from django.urls import path

from transaction.views.user import (
    InitiateEscrowTransactionView,
    UserTransactionListView,
)

urlpatterns = [
    path("user", UserTransactionListView.as_view(), name="user-transactions"),
    path(
        "escrow",
        InitiateEscrowTransactionView.as_view(),
        name="initiate-escrow-transaction",
    ),
]
