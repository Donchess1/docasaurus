from rest_framework import serializers

from users.models.profile import UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    unread_notification_count = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = (
            "id",
            "user_id",
            "user_type",
            "avatar",
            "profile_link",
            "wallet_balance",
            "locked_amount",
            "unlocked_amount",
            "free_escrow_transactions",
            "phone_number_flagged",
            "withdrawn_amount",
            "created_at",
            "updated_at",
            "show_tour_guide",
            "last_login_date",
            "bank_account_id",
            "business_id",
            "kyc_id",
            "unread_notification_count",
        )

    def get_unread_notification_count(self, obj):
        return obj.notification_count()
