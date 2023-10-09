from django.urls import path

from users.views.buyer import RegisterBuyerView
from users.views.login import LoginView
from users.views.password import (
    ChangePasswordView,
    ForgotPasswordView,
    ResetPasswordView,
)
from users.views.profile import UserProfileView
from users.views.seller import RegisterSellerView
from users.views.user import (
    EditSellerBusinessProfileView,
    EditUserProfileView,
    UploadAvatarView,
)
from users.views.verify import ResendAccountVerificationOTPView, VerifyOTPView

urlpatterns = [
    path("register", RegisterBuyerView.as_view(), name="register-buyer"),
    path("register/seller", RegisterSellerView.as_view(), name="register-seller"),
    path(
        "resend-otp",
        ResendAccountVerificationOTPView.as_view(),
        name="resend-account-otp",
    ),
    path("verify-account", VerifyOTPView.as_view(), name="verify-email"),
    path("login", LoginView.as_view(), name="login"),
    path("forgot-password", ForgotPasswordView.as_view(), name="forgot-password"),
    path("reset-password", ResetPasswordView.as_view(), name="reset-password"),
    path("change-password", ChangePasswordView.as_view(), name="change-password"),
    path("profile", UserProfileView.as_view(), name="user-profile"),
    path("profile/edit", EditUserProfileView.as_view(), name="user-profile-edit"),
    path("profile/upload", UploadAvatarView.as_view(), name="user-profile-upload"),
    path(
        "profile/business",
        EditSellerBusinessProfileView.as_view(),
        name="seller-business-profile-edit",
    ),
]
