"""Zip da revista (S15): site estático aberto por `file://`, sem servidor (D-103, D-109).

Conteúdo: as páginas `index.html`, `f1.html` e um `f2-*.html` por infográfico (D-233; modo zip,
sem faixas: D-116), `revista/f1/*` e `revista/f2/*` (cópia de `static/revista/`),
`arquivos/capa.<ext>`, `arquivos/itens/<id>.<tipo>` (arquivo da tarefa, no caminho que o JS do
F1 abre: D-154) e `arquivos/infograficos/<nome>` (imagem dos itens dos infográficos, D-245).
Dados, SVG gerado, tour e modais vão inline nas páginas (D-125). Só sai sem pendências (D-112);
problema do próprio pacote (item inválido, arquivo ausente, arquivada com capa ou imagem trocadas)
também recusa.
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

from nucleo.models import RevistaInfograficoItem, Tarefa
from nucleo.servicos.html import contexto_pagina, link_zip, paginas, template
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


def _imagens(revista, resolvido, erros):
    """{nome no zip: caminho atual} das imagens dos itens dos infográficos do resolvido (D-245).

    O nome vem do resolvido (a foto, na arquivada; é o `src` do HTML); os bytes, do caminho atual
    do item por (tipo, posição), conferido pelo `imagem_sha256`.
    """
    atuais = {
        (tipo, posicao): (caminho, sha)
        for tipo, posicao, caminho, sha in RevistaInfograficoItem.objects.filter(infografico__revista=revista)
        .values_list("infografico__tipo", "posicao", "imagem", "imagem_sha256")
    }  # fmt: skip
    imagens = {}
    for inf in resolvido["f2"].get("infograficos", []):  # foto antiga (arquivada) não tem a chave
        for item in inf["itens"]:  # passo Tarefas desligado: [] (D-243)
            if not item["imagem"]:
                continue
            caminho, sha = atuais.get((inf["tipo"], item["posicao"]), (None, None))
            nome = PurePosixPath(item["imagem"]).name
            if sha != item["imagem_sha256"]:
                erros.append(Pendencia("zip_foto", f"{inf['titulo']}, item {item['posicao']}: a imagem mudou depois da foto de arquivamento."))
            elif imagens.setdefault(nome, caminho) != caminho:
                erros.append(Pendencia("zip_arquivo", f"Outro arquivo já usa o nome {nome}."))
    return imagens


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
    # Arquivada: o HTML sai da foto (D-117), mas capa e imagens são os arquivos atuais, conferidos pelo sha.
    if resolvido["capa_sha256"] != revista.capa_sha256:
        erros.append(Pendencia("zip_foto", "A capa mudou depois da foto de arquivamento; o zip não bateria com o texto."))
    itens = _itens(revista, resolvido, erros)
    imagens = _imagens(revista, resolvido, erros)
    ausentes = [c for c in (revista.capa, *itens.values(), *imagens.values()) if not default_storage.exists(c)]
    erros.extend(Pendencia("zip_arquivo", f"Arquivo ausente no storage: {c}.") for c in ausentes)
    if erros:
        raise Pendente(erros)

    capa = "arquivos/capa" + PurePosixPath(revista.capa).suffix
    html = {}
    for slug, _ in paginas(resolvido):
        # O mesmo `resolvido` das pendências: resolver de novo por página misturaria estados (revista editada no meio).
        ctx = contexto_pagina(revista, slug, preview=False, estaticos="revista/", capa=capa, link=link_zip,
                              base_imagens="arquivos/infograficos/", resolvido=resolvido)  # fmt: skip
        if ctx is None:
            raise Pendente([Pendencia("zip_pagina", f"A página {slug} não tem infográfico.")])
        html[link_zip(slug)] = render_to_string(template(slug), ctx)
    # ponytail: zip em memória (capa ≤ 5 MB + imagens dos infográficos + itens PDF sem limite de tamanho);
    # quando pesar, trocar o BytesIO por tempfile.SpooledTemporaryFile e devolver FileResponse.
    saida = io.BytesIO()
    with zipfile.ZipFile(saida, "w") as z:
        for nome, pagina in html.items():
            z.writestr(_entrada(nome), pagina)
        for arquivo in sorted(ESTATICOS.rglob("*")):
            if arquivo.is_file() and arquivo.suffix in EXTENSOES:
                _copiar(z, "revista/" + arquivo.relative_to(ESTATICOS).as_posix(), arquivo.open("rb"))
        _copiar(z, capa, default_storage.open(revista.capa))
        for nome, caminho in sorted(itens.items()):
            _copiar(z, f"arquivos/itens/{nome}", default_storage.open(caminho))
        for nome, caminho in sorted(imagens.items()):
            _copiar(z, f"arquivos/infograficos/{nome}", default_storage.open(caminho))
    return nome_zip(revista), saida.getvalue()
