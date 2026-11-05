from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    # D-212: ninguém vê o login do admin; o próprio admin manda para cá com o `next`.
    path("admin/login/", RedirectView.as_view(pattern_name="entrar", query_string=True)),
    path("admin/", admin.site.urls),
    path("", include("nucleo.urls")),
]
