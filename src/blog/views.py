from drf_yasg.utils import swagger_auto_schema
from rest_framework import filters, generics, permissions, status

from utils.pagination import CustomPagination
from utils.response import Response

from .models import BlogPost
from .permissions import IsAuthorOrAdmin
from .serializers import BlogPostSerializer


class BlogPostListCreateView(generics.ListCreateAPIView):
    queryset = BlogPost.objects.all().order_by("-created_at")
    serializer_class = BlogPostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = CustomPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ["title", "content"]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @swagger_auto_schema(
        operation_description="List all Blog posts",
        responses={
            200: BlogPostSerializer,
        },
    )
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        qs = self.paginate_queryset(queryset)
        serializer = self.get_serializer(qs, many=True)
        self.pagination_class.message = "Blog Posts retrieved successfully"
        response = self.get_paginated_response(
            serializer.data,
        )
        return response

    @swagger_auto_schema(
        operation_description="Add a new Blog Post",
        request_body=BlogPostSerializer,
        responses={
            201: BlogPostSerializer,
        },
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data,
        )
        if not serializer.is_valid():
            return Response(
                success=False,
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        self.perform_create(serializer)
        return Response(
            success=True,
            message="Blog Post Created",
            status_code=status.HTTP_201_CREATED,
            data=serializer.data,
        )


class BlogPostRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = BlogPost.objects.all()
    serializer_class = BlogPostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrAdmin]

    @swagger_auto_schema(
        operation_description="Retrieve a Blog Post",
        responses={
            200: BlogPostSerializer,
        },
    )
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(
            success=True,
            data=serializer.data,
            message="Blog Post retrieved",
            status_code=status.HTTP_200_OK,
        )

    @swagger_auto_schema(
        operation_description="Update a Blog Post",
        request_body=BlogPostSerializer,
        responses={
            200: BlogPostSerializer,
        },
    )
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if not serializer.is_valid():
            return Response(
                success=False,
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        self.perform_update(serializer)
        return Response(
            success=True,
            message="Blog Post Updated",
            status_code=status.HTTP_200_OK,
            data=serializer.data,
        )

    @swagger_auto_schema(
        operation_description="Delete a Blog Post",
        responses={
            204: "No content",
        },
    )
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            success=True,
            message="Blog Post Deleted",
            status_code=status.HTTP_204_NO_CONTENT,
        )
