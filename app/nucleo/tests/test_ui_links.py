"""Links e mensagens das telas B sem admin nem 403 (S1, D-190): toda pendência do painel abre uma
tela B que o perfil vê; "abrir ano" e "cadastrar componentes" só viram link para quem pode."""

import re

from django.test import TestCase
from django.urls import reverse

from nucleo.models import Ano, ParceiroAno
from nucleo.tests.test_admin_projeto import Base
from nucleo.tests.test_resolver import usuario

CELULA = re.compile(r'<td class="painel-cel[^"]*">(.*?)</td>', re.S)
HREF = re.compile(r'href="([^"]+)"')


class PendenciasDoPainelTest(Base):
    def hrefs(self):
        html = self.client.get(reverse("painel", args=[2026])).content.decode()
        return {h.replace("&amp;", "&") for c in CELULA.findall(html) for h in HREF.findall(c)}

    def test_todo_link_de_pendencia_abre_tela_b(self):
        # Sem matriz (GO) e nome padrão (PE): as faltas de Matriz e Variáveis também viram link.
        ParceiroAno.objects.filter(parceiro__nome="GO").update(matriz=None)
        self.projeto_pe.nome = "PE - NOME DO PROJETO"
        self.projeto_pe.save()
        for user in (self.imp, self.ped):
            with self.subTest(user=user.username):
                self.client.force_login(user)
                hrefs = self.hrefs()
                for prefixo in ("/ui/projeto/", "/ui/revista/2026/", "/ui/impresso/2026/?revista="):
                    self.assertTrue(any(h.startswith(prefixo) for h in hrefs), prefixo)
                for h in hrefs:
                    self.assertNotIn("/admin/", h)
                    self.assertEqual(self.client.get(h).status_code, 200, h)


class MensagensSemAnoTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.imp = usuario("imp", "Impresso")
        cls.ped = usuario("ped", "Pedagógica")

    def test_abrir_ano_so_com_permissao(self):
        abrir = reverse("admin:nucleo_ano_changelist")
        for url in (reverse("cortes_inicio"), reverse("ui_revista_inicio")):
            self.client.force_login(self.imp)
            r = self.client.get(url)
            self.assertContains(r, "Peça a um administrador para abrir o ano.")
            self.assertNotContains(r, abrir)
            self.client.force_login(self.ped)
            r = self.client.get(url)
            self.assertContains(r, abrir)
            self.assertNotContains(r, "Peça a um administrador")

    def test_componentes_so_com_permissao(self):
        Ano.objects.create(ano=2030)  # sem componentes
        url = reverse("ui_lotes_template", args=[2030])
        componentes = reverse("admin:nucleo_componente_changelist")
        self.client.force_login(self.imp)
        self.assertNotContains(self.client.get(url), componentes)
        self.client.force_login(self.ped)
        self.assertContains(self.client.get(url), componentes)

    def test_lotes_inicio_vai_ao_ano_mais_recente(self):
        self.client.force_login(self.imp)
        self.assertRedirects(self.client.get(reverse("ui_lotes_inicio")), "/", fetch_redirect_response=False)
        Ano.objects.create(ano=2030)
        r = self.client.get(reverse("ui_lotes_inicio"))
        self.assertRedirects(r, reverse("ui_lotes_matriz", args=[2030]), fetch_redirect_response=False)
