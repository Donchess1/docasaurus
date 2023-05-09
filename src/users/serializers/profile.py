from rest_framework import serializers

from users.models.profile import UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = (
            "id",
            "user_id",
            "avatar",
            "profile_link",
            "wallet_balance",
            "locked_amount",
            "unlocked_amount",
            "created_at",
            "updated_at",
            "last_login_date",
            "bank_account_id",
            "business_id",
            "kyc_id",
        )
