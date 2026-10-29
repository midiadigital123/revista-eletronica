"""Upload do SVG do F2 e da capa da revista (S09; D-108, D-111, D-118, D-125).

O SVG gravado é o sanitizado, nunca o original: lista fixa de tags e
atributos, ids e classes com prefixo `f2-` (no atributo, no `<style>`, em
`url(#…)` e em `href="#…"`). `svg_ids` guarda os ids sem o prefixo.
Todo processamento é linear (arquivo de 3 MB não pode virar horas de CPU).
"""

import hashlib
import re
import uuid
import xml.etree.ElementTree as ET

from defusedxml import DefusedXmlException
from defusedxml.ElementTree import fromstring
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import transaction

MB = 1024 * 1024
SVG_MAX = 3 * MB
CAPA_MAX = 5 * MB
STYLE_MAX = 1 * MB
ATRIBUTO_MAX = 4 * 1024
NOS_MAX = 200_000
PROFUNDIDADE_MAX = 100
PREFIXO = "f2-"

SVG = "http://www.w3.org/2000/svg"
XLINK = "http://www.w3.org/1999/xlink"
XML = "http://www.w3.org/XML/1998/namespace"

TAGS = {
    "svg", "g", "defs", "style", "title", "desc", "symbol", "use",
    "path", "rect", "circle", "ellipse", "line", "polyline", "polygon",
    "text", "tspan", "image",
    "clipPath", "mask", "pattern", "linearGradient", "radialGradient", "stop",
    "filter", "feGaussianBlur", "feOffset", "feBlend", "feColorMatrix",
    "feComposite", "feFlood", "feMerge", "feMergeNode", "feDropShadow",
}  # fora da lista (script, foreignObject, a, animate, set…) sai com os filhos

ATRIBUTOS = {
    "id", "class", "style", "type", "version", "viewBox", "preserveAspectRatio",
    "x", "y", "x1", "y1", "x2", "y2", "cx", "cy", "r", "rx", "ry", "fx", "fy",
    "dx", "dy", "width", "height", "d", "points", "transform", "offset",
    "fill", "fill-opacity", "fill-rule", "stroke", "stroke-width", "stroke-linecap",
    "stroke-linejoin", "stroke-miterlimit", "stroke-dasharray", "stroke-dashoffset",
    "stroke-opacity", "opacity", "color", "display", "visibility", "overflow",
    "clip-path", "clip-rule", "clipPathUnits", "mask", "maskUnits", "maskContentUnits",
    "filter", "filterUnits", "primitiveUnits", "stdDeviation", "in", "in2", "result",
    "mode", "values", "operator", "k1", "k2", "k3", "k4", "flood-color", "flood-opacity",
    "stop-color", "stop-opacity", "gradientUnits", "gradientTransform", "spreadMethod",
    "patternUnits", "patternContentUnits", "patternTransform",
    "shape-rendering", "mix-blend-mode", "isolation",
    "font-family", "font-size", "font-weight", "font-style", "text-anchor",
    "letter-spacing", "data-name", "href",
    f"{{{XLINK}}}href", f"{{{XML}}}space",
}
# O <svg> raiz não pode cobrir a página (estilo, tamanho, posição, class para CSS, escala).
RAIZ_SEM = {"style", "width", "height", "x", "y", "class", "overflow", "transform"}

# Raster embutido em <image> (o SVG real do Illustrator traz um PNG de ~500 KB assim;
# por isso esse href fica fora do limite de 4 KB por atributo).
DATA_IMAGEM = re.compile(r"^data:image/(png|jpeg|gif|webp);base64,[A-Za-z0-9+/=\s]*$")
ID = re.compile(r"[A-Za-z][\w.:-]{0,100}")
URL_INTERNA = re.compile(r"""url\(\s*(['"]?)#([A-Za-z][\w.:-]*)\1\s*\)""", re.I)
# Depois de tirar os url(#id): outra url, função de imagem, `//` ou `:` (esquema) recusa.
VALOR_PROIBIDO = re.compile(
    r"url\(|image\(|image-set|cross-fade|src\(|element\(|paint\(|attr\(|expression|@import|//|:",
    re.I,
)
# Lista branca de propriedades CSS (no <style> e no style=): só pintura, nada de layout.
PROPRIEDADES = {
    "fill", "stroke", "opacity", "text-anchor", "letter-spacing", "clip-path", "clip-rule",
    "mask", "filter", "mix-blend-mode", "isolation", "shape-rendering", "visibility", "display",
}
PROPRIEDADES_PREFIXO = ("fill-", "stroke-", "font-", "stop-", "flood-")
PROPRIEDADE = re.compile(r"[a-z][a-z-]*")
USE_MAX = 1_000
IDS_MAX = 5_000
SIMPLES = re.compile(r"(?:[.#]-?[A-Za-z_][\w-]*)+")  # .a, #b, .a.b
SELETOR = re.compile(r"([.#])(-?[A-Za-z_][\w-]*)")


def _erro(msg):
    raise ValidationError(msg)


def _ler(arquivo, limite, nome):
    dados = arquivo if isinstance(arquivo, bytes) else arquivo.read(limite + 1)
    if len(dados) > limite:
        _erro(f"{nome} acima de {limite // MB} MB.")
    return dados


def _gravar(pasta, extensao, dados):
    return default_storage.save(f"{pasta}/{uuid.uuid4().hex}.{extensao}", ContentFile(dados))


def _salvar(revista, campos, novo, antigo):
    """Salva a revista; se falhar, apaga o arquivo novo. O antigo sai no commit (decisão do S09)."""
    try:
        revista.save(update_fields=campos)
    except BaseException:
        default_storage.delete(novo)
        raise
    # ponytail: se a transação de fora falhar depois, o arquivo novo fica órfão; varredura se incomodar.
    if antigo and antigo != novo:
        transaction.on_commit(lambda: default_storage.delete(antigo))


# --- CSS --------------------------------------------------------------------


def _valor_css(valor):
    """Valor de CSS ou de atributo, com url(#id) prefixado; recusa o resto perigoso."""
    if "\\" in valor or VALOR_PROIBIDO.search(URL_INTERNA.sub("", valor)):
        _erro(f"SVG com valor não permitido: {valor[:80]!r}")
    return URL_INTERNA.sub(lambda m: f"url(#{PREFIXO}{m.group(2)})", valor)


def _declaracoes(texto):
    saida = []
    for decl in texto.split(";"):
        prop, sep, valor = decl.partition(":")
        prop = prop.strip().lower()
        if not sep:
            if decl.strip():
                _erro(f"CSS do SVG malformado: {decl[:80]!r}")
            continue
        valor = valor.strip()
        if not PROPRIEDADE.fullmatch(prop) or not (
            prop in PROPRIEDADES or prop.startswith(PROPRIEDADES_PREFIXO)
        ):
            _erro(f"Propriedade CSS não permitida no SVG: {prop[:80]!r}")
        if prop == "display" and valor.lower() not in ("none", "inline"):
            _erro(f"display não permitido no SVG: {valor[:80]!r}")
        saida.append(f"{prop}: {_valor_css(valor)}")
    return "; ".join(saida)


def _seletores(texto):
    """Só .classe/#id com descendente, >, +, ~ e vírgula; devolve prefixado."""
    for seletor in texto.split(","):
        partes = re.sub(r"[>+~]", " ", seletor).split()
        if not partes or not all(SIMPLES.fullmatch(p) for p in partes):
            _erro(f"Seletor CSS não permitido no SVG: {seletor.strip()[:80]!r}")
    return SELETOR.sub(rf"\1{PREFIXO}\2", texto.strip())


def _sem_comentarios(texto):
    partes, i = [], 0
    while (j := texto.find("/*", i)) != -1:
        partes.append(texto[i:j])
        k = texto.find("*/", j + 2)
        if k == -1:
            _erro("CSS do SVG com comentário sem fechar.")
        i = k + 2
    partes.append(texto[i:])
    return "".join(partes)


def _css(texto):
    """<style>: só regras `seletor { declarações }`; at-rule e aninhamento recusam."""
    if len(texto) > STYLE_MAX:
        _erro("<style> do SVG acima de 1 MB.")
    *blocos, resto = _sem_comentarios(texto).split("}")
    if resto.strip():
        _erro("CSS do SVG malformado.")
    regras = []
    for bloco in blocos:
        seletor, sep, decl = bloco.partition("{")
        if not sep or "{" in decl or "@" in seletor:
            _erro("CSS do SVG com at-rule ou bloco aninhado.")
        regras.append(f"{_seletores(seletor)} {{ {_declaracoes(decl)} }}")
    return "\n".join(regras)


# --- SVG --------------------------------------------------------------------


def _atributo(tag, nome, valor):
    """Valor sanitizado do atributo, ou None para removê-lo; o perigoso recusa o arquivo."""
    if nome not in ATRIBUTOS or nome.lower().startswith("on"):
        return None
    if nome in ("href", f"{{{XLINK}}}href"):
        v = valor.strip()
        if v.startswith("#"):
            return f"#{PREFIXO}{v[1:]}" if ID.fullmatch(v[1:]) else None
        return v if tag == "image" and DATA_IMAGEM.match(v) else None
    if len(valor) > ATRIBUTO_MAX:
        _erro(f"Atributo {nome} acima de 4 KB no SVG.")
    if nome == "id":
        if not ID.fullmatch(valor):
            _erro(f"Id inválido no SVG: {valor[:80]!r}")
        return PREFIXO + valor
    if nome == "class":
        return " ".join(PREFIXO + c for c in valor.split())
    if nome == "style":
        return _declaracoes(valor)
    if nome == "overflow" and tag == "svg":  # <svg> aninhado não vaza para fora
        return None
    if nome.startswith("data-"):  # rótulo do Illustrator: com algo suspeito, só sai
        return None if "\\" in valor or VALOR_PROIBIDO.search(valor) else valor
    return _valor_css(valor)


def _conferir_tamanho(raiz):
    """Profundidade e nº de nós, sem recursão (antes de _limpar e tostring)."""
    pilha, nos, uses = [(raiz, 1)], 0, 0
    while pilha:
        el, nivel = pilha.pop()
        nos += 1
        if el.tag == f"{{{SVG}}}use":
            uses += 1
            if uses > USE_MAX:
                _erro(f"SVG com mais de {USE_MAX} <use>.")
        if nivel > PROFUNDIDADE_MAX:
            _erro(f"SVG com mais de {PROFUNDIDADE_MAX} níveis de aninhamento.")
        if nos > NOS_MAX:
            _erro(f"SVG com mais de {NOS_MAX} elementos.")
        pilha.extend((filho, nivel + 1) for filho in el)


def _limpar(el, ids):
    tag = el.tag = el.tag.removeprefix(f"{{{SVG}}}")  # namespace volta só na raiz
    for nome, valor in list(el.attrib.items()):
        novo = _atributo(tag, nome, valor)
        del el.attrib[nome]
        if novo is not None:
            if nome == f"{{{XLINK}}}href":  # SVG 2: href simples, sem namespace xlink
                nome = "href"
            el.attrib[nome] = novo
            if nome == "id":
                ids.setdefault(valor)
    if tag in ("style", "title", "desc"):  # só texto: filho e tail escapariam do _css
        el[:] = []
    if tag == "style" and el.text:
        el.text = _css(el.text)
    for filho in list(el):  # tail só some com o filho de style/title/desc (acima)
        if (
            not isinstance(filho.tag, str)
            or not filho.tag.startswith(f"{{{SVG}}}")
            or filho.tag.removeprefix(f"{{{SVG}}}") not in TAGS
        ):
            el.remove(filho)
        else:
            _limpar(filho, ids)


def sanitizar_svg(dados):
    """Bytes do SVG → (bytes sanitizados, ids sem prefixo, na ordem do arquivo)."""
    try:
        raiz = fromstring(dados, forbid_dtd=True)
    except (DefusedXmlException, ET.ParseError) as e:
        _erro(f"SVG inválido ou com DOCTYPE/entidades: {e}")
    if raiz.tag != f"{{{SVG}}}svg":
        _erro("O arquivo não é um SVG.")
    _conferir_tamanho(raiz)
    for nome in RAIZ_SEM:
        raiz.attrib.pop(nome, None)
    ids = {}  # dict: ordem do arquivo e busca O(1)
    _limpar(raiz, ids)
    if len(ids) > IDS_MAX:
        _erro(f"SVG com mais de {IDS_MAX} ids.")
    raiz.set("xmlns", SVG)
    return ET.tostring(raiz, encoding="unicode").encode(), list(ids)  # sem <?xml …?>


def receber_svg(revista, arquivo):
    """Sanitiza e grava o SVG do F2 da revista; preenche svg_f2, svg_sha256 e svg_ids."""
    dados, ids = sanitizar_svg(_ler(arquivo, SVG_MAX, "SVG"))
    antigo = revista.svg_f2
    revista.svg_f2 = _gravar("f2", "svg", dados)
    revista.svg_sha256 = hashlib.sha256(dados).hexdigest()
    revista.svg_ids = ids
    _salvar(revista, ["svg_f2", "svg_sha256", "svg_ids"], revista.svg_f2, antigo)
    return revista


# --- Capa -------------------------------------------------------------------


def tipo_imagem(dados):
    """Extensão pela assinatura mágica (png, jpg, webp) ou None."""
    if dados.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if dados.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if dados[:4] == b"RIFF" and dados[8:12] == b"WEBP":
        return "webp"
    return None


def receber_capa(revista, arquivo):
    """Grava a capa (PNG, JPG ou WebP até 5 MB, tipo pelo conteúdo) e o sha256."""
    dados = _ler(arquivo, CAPA_MAX, "Capa")
    extensao = tipo_imagem(dados) or _erro("Capa precisa ser PNG, JPG ou WebP.")
    antigo = revista.capa
    revista.capa = _gravar("capas", extensao, dados)
    revista.capa_sha256 = hashlib.sha256(dados).hexdigest()
    _salvar(revista, ["capa", "capa_sha256"], revista.capa, antigo)
    return revista


# --- Conferência seções × ids -------------------------------------------------


def ids_esperados(secoes):
    """Seções do F2 → ids do SVG: passoN → passoN; dlg-xx → btn-action-xx (D-111).

    Outras seções (abertura…) não exigem id.
    """
    ids = []
    for s in secoes:
        if re.fullmatch(r"passo\d+", s):
            ids.append(s)
        elif s.startswith("dlg-") and len(s) > 4:
            ids.append("btn-action-" + s[4:])
    return ids


def ids_faltando(revista, secoes):
    """Ids exigidos pelas seções efetivas do F2 que faltam no SVG da revista.

    `secoes`: nomes das seções efetivas (template + cópias); quem resolve é o S07.
    """
    tem = set(revista.svg_ids or [])
    return [i for i in ids_esperados(secoes) if i not in tem]
