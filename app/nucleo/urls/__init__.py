from django.urls import include, path

urlpatterns = [
    path("bloqueio/", include("nucleo.urls.bloqueio")),
    path("impresso/", include("nucleo.urls.impresso")),
    path("painel/", include("nucleo.urls.painel")),
    path("preview/", include("nucleo.urls.preview")),
    path("templates/", include("nucleo.urls.templates")),
]
