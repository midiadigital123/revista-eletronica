import io
import os
import zipfile
from pathlib import Path
from unittest import mock

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.template.loader import render_to_string
from django.test import TestCase
from django.urls import reverse

from nucleo.management.commands.criar_demo import PNG
from nucleo.models import Parceiro, Revista, RevistaFasciculo, RevistaInfografico, RevistaInfograficoItem, Tarefa, TemplateVersao
from nucleo.servicos.arquivos import receber_capa
from nucleo.servicos.cascata import gravar_cortes
from nucleo.servicos.empacotar import Pendente, nome_zip, zip_revista
from nucleo.servicos.html import contexto_pagina, link_zip
from nucleo.servicos.resolver import carregar, resolver
from nucleo.tests.test_preview import F2, dois_infograficos, foto_antiga, gravar_imagens
from nucleo.tests.test_resolver import MediaTemporaria, Mundo, preencher_infograficos, usuario

# Zip que o Playwright zip.spec.ts extrai e abre por file:// (gabarito). Regerar: REGERAR_FIXTURES=1.
GABARITO = Path(__file__).resolve().parents[2] / "e2e" / "fixtures" / "revista.zip"
CORTES = [100, 200, 250, 300]


def conteudo(dados):
    with zipfile.ZipFile(io.BytesIO(dados)) as z:
        return {nome: z.read(nome) for nome in z.namelist()}


class ZipTest(MediaTemporaria, TestCase):
    @classmethod
    def setUpTestData(cls):
        Mundo.montar(cls)
        TemplateVersao.objects.create(template=cls.templates["LP", "F2"], numero=2, texto=F2)

    def setUp(self):
        super().setUp()
        self.rev = carregar(self.go["LP"].pk)
        receber_capa(self.rev, SimpleUploadedFile("capa.png", PNG))
        preencher_infograficos(self.rev)
        gravar_imagens(self.rev)
        self.outras = RevistaInfografico.objects.get(revista=self.rev, tipo="outras").pk
        self.rev = carregar(self.rev.pk)
        self.item(self.tarefa, "itens/item1.png", PNG)  # LP 5EF D01 "Localiza."

    @staticmethod
    def item(tarefa, caminho, dados=None):
        """Aponta `Tarefa.arquivo` para `caminho` (gravando `dados` no storage, se houver)."""
        if dados is not None:
            caminho = default_storage.save(caminho, ContentFile(dados))
        Tarefa.objects.filter(pk=tarefa.pk).update(arquivo=caminho)

    def tarefa_lp(self, etapa, texto):
        return Tarefa.objects.get(
            descritor__matriz_etapa_cc__etapa=etapa, descritor__matriz_etapa_cc__componente=self.lp, texto=texto
        )

    def pendentes(self, revista=None):
        with self.assertRaises(Pendente) as erro:
            zip_revista(revista or carregar(self.rev.pk))
        return erro.exception

    def test_lista_de_arquivos(self):
        nome, dados = zip_revista(self.rev)
        self.assertEqual(nome, "go-lp-2026.zip")
        self.assertEqual(
            sorted(conteudo(dados)),
            [
                "arquivos/capa.png",
                *(f"arquivos/infograficos/{self.outras}-{p}.png" for p in range(1, 5)),
                "arquivos/itens/item1.png",
                "f1.html",
                "f2-outras-etapas.html",
                "index.html",
                "revista/f1/assets/seta-anterior.svg",
                "revista/f1/assets/seta-proxima.svg",
                "revista/f1/script.js",
                "revista/f1/styles.css",
                "revista/f2/f2-init.js",
                "revista/f2/revista.css",
                "revista/f2/svg-tour-modal.js",
                "revista/f2/svg-tour.js",
            ],
        )

    def test_bytes_deterministicos(self):
        a, b = zip_revista(self.rev)[1], zip_revista(carregar(self.rev.pk))[1]
        self.assertEqual(a, b)
        with zipfile.ZipFile(io.BytesIO(a)) as z:
            metodos = {i.filename: i.compress_type for i in z.infolist()}
        self.assertEqual(metodos["arquivos/capa.png"], zipfile.ZIP_STORED)
        self.assertEqual(metodos["index.html"], zipfile.ZIP_DEFLATED)

    def test_paginas_na_ordem_e_com_links_relativos(self):
        dois_infograficos(self.rev)
        with zipfile.ZipFile(io.BytesIO(zip_revista(carregar(self.rev.pk))[1])) as z:
            paginas = [n for n in z.namelist() if n.endswith(".html")]
        self.assertEqual(paginas, ["index.html", "f1.html", "f2-alfa.html", "f2-outras-etapas.html"])

    def test_index_inline_e_sem_fetch(self):
        arquivos = conteudo(zip_revista(self.rev)[1])
        index, f1, f2 = (arquivos[n].decode() for n in ("index.html", "f1.html", "f2-outras-etapas.html"))
        self.assertIn('src="arquivos/capa.png"', index)
        self.assertIn('href="f1.html"', index)
        self.assertIn('href="f2-outras-etapas.html"', index)
        self.assertIn('href="index.html"', f1)  # voltar ao sumário
        self.assertIn('id="dados-revista"', f1)
        self.assertIn('id="f2-descritor"', f2)  # SVG gerado, inline
        self.assertIn('id="dados-tour"', f2)
        self.assertIn('<dialog id="dlg-descritor"', f2)
        self.assertIn('src="revista/f2/f2-init.js"', f2)
        self.assertIn('<img src="arquivos/infograficos/', f2)
        self.assertNotIn("infograficos/infograficos/", f2)
        for html in (index, f1, f2):
            self.assertNotIn("/static/", html)
        # svg-tour.js (cópia sem alteração, D-156) tem `SvgTour.load` com fetch; ninguém o chama.
        for nome, dados in arquivos.items():
            if nome.endswith((".html", ".js")) and nome != "revista/f2/svg-tour.js":
                self.assertNotIn(b"fetch(", dados, nome)
        self.assertNotIn(b"SvgTour.load", arquivos["revista/f2/f2-init.js"])

    def test_faixa_so_no_preview(self):
        """O zip renderiza com preview=False: a faixa que o preview mostra some."""
        RevistaFasciculo.objects.filter(revista=self.rev, fasciculo="F2").update(template=None)

        def corpo(preview):
            ctx = contexto_pagina(self.rev, "f2-outras-etapas", preview=preview, estaticos="revista/", capa=None,
                                  link=link_zip, base_imagens="arquivos/infograficos/")  # fmt: skip
            return render_to_string("revista/f2.html", ctx).split("<body>")[1]

        self.assertIn("faixa-vermelha", corpo(True))
        self.assertNotIn("faixa-vermelha", corpo(False))

    def test_mais_de_um_item(self):
        self.item(self.tarefa_lp(self.e5, "Infere."), "itens/2026/item2.pdf", b"%PDF-1.4 item")
        arquivos = conteudo(zip_revista(carregar(self.rev.pk))[1])
        self.assertEqual(arquivos["arquivos/itens/item2.pdf"], b"%PDF-1.4 item")
        self.assertIn("arquivos/itens/item1.png", arquivos)
        self.assertIn('"item": {"id": "item2", "tipo": "pdf"}', arquivos["f1.html"].decode())

    def test_item_de_etapa_sem_corte_nao_entra(self):
        pa = self.rev.projeto.parceiro_ano
        gravar_cortes(pa, [(self.e5, self.lp, CORTES), (self.e5, self.mt, CORTES)], self.usuario)
        self.item(self.tarefa_lp(self.e9, "Localiza."), "itens/nove.pdf", b"%PDF 9")
        arquivos = conteudo(zip_revista(carregar(self.rev.pk))[1])
        self.assertNotIn("arquivos/itens/nove.pdf", arquivos)
        self.assertIn("arquivos/itens/item1.png", arquivos)

    def test_nome_de_item_invalido(self):
        self.item(self.tarefa, "itens/com espaço.pdf", b"%PDF")
        self.assertIn(f"Tarefa {self.tarefa.pk}: nome de item inválido", str(self.pendentes()))

    def test_colisao_de_nomes(self):
        outra = self.tarefa_lp(self.e5, "Infere.")
        self.item(outra, "outra/item1.png", b"png")
        self.assertIn(f"Tarefa {outra.pk}: outro arquivo já usa o nome item1.png", str(self.pendentes()))

    def test_arquivo_ausente(self):
        self.item(self.tarefa, "itens/sumiu.pdf")
        self.assertIn("Arquivo ausente no storage: itens/sumiu.pdf.", str(self.pendentes()))
        self.item(self.tarefa, "itens/item1.png")
        default_storage.delete(self.rev.capa)
        self.assertIn(f"Arquivo ausente no storage: {self.rev.capa}.", str(self.pendentes()))

    def test_arquivada(self):
        # Tira a LP dos cortes: a cascata arquiva e fotografa (D-117); o zip sai da foto.
        gravar_cortes(self.rev.projeto.parceiro_ano, [(self.e5, self.mt, CORTES)], self.usuario)
        arquivada = carregar(self.rev.pk)
        self.assertIsNotNone(arquivada.arquivada_em)
        self.assertIn("arquivos/itens/item1.png", conteudo(zip_revista(arquivada)[1]))
        receber_capa(arquivada, SimpleUploadedFile("capa.png", PNG + b"\0"))  # outro sha256
        erro = self.pendentes()
        self.assertEqual([p.codigo for p in erro.pendencias], ["zip_foto"])
        self.assertIn("A capa mudou depois da foto de arquivamento; o zip não bateria com o texto.", str(erro))

    def arquivar(self):
        gravar_cortes(self.rev.projeto.parceiro_ano, [(self.e5, self.mt, CORTES)], self.usuario)
        self.assertIsNotNone(carregar(self.rev.pk).arquivada_em)

    def test_arquivada_imagem_trocada(self):
        self.arquivar()
        RevistaInfograficoItem.objects.filter(infografico_id=self.outras, posicao=2).update(imagem_sha256="b" * 64)
        RevistaInfograficoItem.objects.filter(infografico_id=self.outras, posicao=3).delete()
        erro = self.pendentes()
        self.assertEqual([p.codigo for p in erro.pendencias], ["zip_foto", "zip_foto"])
        self.assertIn("Avaliação e Currículo – Outras Etapas, item 2: a imagem mudou depois da foto de arquivamento.", str(erro))
        self.assertIn("Avaliação e Currículo – Outras Etapas, item 3: a imagem mudou", str(erro))

    def test_arquivada_mesma_imagem_caminho_novo_sai(self):
        """Reenviar a mesma imagem (mesmo sha, caminho novo): o zip usa o nome da foto e os bytes do caminho atual."""
        self.arquivar()
        antigo = f"infograficos/{self.outras}-1.png"
        RevistaInfograficoItem.objects.filter(infografico_id=self.outras, posicao=1).update(imagem="infograficos/novo.png")
        default_storage.save("infograficos/novo.png", ContentFile(PNG))
        default_storage.delete(antigo)
        arquivos = conteudo(zip_revista(carregar(self.rev.pk))[1])
        self.assertEqual(arquivos[f"arquivos/{antigo}"], PNG)
        self.assertNotIn("arquivos/infograficos/novo.png", arquivos)

    def test_imagem_ausente(self):
        default_storage.delete(f"infograficos/{self.outras}-3.png")
        erro = self.pendentes()
        self.assertEqual([p.codigo for p in erro.pendencias], ["zip_arquivo"])
        self.assertIn(f"Arquivo ausente no storage: infograficos/{self.outras}-3.png.", str(erro))

    def test_tarefas_desligado_nao_copia_imagens(self):
        RevistaInfografico.objects.filter(pk=self.outras).update(passos_desligados=["tarefas"])
        for p in range(1, 5):
            default_storage.delete(f"infograficos/{self.outras}-{p}.png")
        arquivos = conteudo(zip_revista(carregar(self.rev.pk))[1])
        self.assertFalse([n for n in arquivos if n.startswith("arquivos/infograficos/")])

    def test_colisao_de_nome_de_imagem(self):
        RevistaInfograficoItem.objects.filter(infografico_id=self.outras, posicao=2).update(imagem=f"outra/{self.outras}-1.png")
        erro = self.pendentes()
        self.assertEqual([p.codigo for p in erro.pendencias], ["zip_arquivo"])
        self.assertIn(f"Outro arquivo já usa o nome {self.outras}-1.png.", str(erro))

    def test_foto_antiga_sem_paginas_do_f2(self):
        """Foto de antes da D-237 (sem `infograficos`, com svg_sha256): o zip sai sem f2-*.html."""
        gravar_cortes(self.rev.projeto.parceiro_ano, [(self.e5, self.mt, CORTES)], self.usuario)
        arquivada = carregar(self.rev.pk)
        foto_antiga(arquivada)
        paginas = sorted(n for n in conteudo(zip_revista(arquivada)[1]) if n.endswith(".html"))
        self.assertEqual(paginas, ["f1.html", "index.html"])

    def test_resolve_uma_vez(self):
        """Pendências e páginas saem do mesmo resolvido: edição no meio do zip não mistura estados."""
        dois_infograficos(self.rev)
        contador = mock.Mock(wraps=resolver)
        with mock.patch("nucleo.servicos.empacotar.resolver", contador), mock.patch("nucleo.servicos.html.resolver", contador):
            zip_revista(carregar(self.rev.pk))
        self.assertEqual(contador.call_count, 1)

    def test_recusa_com_pendencias(self):
        erro = self.pendentes(carregar(self.go["MT"].pk))
        self.assertTrue({"infografico", "capa"} <= {p.codigo for p in erro.pendencias})
        self.assertIn("Falta a imagem de capa.", str(erro))

    def test_nome_sem_acento(self):
        Parceiro.objects.filter(pk=self.rev.projeto.parceiro_ano.parceiro_id).update(nome="São Paulo / DEMONSTRAÇÃO")
        self.assertEqual(nome_zip(carregar(self.rev.pk)), "sao-paulo-demonstracao-lp-2026.zip")

    def test_gabarito_do_playwright(self):
        dois_infograficos(self.rev)
        dados = zip_revista(carregar(self.rev.pk))[1]
        if os.environ.get("REGERAR_FIXTURES"):
            GABARITO.write_bytes(dados)
        self.assertEqual(GABARITO.read_bytes(), dados)

    def test_admin_baixar_zip(self):
        url = reverse("admin:nucleo_revista_changelist")
        self.client.force_login(usuario("imp", "Impresso"))  # só ver_tudo: tem view_revista
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
        self.client.force_login(usuario("imp", "Impresso"))  # só ver_tudo: tem view_revista
        antes = Revista.objects.filter(pk=self.rev.pk).values().get()
        mudar = reverse("admin:nucleo_revista_change", args=[self.rev.pk])
        apagar = reverse("admin:nucleo_revista_delete", args=[self.rev.pk])
        self.assertEqual(self.client.get(mudar).status_code, 200)  # só ver
        self.assertEqual(self.client.post(mudar, {"capa": "x", "hash_validado": "0" * 64}).status_code, 403)
        self.assertEqual(self.client.get(apagar).status_code, 403)
        self.assertEqual(self.client.post(apagar, {"post": "yes"}).status_code, 403)
        self.assertEqual(Revista.objects.filter(pk=self.rev.pk).values().get(), antes)
        readonly = set(admin.site._registry[Revista].readonly_fields)
        self.assertTrue({"hash_validado", "validado_em", "validado_por", "arquivada_em"} <= readonly)
