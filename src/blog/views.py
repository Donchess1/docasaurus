from .models import *
from utils.response import Response
from rest_framework import status, viewsets, filters, permissions
from .serializers import *
from drf_yasg.utils import swagger_auto_schema
from .permissions import IsAuthorOrAdmin
from utils.pagination import CustomPagination
from rest_framework.decorators import action
from blog.filter import BlogFilter
from django_filters import rest_framework as django_filters
from django.utils import timezone
from drf_yasg import openapi
class BlogPostViewSet(viewsets.ModelViewSet):
    queryset = BlogPost.objects.all().order_by("-created_at")
    serializer_class = BlogPostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = CustomPagination
    filter_backends = [django_filters.DjangoFilterBackend, filters.SearchFilter]
    search_fields = ["title", "content", "tags"]
    filterset_class = BlogFilter


    def perform_create(self, serializer):
     serializer.save(author=self.request.user)
     
    def get_queryset(self):
        if self.request.user.is_authenticated:
            return BlogPost.objects.filter(author=self.request.user)
        return BlogPost.objects.filter(is_draft=True)
    
    @swagger_auto_schema(
        operation_description="List all Blog post by filter",
        responses={
            200: BlogPostSerializer,
        },
     )
    def list(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
           serializer=self.get_serializer(page, many=True)
           self.pagination_class.message = "Blog Posts retrieved successfully"
           return self.get_paginated_response(serializer.data)
        serializer=self.get_serializer(queryset, many=True)
        return Response(
        {
            "success": True,
            "message": "Blog Posts retrieved successfully",
            "data": serializer.data,
        },
        status=status.HTTP_200_OK
        )
    
    @swagger_auto_schema(
        operation_description="Retrieve a Blog Post",
        responses={200: BlogPostSerializer}
        )
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
                "success": True,
                "message": "Blog Post retrieved",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK
        )

    @swagger_auto_schema(
        operation_description="permanently delete post",
        responses={204: "No content"}
        )
    @action(detail=False, methods=['delete'])
    def permanent_delete(self, request):
        post_ids = request.data.get('post_ids', [])
        if not post_ids:
            return Response(
                {
                    "success": True, 
                    "message": "No post IDs provided."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
        BlogPost.objects.filter(id__in=post_ids).delete()
        return Response(
            {
                "success": True,
                "message": "Selected posts permanently deleted."
                },
        status=status.HTTP_204_NO_CONTENT
    )

    @swagger_auto_schema(
        operation_description="Delete a Blog Post",
        responses={204: "No content"}
        )
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {
                "success": True,
                "message": "Blog Post Deleted",
            },
            status=status.HTTP_200_OK
            )
    
    @swagger_auto_schema(
    operation_description="temporarily delete post",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'post_ids': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(type=openapi.TYPE_INTEGER)
            )
        },
        required=['post_ids']
    ),
    responses={204: "Selected posts deleted successfully."})
    @action(detail=False, methods=['delete'])
    def delete_multiple(self, request, *args, **kwargs):
        post_ids = request.data.get('post_ids', [])
        deleted_post= BlogPost.objects.filter(id__in=post_ids)
        
        if not post_ids:
            return Response(
                {
                    "success": False,
                    "message": "No post IDs provided.",
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            deleted_post.update(deleted_at=timezone.now(),is_archived=True)
            return Response(
                {
                    "success": True,
                    "message": "Selected posts deleted successfully."},
                status=status.HTTP_204_NO_CONTENT
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        
    @swagger_auto_schema(
    operation_description="restore deleted post",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'post_ids': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(type=openapi.TYPE_INTEGER)
            )
        },
        required=['post_ids']
    ),
    responses={200: "Selected posts successfully restored."})
    @action(detail=False, methods=['post'])
    def restore(self, request):
        post_ids = request.data.get('post_ids', [])
        if not post_ids:
            return Response(
                {
                    "error": "No post IDs provided."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                    )
        BlogPost.objects.filter(id__in=post_ids).update(deleted_at=None)
        return Response(
            {
                "success": True,
                "message": "Selected posts successfully restored."
                },
                status=status.HTTP_200_OK
                ) 

    @swagger_auto_schema(
        operation_description="Get deleted post's title",
        responses={204: "No content"}
        )
    @action(detail=False, methods=['get'])
    def show_deleted(self, request):
        deleted_blogs = BlogPost.objects.filter(deleted_at__isnull=False)
        serializer = BlogPostSerializer(deleted_blogs, many=True)
        deleted_blog_titles = [post['title'] for post in serializer.data]
        deleted_titles_str = ", ".join(deleted_blog_titles)
        
        return Response(
            {
                "success": True, 
                "message": f"{deleted_titles_str} was deleted successfully."
            },
            status=status.HTTP_200_OK
            )