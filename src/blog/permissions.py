from rest_framework import permissions


class IsAuthorOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow authors or admin to edit/delete blog posts.
    """

    def has_object_permission(self, request, view, obj):
        # Check if the user is an admin
        if request.user.is_admin:
            return True
        # Check if the user is the author of the blog post
        return obj.author == request.user
