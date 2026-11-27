"""Seed dos infográficos do F2 (D-298): o conteúdo que a Pedagógica mandou em Word, copiado para cada infográfico.

`templates_seed/<ano>/infograficos/<cc>-<tipo>.json` sai de `scripts/docx_infografico.py`, com os nomes de campo
de `nucleo/infografico.py`. A cópia só preenche o que está vazio: o que a revista já tem fica (a edição é na ficha).
"""

import hashlib
import json
from collections import Counter
from pathlib import Path

from django.conf import settings

from nucleo.infografico import EtapaForm, InfograficoForm, ItemForm
from nucleo.models import RevistaInfograficoEtapa, RevistaInfograficoItem
from nucleo.models.revista import EtapaReferencial
from nucleo.servicos import arquivos
from nucleo.texto import TOKENS_BLOCO, TOKENS_INLINE, _proibidos

CAMPOS_INF = ("habilidade", "texto_descritor", "texto_progressao", "texto_habilidades")
CAMPOS_ETAPA = ("marca", "codigo", "texto", "junta_marca", "junta_habilidade")
CAMPOS_ITEM = ("etapa", "descritor", "texto_alternativo", "analise")
RICOS = ("texto_descritor", "texto_progressao", "texto_habilidades")


def pasta(ano):
    return settings.BASE_DIR / "templates_seed" / str(ano) / "infograficos"


def seeds(ano, onde=None):
    """{(código do componente, tipo): seed} da pasta (padrão: a do ano); sem pasta, {}.
    O seed leva `_arquivo` (nome do JSON) e `_pasta` (onde estão as imagens)."""
    onde = Path(onde) if onde else pasta(ano)
    saida = {}
    for arquivo in sorted(onde.glob("*.json")):
        seed = json.loads(arquivo.read_text(encoding="utf-8"))
        saida[(seed["componente"], seed["tipo"])] = {**seed, "_arquivo": arquivo.name, "_pasta": onde}
    return saida


def _imagem(seed, item):
    return (seed["_pasta"] / item["imagem"]).read_bytes()


def validar(seed):
    """Erros do seed pelos mesmos forms da ficha da revista; [] se está bom."""
    erros = []

    def form(Form, dados, onde):
        f = Form(dados)
        if not f.is_valid():
            erros.extend(f"{onde}: {campo}: {' '.join(m)}" for campo, m in f.errors.items())

    try:
        form(InfograficoForm, {c: seed[c] for c in CAMPOS_INF}, "infográfico")
        erros += [f"{c}: vazio" for c in RICOS if not seed[c].strip()]
        erros += [f"{c}: recurso não permitido: {', '.join(r)}" for c in RICOS
                  if (r := _proibidos(seed[c], TOKENS_BLOCO | TOKENS_INLINE))]  # fmt: skip
        if list(seed["etapas"]) != EtapaReferencial.values:
            erros.append(f"etapas fora da lista 1EF–3EM: {list(seed['etapas'])}")
        for etapa, valores in seed["etapas"].items():
            form(EtapaForm, {c: valores[c] for c in CAMPOS_ETAPA}, f"etapa {etapa}")
        if [i["posicao"] for i in seed["itens"]] != [1, 2, 3, 4]:
            erros.append("os itens precisam ser as posições 1 a 4")
        for item in seed["itens"]:
            onde = f"item {item['posicao']}"
            form(ItemForm, {c: item[c] for c in CAMPOS_ITEM}, onde)
            if r := _proibidos(item["analise"], TOKENS_BLOCO | TOKENS_INLINE):
                erros.append(f"{onde}: análise: recurso não permitido: {', '.join(r)}")
            imagem = seed["_pasta"] / item["imagem"]
            dados = imagem.read_bytes() if imagem.is_file() else b""
            if arquivos.tipo_imagem(dados) is None or len(dados) > arquivos.ITEM_MAX:
                erros.append(f"{onde}: imagem {item['imagem']} ausente, fora de PNG/JPG/WebP ou maior que 5 MB")
    except KeyError as e:
        erros.append(f"falta a chave {e}")
    return erros


def _decidir(atual, novo, velho):
    """O que fazer com um campo (D-298): vazio recebe o novo; igual ao seed anterior também (é o
    texto que a carga pôs e ninguém mexeu); outro valor é edição da revista e fica."""
    if atual == novo:
        return None
    if atual in ("", None) or atual is False:  # flag desligada (junta_*) é o vazio do booleano
        return "preenchidos"
    if velho is not None and atual == velho:
        return "atualizados"
    return "mantidos"


def _copiar(obj, novo, velho, campos, conta):
    """Aplica `_decidir` aos `campos` de `obj`; devolve os que mudaram."""
    mudou = []
    for c in campos:
        destino = _decidir(getattr(obj, c), novo[c], velho.get(c) if velho else None)  # seed antigo: sem junta_*
        if destino:
            conta[destino] += 1
        if destino in ("preenchidos", "atualizados"):  # atualizado pode ir para "" (célula mesclada nova)
            setattr(obj, c, novo[c])
            mudou.append(c)
    return mudou


def _salvar(obj, campos, usuario):
    if campos or not obj.pk:
        obj._history_user = usuario
        obj.save(update_fields=campos if obj.pk else None)


def preencher(inf, seed, usuario, anterior=None):
    """Copia o `seed` para o infográfico `inf` (regra em `_decidir`). `anterior`: o seed que a carga
    anterior usou; sem ele, só o vazio é preenchido. Devolve Counter(preenchidos, atualizados, mantidos);
    a imagem conta como um campo, comparada pelo sha256."""
    conta = Counter()
    _salvar(inf, _copiar(inf, seed, anterior, CAMPOS_INF, conta), usuario)

    etapas = {e.etapa: e for e in RevistaInfograficoEtapa.objects.filter(infografico=inf)}
    for etapa, valores in seed["etapas"].items():
        obj = etapas.get(etapa) or RevistaInfograficoEtapa(infografico=inf, ano_id=inf.ano_id, etapa=etapa)
        velho = anterior["etapas"].get(etapa) if anterior else None
        _salvar(obj, _copiar(obj, valores, velho, CAMPOS_ETAPA, conta), usuario)

    itens = {i.posicao: i for i in RevistaInfograficoItem.objects.filter(infografico=inf)}
    velhos = {i["posicao"]: i for i in anterior["itens"]} if anterior else {}
    for valores in seed["itens"]:
        obj = itens.get(valores["posicao"]) or RevistaInfograficoItem(
            infografico=inf, ano_id=inf.ano_id, posicao=valores["posicao"]
        )
        velho = velhos.get(valores["posicao"])
        _salvar(obj, _copiar(obj, valores, velho, CAMPOS_ITEM, conta), usuario)
        dados = _imagem(seed, valores)
        sha_velho = hashlib.sha256(_imagem(anterior, velho)).hexdigest() if velho else None
        destino = _decidir(obj.imagem_sha256, hashlib.sha256(dados).hexdigest(), sha_velho)
        if destino:
            conta[destino] += 1
        if destino in ("preenchidos", "atualizados"):
            # Um arquivo por revista (uuid): o antigo, apagado no commit, nunca é a imagem de outra.
            obj._history_user = usuario
            arquivos.receber_imagem_item(obj, dados)
    return conta
