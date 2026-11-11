import hashlib
from unittest import mock

from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from nucleo.models import Ano, Componente, Parceiro, ParceiroAno, Projeto, Revista
from nucleo.servicos.arquivos import MB, receber_capa
from nucleo.tests.test_resolver import MediaTemporaria

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32


class RevistaComArquivosTest(MediaTemporaria, TestCase):
    @classmethod
    def setUpTestData(cls):
        ano = Ano.objects.create(ano=2026)
        lp = Componente.objects.create(ano=ano, codigo="LP", nome="Língua Portuguesa")
        pa = ParceiroAno.objects.create(parceiro=Parceiro.objects.create(nome="GO"), ano=ano)
        projeto = Projeto.objects.create(parceiro_ano=pa, ano=ano, nome="GO - PROJETO")
        cls.revista = Revista.objects.create(projeto=projeto, componente=lp, ano=ano)

    def test_troca_apaga_arquivo_antigo_apos_commit(self):
        with self.captureOnCommitCallbacks(execute=True):
            receber_capa(self.revista, PNG)
        antigo = self.revista.capa
        with self.captureOnCommitCallbacks(execute=True):
            receber_capa(self.revista, PNG + b"\x00")
        self.assertFalse(default_storage.exists(antigo))
        self.assertTrue(default_storage.exists(self.revista.capa))

    def test_save_falhou_apaga_arquivo_novo(self):
        with mock.patch.object(Revista, "save", side_effect=RuntimeError), \
                self.assertRaises(RuntimeError):
            receber_capa(self.revista, PNG)
        _, arquivos = default_storage.listdir("capas")
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
