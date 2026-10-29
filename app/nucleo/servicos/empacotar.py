"""Zip da revista (S15): site estático aberto por `file://`, sem servidor (D-103, D-109).

Conteúdo: `index.html` (modo zip, sem faixas: D-116), `revista/f1/*` e `revista/f2/*`
(cópia de `static/revista/`), `arquivos/capa.<ext>` e `arquivos/itens/<id>.<tipo>` (arquivo
da tarefa, no caminho que o JS do F1 abre: D-154). Dados, SVG, tour e modais vão inline no
`index.html` (D-125). Só sai sem pendências (D-112); problema do próprio pacote (item
inválido, arquivo ausente, arquivada com SVG/capa trocados) também recusa.
Bytes determinísticos: datas e permissões fixas, entradas em ordem.
"""

import io
import re
import shutil
import unicodedata
import zipfile
from pathlib import Path, PurePosixPath

from django.core.files.storage import default_storage
from django.template.loader import render_to_string

from nucleo.models import Tarefa
from nucleo.servicos.html import contexto_pagina
from nucleo.servicos.resolver import Pendencia, pendencias, resolver

ESTATICOS = Path(__file__).resolve().parents[1] / "static" / "revista"
EXTENSOES = {".js", ".css", ".svg", ".png", ".jpg", ".webp", ".woff2"}  # o resto (ex.: *.test.mjs) fica fora
COMPRIMIDOS = {".pdf", ".png", ".jpg", ".webp", ".woff2"}  # já comprimidos: ZIP_STORED
NOME_ITEM = re.compile(r"[A-Za-z0-9_-]+\.(pdf|png|jpg)")  # o que urlDoItem/tipoDoItem do JS abre


class Pendente(Exception):
    """A revista tem pendências; `pendencias` traz a lista (Pendencia do resolver)."""

    def __init__(self, lista):
        super().__init__(" ".join(p.mensagem for p in lista))
        self.pendencias = lista


def nome_zip(revista):
    """`<parceiro>-<cc>-<ano>.zip`, minúsculo, sem acento, só [a-z0-9-]."""
    projeto = revista.projeto
    bruto = f"{projeto.parceiro_ano.parceiro.nome}-{revista.componente.codigo}-{projeto.ano.ano}"
    ascii_ = unicodedata.normalize("NFKD", bruto).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", ascii_).strip("-") + ".zip"


def _nomes_dos_itens(resolvido):
    """{"<id>.<tipo>"} das linhas do F1 resolvido (a foto, na arquivada)."""
    return {
        f"{linha['item']['id']}.{linha['item']['tipo']}"
        for etapa in resolvido["f1"]["dados"].values()
        for descritor in etapa.values()
        if isinstance(descritor, dict) and "scale" in descritor
        for linhas in descritor["scale"].values()
        for linha in linhas
        if "item" in linha
    }


def _itens(revista, resolvido, erros):
    """{nome no zip: caminho no storage} só dos itens que o HTML usa."""
    nomes, itens, vistos = _nomes_dos_itens(resolvido), {}, set()
    tarefas = (
        Tarefa.objects.filter(
            descritor__matriz_etapa_cc__matriz_id=revista.projeto.parceiro_ano.matriz_id,
            descritor__matriz_etapa_cc__componente_id=revista.componente_id,
        )
        .exclude(arquivo=None)
        .exclude(arquivo="")
        .order_by("pk")
        .values_list("pk", "arquivo")
    )
    for pk, caminho in tarefas:
        nome = PurePosixPath(caminho).name
        if nome not in nomes:
            continue
        vistos.add(nome)
        if not NOME_ITEM.fullmatch(nome):
            erros.append(Pendencia("zip_item", f"Tarefa {pk}: nome de item inválido ({nome}); use letras, números, _ ou - e .pdf, .png ou .jpg."))
        elif itens.setdefault(nome, caminho) != caminho:
            erros.append(Pendencia("zip_item", f"Tarefa {pk}: outro arquivo já usa o nome {nome}."))
    erros.extend(Pendencia("zip_item", f"Item {n} sem arquivo de tarefa.") for n in sorted(nomes - vistos))
    return itens


def _entrada(nome):
    info = zipfile.ZipInfo(nome, date_time=(1980, 1, 1, 0, 0, 0))
    info.external_attr = 0o644 << 16
    info.compress_type = zipfile.ZIP_STORED if PurePosixPath(nome).suffix in COMPRIMIDOS else zipfile.ZIP_DEFLATED
    return info


def _copiar(z, nome, origem):
    with origem as f, z.open(_entrada(nome), "w") as destino:
        shutil.copyfileobj(f, destino)


def zip_revista(revista):
    """(nome, bytes) do zip. Recusa com `Pendente` (use `resolver.carregar(pk)` para a revista)."""
    resolvido = resolver(revista)
    erros = pendencias(revista, resolvido)
    if erros:
        raise Pendente(erros)
    # Arquivada: o HTML sai da foto (D-117), mas SVG e capa são os arquivos atuais.
    if (resolvido["f2"]["svg_sha256"], resolvido["capa_sha256"]) != (revista.svg_sha256, revista.capa_sha256):
        erros.append(Pendencia("zip_foto", "SVG ou capa mudaram depois da foto de arquivamento; o zip não bateria com o texto."))
    itens = _itens(revista, resolvido, erros)
    ausentes = [c for c in (revista.svg_f2, revista.capa, *itens.values()) if not default_storage.exists(c)]
    erros.extend(Pendencia("zip_arquivo", f"Arquivo ausente no storage: {c}.") for c in ausentes)
    if erros:
        raise Pendente(erros)

    capa = "arquivos/capa" + PurePosixPath(revista.capa).suffix
    html = render_to_string(
        "revista/index.html", contexto_pagina(revista, preview=False, estaticos="revista/", capa=capa)
    )
    # ponytail: zip em memória (SVG ~1 MB + capa ≤ 5 MB + itens PDF sem limite de tamanho);
    # quando pesar, trocar o BytesIO por tempfile.SpooledTemporaryFile e devolver FileResponse.
    saida = io.BytesIO()
    with zipfile.ZipFile(saida, "w") as z:
        z.writestr(_entrada("index.html"), html)
        for arquivo in sorted(ESTATICOS.rglob("*")):
            if arquivo.is_file() and arquivo.suffix in EXTENSOES:
                _copiar(z, "revista/" + arquivo.relative_to(ESTATICOS).as_posix(), arquivo.open("rb"))
        _copiar(z, capa, default_storage.open(revista.capa))
        for nome, caminho in sorted(itens.items()):
            _copiar(z, f"arquivos/itens/{nome}", default_storage.open(caminho))
    return nome_zip(revista), saida.getvalue()
