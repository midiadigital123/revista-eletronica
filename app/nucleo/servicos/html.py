"""Página única da revista (S08): contexto do `templates/revista/index.html`.

O mesmo template serve ao preview (S08) e ao zip (S15, aberto por `file://`):
- `estaticos`: prefixo dos arquivos de `static/revista/` ("/static/revista/" no preview,
  "revista/" no zip);
- `capa`: URL da capa (rota do preview ou "arquivos/capa.<ext>" no zip), ou None;
- `preview`: só ele mostra as faixas vermelhas (D-116).
Tudo o que a página lê vem inline (JSON e SVG): nada de `fetch` (D-125).

`json_seguro` e `css_das_cores` portados de api/src/modules/revista/render.ts.
"""

import json
import re
from html import unescape

from django.core.files.storage import default_storage
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe

from nucleo.servicos.resolver import resolver

COR = re.compile(r"#[0-9A-Fa-f]{6}")
# Config do tour (antes em svg-tour/avaliacao-e-curriculo/revista.json); os textos vêm das seções.
ROTULO_TOUR = "Infográfico: tour guiado"


def json_seguro(valor):
    """JSON para dentro de <script>: sem `</script>`, `<!--`, entidades nem separadores de linha JS."""
    return mark_safe(
        json.dumps(valor, ensure_ascii=False)
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
        .replace(" ", "\\u2028")
        .replace(" ", "\\u2029")
    )


def css_das_cores(cores):
    """`:root{...}` com --color-padrao-k e --color-padrao-k-bg (N padrões); "" sem cores.

    Revalida o formato: o valor vai cru para o <style>.
    """
    for chave, cor in cores.items():
        if not (re.fullmatch(r"padrao-[0-9]", chave) and COR.fullmatch(cor)):
            raise ValueError(f"Cor inválida: {chave}={cor!r}")
    vars_ = []
    for chave, cor in sorted(cores.items(), key=lambda kv: int(kv[0][7:])):
        r, g, b = (int(cor[i : i + 2], 16) for i in (1, 3, 5))
        vars_.append(f"--color-{chave}:{cor};--color-{chave}-bg:rgba({r}, {g}, {b}, 0.1);")
    return mark_safe(f":root{{{''.join(vars_)}}}" if vars_ else "")


def _texto(html):
    """HTML já renderizado → texto puro (o svg-tour põe título e texto por textContent)."""
    return unescape(strip_tags(html)).strip()


def _tour(secoes):
    """Textos do tour a partir das seções `abertura` e `passoN` (alvo com o prefixo f2- do SVG)."""
    por_id = {s["id"]: s for s in secoes}
    abertura = por_id.get("abertura", {"titulo": "", "corpo": ""})
    passos = sorted(
        (s for s in secoes if re.fullmatch(r"passo\d+", s["id"])), key=lambda s: int(s["id"][5:])
    )
    return {
        "label": ROTULO_TOUR,
        "intro": {"title": _texto(abertura["titulo"]), "text": _texto(abertura["corpo"])},
        "steps": [{"target": "f2-" + s["id"], "title": _texto(s["titulo"]), "text": _texto(s["corpo"])} for s in passos],
        "modais": [s["id"] for s in secoes if s["id"].startswith("dlg-")],
    }


def contexto_pagina(revista, *, preview, estaticos, capa):
    """Contexto do `revista/index.html` para a revista resolvida (arquivada: a foto, D-117)."""
    r = resolver(revista)
    f1, f2 = r["f1"], r["f2"]
    f1_secoes = {s["id"]: s for s in f1["secoes"] or []}
    f2_secoes = f2["secoes"] or []
    svg = None
    if revista.svg_f2:  # arquivo sumido do storage: FileNotFoundError (a view responde 404)
        with default_storage.open(revista.svg_f2) as arquivo:
            # Só este conteúdo vai com |safe: é o SVG sanitizado e prefixado no upload (D-145).
            svg = mark_safe(arquivo.read().decode())
    return {
        "preview": preview,
        "estaticos": estaticos,
        "capa": capa,
        "etapas": f1["etapas"],
        "dados": json_seguro(f1["dados"]),
        "css_cores": css_das_cores(f1["cores"]),
        "introducao": f1_secoes.get("introducao"),
        "fechamento": f1_secoes.get("fechamento"),
        # Faixas vermelhas (D-116): o texto fica no template; nada do resolvido/foto vira HTML aqui.
        "sem_template_f1": f1["secoes"] is None,
        "sem_template_f2": f2["secoes"] is None,
        "svg": svg,
        "tour": json_seguro(_tour(f2_secoes)),
        "modais": [s for s in f2_secoes if s["id"].startswith("dlg-")],
    }
