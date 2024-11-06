from django.contrib import admin
from django.urls import include, path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

from . import views

schema_view = get_schema_view(
    openapi.Info(
        title="MyBalance API",
        default_version="v1",
        description="Payment Control Service API",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
    url=None,
)

# fmt: off
urlpatterns = [
    path("", views.api_ok, name="api-ok"),
    path("swaggerxyz-docs", schema_view.with_ui("swagger", cache_timeout=0), name="swagger-schema-ui",),
    path('swagger.json', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path("ajazzinauth23qwe/", admin.site.urls),
    path("v1/health-check", views.HealthCheckView.as_view(), name="health-check"),
    path("v1/auth/", include("users.urls")),
    path("v1/shared/", include("common.urls")),
    path("v1/console/", include("console.urls")),
    path("v1/transaction/", include("transaction.urls")),
    path("v1/dispute/", include("dispute.urls")),
    path("v1/notifications/", include("notifications.urls")),
    path("v1/merchants/", include("merchant.urls")),
    path("v1/blog/", include("blog.urls")),
]
# fmt: on
