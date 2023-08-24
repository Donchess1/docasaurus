from rest_framework.permissions import BasePermission


class TransactionHistoryOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        # Check if the user is the owner of the transaction
        return obj.user_id == request.user.id


class IsBuyer(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user.is_authenticated and request.user.is_buyer


class IsSeller(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user.is_authenticated and request.user.is_seller


class IsTransactionStakeholder(BasePermission):
    def has_object_permission(self, request, view, obj):
        # Check if the user is the owner of the transaction or partner_email matches
        if request.method in ["GET", "HEAD"]:
            # Allow reading for buyer, seller, or partner_email match
            return (
                obj.user_id == request.user.id
                or obj.escrowmeta.partner_email == request.user.email
            )
        elif request.method in ["PUT", "PATCH", "DELETE"]:
            # Allow updating and deleting only for the owner of partner_email on escrowmeta
            return obj.escrowmeta.partner_email == request.user.email
        return False
