import hashlib
import shutil
import tempfile
import time
from pathlib import Path
from unittest import mock

from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from nucleo.models import Ano, Componente, Parceiro, ParceiroAno, Projeto, Revista
from nucleo.servicos.arquivos import (
    MB,
    ids_faltando,
    receber_capa,
    receber_svg,
    sanitizar_svg,
)

FIXTURE = Path(__file__).parent / "fixtures" / "f2-lp.svg"
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32


def svg(corpo):
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">'
        f"{corpo}</svg>"
    ).encode()


def limpo(corpo):
    return sanitizar_svg(svg(corpo))[0].decode()


class SanitizarSvgTest(TestCase):
    def test_svg_real_mantem_paths(self):
        original = FIXTURE.read_bytes()
        saida, ids = sanitizar_svg(original)
        self.assertEqual(saida.count(b"<path "), original.count(b"<path "))
        self.assertEqual(saida.count(b"<path "), 1952)
        self.assertIn("btn-action-p2", ids)
        self.assertIn("passo1", ids)
        self.assertNotIn(b'id="passo1"', saida)
        self.assertIn(b'id="f2-passo1"', saida)
        self.assertIn(b"url(#f2-clippath-6)", saida)  # dentro do <style>
        self.assertIn(b"data:image/png;base64,", saida)  # raster embutido fica

    def test_image_onerror_e_href_externo_removidos(self):
        s = limpo('<image href="https://x/a.png" onerror="alert(1)" width="1"/>')
        self.assertNotIn("onerror", s)
        self.assertNotIn("https://", s)
        self.assertIn('width="1"', s)

    def test_tags_proibidas_saem(self):
        s = limpo(
            "<script>alert(1)</script><foreignObject><p>x</p></foreignObject>"
            '<a href="javascript:alert(1)"><path d="M0"/></a><g onclick="x"/>'
        )
        for proibido in ("script", "foreignObject", "javascript", "onclick", "<a"):
            self.assertNotIn(proibido, s)

    def test_href_so_interno(self):
        s = limpo('<use href="#alvo"/><use xlink:href="outro.svg#alvo"/><use xlink:href="#b"/>')
        self.assertIn('href="#f2-alvo"', s)
        self.assertIn('<use href="#f2-b"', s)  # xlink:href vira href (SVG 2)
        self.assertNotIn("outro.svg", s)

    def recusa(self, *corpos):
        for corpo in corpos:
            with self.subTest(corpo=corpo[:60]), self.assertRaises(ValidationError):
                limpo(corpo)

    def test_javascript_em_qualquer_atributo(self):
        self.recusa('<path d="M0" fill="java&#9;script:alert(1)"/>')

    def test_style_prefixa_classes_ids_e_url(self):
        s = limpo(
            "<style>/* x */ .st1, #fundo > .st2 + .a.b ~ .c .d {"
            " fill: url(#grad); stroke: #b2b2b2; stroke-width: .2px }</style>"
            '<rect class="st1 st2" style="fill: url(\'#grad\'); opacity: .5"/>'
        )
        self.assertIn(".f2-st1, #f2-fundo &gt; .f2-st2 + .f2-a.f2-b ~ .f2-c .f2-d", s)
        self.assertIn("url(#f2-grad)", s)
        self.assertIn("#b2b2b2", s)  # cor não é seletor
        self.assertIn(".2px", s)
        self.assertIn('class="f2-st1 f2-st2"', s)
        self.assertIn('style="fill: url(#f2-grad); opacity: .5"', s)

    def test_url_externa_e_funcoes_de_imagem_recusadas(self):
        self.recusa(
            '<rect style="fill: url(https://evil"/>',
            '<rect fill="url(//evil"/>',
            '<rect style="mask: url(http://x/m)"/>',
            "<style>.a { fill: url(https://evil</style>",
            "<style>@import url(https://x/a.css); .a { fill: red }</style>",
            "<style>.a { background: image-set('x.png' 1x) }</style>",
            "<style>.a { mask: attr(x) }</style>",
            '<rect fill="cross-fade(a, b)"/>',
            '<rect fill="paint(x)"/>',
        )

    def test_data_suspeito_so_sai(self):
        s = limpo('<g data-name="Layer: 1"/><g data-name="a//b"/><g data-name="Camada 1"/>')
        self.assertNotIn("Layer", s)
        self.assertNotIn("a//b", s)
        self.assertIn('data-name="Camada 1"', s)

    def test_tail_de_texto_mantido(self):
        self.assertIn("</tspan>c</text>", limpo("<text>a<tspan>b</tspan>c</text>"))

    def test_limites_de_use(self):
        limpo('<use href="#a"/>' * 1_000)
        self.recusa('<use href="#a"/>' * 1_001)

    def test_style_nao_vaza_para_a_pagina(self):
        self.recusa(
            "<style>body { display: none }</style>",
            "<style>* { opacity: 0 }</style>",
            "<style>:root { color: red }</style>",
            "<style>[class] { color: red }</style>",
            "<style>.a:hover { color: red }</style>",
            "<style>@media (min-width: 1px) { .a { opacity: .5 } }</style>",
            "<style>@layer x { .a { color: red } }</style>",
            "<style>@font-face { font-family: x }</style>",
            "<style>.a { position: fixed }</style>",
            "<style>.a { animation-name: x }</style>",
            "<style>.a { margin: -5000px }</style>",
            "<style>.a { float: left }</style>",
            "<style>.a { transform: scale(9) }</style>",
            "<style>.a { width: 300vw }</style>",
            "<style>.a { display: block }</style>",
            '<rect style="height: 300vh"/>',
            '<rect style="z-index: 9"/>',
            '<rect style="inset: 0"/>',
            "<style>.a { color: red</style>",
            "<style>.a { color: red } /* sem fechar</style>",
        )

    def test_filho_de_style_nao_escapa_do_css(self):
        s = limpo(
            "<style>.a { fill: red }<g/>input[value^=a] { background: url(https://evil) }"
            "@import 'x';</style><title>t<g/>x</title>"
        )
        self.assertNotIn("evil", s)
        self.assertNotIn("import", s)
        self.assertNotIn("<g", s)

    def test_raiz_nao_cobre_a_pagina(self):
        s = sanitizar_svg(
            b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1 1" width="9" height="9"'
            b' x="0" y="0" style="position:fixed;inset:0;z-index:99999"/>'
        )[0].decode()
        self.assertEqual(s, '<svg viewBox="0 0 1 1" xmlns="http://www.w3.org/2000/svg" />')
        s = sanitizar_svg(
            b'<svg xmlns="http://www.w3.org/2000/svg" class="r" overflow="visible"'
            b' transform="scale(9)"><svg overflow="visible"/><style>.r { fill: red }</style></svg>'
        )[0].decode()
        for proibido in ('class="', "overflow", "transform"):
            self.assertNotIn(proibido, s)
        with self.assertRaises(ValidationError):
            sanitizar_svg(
                b'<svg xmlns="http://www.w3.org/2000/svg" class="r">'
                b"<style>.r { margin: -5000px; width: 300vw; height: 300vh }</style></svg>"
            )

    def test_ids_e_href_vazio(self):
        self.recusa('<g id="1abc"/>', '<g id="a b"/>', f'<g id="a{"x" * 101}"/>')
        self.assertNotIn("href", limpo('<use href="#"/>'))

    def test_dos_url_repetida(self):
        inicio = time.monotonic()
        self.recusa("<style>.a { fill: " + "url(" * 10_000 + "}</style>")
        self.recusa('<rect style="fill: ' + "url(" * 1_000 + '"/>')
        self.assertLess(time.monotonic() - inicio, 2)

    def test_dos_muitos_ids(self):
        corpo = "".join(f'<g id="g{i}"/>' for i in range(50_000))
        inicio = time.monotonic()
        self.recusa(corpo)  # acima de 5.000 ids
        self.assertLess(time.monotonic() - inicio, 2)
        self.assertEqual(len(sanitizar_svg(svg("".join(f'<g id="g{i}"/>' for i in range(5_000))))[1]), 5_000)

    def test_aninhamento_profundo_recusado(self):
        inicio = time.monotonic()
        self.recusa("<g>" * 5_000 + "</g>" * 5_000)
        self.assertLess(time.monotonic() - inicio, 2)

    def test_sem_declaracao_xml(self):
        self.assertTrue(limpo("").startswith("<svg"))

    def test_billion_laughs_e_doctype_recusados(self):
        bomba = (
            b'<?xml version="1.0"?><!DOCTYPE lolz [<!ENTITY lol "lol">'
            b'<!ENTITY lol2 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">]>'
            b'<svg xmlns="http://www.w3.org/2000/svg"><title>&lol2;</title></svg>'
        )
        with self.assertRaises(ValidationError):
            sanitizar_svg(bomba)

    def test_nao_svg_recusado(self):
        with self.assertRaises(ValidationError):
            sanitizar_svg(b"<html/>")


class RevistaComArquivosTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        ano = Ano.objects.create(ano=2026)
        lp = Componente.objects.create(ano=ano, codigo="LP", nome="Língua Portuguesa")
        pa = ParceiroAno.objects.create(parceiro=Parceiro.objects.create(nome="GO"), ano=ano)
        projeto = Projeto.objects.create(parceiro_ano=pa, ano=ano, nome="GO - PROJETO")
        cls.revista = Revista.objects.create(projeto=projeto, componente=lp, ano=ano)

    def setUp(self):
        self.media = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.media)
        ctx = override_settings(MEDIA_ROOT=self.media)
        ctx.enable()
        self.addCleanup(ctx.disable)

    def test_receber_svg_grava_sanitizado(self):
        r = receber_svg(self.revista, SimpleUploadedFile("x.svg", FIXTURE.read_bytes()))
        r.refresh_from_db()
        self.assertRegex(r.svg_f2, r"^f2/[0-9a-f]{32}\.svg$")
        with default_storage.open(r.svg_f2) as f:
            gravado = f.read()
        self.assertEqual(r.svg_sha256, hashlib.sha256(gravado).hexdigest())
        self.assertIn(b'id="f2-btn-action-p2"', gravado)
        self.assertIn("btn-action-p2", r.svg_ids)
        self.assertFalse(any(i.startswith("f2-") for i in r.svg_ids))

    def test_svg_acima_de_3mb_recusado(self):
        grande = svg("<!--" + "x" * (3 * MB) + "-->")
        with self.assertRaisesMessage(ValidationError, "3 MB"):
            receber_svg(self.revista, SimpleUploadedFile("x.svg", grande))

    def test_troca_apaga_arquivo_antigo_apos_commit(self):
        with self.captureOnCommitCallbacks(execute=True):
            receber_svg(self.revista, svg('<g id="passo1"/>'))
        antigo = self.revista.svg_f2
        with self.captureOnCommitCallbacks(execute=True):
            receber_svg(self.revista, svg('<g id="passo2"/>'))
        self.assertFalse(default_storage.exists(antigo))
        self.assertTrue(default_storage.exists(self.revista.svg_f2))

    def test_save_falhou_apaga_arquivo_novo(self):
        with mock.patch.object(Revista, "save", side_effect=RuntimeError), \
                self.assertRaises(RuntimeError):
            receber_svg(self.revista, svg('<g id="passo1"/>'))
        _, arquivos = default_storage.listdir("f2")
        self.assertEqual(arquivos, [])

    def test_capa_png_aceita(self):
        r = receber_capa(self.revista, SimpleUploadedFile("capa.jpg", PNG))
        r.refresh_from_db()
        self.assertRegex(r.capa, r"^capas/[0-9a-f]{32}\.png$")  # tipo vem do conteúdo
        self.assertEqual(r.capa_sha256, hashlib.sha256(PNG).hexdigest())

    def test_capa_tipo_errado_recusada(self):
        for dados in (b"GIF89a" + b"\x00" * 10, b"<svg/>", b"RIFF\x00\x00\x00\x00AVI "):
            with self.assertRaises(ValidationError):
                receber_capa(self.revista, SimpleUploadedFile("capa.png", dados))

    def test_capa_acima_de_5mb_recusada(self):
        with self.assertRaisesMessage(ValidationError, "5 MB"):
            receber_capa(self.revista, SimpleUploadedFile("capa.png", PNG + b"\x00" * 5 * MB))

    def test_ids_faltando(self):
        self.revista.svg_ids = ["passo1", "btn-action-p2", "fundo"]
        secoes = ["abertura", "passo1", "passo2", "dlg-p2", "dlg-p4-i1"]
        self.assertEqual(ids_faltando(self.revista, secoes), ["passo2", "btn-action-p4-i1"])

