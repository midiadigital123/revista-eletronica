"""Anos fora do admin (/ui/anos/, S3 de D-190): mesma regra do `AnoAdmin.abrir_view`."""

from django.urls import reverse

from nucleo.models import Ano, Matriz
from nucleo.tests.test_admin_cadastro import Base
from nucleo.tests.test_resolver import usuario


class AnosUiTest(Base):
    url = reverse("ui_anos")

    def test_pedagogica_abre_o_proximo_ano(self):
        self.client.force_login(usuario("ped", "Pedagógica"))
        resp = self.client.get(self.url)
        self.assertContains(resp, "O próximo que pode ser aberto é 2027")
        self.assertNotContains(resp, 'value="2027"')  # o usuário digita (não há desfazer)
        self.assertContains(self.client.get(reverse("cortes", args=[2026])), self.url)  # seletor de anos
        resp = self.client.post(self.url, {"ano": 2027}, follow=True)
        self.assertRedirects(resp, self.url)
        self.assertContains(resp, "Ano 2027 aberto a partir de 2026.")
        self.assertTrue(Matriz.objects.filter(ano__ano=2027, duplicada_de=self.matriz).exists())

    def test_fora_de_sequencia_nao_grava(self):
        self.client.force_login(usuario("md", "Mídias Digitais"))
        for ano, erro in ((2029, "próximo ano que pode ser aberto é 2027"), (2026, "2026 já está aberto"), ("x", "número")):
            with self.subTest(ano):
                self.assertContains(self.client.post(self.url, {"ano": ano}), erro)
        self.assertEqual(list(Ano.objects.values_list("ano", flat=True)), [2026])

    def test_impresso_so_le(self):
        self.client.force_login(usuario("imp", "Impresso"))
        resp = self.client.get(self.url)
        self.assertContains(resp, "2026")
        self.assertNotContains(resp, "Abrir ano")
        self.assertNotContains(self.client.get(reverse("cortes", args=[2026])), self.url)
        self.assertEqual(self.client.post(self.url, {"ano": 2027}).status_code, 403)
        self.assertFalse(Ano.objects.filter(ano=2027).exists())
        self.client.force_login(usuario("nada"))  # sem view_ano
        self.assertEqual(self.client.get(self.url).status_code, 403)
