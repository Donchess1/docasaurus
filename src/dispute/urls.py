from django.urls import path

from dispute.views.user import DisputeDetailView, UserDisputeView

urlpatterns = [
    path("", UserDisputeView.as_view(), name="user-disputes"),
    path("<uuid:id>", DisputeDetailView.as_view(), name="dispute-detail"),
]
