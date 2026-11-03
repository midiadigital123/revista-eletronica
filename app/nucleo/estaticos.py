"""URL de estático com versão (`?v=<mtime>`): CSS/JS mudou, a URL muda e o navegador baixa de novo.

Sem isso o `runserver` serve `/static/` sem Cache-Control e o navegador reaproveita o CSS antigo
(ícones SVG gigantes, layout sem as regras novas). O `runserver` serve os estáticos antes dos
middlewares, então um header não resolveria; a versão na URL vale no dev e em produção.
"""
import os

from django.contrib.staticfiles import finders
from django.contrib.staticfiles.storage import StaticFilesStorage


class EstaticosComVersao(StaticFilesStorage):
    def url(self, name):
        url = super().url(name)
        caminho = finders.find(name) if name else None
        if isinstance(caminho, str) and os.path.isfile(caminho):  # pasta (static("revista/")) fica sem versão
            url += f"?v={int(os.path.getmtime(caminho))}"
        return url
