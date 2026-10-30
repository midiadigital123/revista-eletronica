"""Definir senha pelo link do convite (`criar_usuarios`). Views e templates do próprio Django."""
from django.contrib.auth import views
from django.urls import path, reverse_lazy

urlpatterns = [
    path(
        "senha/<uidb64>/<token>/",
        views.PasswordResetConfirmView.as_view(success_url=reverse_lazy("password_reset_complete")),
        name="password_reset_confirm",
    ),
    path("senha/pronto/", views.PasswordResetCompleteView.as_view(), name="password_reset_complete"),
]
