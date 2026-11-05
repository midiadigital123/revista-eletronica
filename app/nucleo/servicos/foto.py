from django.db import connection, transaction

from nucleo.models import FotoRevista
from nucleo.servicos.resolver import carregar, resolver, sha256


def fotografar(revista, motivo, usuario):
    """Grava a foto da revista: o resolvido inteiro e o seu hash (= `hash_validado` no momento).

    O impresso compara pela parte `resolver.impresso_de(foto.conteudo)` (sem SVG e capa, D-118);
    a revista arquivada devolve o conteúdo da foto de arquivamento (D-117).
    Transação (D-138): dentro de transação aberta usa a do chamador (a cascata já roda em
    atomic, onde SET TRANSACTION ISOLATION LEVEL falha após a 1ª query); fora de atomic abre
    uma em REPEATABLE READ, para o resolver ler um retrato só do banco. O clique do impresso
    (`validacao.marcar_impressa`) roda na transação do chamador (com o bloqueio do projeto), sem
    REPEATABLE READ: confere o hash desta foto contra o visto, num savepoint que a desfaz se diferir.
    """
    if connection.in_atomic_block:
        return _gravar(revista, motivo, usuario)
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")
        # Relida dentro do retrato: SVG, capa e arquivada_em vêm do mesmo instante que o resto.
        return _gravar(carregar(revista.pk), motivo, usuario)


def _gravar(revista, motivo, usuario):
    conteudo = resolver(revista)
    return FotoRevista.objects.create(
        revista=revista, motivo=motivo, conteudo=conteudo, hash=sha256(conteudo), criada_por=usuario
    )
