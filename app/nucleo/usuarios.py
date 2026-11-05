"""Regras de quem gerencia usuários (D-142), comuns ao admin (`admin/usuarios.py`) e à tela B
(`urls/ui_usuarios.py`). Não importa nada de `nucleo.admin` (import circular).

O superusuário pode tudo. Quem não é superusuário (o perfil Admin, `gerenciar_usuarios`):
- não vê superusuários (trocaria a senha de um e entraria como ele);
- só dá os grupos Pedagógica e Mídias Digitais: Impresso daria `marcar_impressa`, o que
  anularia ADMIN_MARCA_IMPRESSA = False, e Admin multiplicaria quem gerencia usuários;
  esses dois ficam com o superusuário;
- não muda os próprios grupos nem se desativa;
- não altera outro usuário do grupo Admin (só vê);
- não mexe nos grupos de quem já tem um grupo fora dos permitidos (ex.: Impresso).
Usuário novo nasce `is_staff` (todo perfil usa o admin). Ninguém exclui: desativa com
`is_active` (D-205).
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from nucleo.permissoes import PAPEIS

GRUPOS_DO_ADMIN = ("Pedagógica", "Mídias Digitais")  # o que um não superusuário pode atribuir


def grupos_permitidos(ator):
    return tuple(PAPEIS) if ator.is_superuser else GRUPOS_DO_ADMIN


def grupos_atribuiveis(ator):
    return Group.objects.filter(name__in=grupos_permitidos(ator)).order_by("name")


def visiveis(ator, qs=None):
    qs = get_user_model().objects.all() if qs is None else qs
    return qs if ator.is_superuser else qs.filter(is_superuser=False)


def pode_editar(ator, alvo):
    """Alterar qualquer coisa do alvo (dados, senha). Outro Admin e superusuário: só o superusuário."""
    if ator.is_superuser or alvo == ator:
        return True
    return not alvo.is_superuser and not alvo.groups.filter(name="Admin").exists()


def pode_mudar_ativo(ator, alvo):
    return ator.is_superuser or (alvo != ator and pode_editar(ator, alvo))


def pode_mudar_grupos(ator, alvo):
    if ator.is_superuser:
        return True
    return (
        alvo != ator
        and pode_editar(ator, alvo)
        and not alvo.groups.exclude(name__in=grupos_permitidos(ator)).exists()
    )


def preparar_novo(usuario):
    """Antes do primeiro save: todo perfil entra pelo login do admin."""
    usuario.is_staff = True
    return usuario
