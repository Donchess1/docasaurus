from django.urls import path

from notifications.views.user import (
    UserNotificationDetailView,
    UserNotificationListView,
)

urlpatterns = [
    path("", UserNotificationListView.as_view(), name="user-notifications"),
    path(
        "<str:id>",
        UserNotificationDetailView.as_view(),
        name="user-notification-detail",
    ),
]
