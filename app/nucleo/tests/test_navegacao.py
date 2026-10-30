"""Navegação (rascunho de UI, itens 1, 3 e 4): links do preview, Painel como entrada, links de T12."""

import re

from django.test import TestCase
from django.urls import reverse

from nucleo.models import Revista
from nucleo.servicos.cascata import gravar_cortes
from nucleo.tests.test_admin_projeto import Base
from nucleo.tests.test_resolver import usuario


class PreviewLinkTest(Base):
    def test_revista_lista_e_painel(self):
        rev = self.go["LP"]
        link = f'href="/preview/{rev.pk}/" target="_blank" rel="noopener"'
        self.assertContains(self.client.get(reverse("admin:nucleo_revista_change", args=[rev.pk])), link)
        lista = self.client.get(reverse("admin:nucleo_revista_changelist"))
        self.assertContains(lista, "column-preview")
        self.assertContains(lista, link)
        painel = self.client.get(reverse("painel", args=[2026]))
        for l in painel.context["linhas"]:
            self.assertContains(painel, f'href="/preview/{l["revista"].pk}/" target="_blank"')

    def test_arquivada_diz_versao_arquivada(self):
        mt = self.go["MT"]
        pa = mt.projeto.parceiro_ano  # sem a MT nos cortes, a cascata arquiva e fotografa (D-117)
        gravar_cortes(pa, [(self.e5, self.lp, [100, 200, 250, 300]), (self.e9, self.lp, [100, 200, 250, 300])], self.usuario)
        self.assertIsNotNone(Revista.objects.get(pk=mt.pk).arquivada_em)
        self.assertContains(self.client.get(reverse("admin:nucleo_revista_change", args=[mt.pk])), "Abrir preview (versão arquivada)")
        self.assertContains(self.client.get(reverse("admin:nucleo_revista_changelist")), "versão arquivada ↗")

    def test_impresso_ve_o_link_e_abre(self):
        self.client.force_login(self.imp)
        rev = self.go["LP"]
        self.assertContains(self.client.get(reverse("admin:nucleo_revista_change", args=[rev.pk])), f'href="/preview/{rev.pk}/"')
        self.assertEqual(self.client.get(reverse("preview", args=[rev.pk])).status_code, 200)


class EntradaTest(Base):
    def test_raiz_vai_ao_painel_do_maior_ano(self):
        self.assertRedirects(self.client.get("/"), "/painel/2026/")

    def test_temporada_por_permissao(self):
        r = self.client.get(reverse("admin:index"))
        self.assertContains(r, "Temporada 2026")
        self.assertContains(r, 'href="/painel/2026/?falta=validado">Validar no Painel')
        for texto in ("Cortes", "Variáveis", "Escolher matriz", "Escolher template F1/F2"):
            self.assertContains(r, f">{texto}</a>")
        self.assertNotContains(r, "Revistas para atualizar no impresso")
        self.assertContains(r, "Parceiros")  # a lista padrão continua

        self.client.force_login(self.imp)
        r = self.client.get(reverse("admin:index"))
        self.assertContains(r, 'href="/painel/2026/?falta=impresso">Revistas para atualizar no impresso')
        self.assertNotContains(r, "Escolher matriz")
        self.assertNotContains(r, "Validar no Painel")

    def test_painel_no_topo_de_todas_as_paginas(self):
        url = reverse("admin:nucleo_parceiro_changelist")
        topo = re.search(r'<div id="user-tools">.*?</div>', self.client.get(url).content.decode(), re.S).group()
        self.assertIn('<a href="/painel/2026/">Painel 2026</a>', topo)
        # O painel é a tela B: a navegação dela marca o Painel.
        self.assertContains(self.client.get(reverse("painel", args=[2026])), 'href="/painel/2026/" aria-current="page">Painel</a>')


class SemAnoTest(TestCase):
    def test_raiz_vai_ao_admin_e_indice_avisa(self):
        self.client.force_login(usuario("ped", "Pedagógica"))
        self.assertRedirects(self.client.get("/"), "/admin/")
        r = self.client.get("/admin/")
        self.assertContains(r, "Nenhum ano aberto. Abra o primeiro ano em")
        self.assertNotContains(r, ">Painel ")


class TemplatesLinksTest(Base):
    def test_usado_por_filtra_o_painel(self):
        tpl = self.templates["LP", "F2"]  # GO e PE usam; as MT não
        r = self.client.get("/admin/nucleo/template/?fasciculo__exact=F2")
        href = re.search(rf'href="([^"]*template={tpl.pk})">usado por 2 ', r.content.decode()).group(1)
        painel = self.client.get(href.replace("&amp;", "&"))
        self.assertEqual({l["revista"].pk for l in painel.context["linhas"]}, {self.go["LP"].pk, self.pe["LP"].pk})
        self.assertContains(painel, f"LP · {tpl}")
        self.assertContains(painel, '<a class="link" href="?"')  # Limpar o template
        self.assertContains(painel, f'<input type="hidden" name="template" value="{tpl.pk}">')  # trocar o parceiro mantém
        for invalido in ("abc", "999999"):
            self.assertEqual(len(self.client.get(f"/painel/2026/?template={invalido}").context["linhas"]), 4)

    def test_aba_variaveis_abre_a_planilha(self):
        abas = dict((t, u) for t, u, _ in self.client.get("/admin/nucleo/template/").context["abas"])
        self.assertEqual(abas["Variáveis"], reverse("admin:nucleo_projeto_variaveis"))
        abas = dict((t, u) for t, u, _ in self.client.get(f"/admin/nucleo/template/?ano__id__exact={self.ano.pk}").context["abas"])
        self.assertEqual(abas["Variáveis"], "/admin/nucleo/projeto/variaveis/?ano=2026")
