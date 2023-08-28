from django.urls import path

from dispute.views.user import UserDisputeView

urlpatterns = [
    path("", UserDisputeView.as_view(), name="user-disputes"),
]
