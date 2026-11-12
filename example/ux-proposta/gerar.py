#!/usr/bin/env python3
"""Gera as páginas HTML da demo de UI/UX (só biblioteca padrão).

    python3 gerar.py            # escreve os .html ao lado deste arquivo
    python3 gerar.py --lista    # só lista as páginas que seriam geradas

Cada módulo em paginas/ expõe paginas() -> list[Pagina] e, opcionalmente, CSS e JS próprios.
"""
import importlib
import pathlib
import shutil
import sys

AQUI = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))

from paginas import shell  # noqa: E402

MODULOS = ["hoje", "revistas", "revista", "parceiros", "ano", "biblioteca", "entrega", "conta", "sobre"]


def coletar(so=None):
    paginas, css, js = [], [], []
    for nome in MODULOS:
        if so and nome not in so:
            continue
        try:
            mod = importlib.import_module(f"paginas.{nome}")
        except ModuleNotFoundError as e:
            if e.name != f"paginas.{nome}":
                raise
            print(f"  (pulado: paginas/{nome}.py ainda não existe)")
            continue
        paginas += mod.paginas()
        css.append(getattr(mod, "CSS", ""))
        js.append(getattr(mod, "JS", ""))
    vistos = {}
    for p in paginas:
        assert p.arquivo.endswith(".html"), p.arquivo
        assert p.arquivo not in vistos, f"página repetida: {p.arquivo}"
        vistos[p.arquivo] = p
    return paginas, "\n".join(css), "\n".join(js)


def _opcao(nome):
    return sys.argv[sys.argv.index(nome) + 1] if nome in sys.argv else None


def main():
    """--so hoje,revistas   só esses módulos      --saida PASTA   escreve numa pasta à parte (com cópia dos assets)."""
    so = (_opcao("--so") or "").split(",") if _opcao("--so") else None
    paginas, css, js = coletar(so)
    if "--lista" in sys.argv:
        for p in paginas:
            print(p.arquivo, "·", p.titulo)
        return
    saida = pathlib.Path(_opcao("--saida")).resolve() if _opcao("--saida") else AQUI
    saida.mkdir(parents=True, exist_ok=True)
    if saida != AQUI:  # pasta privada: copia os assets e pode limpar à vontade
        for f in ("app.css", "app.js"):
            shutil.copy(AQUI / f, saida / f)
        shutil.copytree(AQUI / "fontes", saida / "fontes", dirs_exist_ok=True)
    for velho in saida.glob("*.html"):
        velho.unlink()
    (saida / "app-paginas.css").write_text(css or "/* sem estilos de página */\n", encoding="utf-8")
    (saida / "app-paginas.js").write_text(js or "/* sem scripts de página */\n", encoding="utf-8")
    for p in paginas:
        (saida / p.arquivo).write_text(shell.render(p), encoding="utf-8")
    print(f"OK: {len(paginas)} páginas em {saida}")


if __name__ == "__main__":
    main()
