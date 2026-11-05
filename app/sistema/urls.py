from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.generic import RedirectView
from django.views.static import serve

urlpatterns = [
    # D-212: ninguém vê o login do admin; o próprio admin manda para cá com o `next`.
    path("admin/login/", RedirectView.as_view(pattern_name="entrar", query_string=True)),
    path("admin/", admin.site.urls),
]

if not settings.DEBUG:
    # Produção (D-214): o Gunicorn não serve /static/; o collectstatic do compose de produção enche o STATIC_ROOT.
    # ponytail: Django serve os estáticos, ok para a equipe interna; com tráfego alto, whitenoise ou o proxy lendo o STATIC_ROOT.
    urlpatterns.append(re_path(r"^static/(?P<path>.*)$", serve, {"document_root": settings.STATIC_ROOT}))

urlpatterns.append(path("", include("nucleo.urls")))
