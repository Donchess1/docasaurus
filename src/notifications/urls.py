from django.urls import path

from notifications.views.user import (
    UserNotificationDetailView,
    UserNotificationListView,
)

# fmt: off
urlpatterns = [
    path("", UserNotificationListView.as_view(), name="user-notifications"),
    path("<str:id>", UserNotificationDetailView.as_view(), name="user-notification-detail",),
]
# fmt: on
