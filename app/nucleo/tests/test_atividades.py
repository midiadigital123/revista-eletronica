"""PDF das atividades do F2 (D-308, D-309): enviar, baixar, trocar e remover por ano × componente × tipo na tela
Templates; download no preview e link "Acesse aqui as atividades" na página do infográfico do tipo. O zip fica em
test_empacotar."""

from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from nucleo.models import Atividades, TemplateVersao
from nucleo.servicos.arquivos import ATIVIDADES_MAX, atividades_da_revista, receber_atividades, remover_atividades
from nucleo.tests.test_preview import F2, dois_infograficos
from nucleo.tests.test_resolver import MediaTemporaria, Mundo, usuario

PDF = b"%PDF-1.7\n" + b"0" * 32


def pdf(nome="a.pdf", dados=PDF):
    return SimpleUploadedFile(nome, dados, content_type="application/pdf")


class ReceberTest(MediaTemporaria, TestCase):
    @classmethod
    def setUpTestData(cls):
        Mundo.montar(cls)

    def test_grava_e_troca_apagando_o_antigo(self):
        with self.captureOnCommitCallbacks(execute=True):
            a = receber_atividades(self.ano, self.lp, "alfa", pdf())
        antigo = a.arquivo
        self.assertTrue(antigo.startswith("atividades/") and antigo.endswith(".pdf"))
        with self.captureOnCommitCallbacks(execute=True):
            b = receber_atividades(self.ano, self.lp, "alfa", pdf(dados=PDF + b"novo"))
        self.assertEqual(a.pk, b.pk)
        self.assertEqual(Atividades.objects.count(), 1)
        self.assertFalse(default_storage.exists(antigo))
        self.assertTrue(default_storage.exists(b.arquivo))

    def test_so_pdf_e_ate_o_limite(self):
        with self.assertRaisesMessage(ValidationError, "precisam ser um arquivo PDF"):
            receber_atividades(self.ano, self.lp, "alfa", pdf("a.pdf", b"\x89PNG\r\n\x1a\n" + b"0" * 32))
        with self.assertRaisesMessage(ValidationError, "maior que 20 MB"):
            receber_atividades(self.ano, self.lp, "alfa", pdf(dados=PDF + b"0" * ATIVIDADES_MAX))
        self.assertFalse(Atividades.objects.exists())

    def test_remover_apaga_o_registro_e_o_arquivo_no_commit(self):
        a = receber_atividades(self.ano, self.lp, "alfa", pdf())
        with self.captureOnCommitCallbacks(execute=True):
            remover_atividades(a)
        self.assertFalse(Atividades.objects.exists())
        self.assertFalse(default_storage.exists(a.arquivo))

    def test_da_revista_so_o_do_seu_componente(self):
        receber_atividades(self.ano, self.lp, "outras", pdf())
        receber_atividades(self.ano, self.mt, "alfa", pdf())
        self.assertEqual(list(atividades_da_revista(self.go["LP"])), ["outras"])


class TelaTest(MediaTemporaria, TestCase):
    @classmethod
    def setUpTestData(cls):
        Mundo.montar(cls)

    def url(self, cc="LP", tipo="alfa", baixar=False, remover=False):
        nome = "ui_templates_atividades" + ("_baixar" if baixar else "_remover" if remover else "")
        return reverse(nome, args=[2026, cc, tipo])

    def lista(self):
        return self.client.get(reverse("ui_templates", args=[2026]) + "?aba=F2").content.decode()

    def test_ciclo_inteiro_enviar_baixar_trocar_remover_e_volta_ao_vazio(self):  # D-309
        self.client.force_login(usuario("ped", "Pedagógica"))
        html = self.lista()
        self.assertNotIn('data-abrir="dlg-atividades-LP-alfa"', html)  # vazio: só a área de enviar
        self.assertIn("<strong>Enviar o PDF</strong>", html)
        self.client.post(self.url(), {"arquivo": pdf()})
        html = self.lista()
        self.assertIn('Remover PDF<span class="sr-only"> de LP Alfa</span>', html)
        self.assertIn("<strong>Trocar o PDF</strong>", html)
        self.assertIn("atividades-lp-alfa.pdf", html)
        self.assertIn('data-abrir="dlg-atividades-LP-alfa"', html)
        self.assertIn('<dialog class="dialogo" id="dlg-atividades-LP-alfa"', html)
        self.assertIn(f'action="{self.url(remover=True)}"', html)
        self.assertNotIn("dlg-atividades-LP-outras", html)  # só a célula com PDF
        self.client.post(self.url(), {"arquivo": pdf(dados=PDF + b"v2")})  # trocar
        self.assertEqual(b"".join(self.client.get(self.url(baixar=True)).streaming_content), PDF + b"v2")
        with self.captureOnCommitCallbacks(execute=True):
            r = self.client.post(self.url(remover=True), follow=True)
        self.assertContains(r, "PDF das atividades de LP – Alfa removido.")
        self.assertFalse(Atividades.objects.exists())
        self.assertEqual(self.client.get(self.url(baixar=True)).status_code, 404)
        self.assertContains(r, ">Sem PDF<", count=4)

    def test_remover_sem_permissao_403_sem_pdf_404_e_get_405(self):
        receber_atividades(self.ano, self.lp, "alfa", pdf())
        self.client.force_login(usuario("imp", "Impresso"))
        self.assertEqual(self.client.post(self.url(remover=True)).status_code, 403)
        html = self.lista()
        self.assertNotIn("Remover PDF", html)  # só leitura: sem remover nem enviar
        self.assertNotIn('type="file"', html)
        self.assertIn("Baixar", html.replace("(baixar)", "Baixar"))
        self.client.force_login(usuario("ped", "Pedagógica"))
        self.assertEqual(self.client.get(self.url(remover=True)).status_code, 405)
        self.assertEqual(self.client.post(self.url(tipo="outras", remover=True)).status_code, 404)
        self.assertEqual(self.client.post(self.url(tipo="beta", remover=True)).status_code, 404)
        self.assertEqual(Atividades.objects.count(), 1)

    def test_pedagogica_envia_e_baixa(self):
        self.client.force_login(usuario("ped", "Pedagógica"))
        r = self.client.get(reverse("ui_templates", args=[2026]) + "?aba=F2")
        self.assertContains(r, 'id="atividades"')
        self.assertContains(r, ">Sem PDF<", count=4)  # LP e MT × Alfa e Outras Etapas
        r = self.client.post(self.url(), {"arquivo": pdf()})
        self.assertRedirects(r, reverse("ui_templates", args=[2026]) + "?aba=F2#atividades", fetch_redirect_response=False)
        self.assertEqual(Atividades.objects.get().tipo, "alfa")
        r = self.client.get(self.url(baixar=True))
        self.assertEqual(r["Content-Type"], "application/pdf")
        self.assertIn('attachment; filename="atividades-lp-alfa.pdf"', r["Content-Disposition"])
        self.assertEqual(b"".join(r.streaming_content), PDF)

    def test_arquivo_sumido_do_storage_mostra_erro_e_pede_novo_envio(self):
        a = receber_atividades(self.ano, self.lp, "alfa", pdf())
        default_storage.delete(a.arquivo)
        self.client.force_login(usuario("ped", "Pedagógica"))
        html = self.lista()
        self.assertIn(">Arquivo sumiu<", html)
        self.assertIn("O PDF registrado não está no servidor.", html)

    def test_aba_f1_sem_o_bloco(self):
        self.client.force_login(usuario("ped", "Pedagógica"))
        self.assertNotContains(self.client.get(reverse("ui_templates", args=[2026])), 'id="atividades"')

    def test_erro_volta_como_mensagem_e_nada_grava(self):
        self.client.force_login(usuario("ped", "Pedagógica"))
        r = self.client.post(self.url(), {"arquivo": pdf("a.pdf", b"texto")}, follow=True)
        self.assertContains(r, "LP – Alfa: As atividades precisam ser um arquivo PDF.")
        self.assertFalse(Atividades.objects.exists())

    def test_sem_permissao_de_gravar_403_e_tipo_ou_componente_errado_404(self):
        self.client.force_login(usuario("imp", "Impresso"))
        self.assertEqual(self.client.post(self.url(), {"arquivo": pdf()}).status_code, 403)
        self.client.force_login(usuario("ped", "Pedagógica"))
        self.assertEqual(self.client.post(self.url(tipo="beta"), {"arquivo": pdf()}).status_code, 404)
        self.assertEqual(self.client.post(self.url(cc="XX"), {"arquivo": pdf()}).status_code, 404)
        self.assertEqual(self.client.get(self.url(baixar=True)).status_code, 404)  # ainda sem PDF


class PaginaTest(MediaTemporaria, TestCase):
    @classmethod
    def setUpTestData(cls):
        Mundo.montar(cls)
        TemplateVersao.objects.create(template=cls.templates["LP", "F2"], numero=2, texto=F2)

    def setUp(self):
        super().setUp()
        self.client.force_login(usuario("ped", "Pedagógica"))
        self.rev = self.go["LP"]
        dois_infograficos(self.rev)

    def pagina(self, tipo):
        return self.client.get(reverse("preview_f2", args=[self.rev.pk, tipo])).content.decode()

    def test_link_so_na_pagina_do_tipo_com_pdf(self):
        receber_atividades(self.ano, self.lp, "outras", pdf())
        url = reverse("preview_atividades", args=[self.rev.pk, "outras"])
        self.assertIn(f'<a href="{url}" download>Acesse aqui as atividades</a>', self.pagina("outras"))
        self.assertNotIn("Acesse aqui as atividades", self.pagina("alfa"))
        r = self.client.get(url)
        self.assertIn('filename="atividades-outras.pdf"', r["Content-Disposition"])
        self.assertEqual(self.client.get(reverse("preview_atividades", args=[self.rev.pk, "alfa"])).status_code, 404)

    def test_link_do_template_pendente_sai_em_vermelho(self):
        TemplateVersao.objects.create(
            template=self.templates["LP", "F2"], numero=3,
            texto=F2.replace("Use o template.", "[**Acesse aqui** o template.](#pendente) [Site](https://caed.example/x)"),
        )  # fmt: skip
        html = self.pagina("outras")
        self.assertIn('<span class="variavel-vazia"><strong>Acesse aqui</strong> o template.</span>', html)
        self.assertIn('<a href="https://caed.example/x" target="_blank" rel="noopener">Site</a>', html)
