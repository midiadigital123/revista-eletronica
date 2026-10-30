"""Bloqueio de escrita (D-080, D-081, D-093, D-109, D-121, D-125 item 4).

Quem abre primeiro edita; o outro só vê. Expira em 30 s sem renovação; a
página renova a cada 10 s. Todo horário vem do `now()` do banco, nunca do
relógio do servidor web. "Mesma sessão" = mesmo usuário e mesma aba
(`sessao_edicao`). A mesma pessoa em outra aba ou carga nova toma o bloqueio (D-191): a
página anterior só o solta no `pagehide`, depois que a nova já pediu o dela. A sessão
antiga perde a renovação e a escrita (`renovar`/`conferir_na_transacao` exigem a sessão).

`alvo` é uma instância de MatrizEtapaCC, Projeto ou Template (basta o pk).
"""

import secrets

from django.db import connection
from django.db.models.functions import Now

from nucleo.models import Bloqueio
from nucleo.models.controle import ALVOS

TTL = "30 seconds"  # a página renova a cada 10 s (static/nucleo/bloqueio.js)

# nome do campo do alvo -> modelo (usado pela rota de renovar)
MODELOS = {nome: Bloqueio._meta.get_field(nome).related_model for nome in ALVOS}


def campo(alvo):
    for nome, modelo in MODELOS.items():
        if isinstance(alvo, modelo):
            return nome
    raise TypeError(f"{type(alvo).__name__} não é alvo de bloqueio")


def nova_sessao():
    return secrets.token_hex(16)


def _executar(sql, params):
    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        return cursor.fetchone() is not None


def adquirir(alvo, usuario, sessao):
    """Pega o bloqueio se livre, expirado ou já do mesmo usuário (D-191). Atômico (ON CONFLICT)."""
    col = f"{campo(alvo)}_id"
    return _executar(
        f"""
        INSERT INTO bloqueio ({col}, usuario_id, sessao_edicao, expira_em)
        VALUES (%s, %s, %s, now() + interval '{TTL}')
        ON CONFLICT ({col}) WHERE {col} IS NOT NULL DO UPDATE
            SET usuario_id = EXCLUDED.usuario_id,
                sessao_edicao = EXCLUDED.sessao_edicao,
                expira_em = EXCLUDED.expira_em
            WHERE bloqueio.expira_em < now()
               OR bloqueio.usuario_id = EXCLUDED.usuario_id
        RETURNING id
        """,
        [alvo.pk, usuario.pk, sessao],
    )


def renovar(alvo, usuario, sessao):
    """Estende só o bloqueio ainda válido desta sessão; nunca readquire."""
    col = f"{campo(alvo)}_id"
    return _executar(
        f"""
        UPDATE bloqueio SET expira_em = now() + interval '{TTL}'
        WHERE {col} = %s AND usuario_id = %s AND sessao_edicao = %s AND expira_em >= now()
        RETURNING id
        """,
        [alvo.pk, usuario.pk, sessao],
    )


def liberar(alvo, usuario, sessao):
    """Apaga o bloqueio se for desta sessão. Idempotente."""
    Bloqueio.objects.filter(
        **{campo(alvo): alvo.pk}, usuario=usuario, sessao_edicao=sessao
    ).delete()


def conferir_na_transacao(alvo, usuario, sessao):
    """True se esta sessão detém o bloqueio válido. Usar dentro da transação da escrita.

    FOR SHARE segura a linha até o commit: ninguém toma o bloqueio (o DO UPDATE
    do `adquirir` espera) enquanto a escrita não termina.
    """
    if not connection.in_atomic_block:
        raise RuntimeError("conferir_na_transacao precisa de transaction.atomic()")
    col = f"{campo(alvo)}_id"
    return _executar(
        f"""
        SELECT 1 FROM bloqueio
        WHERE {col} = %s AND usuario_id = %s AND sessao_edicao = %s AND expira_em >= now()
        FOR SHARE
        """,
        [alvo.pk, usuario.pk, sessao],
    )


def quem_bloqueia(alvo):
    """Bloqueio válido do alvo (com usuário) ou None. Serve ao aviso e aos lotes (D-121)."""
    return (
        Bloqueio.objects.filter(**{campo(alvo): alvo.pk}, expira_em__gte=Now())
        .select_related("usuario")
        .first()
    )
