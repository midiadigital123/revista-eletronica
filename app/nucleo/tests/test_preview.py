import json
import os
import re
import shutil
import tempfile
from pathlib import Path

from django.core.files.uploadedfile import SimpleUploadedFile
from django.template.loader import render_to_string
from django.test import TestCase, override_settings
from django.urls import reverse

from nucleo.models import Revista, RevistaFasciculo, TemplateVersao
from nucleo.servicos.arquivos import receber_capa, receber_svg
from nucleo.servicos.cascata import gravar_cortes
from nucleo.servicos.html import contexto_pagina, css_das_cores, json_seguro
from nucleo.tests.test_resolver import Mundo

# Página que o Playwright pagina.spec.ts abre (gabarito). Regerar: REGERAR_FIXTURES=1.
GABARITO = Path(__file__).resolve().parents[2] / "e2e" / "fixtures" / "pagina.html"
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
F2 = (
    "## abertura\nAvaliação & Currículo\n\nSiga o tour.\n\n"
    "## passo1\nDescritor\n\nPrimeiro bloco.\n\n## passo2\nItens\n\nSegundo bloco.\n\n"
    "## dlg-p2\nItens por ano\n\nDetalhe do item.\n"
)
# SVG pequeno com a convenção de ids (D-108): passoN e btn-action-xx.
SVG = b"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 400">
<style>.bolinha{fill:#ffeb00;stroke:#000}</style>
<rect id="fundo" width="800" height="400" fill="#f8f9fa"/>
<g id="passo1"><rect x="40" y="40" width="340" height="320" fill="#b3ccff"/></g>
<g id="passo2"><rect x="420" y="40" width="340" height="320" fill="#ff8d43"/>
<g id="btn-action-p2"><circle class="bolinha" cx="590" cy="200" r="24"/></g></g>
</svg>"""


class PaginaTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        Mundo.montar(cls)
        cls.rev = cls.go["LP"]
        TemplateVersao.objects.create(template=cls.templates["LP", "F2"], numero=2, texto=F2)

    def setUp(self):
        media = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, media)
        ctx = override_settings(MEDIA_ROOT=media)
        ctx.enable()
        self.addCleanup(ctx.disable)
        self.client.force_login(self.usuario)

    def get(self, revista):
        return self.client.get(reverse("preview", args=[revista.pk]))

    def test_login_obrigatorio(self):
        self.client.logout()
        r = self.get(self.rev)
        self.assertEqual(r.status_code, 302)
        self.assertIn("/admin/login/", r["Location"])

    def test_200_com_f1_f2_e_dados_inline(self):
        receber_svg(self.rev, SimpleUploadedFile("x.svg", SVG))
        r = self.get(self.rev)
        self.assertEqual(r.status_code, 200)
        html = r.content.decode()
        self.assertIn('id="dados-revista"', html)
        self.assertIn('<g id="f2-passo1">', html)  # SVG inline, sanitizado e prefixado
        self.assertIn('<dialog id="dlg-p2" aria-labelledby="dlgTitle-p2">', html)
        self.assertIn("<p>Texto <strong>Projeto GO</strong>.</p>", html)  # introdução, sem reescapar
        self.assertIn("/static/revista/f2/f2-init.js", html)
        self.assertNotIn("faixa-vermelha", html.split("<body>")[1])
        self.assertNotIn("fetch(", html)
        tour = json.loads(re.search(r'id="dados-tour">(.*?)</script>', html).group(1))
        self.assertEqual(tour["intro"]["title"], "Avaliação & Currículo")  # texto puro (textContent)
        self.assertEqual([s["target"] for s in tour["steps"]], ["f2-passo1", "f2-passo2"])
        self.assertEqual(tour["modais"], ["dlg-p2"])

    def test_faixa_vermelha_sem_template(self):
        RevistaFasciculo.objects.filter(revista=self.rev, fasciculo="F1").update(template=None)
        html = self.get(self.rev).content.decode()
        self.assertIn("Falta escolher o template do F1.", html)
        self.assertIn("Falta o SVG do F2.", html)

    def test_arquivada_mostra_a_foto(self):
        mt = self.go["MT"]
        # Tira a MT dos cortes: a cascata arquiva e fotografa (D-117); depois o template muda.
        gravar_cortes(
            self.rev.projeto.parceiro_ano,
            [(self.e5, self.lp, [100, 200, 250, 300]), (self.e9, self.lp, [100, 200, 250, 300])],
            self.usuario,
        )
        TemplateVersao.objects.create(
            template=self.templates["MT", "F1"], numero=2,
            texto="## introducao\nNovo título\n\nTexto novo.\n\n## fechamento\nFim\n\nFim.\n",
        )  # fmt: skip
        self.assertIsNotNone(Revista.objects.get(pk=mt.pk).arquivada_em)
        html = self.get(mt).content.decode()
        self.assertIn("Análise de GO", html)
        self.assertNotIn("Texto novo.", html)

    def test_capa_com_tipo_fixo_e_nosniff(self):
        receber_capa(self.rev, SimpleUploadedFile("capa.jpg", PNG))
        self.assertIn(reverse("preview_capa", args=[self.rev.pk]), self.get(self.rev).content.decode())
        r = self.client.get(reverse("preview_capa", args=[self.rev.pk]))
        self.assertEqual((r.status_code, r["Content-Type"]), (200, "image/png"))
        self.assertEqual(r["X-Content-Type-Options"], "nosniff")

    def test_gabarito_do_playwright(self):
        """Modo zip (S15): caminhos relativos e sem faixas; o Playwright abre este HTML."""
        receber_svg(self.rev, SimpleUploadedFile("x.svg", SVG))
        html = render_to_string(
            "revista/index.html",
            contexto_pagina(self.rev, preview=False, estaticos="revista/", capa="arquivos/capa.png"),
        )
        if os.environ.get("REGERAR_FIXTURES"):
            GABARITO.write_text(html, encoding="utf-8")
        self.assertEqual(GABARITO.read_text(encoding="utf-8"), html)


class HtmlTest(TestCase):
    def test_json_seguro(self):
        s = json_seguro({"x": "</script><!--&  "})
        self.assertNotRegex(s, "[<>&  ]")
        self.assertEqual(json.loads(s), {"x": "</script><!--&  "})

    def test_css_das_cores_n_padroes(self):
        css = css_das_cores({"padrao-2": "#FF8D43", "padrao-1": "#F72628"})
        self.assertEqual(
            css,
            ":root{--color-padrao-1:#F72628;--color-padrao-1-bg:rgba(247, 38, 40, 0.1);"
            "--color-padrao-2:#FF8D43;--color-padrao-2-bg:rgba(255, 141, 67, 0.1);}",
        )
        self.assertEqual(css_das_cores({}), "")
        with self.assertRaises(ValueError):
            css_das_cores({"padrao-1": "red;}body{x:y"})
