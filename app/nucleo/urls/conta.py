"""Entrar e sair das telas B (D-212) e definir senha pelo link do convite (`criar_usuarios`).
Views do próprio Django; o login usa `ui/entrar.html`, o resto os templates padrão."""
from django.contrib.auth import views
from django.urls import path, reverse_lazy

urlpatterns = [
    path("entrar/", views.LoginView.as_view(template_name="ui/entrar.html", redirect_authenticated_user=True), name="entrar"),
    path("sair/", views.LogoutView.as_view(), name="sair"),
    path(
        "senha/<uidb64>/<token>/",
        views.PasswordResetConfirmView.as_view(success_url=reverse_lazy("password_reset_complete")),
        name="password_reset_confirm",
    ),
    path("senha/pronto/", views.PasswordResetCompleteView.as_view(), name="password_reset_complete"),
]
