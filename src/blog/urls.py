from django.urls import include, path
from rest_framework.routers import DefaultRouter

from blog.views.blog import BlogPostViewSet
from blog.views.tag import TagViewSet

router = DefaultRouter()
router.register(r"tags", TagViewSet)
router.register(r"", BlogPostViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
