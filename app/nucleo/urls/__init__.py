from django.urls import include, path

urlpatterns = [
    path("bloqueio/", include("nucleo.urls.bloqueio")),
    path("preview/", include("nucleo.urls.preview")),
]
