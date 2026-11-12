#!/usr/bin/env python3
"""Confere a demo sem abrir navegador: links, âncoras, diálogos e abas.

    python3 verificar_links.py            # todas as páginas dos módulos que existem
    python3 verificar_links.py hoje       # só as páginas de um módulo (links para outros módulos viram "pendentes")

Falha (exit 1) se: href local aponta para arquivo fora do contrato; #âncora não existe na página de destino;
data-abrir aponta para um <dialog> inexistente; data-aba sem data-painel (ou o contrário); id repetido.
"""
import re
import sys
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))

import dados as D  # noqa: E402
import gerar  # noqa: E402
from paginas import shell  # noqa: E402


def contrato():
    """Todos os arquivos que as páginas podem citar (o que cada módulo promete gerar)."""
    f = {"index.html", "revistas.html", "parceiros.html", "ano.html", "ano-abrir.html", "matrizes.html", "matriz-etapa.html",
         "matriz-importar.html", "matriz-diferencas.html", "templates.html", "template-lp-f1.html", "template-lp-f2.html",
         "entrega-validar.html", "entrega-impresso.html", "entrega-pacotes.html", "entrar.html", "senha.html",
         "senha-invalida.html", "senha-pronto.html", "usuarios.html", "usuario-novo.html", "usuario-link.html",
         "excluir-em-uso.html", "excluir-livre.html", "estados.html", "sobre.html"}
    f |= {f"revista-{r['id']}.html" for r in D.REVISTAS}
    f |= {f"parceiro-{p['id']}.html" for p in D.PARCEIROS}
    f |= {f"matriz-{m['id']}.html" for m in D.MATRIZES}
    return f


class Coleta(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs, self.ids, self.abrir, self.abas, self.paineis, self.ir_abas = [], [], [], [], [], []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "a" and a.get("href"):
            self.hrefs.append(a["href"])
        if a.get("id"):
            self.ids.append(a["id"])
        if a.get("data-abrir"):
            self.abrir.append(a["data-abrir"])
        if a.get("data-aba"):
            self.abas.append(a["data-aba"])
        if a.get("data-painel"):
            self.paineis.append(a["data-painel"])
        if a.get("data-ir-aba"):
            self.ir_abas.append(a["data-ir-aba"])


def main():
    filtro = set(sys.argv[1:])
    paginas, _, _ = gerar.coletar()
    if filtro:
        paginas = [p for p in paginas if any(p.arquivo.startswith(x) or x in p.arquivo for x in filtro)]
    prometidos = contrato()
    gerados = {p.arquivo for p in gerar.coletar()[0]}
    info = {}
    for p in paginas:
        c = Coleta()
        c.feed(shell.render(p))
        info[p.arquivo] = c
    erros, pendentes = [], Counter()
    for arq, c in info.items():
        for k, n in Counter(c.ids).items():
            if n > 1:
                erros.append(f"{arq}: id repetido '{k}'")
        for h in c.hrefs:
            if re.match(r"^(https?:|mailto:|javascript:|#?$)", h) or h.startswith("https://example.invalid"):
                continue
            alvo, _, frag = h.split("?")[0].partition("#") if "#" in h.split("?")[0] else (h.split("?")[0], "", "")
            if "#" in h and "?" in h and h.index("?") > h.index("#"):
                alvo, _, frag = h.partition("#")
            if not alvo:
                alvo = arq
            if alvo not in prometidos:
                erros.append(f"{arq}: link fora do contrato -> {h}")
                continue
            if alvo not in gerados:
                pendentes[alvo] += 1
                continue
            if frag:
                dest = info.get(alvo)
                if dest is None:
                    continue  # página existe mas fora do filtro
                if frag not in dest.ids and frag not in dest.abas:
                    erros.append(f"{arq}: âncora inexistente -> {h}")
        for d in c.abrir:
            if d not in c.ids:
                erros.append(f"{arq}: data-abrir='{d}' sem <dialog id>")
        for a in set(c.abas):
            if a not in c.paineis:
                erros.append(f"{arq}: data-aba='{a}' sem data-painel")
        for a in set(c.paineis):
            if a not in c.abas:
                erros.append(f"{arq}: data-painel='{a}' sem data-aba")
        for a in set(c.ir_abas):
            if a not in c.abas:
                erros.append(f"{arq}: data-ir-aba='{a}' sem aba")
    if pendentes:
        print(f"pendentes (arquivo prometido, ainda não gerado): {len(pendentes)} arquivos, {sum(pendentes.values())} links")
    if erros:
        print("\n".join(sorted(set(erros))))
        print(f"FALHOU: {len(set(erros))} problemas em {len(info)} páginas")
        sys.exit(1)
    print(f"OK: {len(info)} páginas conferidas")


if __name__ == "__main__":
    main()
