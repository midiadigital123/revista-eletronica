import io
import os
import shutil
import tempfile
import zipfile
from pathlib import Path

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from nucleo.management.commands.criar_demo import png
from nucleo.models import Parceiro, Revista, Tarefa, TemplateVersao
from nucleo.servicos.arquivos import receber_capa, receber_svg
from nucleo.servicos.empacotar import ESTATICOS, Pendente, nome_zip, zip_revista
from nucleo.servicos.resolver import carregar
from nucleo.tests.test_preview import F2, SVG
from nucleo.tests.test_resolver import Mundo

# Zip que o Playwright zip.spec.ts extrai e abre por file:// (gabarito). Regerar: REGERAR_FIXTURES=1.
GABARITO = Path(__file__).resolve().parents[2] / "e2e" / "fixtures" / "revista.zip"


def conteudo(dados):
    with zipfile.ZipFile(io.BytesIO(dados)) as z:
        return {nome: z.read(nome) for nome in z.namelist()}


class ZipTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        Mundo.montar(cls)
        TemplateVersao.objects.create(template=cls.templates["LP", "F2"], numero=2, texto=F2)

    def setUp(self):
        media = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, media)
        ctx = override_settings(MEDIA_ROOT=media)
        ctx.enable()
        self.addCleanup(ctx.disable)
        self.rev = carregar(self.go["LP"].pk)
        receber_svg(self.rev, SimpleUploadedFile("x.svg", SVG))
        receber_capa(self.rev, SimpleUploadedFile("capa.png", png(4, 4, (255, 235, 0))))
        self.rev = carregar(self.rev.pk)

    def test_lista_de_arquivos(self):
        nome, dados = zip_revista(self.rev)
        self.assertEqual(nome, "go-lp-2026.zip")
        estaticos = {
            "revista/" + p.relative_to(ESTATICOS).as_posix()
            for p in ESTATICOS.rglob("*")
            if p.is_file() and not p.name.endswith(".test.mjs")
        }
        self.assertIn("revista/f1/script.js", estaticos)
        self.assertIn("revista/f2/f2-init.js", estaticos)
        self.assertEqual(set(conteudo(dados)), {"index.html", "arquivos/capa.png", *estaticos})

    def test_index_inline_sem_faixas_e_sem_fetch(self):
        arquivos = conteudo(zip_revista(self.rev)[1])
        html = arquivos["index.html"].decode()
        self.assertIn('<g id="f2-passo1">', html)  # SVG inline
        self.assertIn('id="dados-tour"', html)
        self.assertIn('<dialog id="dlg-p2"', html)
        self.assertIn('src="arquivos/capa.png"', html)
        self.assertIn('src="revista/f2/f2-init.js"', html)
        self.assertNotIn("faixa-vermelha", html.split("<body>")[1])
        self.assertNotIn("/static/", html)
        # svg-tour.js (cópia sem alteração, D-156) tem `SvgTour.load` com fetch; ninguém o chama.
        for nome, dados in arquivos.items():
            if nome.endswith((".html", ".js")) and nome != "revista/f2/svg-tour.js":
                self.assertNotIn(b"fetch(", dados, nome)
        self.assertNotIn(b"SvgTour.load", arquivos["revista/f2/f2-init.js"])

    def test_item_da_tarefa(self):
        caminho = default_storage.save("itens/2026/abc.pdf", ContentFile(b"%PDF-1.4 item"))
        Tarefa.objects.filter(pk=self.tarefa.pk).update(arquivo=caminho)
        arquivos = conteudo(zip_revista(self.rev)[1])
        self.assertEqual(arquivos["arquivos/itens/abc.pdf"], b"%PDF-1.4 item")
        self.assertIn('"item": {"id": "abc", "tipo": "pdf"}', arquivos["index.html"].decode())

    def test_recusa_com_pendencias(self):
        sem_capa = carregar(self.go["MT"].pk)
        with self.assertRaises(Pendente) as erro:
            zip_revista(sem_capa)
        codigos = {p.codigo for p in erro.exception.pendencias}
        self.assertTrue({"svg", "capa"} <= codigos)
        self.assertIn("Falta a imagem de capa.", str(erro.exception))

    def test_nome_sem_acento(self):
        Parceiro.objects.filter(pk=self.rev.projeto.parceiro_ano.parceiro_id).update(nome="São Paulo / DEMONSTRAÇÃO")
        self.assertEqual(nome_zip(carregar(self.rev.pk)), "sao-paulo-demonstracao-lp-2026.zip")

    def test_gabarito_do_playwright(self):
        dados = zip_revista(self.rev)[1]
        if os.environ.get("REGERAR_FIXTURES"):
            GABARITO.write_bytes(dados)
        self.assertEqual(conteudo(GABARITO.read_bytes()), conteudo(dados))

    def test_admin_baixar_zip(self):
        url = reverse("admin:nucleo_revista_changelist")
        impresso = get_user_model().objects.create(username="imp", is_staff=True)
        impresso.groups.add(Group.objects.get(name="Impresso"))  # só ver_tudo: tem view_revista
        self.client.force_login(impresso)
        acao = {"action": "baixar_zip", "_selected_action": [self.rev.pk]}
        r = self.client.post(url, acao)
        self.assertEqual(r["Content-Type"], "application/zip")
        self.assertEqual(r["Content-Disposition"], 'attachment; filename="go-lp-2026.zip"')
        self.assertIn("index.html", conteudo(r.content))

        r = self.client.post(url, {**acao, "_selected_action": [self.go["MT"].pk]}, follow=True)
        self.assertContains(r, "Zip recusado. Pendências: ")
        r = self.client.post(url, {**acao, "_selected_action": [self.rev.pk, self.go["MT"].pk]}, follow=True)
        self.assertContains(r, "Escolha uma revista por vez")

        sem_permissao = get_user_model().objects.create(username="nada", is_staff=True)
        self.client.force_login(sem_permissao)
        self.assertEqual(self.client.post(url, acao).status_code, 403)

    def test_admin_so_leitura(self):
        modelo = admin.site._registry[Revista]
        self.assertFalse(modelo.has_delete_permission(None))
        self.assertFalse(modelo.has_change_permission(None))
        self.assertTrue(
            {"hash_validado", "validado_em", "validado_por", "arquivada_em"} <= set(modelo.readonly_fields)
        )
