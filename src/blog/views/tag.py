from rest_framework import filters, permissions, status, viewsets

from blog.models import Tag
from blog.permissions import IsAuthorOrAdmin
from blog.serializers import TagSerializer
from utils.pagination import CustomPagination
from utils.response import Response


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all().order_by("name")
    serializer_class = TagSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter]
    pagination_class = CustomPagination
    search_fields = ["name"]

    def get_permissions(self):
        if self.action in ["create", "destroy", "update"]:
            self.permission_classes = [IsAuthorOrAdmin]
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        """Handle Tag creation."""
        data = request.data
        serializer = self.get_serializer(data=data)
        if not serializer.is_valid():
            return Response(
                status_code=status.HTTP_400_BAD_REQUEST,
                success=False,
                errors=serializer.errors,
            )
        tag_name = serializer.validated_data.get("name")
        if Tag.objects.filter(name=tag_name.upper()).exists():
            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                message=f"Tag '{tag_name.upper()}' already exists.",
            )
        serializer.save()
        return Response(
            status_code=status.HTTP_201_CREATED,
            success=True,
            data=serializer.data,
            message="Tag created successfully.",
        )

    def update(self, request, *args, **kwargs):
        """Handle updating a Tag."""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                status_code=status.HTTP_200_OK,
                success=True,
                data=serializer.data,
                message="Tag updated successfully.",
            )
        return Response(
            status_code=status.HTTP_400_BAD_REQUEST,
            success=False,
            errors=serializer.errors,
            message="Failed to update tag.",
        )

    def retrieve(self, request, *args, **kwargs):
        """Retrieve a specific Tag."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(
            status_code=status.HTTP_200_OK,
            success=True,
            data=serializer.data,
            message="Tag retrieved successfully.",
        )

    def list(self, request, *args, **kwargs):
        """List all Tags."""
        queryset = self.filter_queryset(self.get_queryset())
        qs = self.paginate_queryset(queryset)
        serializer = self.get_serializer(qs, many=True)
        self.pagination_class.message = "Tags retrieved successfully"
        response = self.get_paginated_response(
            serializer.data,
        )
        return response

    def destroy(self, request, *args, **kwargs):
        """Delete a Tag."""
        instance = self.get_object()
        instance.delete()
        return Response(
            status_code=status.HTTP_204_NO_CONTENT,
            success=True,
            message="Tag deleted successfully.",
        )
