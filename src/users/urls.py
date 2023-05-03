from django.urls import path
from rest_framework.routers import DefaultRouter

from users.views.base import UserViewSet
from users.views.buyer import RegisterBuyerView
from users.views.login import LoginView
from users.views.profile import UserProfile
from users.views.verify import VerifyOTPView

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="users")

urlpatterns = [
    path("register", RegisterBuyerView.as_view(), name="register-buyer"),
    path("verify", VerifyOTPView.as_view(), name="verify-email"),
    path("login", LoginView.as_view(), name="login"),
] + router.urls
