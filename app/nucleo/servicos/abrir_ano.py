"""Abre o ano seguinte ao maior existente, copiando os cadastros dele (D-054, D-086, D-119).

Copia etapas, componentes, cores, matrizes (MEC, descritores e tarefas) e templates
(a última versão vira a versão 1). Não copia parceiro_ano, cortes, projetos nem escolhas
de matriz/template: o ano nasce em branco e os projetos vêm da cascata dos cortes novos
(D-106, D-119). Tudo numa transação (D-125): falhou, nada fica.
"""
from django.db import IntegrityError, connection, transaction
from django.db.models import Max
from simple_history.utils import bulk_create_with_history

from nucleo.models import (
    Ano, Componente, CorPadrao, Descritor, Etapa, Matriz, MatrizEtapaCC, Tarefa, Template,
    TemplateVersao,
)


class AnoRecusado(ValueError):
    pass


def clonar(queryset, usuario, motivo, **trocas):
    """Clona as linhas do queryset trocando campos (também usado por duplicar matriz).
    Cada troca é um dict {valor antigo: novo}, uma função do objeto de origem ou uma
    constante. Devolve {id antigo: id novo}."""
    antigos, objs = [], []
    for obj in queryset.order_by("pk"):
        valores = {
            campo: t[getattr(obj, campo)] if isinstance(t, dict) else t(obj) if callable(t) else t
            for campo, t in trocas.items()
        }
        antigos.append(obj.pk)
        obj.pk, obj._state.adding = None, True
        for campo, valor in valores.items():
            setattr(obj, campo, valor)
        objs.append(obj)
    objs = bulk_create_with_history(
        objs, queryset.model, default_user=usuario, default_change_reason=motivo[:100]
    )
    return {a: o.pk for a, o in zip(antigos, objs)}


def abrir_ano(ano, usuario=None):
    """Cria `ano`, que precisa ser o seguinte ao maior existente, copiando esse ano.
    Devolve (ano novo, ano de origem).

    `usuario` vai para o histórico e para `TemplateVersao.criada_por` (nulo pelo comando).
    A permissão `abrir_ano` é conferida por quem chama (ação do admin, S11a).
    """
    fora_de_atomic = not connection.in_atomic_block
    with transaction.atomic():
        if fora_de_atomic:
            # Foto única da origem (regra do foto.py, D-138): uma reimportação concorrente
            # (gravar_matriz com substituir) recria descritores com ids novos, e ler cada
            # tabela num instante diferente quebraria o mapa de ids. SET TRANSACTION só vale
            # como 1ª instrução, por isso só fora de atomic.
            # ponytail: chamado dentro de atomic (testes), usa o isolamento do chamador.
            with connection.cursor() as c:
                c.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")
        if Ano.objects.filter(ano=ano).exists():
            raise AnoRecusado(f"{ano} já está aberto")
        maior = Ano.objects.aggregate(m=Max("ano"))["m"]
        if maior is None:
            raise AnoRecusado(f"nenhum ano anterior a {ano} para copiar")
        if ano != maior + 1:  # sem buracos: barra typo (20277) e 2027 × 2028 ao mesmo tempo
            raise AnoRecusado(f"{ano} recusado: o próximo ano que pode ser aberto é {maior + 1}")
        origem = Ano.objects.get(ano=maior)
        motivo = f"abrir ano {ano} a partir de {origem}"

        novo = Ano(ano=ano)
        novo._history_user, novo._change_reason = usuario, motivo
        try:
            with transaction.atomic():  # o UNIQUE continua barrando a corrida de dois 2027
                novo.save()
        except IntegrityError:
            raise AnoRecusado(f"{ano} já está aberto") from None

        def copiar(modelo, **trocas):
            filtro = {
                MatrizEtapaCC: "ano", Descritor: "matriz_etapa_cc__ano",
                Tarefa: "descritor__matriz_etapa_cc__ano",
            }.get(modelo, "ano")  # fmt: skip
            return clonar(modelo.objects.filter(**{filtro: origem}), usuario, motivo, **trocas)

        etapas = copiar(Etapa, ano_id=novo.pk)
        componentes = copiar(Componente, ano_id=novo.pk)
        copiar(CorPadrao, ano_id=novo.pk)
        # A cópia aponta para a matriz de origem, não para a origem dela (D-113: só consulta).
        matrizes = copiar(Matriz, ano_id=novo.pk, duplicada_de_id=lambda m: m.pk)
        mecs = copiar(
            MatrizEtapaCC, ano_id=novo.pk, matriz_id=matrizes, etapa_id=etapas,
            componente_id=componentes,
        )  # fmt: skip
        descritores = copiar(Descritor, matriz_etapa_cc_id=mecs)
        copiar(Tarefa, descritor_id=descritores)
        templates = copiar(Template, ano_id=novo.pk, componente_id=componentes)

        # template_versao é só INSERT e sem histórico (D-115, D-133).
        ultimas = (
            TemplateVersao.objects.filter(template__ano=origem)
            .order_by("template_id", "-numero")
            .distinct("template_id")
        )
        TemplateVersao.objects.bulk_create(
            TemplateVersao(template_id=templates[v.template_id], numero=1, texto=v.texto, criada_por=usuario)
            for v in ultimas
        )
    return novo, origem
