"""Páginas da revista (S08, D-233): contexto de `templates/revista/{index,f1,f2}.html`.

Sumário (`index`), F1 (`f1`) e uma página por infográfico ativo (`f2-alfa`, `f2-outras-etapas`).
Os mesmos templates servem ao preview (S08) e ao zip (S15, aberto por `file://`):
- `estaticos`: prefixo dos arquivos de `static/revista/` ("/static/revista/" no preview,
  "revista/" no zip);
- `capa`: URL da capa (rota do preview ou "arquivos/capa.<ext>" no zip), ou None;
- `link(slug)`: URL de uma página (rota do preview ou `link_zip`);
- `base_imagens`: prefixo das imagens dos itens do infográfico;
- `preview`: só ele mostra as faixas vermelhas (D-116).
Tudo o que a página lê vem inline (JSON e SVG): nada de `fetch` (D-125).

`css_das_cores` portado de api/src/modules/revista/render.ts.
"""

import re

from django.utils.safestring import mark_safe

from nucleo.servicos import f2
from nucleo.servicos.resolver import resolver

COR = re.compile(r"#[0-9A-Fa-f]{6}")
PAGINAS_F2 = {"alfa": "f2-alfa", "outras": "f2-outras-etapas"}  # tipo do infográfico -> slug da página
TIPO_DA_PAGINA = {slug: tipo for tipo, slug in PAGINAS_F2.items()}


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


def paginas(resolvido):
    """[(slug, título)]: `index`, `f1` e um infográfico por página, na ordem do resolvido.

    Foto antiga (arquivada antes da D-237) não tem `infograficos`: só `index` e `f1`.
    """
    return [("index", "Sumário"), ("f1", "Escalas de proficiência")] + [
        (PAGINAS_F2[inf["tipo"]], inf["titulo"]) for inf in resolvido["f2"].get("infograficos", [])
    ]


def link_zip(slug):
    """Link de uma página no zip (aberto por `file://`): o arquivo ao lado."""
    return f"{slug}.html"


def template(slug):
    """Template da página `slug` (de `paginas`)."""
    return f"revista/{slug}.html" if slug in ("index", "f1") else "revista/f2.html"


CHAVES_DA_ETAPA = {"scaleRange", "cortes", "padroes"}  # o resto das chaves são descritores


def contexto_pagina(revista, pagina, *, preview, estaticos, capa, link, base_imagens, resolvido=None):
    """Contexto de `template(pagina)` para a revista resolvida (arquivada: a foto, D-117).

    `pagina`: o slug de `paginas` ("index", "f1", "f2-alfa"...); None se o infográfico não existe (404).
    `resolvido`: um já montado (o zip passa o mesmo para todas as páginas); sem ele, resolve aqui.
    """
    r = resolvido or resolver(revista)
    f1, secoes_f2 = r["f1"], r["f2"]["secoes"]
    f1_secoes = {s["id"]: s for s in f1["secoes"] or []}
    comum = {
        "preview": preview,
        "estaticos": estaticos,
        "css_cores": css_das_cores(f1["cores"]),
        "introducao": f1_secoes.get("introducao"),
        "sumario": link("index"),
    }
    if pagina == "index":
        return {**comum, "capa": capa, "paginas": [(link(s), t) for s, t in paginas(r)[1:]]}
    if pagina == "f1":
        return {
            **comum,
            "etapas": f1["etapas"],
            "dados": f1["dados"],
            "fechamento": f1_secoes.get("fechamento"),
            # Faixas vermelhas (D-116): o texto fica no template; nada do resolvido/foto vira HTML aqui.
            "sem_template_f1": f1["secoes"] is None,
            # Item 21 (D-190): etapa sem descritor = sem matriz (ou sem a etapa × CC na matriz). Sai dos
            # `dados`, não do resolvido: uma chave nova lá mudaria o hash de toda revista.
            "sem_matriz": [e.upper() for e in f1["etapas"] if not set(f1["dados"][e]) - CHAVES_DA_ETAPA],
        }
    tipo = TIPO_DA_PAGINA.get(pagina)
    inf = next((i for i in r["f2"].get("infograficos", []) if i["tipo"] == tipo), None)
    if inf is None:
        return None
    por_id = {s["id"]: s for s in secoes_f2 or []}
    gerado = f2.gerar(inf, por_id, base_imagens, revista.componente.nome)
    return {
        **comum,
        "titulo": inf["titulo"],
        "abertura": por_id.get("abertura"),
        # Compara os itens: vem depois do infográfico e só com o passo Tarefas ligado (D-258).
        "tarefas_fechamento": por_id.get("tarefas-fechamento") if "tarefas" in inf["passos"] else None,
        "fechamento": por_id.get("fechamento"),
        "sem_template_f2": secoes_f2 is None,
        **gerado,  # svg (montado pelo f2.svg: vai com |safe), tour e modais
    }
