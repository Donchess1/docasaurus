from django.urls import path

from .views import BlogPostListCreateView, BlogPostRetrieveUpdateDestroyView

urlpatterns = [
    path("", BlogPostListCreateView.as_view(), name="blog-post-list"),
    path(
        "<uuid:pk>/",
        BlogPostRetrieveUpdateDestroyView.as_view(),
        name="blog-post-detail",
    ),
]
