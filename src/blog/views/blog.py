from django.utils import timezone
from django_filters import rest_framework as django_filters
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action

from blog.filter import BlogFilter
from blog.models import BlogPost, Tag
from blog.permissions import IsAuthorOrAdmin
from blog.serializers import BlogPostSerializer
from utils.pagination import CustomPagination
from utils.response import Response


class BlogPostViewSet(viewsets.ModelViewSet):
    queryset = BlogPost.objects.all().order_by("-created_at")
    serializer_class = BlogPostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = CustomPagination
    filter_backends = [django_filters.DjangoFilterBackend, filters.SearchFilter]
    search_fields = ["title", "content", "tags__name"]
    filterset_class = BlogFilter

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_permissions(self):
        if self.action in ["create", "update", "add_tags", "remove_tags"]:
            self.permission_classes = [IsAuthorOrAdmin]
        return super().get_permissions()

    def manage_tags(self, tags_string):
        tag_names = [tag.strip() for tag in tags_string.split(",") if tag.strip()]
        tags = [
            Tag.objects.get_or_create(name=tag_name.upper())[0]
            for tag_name in tag_names
        ]
        return tags

    def destroy(self, request, *args, **kwargs):
        return Response(
            success=False,
            message="Action not permitted!",
            status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    @swagger_auto_schema(
        operation_description="Add a new Blog Post",
        request_body=BlogPostSerializer,
        responses={
            201: BlogPostSerializer,
        },
    )
    def create(self, request, *args, **kwargs):
        tag_names = request.data.get("tags", "")
        tags = self.manage_tags(tag_names)
        serializer = self.get_serializer(data=request.data, context={"tags": tags})
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

    @swagger_auto_schema(
        operation_description="Update Blog Post",
        request_body=BlogPostSerializer,
        responses={
            201: BlogPostSerializer,
        },
    )
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        tag_names = request.data.get("tags", "")
        tags = self.manage_tags(tag_names)
        current_tags = instance.tags.all()
        updated_tags = list(set(current_tags) | set(tags))
        serializer = self.get_serializer(
            instance, data=request.data, partial=True, context={"tags": updated_tags}
        )
        if not serializer.is_valid():
            return Response(
                success=False,
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        is_draft = serializer.validated_data.get("is_draft", False)
        if not is_draft:
            serializer.validated_data["published_at"] = timezone.now()

        self.perform_update(serializer)
        instance.tags.set(updated_tags)
        return Response(
            success=True,
            message="Blog Post Updated",
            status_code=status.HTTP_200_OK,
            data=serializer.data,
        )

    @swagger_auto_schema(
        operation_description="List all Blog post by filter",
        responses={
            200: BlogPostSerializer,
        },
    )
    def list(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        qs = self.paginate_queryset(queryset)
        serializer = self.get_serializer(qs, many=True)
        self.pagination_class.message = "Blog Posts retrieved successfully"
        response = self.get_paginated_response(
            serializer.data,
        )
        return response

    @swagger_auto_schema(
        operation_description="Retrieve a Blog Post",
        responses={200: BlogPostSerializer},
    )
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(
            success=True,
            message="Blog Post retrieved",
            status_code=status.HTTP_200_OK,
            data=serializer.data,
        )

    @swagger_auto_schema(
        operation_description="temporarily delete multiple posts",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "post_ids": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_INTEGER),
                )
            },
            required=["post_ids"],
        ),
        responses={204: "Selected posts deleted successfully."},
    )
    @action(detail=False, methods=["delete"], url_path="archive")
    def temporary_delete_posts(self, request, *args, **kwargs):
        post_ids = request.data.get("post_ids", [])
        if not post_ids:
            return Response(
                success=False,
                message="No post IDs provided.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        deleted_post = BlogPost.objects.filter(id__in=post_ids)
        try:
            deleted_post.update(deleted_at=timezone.now(), is_archived=True)
            return Response(
                success=True,
                message="Selected posts deleted successfully.",
                status_code=status.HTTP_204_NO_CONTENT,
            )
        except Exception as e:
            return Response(
                success=False, error=str(e), status_code=status.HTTP_400_BAD_REQUEST
            )

    @swagger_auto_schema(
        operation_description="restore deleted post",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "post_ids": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_INTEGER),
                )
            },
            required=["post_ids"],
        ),
        responses={200: "Selected posts successfully restored."},
    )
    @action(detail=False, methods=["put"], url_path="restore")
    def restore_posts(self, request):
        post_ids = request.data.get("post_ids", [])
        if not post_ids:
            return Response(
                success=False,
                error="No post IDs provided.",
                status=status.HTTP_400_BAD_REQUEST,
            )
        BlogPost.objects.filter(id__in=post_ids).update(
            deleted_at=None, is_archived=False
        )
        return Response(
            success=True,
            message="Selected posts successfully restored.",
            status_code=status.HTTP_200_OK,
        )

    @swagger_auto_schema(
        operation_description="permanently delete multiple posts",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "post_ids": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_INTEGER),
                )
            },
            required=["post_ids"],
        ),
        responses={204: "Selected posts permanently deleted."},
    )
    @action(detail=False, methods=["delete"], url_path="delete")
    def permanent_delete_posts(self, request):
        post_ids = request.data.get("post_ids", [])
        if not post_ids:
            return Response(
                success=True,
                message="No post IDs provided.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        BlogPost.objects.filter(id__in=post_ids).delete()
        return Response(
            success=True,
            message="Selected posts permanently deleted.",
            status_code=status.HTTP_204_NO_CONTENT,
        )

    @swagger_auto_schema(
        operation_description="Get deleted post's title", responses={204: "No content"}
    )
    @action(detail=False, methods=["get"])
    def show_deleted(self, request):
        deleted_blogs = BlogPost.objects.filter(deleted_at__isnull=False)
        serializer = BlogPostSerializer(deleted_blogs, many=True)
        deleted_blog_titles = [post["title"] for post in serializer.data]
        deleted_titles_str = ", ".join(deleted_blog_titles)
        return Response(
            success=True,
            message=f"{deleted_titles_str} was deleted successfully.",
            status=status.HTTP_200_OK,
            data=serializer.data,
        )
