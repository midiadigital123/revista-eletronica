"""Quem perde o "Validado" com uma gravação (U2, modal de impacto das telas B).

`perdem_validado` simula a gravação num savepoint desfeito e compara o hash: exato, sem repetir a
regra do resolver. Usado pelo renomear parceiro, pela grade de cortes e pelos lotes.
"""

from collections.abc import Callable, Iterable

from django.contrib import messages
from django.db import transaction
from django.urls import reverse
from django.utils.html import format_html, format_html_join

from nucleo.models import Revista
from nucleo.servicos.resolver import hash_validado
from nucleo.servicos.validacao import validada


class _Desfazer(Exception):
    pass


def perdem_validado(gravar: Callable[[], None], revistas: Iterable[Revista]) -> list[Revista]:
    """Das `revistas` validadas agora, as que deixam de estar depois de `gravar()`.
    `gravar()` roda num savepoint desfeito; exceção dele (ex.: conflito) sobe para quem chama."""
    validadas = [r for r in revistas if r.hash_validado is not None and validada(r, hash_validado(r))]
    if not validadas:
        return []
    perdem = []
    try:
        with transaction.atomic():
            gravar()
            for r in validadas:
                depois = Revista.objects.filter(pk=r.pk).first()
                if depois is None or not validada(depois, hash_validado(depois)):
                    perdem.append(r)
            raise _Desfazer
    except _Desfazer:
        pass
    return perdem


MAX_NOMES = 20


def nomes(revistas):
    """"A, B e mais 3": no máximo MAX_NOMES nomes numa mensagem."""
    resto = len(revistas) - MAX_NOMES
    lista = format_html_join(", ", "{}", ((r,) for r in revistas[:MAX_NOMES]))
    return format_html("{} e mais {}", lista, resto) if resto > 0 else lista


def avisar_perdidos(request, perdem, ano):
    """Aviso de pós-gravação: quem perdeu o "Validado" e o link para revalidar no Painel."""
    messages.warning(request, format_html(
        "{} revista(s) perderam o “Validado”: {}. Revalide no <a href=\"{}\">Painel</a>.",
        len(perdem), nomes(perdem), reverse("painel", args=[ano]) + "?falta=validado",
    ))  # fmt: skip
