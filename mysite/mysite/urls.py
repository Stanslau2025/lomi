from django.contrib import admin
from django.urls import include, path

from store.views import home


urlpatterns = [
    path("", home, name="home"),
    path("admin/", admin.site.urls),
    path("api/", include("store.urls")),
    path("accounts/", include("django.contrib.auth.urls")),
]
