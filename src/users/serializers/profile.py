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
            "free_escrow_transactions",
            "phone_number_flagged",
            # "wallet_balance", # DEPRECATED
            # "locked_amount", # DEPRECATED
            # "unlocked_amount", # DEPRECATED
            # "withdrawn_amount", # DEPRECATED
            "created_at",
            "updated_at",
            "show_tour_guide",
            "last_login_date",
            "bank_account_id",
            "business_id",
            "kyc_id",
            "is_flagged",
            "is_deactivated",
            "unread_notification_count",
        )

    def get_unread_notification_count(self, obj):
        return obj.notification_count()
