from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)

from users.views import frontend_page

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("users.urls")),
    path("api/groups/", include("groups.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path("", frontend_page, {"page": "login"}, name="home"),
    path("login/", frontend_page, {"page": "login"}, name="login"),
    path("register/", frontend_page, {"page": "register"}, name="register"),
    path("dashboard/", frontend_page, {"page": "dashboard"}, name="dashboard"),
    path(
        "groups/<int:group_id>/",
        frontend_page,
        {"page": "group"},
        name="group-detail",
    ),
]
