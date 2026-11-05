"""Usuários na tela B (S9; D-142, D-205): listar, criar, mudar o grupo, ativar ou desativar e
redefinir a senha, com as mesmas regras do admin (`nucleo/usuarios.py`).

Ver e alterar exigem `auth.change_user`; criar exige também `auth.add_user` (403). O alvo vem do
`pk` da URL, filtrado por `visiveis` (superusuário fora da lista de quem não é superusuário: 404)
e cada ação repete a regra no servidor (403), porque o template só esconde o controle. Nenhum
campo de privilégio (`is_superuser`, `is_staff`, `user_permissions`) entra pelo POST: os forms
declaram só os campos que gravam. Senha só por `UserCreationForm`/`SetPasswordForm` (validadores
do Django). Ninguém se exclui: desativa.
"""

from django import forms
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.forms import SetPasswordForm, UserCreationForm
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import path
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from nucleo import usuarios as regra

GERENCIAR = "auth.change_user"  # `gerenciar_usuarios` (nucleo/permissoes.py): só o Admin


def _classes(form):
    for campo in form.fields.values():
        campo.widget.attrs["class"] = "select" if isinstance(campo.widget, forms.Select) else "input"
    return form


def _dados(request):
    return request.POST if request.method == "POST" else None


def _alvo(request, pk):
    return get_object_or_404(regra.visiveis(request.user), pk=pk)


class GrupoForm(forms.Form):
    grupo = forms.ModelChoiceField(queryset=Group.objects.none(), label="Grupo", empty_label="Escolha o grupo")

    def __init__(self, ator, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["grupo"].queryset = regra.grupos_atribuiveis(ator)


class NovoUsuarioForm(UserCreationForm):
    grupo = forms.ModelChoiceField(queryset=Group.objects.none(), label="Grupo", empty_label="Escolha o grupo")

    class Meta(UserCreationForm.Meta):
        fields = ("username", "first_name", "last_name", "email")

    def __init__(self, ator, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["grupo"].queryset = regra.grupos_atribuiveis(ator)
        self.order_fields(["username", "first_name", "last_name", "email", "grupo"])


@require_GET
@login_required(login_url="admin:login")
@permission_required(GERENCIAR, raise_exception=True)
def lista(request):
    ator = request.user
    linhas = [
        {
            "u": u,
            "grupos": ", ".join(g.name for g in u.groups.all()),
            "grupo_atual": next(iter(u.groups.all()), None),
            "editar": regra.pode_editar(ator, u),
            "mudar_ativo": regra.pode_mudar_ativo(ator, u),
            "mudar_grupo": regra.pode_mudar_grupos(ator, u),
        }
        for u in regra.visiveis(ator).prefetch_related("groups").order_by("-is_active", "username")
    ]  # ponytail: 3 consultas por linha nas regras; são dezenas de usuários
    return TemplateResponse(
        request,
        "ui/usuarios/lista.html",
        {"linhas": linhas, "grupos": list(regra.grupos_atribuiveis(ator)), "secao": "usuarios"},
    )


@require_http_methods(["GET", "POST"])
@login_required(login_url="admin:login")
@permission_required([GERENCIAR, "auth.add_user"], raise_exception=True)
def novo(request):
    form = _classes(NovoUsuarioForm(request.user, _dados(request)))
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            u = regra.preparar_novo(form.save(commit=False))
            u.save()
            u.groups.set([form.cleaned_data["grupo"]])
        messages.success(request, f"Usuário {u.username} criado no grupo {form.cleaned_data['grupo']}.")
        return redirect("ui_usuarios")
    contexto = {"form": form, "titulo": "Novo usuário", "botao": "Criar usuário", "secao": "usuarios",
                "texto": "Entra pelo login do sistema com este nome de usuário e senha."}  # fmt: skip
    return TemplateResponse(request, "ui/usuarios/form.html", contexto)


@require_POST
@login_required(login_url="admin:login")
@permission_required(GERENCIAR, raise_exception=True)
def grupo(request, pk):
    alvo = _alvo(request, pk)
    if not regra.pode_mudar_grupos(request.user, alvo):
        raise PermissionDenied
    form = GrupoForm(request.user, request.POST)
    if form.is_valid():
        alvo.groups.set([form.cleaned_data["grupo"]])
        messages.success(request, f"{alvo.username} agora está no grupo {form.cleaned_data['grupo']}.")
    else:
        messages.error(request, f"Grupo de {alvo.username} não mudou: escolha um dos grupos da lista.")
    return redirect("ui_usuarios")


@require_POST
@login_required(login_url="admin:login")
@permission_required(GERENCIAR, raise_exception=True)
def ativo(request, pk):
    alvo = _alvo(request, pk)
    if not regra.pode_mudar_ativo(request.user, alvo):
        raise PermissionDenied
    acoes = {"desativar": False, "ativar": True}
    if request.POST.get("acao") not in acoes:
        raise Http404
    alvo.is_active = acoes[request.POST["acao"]]
    alvo.save(update_fields=["is_active"])
    if alvo.is_active:
        messages.success(request, f"{alvo.username} ativado: volta a entrar no sistema.")
    else:
        messages.success(request, f"{alvo.username} desativado: não entra mais. O histórico dele fica.")
    return redirect("ui_usuarios")


@require_http_methods(["GET", "POST"])
@login_required(login_url="admin:login")
@permission_required(GERENCIAR, raise_exception=True)
def senha(request, pk):
    alvo = _alvo(request, pk)
    if not regra.pode_editar(request.user, alvo):
        raise PermissionDenied
    form = _classes(SetPasswordForm(alvo, _dados(request)))
    if request.method == "POST" and form.is_valid():
        form.save()
        if alvo == request.user:
            update_session_auth_hash(request, alvo)  # como o admin: quem troca a própria senha segue logado
        messages.success(request, f"Senha de {alvo.username} redefinida. Passe a senha nova a ele por um canal seguro.")
        return redirect("ui_usuarios")
    contexto = {"form": form, "alvo": alvo, "titulo": f"Redefinir senha de {alvo.username}", "botao": "Redefinir senha",
                "secao": "usuarios", "texto": "A senha atual deixa de valer, e as sessões abertas dele se encerram."}  # fmt: skip
    return TemplateResponse(request, "ui/usuarios/form.html", contexto)


urlpatterns = [
    path("", lista, name="ui_usuarios"),
    path("novo/", novo, name="ui_usuarios_novo"),
    path("<int:pk>/grupo/", grupo, name="ui_usuarios_grupo"),
    path("<int:pk>/ativo/", ativo, name="ui_usuarios_ativo"),
    path("<int:pk>/senha/", senha, name="ui_usuarios_senha"),
]
