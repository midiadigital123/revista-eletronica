"""Regras de quem gerencia usuários (D-142), comuns ao admin (`admin/usuarios.py`) e à tela B
(`urls/ui_usuarios.py`). Não importa nada de `nucleo.admin` (import circular).

O superusuário pode tudo. Quem não é superusuário (o perfil Admin, `gerenciar_usuarios`):
- não vê superusuários (trocaria a senha de um e entraria como ele);
- dá os grupos Pedagógica, Mídias Digitais e Impresso (D-220; ele mesmo marca impressa,
  ADMIN_MARCA_IMPRESSA). Admin, não: multiplicaria quem gerencia usuários; fica com o superusuário;
- não muda os próprios grupos nem se desativa;
- não altera (dados, senha, grupo, ativo) quem tem grupo fora dos permitidos, ou seja, outro
  Admin: só vê.
Usuário novo nasce `is_staff` (o admin do Django exige; o login é o das telas B, D-212). Sai desativado (`is_active`); excluir só
quem não tem rastro (D-218).
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from nucleo.permissoes import PAPEIS

GRUPOS_DO_ADMIN = ("Pedagógica", "Mídias Digitais", "Impresso")  # o que um não superusuário pode atribuir (D-220)


def grupos_permitidos(ator):
    return tuple(PAPEIS) if ator.is_superuser else GRUPOS_DO_ADMIN


def grupos_atribuiveis(ator):
    return Group.objects.filter(name__in=grupos_permitidos(ator)).order_by("name")


def visiveis(ator, qs=None):
    qs = get_user_model().objects.all() if qs is None else qs
    return qs if ator.is_superuser else qs.filter(is_superuser=False)


def pode_editar(ator, alvo):
    """Alterar qualquer coisa do alvo (dados, senha). Superusuário, outro Admin e Impresso: só o superusuário."""
    if ator.is_superuser or alvo == ator:
        return True
    return not alvo.is_superuser and not alvo.groups.exclude(name__in=grupos_permitidos(ator)).exists()


def pode_mudar_ativo(ator, alvo):
    return ator.is_superuser or (alvo != ator and pode_editar(ator, alvo))


def pode_mudar_grupos(ator, alvo):
    if ator.is_superuser:
        return True
    return alvo != ator and pode_editar(ator, alvo)


def preparar_novo(usuario):
    """Antes do primeiro save: `is_staff`, que o admin do Django exige."""
    usuario.is_staff = True
    return usuario


def caminho_definir_senha(usuario):
    """Caminho do link do Django para a pessoa definir a própria senha (primeiro acesso ou senha esquecida).
    Vale `PASSWORD_RESET_TIMEOUT` e deixa de valer quando a senha muda ou a pessoa entra."""
    uid = urlsafe_base64_encode(force_bytes(usuario.pk))
    return reverse("password_reset_confirm", args=[uid, default_token_generator.make_token(usuario)])


# Rastro de um usuário: o que ele fez e o sistema guarda (D-218). Bloqueio é trava de 30 s, não rastro.
ROTULOS = {
    "TemplateVersao": "versões de template que criou",
    "Revista": "revistas que validou",
    "FotoRevista": "fotos de revista que gerou",
    "LogEntry": "ações registradas no admin",
}
NAO_E_RASTRO = {"Bloqueio"}
HISTORICO = "edições registradas no histórico"


def rastros(alvo):
    """[(rótulo, contagem)] do que impede excluir `alvo`; vazio = pode excluir.

    Relações diretas (as PROTECT e o log do admin) e o `history_user` das tabelas do django-simple-history,
    que é SET_NULL e escondido (`related_name="+"`): sem esta conta, excluir apagaria o autor do histórico."""
    from django.apps import apps

    saida = []
    for rel in alvo._meta.related_objects:
        nome = rel.related_model.__name__
        if rel.many_to_many or nome in NAO_E_RASTRO:
            continue
        n = rel.related_model._base_manager.filter(**{rel.field.name: alvo}).count()
        if n:
            saida.append((ROTULOS.get(nome, str(rel.related_model._meta.verbose_name_plural)), n))
    historico = sum(
        m._base_manager.filter(history_user=alvo).count()
        for m in apps.get_models()
        if any(f.name == "history_user" for f in m._meta.fields)
    )  # ponytail: uma contagem por tabela de histórico (~20); é uma página, não uma lista
    if historico:
        saida.append((HISTORICO, historico))
    return saida


class TemRastro(Exception):
    def __init__(self, rastros):
        super().__init__("tem rastro")
        self.rastros = rastros


def excluir(alvo):
    """Exclui `alvo` sem rastro. Trava a linha do usuário e confere de novo; com rastro, levanta TemRastro."""
    from django.db import transaction

    with transaction.atomic():
        alvo = get_user_model().objects.select_for_update().get(pk=alvo.pk)
        achados = rastros(alvo)
        if achados:
            raise TemRastro(achados)
        alvo.delete()  # leva junto grupos, permissões avulsas e bloqueios (CASCADE)
