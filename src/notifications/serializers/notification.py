from rest_framework import serializers

from notifications.models.notification import UserNotification


class UserNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserNotification
        fields = (
            "id",
            "user",
            "category",
            "title",
            "content",
            "is_seen",
            "action_url",
            "created_at",
            "updated_at",
        )
