from rest_framework.permissions import BasePermission


class TransactionHistoryOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        # Check if the user is the owner of the transaction
        return obj.user_id == request.user.id


class IsTransactionStakeholder(BasePermission):
    def has_object_permission(self, request, view, obj):
        # Check if the user is the owner of the transaction
        return obj.user_id == request.user.id
