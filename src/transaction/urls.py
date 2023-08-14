from django.urls import path

from transaction.views.user import UserTransactionListView

urlpatterns = [
    path("user", UserTransactionListView.as_view(), name="user-transactions"),
]
