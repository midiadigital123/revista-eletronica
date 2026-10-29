"""Zip da revista (S15): site estático aberto por `file://`, sem servidor (D-103, D-109).

Conteúdo: `index.html` (modo zip, sem faixas: D-116), `revista/f1/*` e `revista/f2/*`
(cópia de `static/revista/`), `arquivos/capa.<ext>` e `arquivos/itens/<id>.<tipo>` (arquivo
da tarefa, no caminho que o JS do F1 abre: D-154). Dados, SVG, tour e modais vão inline no
`index.html` (D-125). Só sai sem pendências (D-112).
"""

import io
import re
import unicodedata
import zipfile
from pathlib import Path, PurePosixPath

from django.core.files.storage import default_storage
from django.template.loader import render_to_string

from nucleo.models import Tarefa
from nucleo.servicos.html import contexto_pagina
from nucleo.servicos.resolver import pendencias, resolver

ESTATICOS = Path(__file__).resolve().parents[1] / "static" / "revista"


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


def zip_revista(revista):
    """(nome, bytes) do zip. Recusa com `Pendente` (use `resolver.carregar(pk)` para a revista)."""
    lista = pendencias(revista, resolver(revista))
    if lista:
        raise Pendente(lista)
    capa = "arquivos/capa" + PurePosixPath(revista.capa).suffix
    html = render_to_string(
        "revista/index.html", contexto_pagina(revista, preview=False, estaticos="revista/", capa=capa)
    )
    itens = (
        Tarefa.objects.filter(
            descritor__matriz_etapa_cc__matriz_id=revista.projeto.parceiro_ano.matriz_id,
            descritor__matriz_etapa_cc__componente_id=revista.componente_id,
        )
        .exclude(arquivo=None)
        .exclude(arquivo="")
        .values_list("arquivo", flat=True)
    )
    # ponytail: zip em memória (SVG ~1 MB + capa ≤ 5 MB + itens); com muitos itens grandes,
    # trocar o BytesIO por tempfile.SpooledTemporaryFile e FileResponse.
    saida = io.BytesIO()
    with zipfile.ZipFile(saida, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("index.html", html)
        for arquivo in sorted(ESTATICOS.rglob("*")):
            if arquivo.is_file() and not arquivo.name.endswith(".test.mjs"):
                z.write(arquivo, "revista/" + arquivo.relative_to(ESTATICOS).as_posix())
        with default_storage.open(revista.capa) as f:
            z.writestr(capa, f.read())
        # Só o nome do arquivo (id.tipo) entra no zip: nada de "../" vindo do caminho.
        for nome, caminho in sorted({PurePosixPath(c).name: c for c in itens}.items()):
            with default_storage.open(caminho) as f:
                z.writestr(f"arquivos/itens/{nome}", f.read())
    return nome_zip(revista), saida.getvalue()
