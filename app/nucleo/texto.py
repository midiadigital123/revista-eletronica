"""Templates de texto: seções, validação e renderização (D-105, D-114, D-123, D-125).

Formato: Markdown restrito (negrito, itálico, parágrafos e listas) com
`{{variavel}}` da lista fixa `VARIAVEIS`. Não há motor Handlebars: a variável
é só um marcador trocado pelo valor escapado.

O documento é uma sequência de seções `## id`. Em toda seção a 1ª linha é o
título (texto puro) e o resto é o corpo em Markdown.
"""

import re
import secrets
from html import escape

from django.core.exceptions import ValidationError
from markdown_it import MarkdownIt

from nucleo.variaveis import VARIAVEIS

NOMES = frozenset(v.nome for v in VARIAVEIS)

SECAO = re.compile(r"^## +(\S+) *$", re.M)
VAR = re.compile(r"\{\{([a-z_][a-z0-9_]*)\}\}")
CHAVES = re.compile(r"\{\{[^{}]*\}\}|\{\{|\}\}|[{}]")  # linear: sem .*? (ReDoS)
CONTROLE = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f‪-‮⁦-⁩]")  # controle e bidi
REF_LINK = re.compile(r"^ {0,3}\[[^\]]+\]:", re.M)  # definição de referência some do token stream

SECOES_F1 = ("introducao", "fechamento")
ID_F2 = re.compile(r"abertura|passo[1-9][0-9]*|dlg-[a-z0-9]+(-[a-z0-9]+)*")

# Marcador neutro da variável: caracteres de uso privado do Unicode em volta de um
# nonce por chamada. O markdown-it os trata como letras (nem pontuação nem espaço),
# então `**{{x}}**` continua negrito, e eles não abrem nenhuma regra. O nonce
# impede forjar o marcador (inclusive por entidade, como `&#xE000;`).
INI, FIM = "\ue000", "\ue001"

# Renderização: só as regras do formato; o resto (link, imagem, título, HTML,
# código) sai como texto literal, mesmo que tenha escapado da validação.
_md = MarkdownIt("zero", {"html": False}).enable(["emphasis", "list", "newline", "escape", "entity"])

# Validação: CommonMark completo com HTML ligado, para enxergar o que é recusado.
_md_validacao = MarkdownIt("commonmark")
TOKENS_BLOCO = {
    "paragraph_open", "paragraph_close", "inline",
    "bullet_list_open", "bullet_list_close", "ordered_list_open", "ordered_list_close",
    "list_item_open", "list_item_close",
}  # fmt: skip
TOKENS_INLINE = {"text", "text_special", "softbreak", "hardbreak", "strong_open", "strong_close", "em_open", "em_close"}
NOMES_TOKEN = {
    "heading_open": "título (#)",
    "link_open": "link",
    "image": "imagem",
    "html_block": "HTML",
    "html_inline": "HTML",
}


def _blocos(texto):
    """[(id, titulo, corpo)] na ordem do texto, mais o que vier antes da 1ª seção."""
    partes = SECAO.split(texto.lstrip("\ufeff").replace("\r\n", "\n"))
    antes, resto = partes[0], partes[1:]
    blocos = []
    for i in range(0, len(resto), 2):
        titulo, _, corpo = resto[i + 1].strip("\n").partition("\n")
        blocos.append((resto[i], titulo.strip(), corpo.strip()))
    return antes, blocos


def secoes(texto):
    """{id: (titulo, corpo)}. Seção repetida: vale a última (validar recusa)."""
    return {id_: (titulo, corpo) for id_, titulo, corpo in _blocos(texto)[1]}


def variaveis_usadas(texto):
    return set(VAR.findall(texto)) & NOMES


def _proibidos(markdown, permitidos):
    """Nomes dos recursos fora de `permitidos` encontrados no Markdown."""
    achados = []
    for tok in _md_validacao.parse(markdown):
        for t in [tok, *(tok.children or [])]:
            if t.type not in permitidos | {"inline"}:
                nome = NOMES_TOKEN.get(t.type, t.type.removesuffix("_open"))
                if nome not in achados:
                    achados.append(nome)
    return achados


def validar(texto, fasciculo):
    """Levanta ValidationError com todos os problemas do template."""
    erros = []
    antes, blocos = _blocos(texto)
    if antes.strip():
        erros.append("Há texto antes da primeira seção (## id).")
    if CONTROLE.search(texto):
        erros.append("Há caracteres de controle ou de direção de texto (bidi).")
    if REF_LINK.search(texto):
        erros.append("Há definição de referência de link ([x]: ...).")

    ids = [b[0] for b in blocos]
    for id_ in sorted({i for i in ids if ids.count(i) > 1}):
        erros.append(f"Seção repetida: {id_}.")

    if fasciculo == "F1":
        faltando = [s for s in SECOES_F1 if s not in ids]
        estranhas = [i for i in ids if i not in SECOES_F1]
    elif fasciculo == "F2":
        faltando = ["abertura"] if "abertura" not in ids else []
        if not any(i.startswith("passo") for i in ids):
            faltando.append("passo1")
        estranhas = [i for i in ids if not ID_F2.fullmatch(i)]
    else:
        raise ValueError(f"fascículo desconhecido: {fasciculo}")
    if faltando:
        erros.append(f"Seções obrigatórias faltando: {', '.join(faltando)}.")
    if estranhas:
        erros.append(f"Seções não previstas no {fasciculo}: {', '.join(estranhas)}.")

    for id_, titulo, corpo in blocos:
        if not titulo:
            erros.append(f"Seção {id_}: falta o título (1ª linha).")
        elif ruins := _proibidos(titulo, {"paragraph_open", "paragraph_close", "text", "text_special"}):
            erros.append(f"Seção {id_}: o título é texto puro; tem {', '.join(ruins)}.")
        if not corpo:
            erros.append(f"Seção {id_}: corpo vazio.")
        elif ruins := _proibidos(corpo, TOKENS_BLOCO | TOKENS_INLINE):
            erros.append(f"Seção {id_}: recurso não permitido: {', '.join(ruins)}.")

    sobras = CHAVES.findall(VAR.sub(lambda m: "" if m[1] in NOMES else m[0], texto))
    if sobras:
        erros.append(f"Variáveis fora da lista ou chaves soltas: {', '.join(dict.fromkeys(sobras))}.")

    if erros:
        raise ValidationError(erros)


def _valor(nome, valores):
    valor = valores.get(nome)
    if valor is None or not str(valor).strip():  # sem valor: destaque no preview e "Validado" bloqueado (D-100)
        return f'<span class="variavel-vazia">{{{{{nome}}}}}</span>'
    return escape(str(valor))


def renderizar(corpo, valores):
    """Markdown restrito -> HTML. Os valores entram escapados, depois do markdown-it,
    então não viram formatação nem são escapados duas vezes."""
    nomes, nonce = [], secrets.token_hex(8)
    marcador = re.compile(INI + nonce + r"(\d+)" + FIM)

    def marcar(m):
        nomes.append(m[1])
        return f"{INI}{nonce}{len(nomes) - 1}{FIM}"

    marcado = VAR.sub(marcar, corpo.replace(INI, "").replace(FIM, ""))
    return marcador.sub(lambda m: _valor(nomes[int(m[1])], valores), _md.render(marcado))


def renderizar_texto_puro(texto, valores):
    """Título: texto escapado com as variáveis trocadas, sem Markdown."""
    return VAR.sub(lambda m: _valor(m[1], valores), escape(texto))
