from rest_framework import permissions


class IsAuthorOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow authors or admin to edit/delete blog posts.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        # Check if the user is the author of the blog post or is an admin
        return obj.author == request.user or (request.user and request.user.is_admin)
