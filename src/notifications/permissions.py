from rest_framework import permissions

from .models.user import CustomUser


class IsUserOwnedResource(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        business_accounts = BusinessAccount.objects.filter(users=request.user)
        if business_accounts.exists() == False:
            business_accounts = BusinessAccount.objects.filter(user=request.user)
        return obj.business_account in business_accounts
