"""Etapa do projeto (D-227): cópia própria de uma etapa de matriz, com vínculo à base.

A foto é o conteúdo canônico de uma etapa de matriz (por código de descritor, não por id),
guardada em `base_foto` ao clonar para saber depois o que a base mudou desde então.
"""
from typing import NamedTuple

from django.db import IntegrityError, transaction
from django.db.models import Q

from nucleo.models import Descritor, Matriz, MatrizEtapaCC, Tarefa
from nucleo.servicos.abrir_ano import clonar
from nucleo.servicos.matriz import CAMPOS_DESCRITOR
from nucleo.servicos.resolver import sha256


class CriacaoRecusada(ValueError):
    pass


def _norm(texto):
    return " ".join(texto.split())


def foto(mec):
    """Conteúdo canônico da etapa, só valores JSON: {"passo", "descritores": {codigo: {"ordem",
    <CAMPOS_DESCRITOR>, "tarefas": {"inicio-fim#n": {texto, arquivo, texto_alternativo, ordem}}}}}.
    Texto com os espaços normalizados."""
    descritores, por_pk = {}, {}
    for d in Descritor.objects.filter(matriz_etapa_cc=mec):
        dados = {c: _norm(getattr(d, c)) for c in CAMPOS_DESCRITOR if c != "prerequisitos"}
        dados["prerequisitos"] = [_norm(p) for p in d.prerequisitos]
        dados["ordem"], dados["tarefas"] = d.ordem, {}
        descritores[d.codigo] = por_pk[d.pk] = dados
    contagem = {}
    for t in Tarefa.objects.filter(descritor__matriz_etapa_cc=mec).order_by("ordem", "pk"):
        faixa = (t.descritor_id, t.inicio, t.fim)
        contagem[faixa] = n = contagem.get(faixa, 0) + 1
        # ponytail: identidade pela faixa; corrigir a faixa aparece como remover + criar.
        # Parear por (inicio, fim) se incomodar.
        por_pk[t.descritor_id]["tarefas"][f"{t.inicio}-{t.fim}#{n}"] = {
            "texto": _norm(t.texto),
            "arquivo": t.arquivo or None,
            "texto_alternativo": _norm(t.texto_alternativo),
            "ordem": t.ordem,
        }
    return {"passo": mec.passo, "descritores": descritores}


def hash_foto(f):
    return sha256(f)


class Item(NamedTuple):
    """Uma célula que a base mudou. `campo` é "existe" quando o descritor/tarefa inteiro foi
    criado ou apagado (então antes/base/local são o dict inteiro, ou None se ausente)."""

    chave: str  # "passo", "D01" ou "D01/100-150#1"
    campo: str
    antes: object
    base: object
    local: object
    situacao: str  # "entra" (só a base mudou) ou "conflito" (os dois mudaram)


def _celula(chave, campo, antes, base, local):
    """Regra de 3 vias de uma célula; `[]` ou um `Item`."""
    if base == antes or local == base:
        return []
    return [Item(chave, campo, antes, base, local, "entra" if local == antes else "conflito")]


def _natural(chave):  # "100-150#10" -> (100, 150, 10): "2-3#1" vem antes de "10-20#1", "#2" antes de "#10"
    faixa, n = chave.split("#")
    inicio, fim = faixa.split("-")
    return int(inicio), int(fim), int(n)


def _ordem_descritores(antes, base, local):
    # Os da base pela ordem dela; os que só existem em local/antes vêm depois, na ordem de local.
    da_base = sorted(base, key=lambda c: (base[c]["ordem"], c))
    return da_base + [c for c in dict.fromkeys((*local, *antes)) if c not in base]


def classificar(antes, base, local):
    """Compara 3 fotos (`foto()`): `antes` = a base quando clonou, `base` = a base agora,
    `local` = o conteúdo do projeto. Devolve os `Item` que a base mudou, "entra" ou "conflito".
    Ausente conta como None. Função pura: sem banco."""
    itens = _celula("passo", "passo", antes["passo"], base["passo"], local["passo"])
    for codigo in _ordem_descritores(antes["descritores"], base["descritores"], local["descritores"]):
        a, b, l = (f["descritores"].get(codigo) for f in (antes, base, local))
        if None in (a, b, l):
            itens += _celula(codigo, "existe", a, b, l)
            continue
        for campo in (*CAMPOS_DESCRITOR, "ordem"):
            itens += _celula(codigo, campo, a[campo], b[campo], l[campo])
        for chave in sorted({*a["tarefas"], *b["tarefas"], *l["tarefas"]}, key=_natural):
            ta, tb, tl = (x["tarefas"].get(chave) for x in (a, b, l))
            onde = f"{codigo}/{chave}"
            if None in (ta, tb, tl):
                itens += _celula(onde, "existe", ta, tb, tl)
                continue
            for campo in ("texto", "arquivo", "texto_alternativo", "ordem"):
                itens += _celula(onde, campo, ta[campo], tb[campo], tl[campo])
    return itens


def criar(projeto, etapa, componente, usuario, base=None):
    """Cria a etapa × componente do projeto: em branco, ou clonada de `base` (etapa de matriz)
    com `base_foto`. Recusa com `CriacaoRecusada`; tudo numa transação."""
    with transaction.atomic():
        if projeto.arquivado_em is not None:
            raise CriacaoRecusada("projeto arquivado")
        if base is not None:
            if base.matriz_id is None:
                raise CriacaoRecusada("a base precisa ser etapa de matriz")
            if base.componente.codigo != componente.codigo:
                raise CriacaoRecusada("a base precisa ser do mesmo componente")
        nome = f"{etapa.codigo} {componente.codigo}"
        matriz_id = projeto.parceiro_ano.matriz_id
        if matriz_id and MatrizEtapaCC.objects.filter(matriz_id=matriz_id, etapa=etapa, componente=componente).exists():
            raise CriacaoRecusada(f"a matriz do parceiro já tem {nome}")
        if MatrizEtapaCC.objects.filter(projeto=projeto, etapa=etapa, componente=componente).exists():
            raise CriacaoRecusada(f"o projeto já tem {nome}")

        mec = MatrizEtapaCC(projeto=projeto, etapa=etapa, componente=componente, ano_id=projeto.ano_id)
        motivo = f"clone de {base}"[:100] if base else "etapa do projeto"
        if base is not None:
            # Trava a matriz da base: uma reimportação recriaria descritores no meio da cópia.
            Matriz.objects.select_for_update(no_key=True).filter(pk=base.matriz_id).first()
            base.refresh_from_db()
            mec.base, mec.base_foto, mec.passo = base, foto(base), base.passo
        # O CHECK e o trigger exigem base e base_foto no mesmo INSERT.
        mec._history_user, mec._change_reason = usuario, motivo
        try:
            with transaction.atomic():
                mec.save()
        except IntegrityError:  # corrida com outro `criar` igual (unique parcial)
            raise CriacaoRecusada(f"o projeto já tem {nome}") from None
        if base is not None:
            mapa = clonar(
                Descritor.objects.filter(matriz_etapa_cc=base), usuario, motivo, matriz_etapa_cc_id=mec.pk
            )
            clonar(Tarefa.objects.filter(descritor__in=list(mapa)), usuario, motivo, descritor_id=mapa)
    return mec


def derivadas(*mecs):
    """MECs de projeto ativo clonadas de uma destas (etapas de matriz)."""
    return MatrizEtapaCC.objects.filter(base__in=mecs, projeto__arquivado_em__isnull=True)


def mecs_por_etapa(projeto, componente_id, etapa_ids):
    """{etapa_id: (MEC da matriz do parceiro, MEC do projeto)}, None onde não há."""
    dono = Q(projeto=projeto)
    if projeto.parceiro_ano.matriz_id is not None:  # matriz_id=None casaria toda MEC de projeto
        dono |= Q(matriz_id=projeto.parceiro_ano.matriz_id)
    saida = {}
    for m in MatrizEtapaCC.objects.filter(dono, componente_id=componente_id, etapa_id__in=list(etapa_ids)):
        par = saida.setdefault(m.etapa_id, [None, None])
        par[m.projeto_id is not None] = m
    return {e: tuple(par) for e, par in saida.items()}


def vigente(da_matriz, do_projeto):
    """A MEC que a revista usa: a única que existe; as duas, a do projeto até escolher a da
    matriz (D-228, D-231)."""
    if do_projeto is None or (da_matriz is not None and do_projeto.preferida == "matriz"):
        return da_matriz
    return do_projeto


def mec_vigente(projeto, etapa_id, componente_id):
    return vigente(*mecs_por_etapa(projeto, componente_id, [etapa_id]).get(etapa_id, (None, None)))
