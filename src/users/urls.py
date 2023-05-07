from django.urls import path

from users.views.buyer import RegisterBuyerView
from users.views.login import LoginView
from users.views.password import ForgotPasswordView, ResetPasswordView
from users.views.profile import UserProfileView
from users.views.seller import RegisterSellerView
from users.views.verify import VerifyOTPView

urlpatterns = [
    path("register", RegisterBuyerView.as_view(), name="register-buyer"),
    path("register/seller", RegisterSellerView.as_view(), name="register-seller"),
    path("verify-account", VerifyOTPView.as_view(), name="verify-email"),
    path("login", LoginView.as_view(), name="login"),
    path("forgot-password", ForgotPasswordView.as_view(), name="forgot-password"),
    path("reset-password", ResetPasswordView.as_view(), name="reset-password"),
    path("profile", UserProfileView.as_view(), name="user-profile"),
]
