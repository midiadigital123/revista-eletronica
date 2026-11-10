import hashlib

from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone

from nucleo.infografico import form_do_campo
from nucleo.models import (
    Ano,
    Componente,
    Parceiro,
    ParceiroAno,
    Projeto,
    Revista,
    RevistaInfografico,
    RevistaInfograficoEtapa,
    RevistaInfograficoItem,
)
from nucleo.tests.test_arquivos import PNG
from nucleo.tests.test_resolver import MediaTemporaria

JPG = b"\xff\xd8\xff" + b"\x00" * 32
GIF = b"GIF89a" + b"\x00" * 32


class FormDoCampoTest(MediaTemporaria, TestCase):
    @classmethod
    def setUpTestData(cls):
        ano = Ano.objects.create(ano=2026)
        lp = Componente.objects.create(ano=ano, codigo="LP", nome="Língua Portuguesa")
        mt = Componente.objects.create(ano=ano, codigo="MT", nome="Matemática")
        pa = ParceiroAno.objects.create(parceiro=Parceiro.objects.create(nome="GO"), ano=ano)
        projeto = Projeto.objects.create(parceiro_ano=pa, ano=ano, nome="GO - PROJETO")
        cls.revista = Revista.objects.create(projeto=projeto, componente=lp, ano=ano)
        outra = Revista.objects.create(projeto=projeto, componente=mt, ano=ano)
        cls.inf = RevistaInfografico.objects.create(revista=cls.revista, componente=lp, ano=ano, tipo="outras")
        cls.inf_outra = RevistaInfografico.objects.create(revista=outra, componente=mt, ano=ano, tipo="outras")

    def campo(self, resto):
        return f"inf-{self.inf.pk}-{resto}"

    def gravar(self, resto, valor="", arquivo=None):
        """Valida e grava como a view (Tarefa 3) fará."""
        form, gravar, _ = form_do_campo(self.revista, self.campo(resto), valor, arquivo)
        self.assertTrue(form.is_valid(), form.errors)
        gravar(form.cleaned_data)

    def erros(self, resto, valor="", arquivo=None):
        form, _, _ = form_do_campo(self.revista, self.campo(resto), valor, arquivo)
        self.assertFalse(form.is_valid())
        return form.errors

    def test_campos_do_infografico(self):
        campos = ("habilidade", "texto_descritor", "texto_habilidades", "texto_progressao")
        for c in campos:
            self.gravar(c, f"Valor de {c}")
        self.inf.refresh_from_db()
        self.assertEqual([getattr(self.inf, c) for c in campos], [f"Valor de {c}" for c in campos])
        self.assertEqual(self.inf.history.count(), 1 + len(campos))  # .save(): o histórico registra

    def test_etapa_cria_a_linha_e_grava(self):
        self.gravar("etapa-5EF-marca", "I")
        self.gravar("etapa-5EF-codigo", "EF15LP18")
        self.gravar("etapa-5EF-texto", "Relacionar.")
        linha = RevistaInfograficoEtapa.objects.get(infografico=self.inf)
        self.assertEqual(
            (linha.etapa, linha.ano_id, linha.marca, linha.codigo, linha.texto),
            ("5EF", self.inf.ano_id, "I", "EF15LP18", "Relacionar."),
        )
        self.gravar("etapa-5EF-marca", "")  # vazio = sem marca
        linha.refresh_from_db()
        self.assertEqual((linha.marca, linha.codigo), ("", "EF15LP18"))

    def test_item_cria_a_linha_e_grava(self):
        self.gravar("item-3-etapa", "9EF")
        self.gravar("item-3-descritor", "D05")
        self.gravar("item-3-texto_alternativo", "Um gráfico.")
        self.gravar("item-3-analise", "A análise.")
        item = RevistaInfograficoItem.objects.get(infografico=self.inf)
        self.assertEqual(
            (item.posicao, item.ano_id, item.etapa, item.descritor, item.texto_alternativo, item.analise),
            (3, self.inf.ano_id, "9EF", "D05", "Um gráfico.", "A análise."),
        )

    def test_passo_desliga_e_religa_so_ele(self):
        RevistaInfografico.objects.filter(pk=self.inf.pk).update(passos_desligados=["tarefas"])
        self.gravar("passo-habilidades", "")
        self.inf.refresh_from_db()
        self.assertEqual(sorted(self.inf.passos_desligados), ["habilidades", "tarefas"])
        self.gravar("passo-habilidades", "on")
        self.inf.refresh_from_db()
        self.assertEqual(self.inf.passos_desligados, ["tarefas"])

    def test_campo_desconhecido_ou_de_outra_revista(self):
        for campo in (
            f"inf-{self.inf_outra.pk}-habilidade",
            f"inf-{self.inf.pk + self.inf_outra.pk}-habilidade",
            self.campo("etapa-0EF-codigo"),
            self.campo("etapa-5EF-outro"),
            self.campo("item-5-analise"),
            self.campo("item-1-imagem_sha256"),
            self.campo("passo-descritor"),
            self.campo("passos_desligados"),
            "habilidade",
        ):
            self.assertIsNone(form_do_campo(self.revista, campo, "x"), campo)

    def test_infografico_arquivado(self):
        RevistaInfografico.objects.filter(pk=self.inf.pk).update(arquivado_em=timezone.now())
        self.assertIsNone(form_do_campo(self.revista, self.campo("habilidade"), "x"))

    def test_limites_e_escolhas_viram_erro_de_form(self):
        self.gravar("habilidade", "x" * 500)
        self.assertIn("habilidade", self.erros("habilidade", "x" * 501))
        self.assertIn("marca", self.erros("etapa-5EF-marca", "X"))
        self.assertIn("codigo", self.erros("etapa-5EF-codigo", "x" * 51))
        self.assertIn("etapa", self.erros("item-1-etapa", "X"))
        self.assertIn("descritor", self.erros("item-1-descritor", "x" * 21))
        self.assertIn("texto_alternativo", self.erros("item-1-texto_alternativo", "x" * 1001))
        self.assertFalse(RevistaInfograficoEtapa.objects.exists() or RevistaInfograficoItem.objects.exists())

    def test_imagem_png_grava_imagem_e_sha256(self):
        self.gravar("item-2-imagem", arquivo=SimpleUploadedFile("x.gif", PNG))  # tipo pelos bytes
        item = RevistaInfograficoItem.objects.get(infografico=self.inf, posicao=2)
        self.assertRegex(item.imagem, r"^infograficos/[0-9a-f]{32}\.png$")
        self.assertEqual(item.imagem_sha256, hashlib.sha256(PNG).hexdigest())
        self.assertTrue(default_storage.exists(item.imagem))

    def test_imagem_gif_recusada(self):
        self.assertIn("arquivo", self.erros("item-2-imagem", arquivo=SimpleUploadedFile("x.png", GIF)))
        self.assertFalse(RevistaInfograficoItem.objects.exists())

    def test_simular_imagem_nao_grava_arquivo(self):
        form, _, simular = form_do_campo(self.revista, self.campo("item-2-imagem"), "", SimpleUploadedFile("x.png", PNG))
        self.assertTrue(form.is_valid())
        simular(form.cleaned_data)
        item = RevistaInfograficoItem.objects.get(infografico=self.inf, posicao=2)
        self.assertEqual(item.imagem_sha256, hashlib.sha256(PNG).hexdigest())
        self.assertFalse(default_storage.exists("infograficos"))

    def test_trocar_imagem_apaga_a_antiga_no_commit(self):
        with self.captureOnCommitCallbacks(execute=True):
            self.gravar("item-1-imagem", arquivo=SimpleUploadedFile("a.png", PNG))
        antigo = RevistaInfograficoItem.objects.get(infografico=self.inf).imagem
        with self.captureOnCommitCallbacks(execute=True):
            self.gravar("item-1-imagem", arquivo=SimpleUploadedFile("b.jpg", JPG))
        novo = RevistaInfograficoItem.objects.get(infografico=self.inf).imagem
        self.assertRegex(novo, r"\.jpg$")
        self.assertFalse(default_storage.exists(antigo))
        self.assertTrue(default_storage.exists(novo))
