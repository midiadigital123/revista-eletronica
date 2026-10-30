"""Duplicar matriz, diferenças contra a origem e impacto de uma edição (D-076, D-101, D-113, D-124)."""

from django.db import IntegrityError, transaction
from django.db.models import Q

from nucleo.models import Componente, Descritor, Etapa, Matriz, MatrizEtapaCC, Revista, Tarefa
from nucleo.servicos.abrir_ano import clonar
from nucleo.servicos.resolver import hash_validado
from nucleo.servicos.validacao import validada

# Campos do descritor comparados no diff (ordem de exibição).
CAMPOS_DESCRITOR = (
    "descricao", "prerequisitos", "praticas", "conhecimento",
    "habilidades_relacionadas", "habilidade_correspondente",
)  # fmt: skip


class DuplicacaoRecusada(ValueError):
    pass


def duplicar_matriz(origem, ano, nome, usuario=None):
    """Copia `origem` (de qualquer ano) para `ano` com o nome `nome`: MECs, descritores e
    tarefas. Etapa e componente casam pelo `codigo` (FKs compostas de ano, D-124).
    A cópia guarda `duplicada_de = origem` só para consulta (D-113). Devolve a matriz nova."""
    motivo = f"duplicada de {origem}"[:100]  # history_change_reason é varchar(100)
    # ponytail: lê em READ COMMITTED; uma edição de descritor salva no meio da cópia pode
    # entrar pela metade (só a reimportação, que recria ids, é barrada pela trava abaixo).
    # ponytail: escala_max da etapa destino não é comparada com a da origem; tarefa fora
    # da escala nova só aparece no preview.
    with transaction.atomic():
        # Trava a origem: uma reimportação (gravar_matriz trava a Matriz) recriaria
        # descritores com ids novos no meio da cópia.
        Matriz.objects.select_for_update(no_key=True).filter(pk=origem.pk).first()
        mecs = MatrizEtapaCC.objects.filter(matriz=origem)
        etapas = {e.codigo: e.pk for e in Etapa.objects.filter(ano=ano)}
        componentes = {c.codigo: c.pk for c in Componente.objects.filter(ano=ano)}
        usadas_e = dict(Etapa.objects.filter(matrizetapacc__in=mecs).values_list("pk", "codigo").distinct())
        usados_c = dict(
            Componente.objects.filter(matrizetapacc__in=mecs).values_list("pk", "codigo").distinct()
        )
        faltam = sorted(
            {f"etapa {c}" for c in usadas_e.values() if c not in etapas}
            | {f"componente {c}" for c in usados_c.values() if c not in componentes}
        )
        if faltam:
            raise DuplicacaoRecusada(f"não cadastrados em {ano}: {', '.join(faltam)}")

        nova = Matriz(ano=ano, nome=nome, duplicada_de=origem)
        nova._history_user, nova._change_reason = usuario, motivo
        try:
            with transaction.atomic():
                nova.save()
        except IntegrityError:
            raise DuplicacaoRecusada(f"já existe a matriz {nome} em {ano}") from None

        mapa_mec = clonar(
            mecs, usuario, motivo, matriz_id=nova.pk, ano_id=ano.pk,
            etapa_id={pk: etapas[c] for pk, c in usadas_e.items()},
            componente_id={pk: componentes[c] for pk, c in usados_c.items()},
        )  # fmt: skip
        mapa_desc = clonar(
            Descritor.objects.filter(matriz_etapa_cc__matriz=origem), usuario, motivo,
            matriz_etapa_cc_id=mapa_mec,
        )  # fmt: skip
        clonar(
            Tarefa.objects.filter(descritor__matriz_etapa_cc__matriz=origem), usuario, motivo,
            descritor_id=mapa_desc,
        )  # fmt: skip
    return nova


def _conteudo(matriz):
    """{(etapa, cc): {"passo", "descritores": {codigo: {campos..., "tarefas"}}}}"""
    mecs = {
        m.pk: {"chave": (m.etapa.codigo, m.componente.codigo), "passo": m.passo, "descritores": {}}
        for m in MatrizEtapaCC.objects.filter(matriz=matriz).select_related("etapa", "componente")
    }
    descritores = {}
    for d in Descritor.objects.filter(matriz_etapa_cc__matriz=matriz):
        dados = {c: getattr(d, c) for c in CAMPOS_DESCRITOR}
        dados["tarefas"] = []
        mecs[d.matriz_etapa_cc_id]["descritores"][d.codigo] = descritores[d.pk] = dados
    for t in Tarefa.objects.filter(descritor__matriz_etapa_cc__matriz=matriz).order_by("ordem", "pk"):
        descritores[t.descritor_id]["tarefas"].append(f"{t.inicio}–{t.fim}: {t.texto}")
    return {m["chave"]: m for m in mecs.values()}


def _texto(valor):
    if isinstance(valor, list):
        return "\n".join(valor)
    return "" if valor is None else str(valor)


def diferencas(matriz):
    """Linhas (onde, campo, na origem, na cópia) do que difere de `duplicada_de`. Só consulta."""
    if matriz.duplicada_de_id is None:
        return []
    origem, copia = _conteudo(matriz.duplicada_de), _conteudo(matriz)
    linhas = []
    ordem = {e.codigo: e.ordem for e in Etapa.objects.filter(ano__in=[matriz.ano_id, matriz.duplicada_de.ano_id])}
    for chave in sorted(origem.keys() | copia.keys(), key=lambda k: (ordem.get(k[0], 0), k)):
        onde = " ".join(chave)
        a, b = origem.get(chave), copia.get(chave)
        if a is None or b is None:
            linhas.append((onde, "etapa × CC", "existe" if a else "—", "existe" if b else "—"))
            continue
        if a["passo"] != b["passo"]:
            linhas.append((onde, "intervalo mínimo", _texto(a["passo"]), _texto(b["passo"])))
        da, db = a["descritores"], b["descritores"]
        for codigo in sorted(da.keys() | db.keys()):
            x, y = da.get(codigo), db.get(codigo)
            if x is None or y is None:
                linhas.append((f"{onde} {codigo}", "descritor", "existe" if x else "—", "existe" if y else "—"))
                continue
            for campo in (*CAMPOS_DESCRITOR, "tarefas"):
                if x[campo] != y[campo]:
                    linhas.append((f"{onde} {codigo}", campo, _texto(x[campo]), _texto(y[campo])))
    return linhas


def revistas_afetadas(*mecs):
    """Quantas revistas ativas mudam com uma edição destas MECs (D-076)."""
    return _afetadas(mecs).count() if mecs else 0


def impacto(*mecs):
    """[(revista, validada agora)] das revistas ativas afetadas: as validadas perdem o
    "Validado" com a edição, porque o hash muda (D-076, D-181)."""
    # ponytail: um resolver por revista (~25 na Comunitária); cache se a página ficar lenta.
    revistas = _afetadas(mecs).select_related(
        "projeto__parceiro_ano__parceiro", "projeto__ano", "componente"
    ).order_by("projeto__parceiro_ano__parceiro__nome", "componente__codigo") if mecs else []
    return [(r, validada(r, hash_validado(r))) for r in revistas]


def _afetadas(mecs):
    """Revistas ativas que mudam com uma edição destas MECs: o ParceiroAno usa a matriz, a
    revista é do componente e há corte nessa etapa × componente."""
    q = Q()
    for m in mecs:  # num filter() só: as condições sobre o corte usam o mesmo JOIN
        q |= Q(
            componente_id=m.componente_id,
            projeto__parceiro_ano__matriz_id=m.matriz_id,
            projeto__parceiro_ano__corte__etapa_id=m.etapa_id,
            projeto__parceiro_ano__corte__componente_id=m.componente_id,
        )
    return Revista.objects.filter(q, arquivada_em__isnull=True).distinct()
