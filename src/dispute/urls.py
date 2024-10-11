from django.urls import path

from dispute.views.user import DisputeDetailView, UserDisputeView

# fmt: off
urlpatterns = [
    path("", UserDisputeView.as_view(), name="user-disputes"),
    path("<uuid:id>", DisputeDetailView.as_view(), name="dispute-detail"),
]
# fmt: on
