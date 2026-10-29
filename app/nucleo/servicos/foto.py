import hashlib
import json

from nucleo.models import FotoRevista


def fotografar(revista, motivo, usuario):
    """Grava a foto da revista. STUB do S06: conteúdo `{}`.

    O S07 troca o corpo (resolver + hash em REPEATABLE READ) mantendo a assinatura.
    O CHECK de sha256 não aceita hash vazio: usa o sha256 do JSON canônico de `{}`.
    Transação: dentro de transação aberta usa a transação do chamador (a cascata já
    roda em atomic, onde SET TRANSACTION ISOLATION LEVEL não é permitido);
    REPEATABLE READ só quando chamado fora de atomic (clique do impresso).
    """
    conteudo = {}
    canonico = json.dumps(conteudo, sort_keys=True, separators=(",", ":"))
    return FotoRevista.objects.create(
        revista=revista,
        motivo=motivo,
        conteudo=conteudo,
        hash=hashlib.sha256(canonico.encode()).hexdigest(),
        criada_por=usuario,
    )
