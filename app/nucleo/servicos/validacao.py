"""Clique "Validado" (S12, D-074, D-089, D-094, D-120).

O estado "validado" não é guardado: é `hash_validado == hash atual`, calculado na hora.
Desfazer a mudança faz o hash voltar e o "Validado" volta junto (D-094). Seção desatualizada
só avisa (D-087): quem chama mostra `secoes_desatualizadas`, aqui não entra.
O bloqueio do projeto é de quem chama (change form: sessão da aba; lote: `escrever_travado`).
"""

from django.utils import timezone

from nucleo.models import Revista
from nucleo.servicos import resolver


def validada(revista, hash_atual):
    return revista.hash_validado is not None and revista.hash_validado == hash_atual


def validar(revista_pk, hash_visto, usuario):
    """Grava o "Validado" se `hash_visto` é o hash atual e não há pendência.

    Devolve None se gravou, ou o motivo da recusa. Rodar dentro de transação: o FOR UPDATE
    na revista enfileira dois cliques simultâneos.
    """
    revista = (
        Revista.objects.select_for_update(of=("self",))
        .select_related("projeto__parceiro_ano__parceiro", "projeto__ano")
        .get(pk=revista_pk)
    )
    if revista.arquivada_em is not None:
        return "revista arquivada"
    resolvido = resolver.resolver(revista)
    atual = resolver.hash_validado(revista, resolvido)
    if hash_visto != atual:
        return "a revista mudou depois que a página abriu; confira de novo"
    if validada(revista, atual):
        return None  # já validada nesta versão: mantém quem e quando validou
    if pendentes := resolver.pendencias(revista, resolvido):
        return "pendências: " + " ".join(p.mensagem for p in pendentes)
    revista.hash_validado, revista.validado_em, revista.validado_por = atual, timezone.now(), usuario
    revista.save(update_fields=["hash_validado", "validado_em", "validado_por"])
    return None
