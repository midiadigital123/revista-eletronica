"""Links e mensagens das telas B sem admin nem 403 (S1, D-190): toda pendência do painel abre uma
tela B que o perfil vê; "abrir ano" e "cadastrar componentes" só viram link para quem pode."""

import re

from django.test import TestCase
from django.urls import reverse

from nucleo.models import Ano, Parceiro, ParceiroAno, Projeto
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
        abrir = reverse("ui_anos")
        for url in (reverse("cortes_inicio"), reverse("ui_revista_inicio"), reverse("ui_projeto_inicio")):
            self.client.force_login(self.imp)
            r = self.client.get(url, follow=True)
            self.assertContains(r, "Peça a um administrador para abrir o ano.")
            self.assertNotContains(r, abrir)
            self.client.force_login(self.ped)
            r = self.client.get(url, follow=True)
            self.assertContains(r, abrir)
            self.assertNotContains(r, "Peça a um administrador")

    def test_componentes_so_com_permissao(self):
        ano = Ano.objects.create(ano=2030)  # sem componentes; um parceiro para a Lista ter a barra
        ParceiroAno.objects.create(parceiro=Parceiro.objects.create(nome="GO"), ano=ano)
        url = reverse("ui_projeto_lista", args=[2030])  # U7a: "Atribuir template…" da Lista
        componentes = f'<a class="link" href="{reverse("ui_ano", args=[2030])}">cadastre os componentes</a>'
        self.client.force_login(self.imp)
        self.assertNotContains(self.client.get(url), componentes)
        self.client.force_login(self.ped)
        self.assertContains(self.client.get(url), componentes)

    def test_lotes_inicio_vai_ao_ano_mais_recente(self):
        self.client.force_login(self.imp)
        self.assertRedirects(self.client.get(reverse("ui_lotes_inicio")), "/", fetch_redirect_response=False)
        Ano.objects.create(ano=2030)
        r = self.client.get(reverse("ui_lotes_inicio"))
        self.assertRedirects(r, reverse("ui_projeto_lista", args=[2030]), fetch_redirect_response=False)


SELETOR = re.compile(r'<div[^>]*id="seletor-ano"[^>]*>(.*?)</div>', re.S)


class SeletorAnoTest(Base):
    """U6: o seletor do cabeçalho troca o ano sem perder a tela (Foco da revisão, item 5)."""

    def seletor(self, url):
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200, url)
        return SELETOR.search(r.content.decode()).group(1).replace("&amp;", "&")

    def test_troca_de_ano_mantem_rota_e_query(self):
        Ano.objects.create(ano=2025)
        html = self.seletor("/painel/2026/?falta=validado")
        self.assertIn('href="/painel/2025/?falta=validado"', html)
        self.assertIn('href="/painel/2026/?falta=validado" aria-current="page"', html)
        self.assertEqual(self.client.session["ano"], 2026)

    def test_troca_em_projeto_vai_ao_mesmo_parceiro(self):
        Ano.objects.create(ano=2025)  # GO sem projeto em 2025: vai à lista
        a27 = Ano.objects.create(ano=2027)
        go = Parceiro.objects.get(nome="GO")
        p27 = Projeto.objects.create(parceiro_ano=ParceiroAno.objects.create(parceiro=go, ano=a27), ano=a27, nome="GO 27")
        html = self.seletor(f"/ui/projeto/{self.projeto_go.pk}/")
        self.assertIn(f'href="/ui/projeto/{p27.pk}/"', html)
        self.assertIn('href="/ui/projeto/ano/2025/"', html)
        for h in HREF.findall(html):
            self.assertEqual(self.client.get(h).status_code, 200, h)

    def test_abrir_ano_so_com_permissao(self):
        abrir = f'href="{reverse("ui_anos")}"'
        self.client.force_login(self.imp)
        html = self.seletor("/painel/2026/")
        self.assertNotIn(abrir, html)
        self.assertNotIn("Abrir novo ano", html)
        self.client.force_login(self.ped)
        html = self.seletor("/painel/2026/")
        self.assertIn(abrir, html)
        self.assertIn("Abrir novo ano", html)
        self.assertIn('href="/ui/anos/2026/"', html)  # Configurar 2026

    def test_inicio_usa_o_ano_da_sessao(self):
        Ano.objects.create(ano=2027)
        self.client.get(f"/ui/projeto/{self.projeto_go.pk}/")  # o ano do objeto da página vai para a sessão
        self.assertEqual(self.client.session["ano"], 2026)
        for nome, destino in [("cortes_inicio", "/ui/projeto/ano/2026/cortes/"), ("ui_projeto_inicio", "/ui/projeto/ano/2026/"),
                              ("ui_matriz_inicio", "/ui/matriz/2026/"), ("ui_templates_inicio", "/ui/templates/2026/"),
                              ("ui_revista_inicio", "/ui/projeto/ano/2026/"), ("ui_variaveis_inicio", "/ui/projeto/ano/2026/variaveis/"),
                              ("ui_lotes_inicio", "/ui/projeto/ano/2026/"), ("ui_impresso", "/ui/impresso/2026/")]:
            with self.subTest(nome=nome):
                self.assertRedirects(self.client.get(reverse(nome)), destino, fetch_redirect_response=False)
