from django.urls import path

from users.views.bank import UserBankAccountListCreateView
from users.views.buyer import RegisterBuyerView
from users.views.login import LoginView
from users.views.merchant import RegisterMerchantView
from users.views.password import (
    ChangePasswordView,
    ForgotPasswordView,
    ResetPasswordView,
    MerchantForgotPasswordView,
)
from users.views.profile import EndUserTourGuideView, UserProfileView
from users.views.seller import RegisterSellerView
from users.views.user import (
    EditSellerBusinessProfileView,
    EditUserProfileView,
    GenerateOneTimeLoginCodeView,
    GenerateOneTimeVerificationCodeView,
    UpdateKYCView,
    UploadAvatarView,
)
from users.views.verify import (
    ResendAccountVerificationOTPView,
    VerifyOneTimeLoginCodeView,
    VerifyOTPView,
)
from users.views.wallet import UserWalletListView

# fmt: off
urlpatterns = [
    # =================================================================
    # USER ONBOARDING & LOGIN
    # =================================================================
    path("register", RegisterBuyerView.as_view(), name="register-buyer"),
    path("register/seller", RegisterSellerView.as_view(), name="register-seller"),
    path("register/merchant", RegisterMerchantView.as_view(), name="register-merchant"),
    path("resend-otp", ResendAccountVerificationOTPView.as_view(), name="resend-account-otp",),
    path("verify-account", VerifyOTPView.as_view(), name="verify-email"),
    path("login", LoginView.as_view(), name="login"),
    path("send-login-otc", GenerateOneTimeLoginCodeView.as_view(), name="send-login-otc"),
    path("verify-login-otc", VerifyOneTimeLoginCodeView.as_view(), name="verify-login-otc",),
    path("generate-otc", GenerateOneTimeVerificationCodeView.as_view(), name="send-login-otc"),
    path("verify-otc", VerifyOneTimeLoginCodeView.as_view(), name="verify-login-otc",),
    # =================================================================
    # USER PROFILE MANAGEMENT
    # =================================================================
    path("profile", UserProfileView.as_view(), name="user-profile"),
    path("wallets", UserWalletListView.as_view(), name="user-wallets",),
    path("bank-accounts", UserBankAccountListCreateView.as_view(), name="user-bank-accounts",),
    path("end-tour-guide", EndUserTourGuideView.as_view(), name="end-tour-guide"),
    path("kyc", UpdateKYCView.as_view(), name="update-kyc"),
    path("profile/edit", EditUserProfileView.as_view(), name="user-profile-edit"),
    path("profile/upload", UploadAvatarView.as_view(), name="user-profile-upload"),
    path("profile/business", EditSellerBusinessProfileView.as_view(), name="seller-business-profile-edit",),
    # =================================================================
    # PASSWORD RESET 
    # =================================================================
    path("forgot-password", ForgotPasswordView.as_view(), name="forgot-password"),
    path("reset-password", ResetPasswordView.as_view(), name="reset-password"),
    path("change-password", ChangePasswordView.as_view(), name="change-password"),
    path("merchant/forgot-password", MerchantForgotPasswordView.as_view(), name="merchant-forgot-password"),
]
# fmt: on
