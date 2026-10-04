from django.contrib import admin
from django.urls import include, path

from apps.dashboard.views import landing

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", landing, name="landing"),
    path("accounts/", include("apps.accounts.urls")),
    path("dashboard/", include("apps.dashboard.urls")),
    path("chat/", include("apps.chat.urls")),
    path("mood/", include("apps.mood.urls")),
    path("exercises/", include("apps.exercises.urls")),
]
