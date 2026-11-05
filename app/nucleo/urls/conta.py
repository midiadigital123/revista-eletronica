"""Entrar e sair das telas B (D-212) e definir senha pelo link de acesso (tela Usuários ou `criar_usuarios`).
Views do próprio Django com templates das telas B (`ui/entrar.html`, `ui/senha_*.html`): ninguém vê o admin."""
from django.contrib.auth import views
from django.urls import path, reverse_lazy

urlpatterns = [
    path("entrar/", views.LoginView.as_view(template_name="ui/entrar.html", redirect_authenticated_user=True), name="entrar"),
    path("sair/", views.LogoutView.as_view(), name="sair"),
    path(
        "senha/<uidb64>/<token>/",
        views.PasswordResetConfirmView.as_view(
            template_name="ui/senha_definir.html", success_url=reverse_lazy("password_reset_complete")
        ),
        name="password_reset_confirm",
    ),
    path("senha/pronto/", views.PasswordResetCompleteView.as_view(template_name="ui/senha_pronto.html"), name="password_reset_complete"),
]
