from django.urls import path

from users.views.buyer import RegisterBuyerView
from users.views.login import LoginView
from users.views.password import (
    ChangePasswordView,
    ForgotPasswordView,
    ResetPasswordView,
)
from users.views.profile import EndUserTourGuideView, UserProfileView
from users.views.seller import RegisterSellerView
from users.views.user import (
    EditSellerBusinessProfileView,
    EditUserProfileView,
    UpdateKYCView,
    UploadAvatarView,
)
from users.views.verify import ResendAccountVerificationOTPView, VerifyOTPView

urlpatterns = [
    path("register", RegisterBuyerView.as_view(), name="register-buyer"),
    path("register/seller", RegisterSellerView.as_view(), name="register-seller"),
    path("kyc", UpdateKYCView.as_view(), name="update-kyc"),
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
    path("end-tour-guide", EndUserTourGuideView.as_view(), name="end-tour-guide"),
    path("profile/edit", EndUserTourGuideView.as_view(), name="user-profile-edit"),
    path("profile/upload", UploadAvatarView.as_view(), name="user-profile-upload"),
    path(
        "profile/business",
        EditSellerBusinessProfileView.as_view(),
        name="seller-business-profile-edit",
    ),
]
