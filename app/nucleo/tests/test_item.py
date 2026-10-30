"""Arquivo do item na matriz (D-180)."""

from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from nucleo.models import Ano, Descritor, Matriz, MatrizEtapaCC, Revista, Tarefa
from nucleo.servicos import bloqueio
from nucleo.servicos.arquivos import receber_item, remover_item
from nucleo.servicos.resolver import carregar, hash_validado, resolver
from nucleo.servicos.validacao import validada
from nucleo.tests.test_resolver import MediaTemporaria, Mundo, usuario

PNG = b"\x89PNG\r\n\x1a\n" + b"\0" * 32
JPG = b"\xff\xd8\xff\xe0" + b"\0" * 32
PDF = b"%PDF-1.4\n%%EOF\n"


def upload(nome, dados, mime):
    return SimpleUploadedFile(nome, dados, content_type=mime)


class Base(MediaTemporaria, TestCase):
    @classmethod
    def setUpTestData(cls):
        Mundo.montar(cls)
        cls.root = usuario("root", is_superuser=True)

    def setUp(self):
        super().setUp()
        self.client.force_login(self.root)
        self.tarefa.refresh_from_db()

    def receber(self, tarefa, *args):
        with self.captureOnCommitCallbacks(execute=True):
            return receber_item(tarefa, *args)


class ReceberItemTest(Base):
    def test_png_jpg_e_pdf_validos_entram(self):
        for nome, dados, mime, tipo in (
            ("a.png", PNG, "image/png", "png"),
            ("a.jpg", JPG, "image/jpeg", "jpg"),
            ("a.pdf", PDF, "application/pdf", "pdf"),
        ):
            with self.subTest(tipo=tipo):
                self.receber(self.tarefa, upload(nome, dados, mime), "")
                self.tarefa.refresh_from_db()
                self.assertTrue(self.tarefa.arquivo.startswith("itens/"))
                self.assertTrue(self.tarefa.arquivo.endswith(f".{tipo}"))
                self.assertEqual(default_storage.open(self.tarefa.arquivo).read(), dados)

    def test_png_com_bytes_de_pdf_e_recusado(self):
        with self.assertRaisesMessage(ValidationError, "O conteúdo do arquivo não é do tipo informado"):
            receber_item(self.tarefa, upload("a.png", PDF, "image/png"), "")
        self.tarefa.refresh_from_db()
        self.assertIsNone(self.tarefa.arquivo)

    def test_tipo_fora_da_lista_e_recusado(self):
        with self.assertRaisesMessage(ValidationError, "PDF, PNG ou JPG"):
            receber_item(self.tarefa, upload("a.gif", b"GIF89a" + b"\0" * 10, "image/gif"), "")

    def test_6_mb_e_recusado(self):
        with self.assertRaisesMessage(ValidationError, "acima de 5 MB"):
            receber_item(self.tarefa, upload("a.png", PNG + b"\0" * (6 * 2**20), "image/png"), "")

    def test_texto_alternativo_no_resolvido_e_no_preview(self):
        self.receber(self.tarefa, upload("a.png", PNG, "image/png"), "Grafico de barras com 4 colunas")
        rev = carregar(self.go["LP"].pk)
        linhas = [
            linha
            for padrao in resolver(rev)["f1"]["dados"]["5ef"]["D01"]["scale"].values()
            for linha in padrao
            if "item" in linha
        ]
        self.assertEqual(len(linhas), 1)
        self.assertEqual(linhas[0]["item"]["alt"], "Grafico de barras com 4 colunas")
        resp = self.client.get(reverse("preview", args=[rev.pk]))
        self.assertContains(resp, "Grafico de barras com 4 colunas")
        nome = self.tarefa.arquivo.split("/")[-1]
        item = self.client.get(reverse("preview_item", args=[rev.pk, nome]))
        self.assertEqual(item["Content-Type"], "image/png")
        self.assertEqual(b"".join(item.streaming_content), PNG)
        # Item de outra matriz/componente não sai pelo preview desta revista.
        self.assertEqual(self.client.get(reverse("preview_item", args=[self.go["MT"].pk, nome])).status_code, 404)


class ModalTest(Base):
    def url(self):
        return reverse("admin:nucleo_descritor_item", args=[self.tarefa.descritor_id, self.tarefa.pk])

    def sessao(self, resp=None):
        """Sessão do bloqueio da página (a do redirect, quando houver: o GET seguinte readquire)."""
        resp = resp or self.client.get(reverse("admin:nucleo_descritor_change", args=[self.tarefa.descritor_id]))
        self.assertContains(resp, f'data-dialogo="item-{self.tarefa.pk}"')
        self.assertContains(resp, "Texto alternativo (opcional)")
        self.assertContains(resp, "perde(m) o “Validado”")
        return resp.context["bloqueio"]["sessao"]

    def test_envia_pede_impacto_e_remove(self):
        arquivo = upload("a.png", PNG, "image/png")
        dados = {"_bloqueio_sessao": self.sessao(), "arquivo": arquivo, "texto_alternativo": "Mapa"}
        resp = self.client.post(self.url(), dados, follow=True)
        self.assertContains(resp, "afeta 2 revista(s) ativa(s)")  # GO e PE, LP 5EF
        self.tarefa.refresh_from_db()
        self.assertIsNone(self.tarefa.arquivo)

        arquivo.seek(0)
        dados = {**dados, "_bloqueio_sessao": self.sessao(resp), "confirmar_impacto": "on"}
        with self.captureOnCommitCallbacks(execute=True):
            resp = self.client.post(self.url(), dados, follow=True)
        self.assertContains(resp, "Arquivo do item enviado")
        self.tarefa.refresh_from_db()
        self.assertEqual(self.tarefa.texto_alternativo, "Mapa")
        caminho = self.tarefa.arquivo
        self.assertEqual(b"".join(self.client.get(self.url()).streaming_content), PNG)

        dados = {"_bloqueio_sessao": self.sessao(resp), "confirmar_impacto": "on", "_remover": "1"}
        with self.captureOnCommitCallbacks(execute=True):
            self.client.post(self.url(), dados)
        self.tarefa.refresh_from_db()
        self.assertIsNone(self.tarefa.arquivo)
        self.assertFalse(default_storage.exists(caminho))

    def test_sem_o_bloqueio_nao_grava(self):
        bia = usuario("bia", "Pedagógica")
        self.assertTrue(bloqueio.adquirir(self.tarefa.descritor.matriz_etapa_cc, bia, "aba-bia"))
        dados = {"_bloqueio_sessao": "aba-root", "arquivo": upload("a.png", PNG, "image/png"), "confirmar_impacto": "on"}
        resp = self.client.post(self.url(), dados, follow=True)
        self.assertContains(resp, "perdeu o bloqueio")
        self.tarefa.refresh_from_db()
        self.assertIsNone(self.tarefa.arquivo)


class DiscoTest(Base):
    """D-150: o arquivo só sai do disco quando nenhuma tarefa de nenhum ano aponta para ele."""

    def outro_ano(self, caminho):
        ano = Ano.objects.create(ano=2027)
        etapa, comp = self.e5, self.lp
        etapa.pk = comp.pk = None
        etapa.ano = comp.ano = ano
        etapa.save()
        comp.save()
        mec = MatrizEtapaCC.objects.create(
            matriz=Matriz.objects.create(ano=ano, nome="Comunitária"), etapa=etapa, componente=comp, ano=ano
        )
        d = Descritor.objects.create(matriz_etapa_cc=mec, codigo="D01", descricao="x", ordem=1)
        return Tarefa.objects.create(descritor=d, inicio=100, fim=150, texto="x", ordem=1, arquivo=caminho)

    def test_compartilhado_com_outro_ano_fica(self):
        self.receber(self.tarefa, upload("a.png", PNG, "image/png"), "")
        caminho = self.tarefa.arquivo
        self.outro_ano(caminho)
        with self.captureOnCommitCallbacks(execute=True):
            remover_item(self.tarefa)
        self.assertTrue(default_storage.exists(caminho))

    def test_sem_referencia_sai_na_troca(self):
        self.receber(self.tarefa, upload("a.png", PNG, "image/png"), "")
        primeiro = self.tarefa.arquivo
        self.receber(self.tarefa, upload("a.jpg", JPG, "image/jpeg"), "")
        self.assertFalse(default_storage.exists(primeiro))
