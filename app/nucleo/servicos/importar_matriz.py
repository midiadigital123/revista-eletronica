"""Importa a matriz (descritores e tarefas) de um PDF do SAEGO ou de uma planilha.

O alcance é o conjunto de etapa × CC presentes no arquivo: o PDF de LP não mexe nas
etapas que vieram do PDF Alfa. Dentro desse alcance, reimportar substitui descritores e
tarefas (D-071); a linha da MEC fica (mesmo id, `passo` e travas preservados).
"""
from pathlib import Path

from django.db import transaction
from django.db.models.functions import Now
from simple_history.utils import bulk_create_with_history

from nucleo.importacao import pdf, xlsx
from nucleo.models import Bloqueio, Componente, Descritor, Etapa, Matriz, MatrizEtapaCC, Tarefa

LEITORES = {".pdf": pdf.extrair, ".xlsx": xlsx.extrair}
MANTER = object()  # passo não informado: mantém o da MEC existente (nova MEC: NULL)


class ImportacaoRecusada(ValueError):
    pass


def ler(arquivo):
    """{(cc, etapa): {"escala", "descritores"}} conforme a extensão. Fica fora da transação:
    ler o PDF leva segundos e não precisa segurar trava."""
    leitor = LEITORES.get(Path(arquivo).suffix.lower())
    if not leitor:
        raise ImportacaoRecusada(f"formato não suportado: {Path(arquivo).name} (use .pdf ou .xlsx)")
    return leitor(str(arquivo))


def importar_matriz(matriz, arquivo, substituir=False, passo=MANTER):
    return gravar_matriz(matriz, ler(arquivo), substituir, passo, origem=Path(arquivo).name)


def gravar_matriz(matriz, dados, substituir=False, passo=MANTER, origem="arquivo"):
    """Grava as etapa × CC de `dados` (saída de `ler`) na matriz. Devolve {(cc, etapa): nº de descritores}.

    Sem `substituir`, recusa se alguma etapa × CC já existe na matriz. Com `substituir`,
    recusa se alguém está editando uma delas; senão apaga os descritores (tarefas em
    cascata) e recria. `passo` só muda quando informado (D-053, D-091).
    """
    if passo is not MANTER and passo is not None and passo <= 0:
        raise ImportacaoRecusada(f"passo deve ser positivo (recebido {passo})")
    etapas = {e.codigo: e for e in Etapa.objects.filter(ano=matriz.ano_id)}
    componentes = {c.codigo: c for c in Componente.objects.filter(ano=matriz.ano_id)}
    faltam = sorted(
        {f"etapa {e}" for _, e in dados if e not in etapas}
        | {f"componente {c}" for c, _ in dados if c not in componentes}
    )
    if faltam:
        raise ImportacaoRecusada(
            f"não cadastrados em {matriz.ano}: {', '.join(faltam)} (rode carregar_cadastros)"
        )
    for (cc, e), d in dados.items():
        if d["escala"]["max"] != etapas[e].escala_max:
            raise ImportacaoRecusada(
                f"{cc} {e}: escala do arquivo vai até {d['escala']['max']}, "
                f"a etapa até {etapas[e].escala_max}"
            )
    motivo = f"importação de {origem}"

    with transaction.atomic():
        # Dois imports na mesma matriz: o segundo espera aqui em vez de bater no UNIQUE da MEC.
        Matriz.objects.select_for_update().filter(pk=matriz.pk).first()
        existentes = {
            (m.componente.codigo, m.etapa.codigo): m
            for m in MatrizEtapaCC.objects.select_for_update(of=("self",))
            .select_related("etapa", "componente")
            .filter(
                matriz=matriz,
                etapa__codigo__in={e for _, e in dados},
                componente__codigo__in={c for c, _ in dados},
            )
            if (m.componente.codigo, m.etapa.codigo) in dados
        }
        if existentes and not substituir:
            raise ImportacaoRecusada(
                f"a matriz {matriz} já tem {', '.join(' '.join(k) for k in sorted(existentes))}; "
                "reimportar substitui descritores e tarefas (confirme com substituir)"
            )
        travas = [
            f"{b.matriz_etapa_cc.componente.codigo} {b.matriz_etapa_cc.etapa.codigo} ({b.usuario})"
            for b in Bloqueio.objects.select_related(
                "usuario", "matriz_etapa_cc__etapa", "matriz_etapa_cc__componente"
            ).filter(matriz_etapa_cc__in=existentes.values(), expira_em__gt=Now())
        ]
        if travas:
            raise ImportacaoRecusada(f"em edição agora: {', '.join(sorted(travas))}; tente depois")
        Descritor.objects.filter(matriz_etapa_cc__in=existentes.values()).delete()

        resumo = {}
        for (cc, e), d in sorted(dados.items(), key=lambda kv: (kv[0][0], etapas[kv[0][1]].ordem)):
            mec = existentes.get((cc, e)) or MatrizEtapaCC(
                matriz=matriz, etapa=etapas[e], componente=componentes[cc], ano_id=matriz.ano_id
            )
            if mec.pk is None or passo is not MANTER:
                mec.passo = None if passo is MANTER else passo
                mec._change_reason = motivo
                mec.save()
            descritores = bulk_create_with_history(
                [
                    Descritor(
                        matriz_etapa_cc=mec,
                        ordem=i,
                        **{k: v for k, v in desc.items() if k != "tarefas"},
                    )
                    for i, desc in enumerate(d["descritores"], start=1)
                ],
                Descritor,
                default_change_reason=motivo,
            )
            bulk_create_with_history(
                [
                    Tarefa(descritor=obj, ordem=j, arquivo=None, **t)
                    for obj, desc in zip(descritores, d["descritores"])
                    for j, t in enumerate(desc["tarefas"], start=1)
                ],
                Tarefa,
                default_change_reason=motivo,
            )
            resumo[(cc, e)] = len(descritores)
    return resumo
