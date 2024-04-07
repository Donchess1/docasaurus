from django.urls import path

from merchant.views.base import (
    MerchantCreateView,
    MerchantListView,
    MerchantProfileView,
    MerchantResetKeyView,
)

urlpatterns = [
    path("list", MerchantListView.as_view(), name="list-merchants"),
    path("profile", MerchantProfileView.as_view(), name="merchant-profile"),
    path("create", MerchantCreateView.as_view(), name="create-merchants"),
    path("reset-api-key", MerchantResetKeyView.as_view(), name="reset-api-key"),
    # path("sellers", RegisterBuyerView.as_view(), name="register-merchant-seller"),
    # path("buyers", RegisterSellerView.as_view(), name="register-merchant-buyer"),
    # path("initiate-escrow", UpdateKYCView.as_view(), name="initiate-merchant-escrow"),
    # path("transactions", VerifyOTPView.as_view(), name="merchant-transactions"),
    # path("transactions/<str:id>",UserTransactionDetailView.as_view(),name="merchant-transaction-detail"),
]
