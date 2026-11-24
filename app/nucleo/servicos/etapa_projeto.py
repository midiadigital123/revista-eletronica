"""Etapa do projeto (D-280): cópia própria de uma etapa de matriz, com vínculo à base.

A foto é o conteúdo canônico de uma etapa de matriz (por código de descritor, não por id),
guardada em `base_foto` ao clonar para saber depois o que a base mudou desde então.
"""
from typing import NamedTuple

from django.db import IntegrityError, transaction
from django.db.models import Q

from nucleo.models import Descritor, Matriz, MatrizEtapaCC, Tarefa
from nucleo.models.cadastro import ETAPAS_CANONICAS
from nucleo.servicos.abrir_ano import clonar
from nucleo.servicos.arquivos import apagar_item_orfao
from nucleo.servicos.matriz import CAMPOS_DESCRITOR
from nucleo.servicos.resolver import sha256


class CriacaoRecusada(ValueError):
    pass


class RevisaoRecusada(ValueError):
    pass


class RevisaoMudou(ValueError):
    """O `visto` não é mais a classificação de agora: base, local ou foto mudaram."""


class RevisaoIncompleta(ValueError):
    """Há conflito sem escolha."""


def _norm(texto):
    return " ".join(texto.split())


def _objetos(mec):
    """{codigo: (descritor, {"inicio-fim#n": tarefa})}: os objetos do banco que a `foto` descreve, na
    mesma chave. É a única origem do `#n` (ordinal da tarefa dentro da faixa, por ordem e pk)."""
    saida = {d.codigo: (d, {}) for d in Descritor.objects.filter(matriz_etapa_cc=mec)}
    por_pk = {d.pk: tarefas for d, tarefas in saida.values()}
    contagem = {}
    for t in Tarefa.objects.filter(descritor__matriz_etapa_cc=mec).order_by("ordem", "pk"):
        faixa = (t.descritor_id, t.inicio, t.fim)
        contagem[faixa] = n = contagem.get(faixa, 0) + 1
        # ponytail: identidade pela faixa; corrigir a faixa aparece como remover + criar.
        # Parear por (inicio, fim) se incomodar.
        por_pk[t.descritor_id][f"{t.inicio}-{t.fim}#{n}"] = t
    return saida


def foto(mec):
    """Conteúdo canônico da etapa, só valores JSON: {"passo", "descritores": {codigo: {"ordem",
    <CAMPOS_DESCRITOR>, "tarefas": {"inicio-fim#n": {texto, arquivo, texto_alternativo, ordem}}}}}.
    Texto com os espaços normalizados."""
    return _foto(mec.passo, _objetos(mec))


def _foto(passo, objetos):
    """A `foto` a partir de `_objetos` já lidos: quem precisa da foto e dos objetos lê o banco uma vez só."""
    descritores = {}
    for codigo, (d, tarefas) in objetos.items():
        dados = {c: _norm(getattr(d, c)) for c in CAMPOS_DESCRITOR if c != "prerequisitos"}
        dados["prerequisitos"] = [_norm(p) for p in d.prerequisitos]
        dados["ordem"] = d.ordem
        dados["tarefas"] = {
            chave: {
                "texto": _norm(t.texto),
                "arquivo": t.arquivo or None,
                "texto_alternativo": _norm(t.texto_alternativo),
                "ordem": t.ordem,
            }
            for chave, t in tarefas.items()
        }
        descritores[codigo] = dados
    return {"passo": passo, "descritores": descritores}


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
    """Cria a etapa × componente do projeto, clonada de `base` com `base_foto`. Se a matriz do
    parceiro tem a etapa, é a cópia local dela (D-288): a base é essa etapa (`base=None` a usa). Se
    não tem, a etapa é não canônica e a base é etapa canônica de uma matriz (qualquer matriz,
    qualquer ano), do mesmo componente (D-276). Recusa com `CriacaoRecusada`; tudo numa transação."""
    with transaction.atomic():
        if projeto.arquivado_em is not None:
            raise CriacaoRecusada("projeto arquivado")
        nome = f"{etapa.codigo} {componente.codigo}"
        matriz_id = projeto.parceiro_ano.matriz_id
        da_matriz = matriz_id and MatrizEtapaCC.objects.filter(matriz_id=matriz_id, etapa=etapa, componente=componente).first()
        if da_matriz:
            if base is not None and base.pk != da_matriz.pk:
                raise CriacaoRecusada("a base da cópia local é a etapa da matriz do parceiro")
            base = da_matriz
        elif etapa.codigo in ETAPAS_CANONICAS:
            raise CriacaoRecusada(f"{etapa.codigo} é etapa canônica: corrija na matriz")
        elif base is None:
            raise CriacaoRecusada("a etapa do projeto precisa de uma base")
        elif base.matriz_id is None:
            raise CriacaoRecusada("a base precisa ser etapa de matriz")
        elif base.etapa.codigo not in ETAPAS_CANONICAS:
            raise CriacaoRecusada("a base precisa ser etapa canônica (2EF, 5EF, 9EF ou 3EM)")
        if base.componente.codigo != componente.codigo:
            raise CriacaoRecusada("a base precisa ser do mesmo componente")
        if MatrizEtapaCC.objects.filter(projeto=projeto, etapa=etapa, componente=componente).exists():
            raise CriacaoRecusada(f"o projeto já tem {nome}")

        mec = MatrizEtapaCC(projeto=projeto, etapa=etapa, componente=componente, ano_id=projeto.ano_id)
        motivo = f"clone de {base}"[:100]
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
        mapa = clonar(Descritor.objects.filter(matriz_etapa_cc=base), usuario, motivo, matriz_etapa_cc_id=mec.pk)
        clonar(Tarefa.objects.filter(descritor__in=list(mapa)), usuario, motivo, descritor_id=mapa)
    return mec


def revisao(mec):
    """O que a base mudou desde o clone: `(itens, visto)`. `visto` é o hash dos itens (base, local e foto
    de uma vez): quem conclui devolve o que viu, e `concluir` recusa se algo mudou."""
    itens = classificar(mec.base_foto, foto(mec.base), foto(mec))
    return itens, sha256(itens)


def pendente(mec):
    """A base mudou desde a cópia e ninguém revisou: a condição da lacuna "base" (o resolver pergunta aqui)."""
    # ponytail: uma foto da base por chamada (o resolver chama por etapa do projeto); cache se a página ficar lenta.
    return bool(mec.projeto_id and mec.base_id and hash_foto(foto(mec.base)) != hash_foto(mec.base_foto))


# Campos em que a escolha ("texto", s) vale: os de texto livre do descritor e da tarefa.
CAMPOS_TEXTO = {
    "descricao", "praticas", "conhecimento", "habilidades_relacionadas", "habilidade_correspondente",
    "texto", "texto_alternativo",
}  # fmt: skip
MOTIVO = "revisão da base"


def _partir(chave, *objetos):
    """(código, tarefa) da chave; tarefa "" se a chave é de descritor. O código é livre e pode ter
    barra: primeiro a chave inteira como código; a da tarefa ("inicio-fim#n") nunca tem barra."""
    if any(chave in o for o in objetos):
        return chave, ""
    codigo, _, tarefa = chave.rpartition("/")
    return codigo, tarefa


def _objeto(objetos, chave):
    """O descritor ou a tarefa que a chave ("D01" ou "D01/100-150#1") nomeia em `_objetos`, ou None."""
    codigo, tarefa = _partir(chave, objetos)
    if codigo not in objetos:
        return None
    return objetos[codigo][1].get(tarefa) if tarefa else objetos[codigo][0]


def textos_locais(mec, itens):
    """{(chave, campo): texto} do projeto como está no banco, nos `CAMPOS_TEXTO`. `Item.local` vem da
    foto, que junta espaços e quebras de linha: quem edita o texto na revisão parte deste."""
    objetos = _objetos(mec)
    return {(i.chave, i.campo): getattr(_objeto(objetos, i.chave), i.campo) for i in itens if i.campo in CAMPOS_TEXTO}


def concluir(mec, escolhas, visto, usuario):
    """Grava a decisão da revisão em 3 vias e avança `base_foto`. `escolhas` é
    {(chave, campo): "base" | "local" | ("texto", s)}; "entra" sem escolha vale "base", "conflito" sem
    escolha é `RevisaoIncompleta`. Escolha de chave que não está nos itens é ignorada. `visto` é o de
    `revisao()`: outro valor é `RevisaoMudou`. Tudo numa transação; devolve quantas células aplicou.
    Quem chama relê a MEC do banco antes de outra `revisao()` (a instância recebida não é atualizada)
    e, pela tela, chama sob o bloqueio de escrita (`servicos/bloqueio.py`)."""
    with transaction.atomic():
        mec = MatrizEtapaCC.objects.select_for_update().get(pk=mec.pk)
        if mec.projeto_id is None:
            raise RevisaoRecusada("só a etapa do projeto tem revisão")
        if mec.base_id is None:
            raise RevisaoRecusada("etapa sem base")
        if mec.projeto.arquivado_em is not None:
            raise RevisaoRecusada("projeto arquivado")
        base = mec.base
        # Trava a matriz da base (como o `criar`): uma reimportação recriaria descritores no meio.
        Matriz.objects.select_for_update(no_key=True).filter(pk=base.matriz_id).first()
        base.refresh_from_db()
        # Base e local lidos uma vez só: a edição da matriz não toma a trava acima, e uma segunda
        # leitura poderia pôr em `base_foto` uma mudança que ninguém viu.
        locais, da_base = _objetos(mec), _objetos(base)
        foto_base = _foto(base.passo, da_base)
        itens = classificar(mec.base_foto, foto_base, _foto(mec.passo, locais))
        if visto != sha256(itens):
            raise RevisaoMudou("a base ou a etapa mudou desde que a revisão foi aberta")
        decididas = []
        for item in itens:
            escolha = escolhas.get((item.chave, item.campo), "base" if item.situacao == "entra" else None)
            if escolha is None:
                raise RevisaoIncompleta(f"escolha {item.chave} · {item.campo}")
            if escolha not in ("base", "local"):
                if not (isinstance(escolha, tuple) and len(escolha) == 2 and escolha[0] == "texto" and isinstance(escolha[1], str)):
                    raise RevisaoRecusada(f"escolha inválida: {escolha!r}")
                if item.campo not in CAMPOS_TEXTO:
                    raise RevisaoRecusada(f"{item.campo} não é campo de texto")
                if item.campo == "texto_alternativo" and len(escolha[1]) > 1000:  # o max_len do banco
                    raise RevisaoRecusada("texto alternativo com mais de 1000 caracteres")
            decididas.append((item, escolha))

        # `locais` e `da_base` vêm de antes de aplicar: apagar uma tarefa mudaria o `#n` das seguintes.
        sujos, aplicadas = {}, 0
        for item, escolha in decididas:
            if escolha == "local":
                continue
            aplicadas += 1
            if item.campo == "passo":
                mec.passo = base.passo
            elif item.campo == "existe":
                _aplicar_existe(mec, item.chave, locais, da_base, usuario)
            else:
                alvo = _objeto(locais, item.chave)
                antigo = getattr(alvo, item.campo)
                setattr(alvo, item.campo, getattr(_objeto(da_base, item.chave), item.campo) if escolha == "base" else escolha[1])
                sujos.setdefault(id(alvo), (alvo, []))[1].append(item.campo)
                if item.campo == "arquivo":
                    apagar_item_orfao(antigo)
        for alvo, campos in sujos.values():
            alvo._history_user, alvo._change_reason = usuario, MOTIVO
            alvo.save(update_fields=campos)

        mec.base_foto = foto_base
        mec._history_user = usuario
        mec._change_reason = f"{MOTIVO}: aplicou {aplicadas}, manteve {len(decididas) - aplicadas}"
        mec.save(update_fields=["passo", "base_foto"])  # sem `base`: o trigger recusa mudá-la
    return aplicadas


def _aplicar_existe(mec, chave, locais, da_base, usuario):
    """O descritor ou a tarefa inteira passa a ser o da base: apaga o local, se houver, e copia o da base."""
    local, nova = _objeto(locais, chave), _objeto(da_base, chave)
    motivo = f"{MOTIVO}: cópia de {mec.base}"[:100]
    codigo, tarefa = _partir(chave, locais, da_base)
    if local is not None:
        # As tarefas do descritor saem antes, uma a uma: em cascata ficariam sem usuário no histórico.
        for obj in (*([] if tarefa else locais[codigo][1].values()), local):
            obj._history_user, obj._change_reason = usuario, MOTIVO
            obj.delete()  # o arquivo órfão sai pelo post_delete da Tarefa
    if nova is None:
        return
    if tarefa:  # o descritor existe nos dois lados
        clonar(Tarefa.objects.filter(pk=nova.pk), usuario, motivo, descritor_id=locais[codigo][0].pk)
    else:
        mapa = clonar(Descritor.objects.filter(pk=nova.pk), usuario, motivo, matriz_etapa_cc_id=mec.pk)
        clonar(Tarefa.objects.filter(descritor__in=list(mapa)), usuario, motivo, descritor_id=mapa)


def desfazer(mec, usuario):
    """Desfaz o apontamento (D-287): apaga a etapa do projeto com os descritores e as tarefas dela.
    Um a um, para o histórico levar o usuário; o arquivo de item órfão sai pelo sinal da Tarefa."""
    with transaction.atomic():
        mec = MatrizEtapaCC.objects.select_for_update().get(pk=mec.pk)
        if mec.projeto_id is None:
            raise RevisaoRecusada("só a etapa do projeto tem apontamento")
        if mec.projeto.arquivado_em is not None:
            raise RevisaoRecusada("projeto arquivado")
        motivo = "apontamento desfeito"
        descritores = list(Descritor.objects.filter(matriz_etapa_cc=mec))
        for obj in [*Tarefa.objects.filter(descritor__in=descritores), *descritores, mec]:
            obj._history_user, obj._change_reason = usuario, motivo
            obj.delete()


def derivadas(*mecs):
    """MECs de projeto ativo clonadas de uma destas (etapas de matriz)."""
    return MatrizEtapaCC.objects.filter(base__in=mecs, projeto__arquivado_em__isnull=True)


def _dono(projeto):
    """As MECs que as revistas do projeto podem usar: as da matriz do parceiro e as do projeto."""
    dono = Q(projeto=projeto)
    if projeto.parceiro_ano.matriz_id is not None:  # matriz_id=None casaria toda MEC de projeto
        dono |= Q(matriz_id=projeto.parceiro_ano.matriz_id)
    return dono


def mecs_por_etapa(projeto, componente_id, etapa_ids):
    """{etapa_id: (MEC da matriz do parceiro, MEC do projeto)}, None onde não há."""
    saida = {}
    for m in MatrizEtapaCC.objects.filter(_dono(projeto), componente_id=componente_id, etapa_id__in=list(etapa_ids)):
        par = saida.setdefault(m.etapa_id, [None, None])
        par[m.projeto_id is not None] = m
    return {e: tuple(par) for e, par in saida.items()}


def tarefas_da_revista(revista):
    """Tarefas das MECs que a revista pode usar: onde o zip e o preview acham o arquivo do item."""
    mecs = MatrizEtapaCC.objects.filter(_dono(revista.projeto), componente_id=revista.componente_id)
    return Tarefa.objects.filter(descritor__matriz_etapa_cc__in=mecs)


def vigente(da_matriz, do_projeto):
    """A MEC que a revista usa: a cópia do projeto sempre vale sobre a da matriz (D-288)."""
    return do_projeto or da_matriz


def mec_vigente(projeto, etapa_id, componente_id):
    return vigente(*mecs_por_etapa(projeto, componente_id, [etapa_id]).get(etapa_id, (None, None)))
