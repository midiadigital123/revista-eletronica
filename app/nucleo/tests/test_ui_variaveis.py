"""Planilha de variáveis fora do admin (/ui/variaveis/<ano>/, T17 opção B): critérios de aceite da ficha."""

from django.contrib.auth import get_user_model
from django.urls import reverse

from nucleo.models import Ano, ParceiroAno, Projeto
from nucleo.tests.test_admin_projeto import VARS, Base, mensagens


def dados(resposta):
    """POST da planilha com os valores da carga (como o navegador mandaria sem mexer)."""
    projetos = [l["form"].instance for l in resposta.context["linhas"]]
    saida = {"form-TOTAL_FORMS": len(projetos), "form-INITIAL_FORMS": len(projetos), "form-MIN_NUM_FORMS": 0, "form-MAX_NUM_FORMS": 1000}
    for i, p in enumerate(projetos):
        saida[f"form-{i}-id"] = p.pk
        for nome in VARS:
            saida[f"form-{i}-{nome}"] = saida[f"initial-form-{i}-{nome}"] = getattr(p, nome)
    return saida


class VariaveisUiTest(Base):
    url = reverse("ui_variaveis", args=[2026])

    def test_get_com_permissao(self):
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "ui/base.html")
        self.assertEqual([l["form"].instance for l in r.context["linhas"]], [self.projeto_go, self.projeto_pe])
        self.assertContains(r, "Salvar variáveis")
        self.assertContains(r, "Copiar de 2025", count=2)
        self.assertContains(r, 'placeholder="padrão do ano: Padrão 02"', count=2)  # D-175
        self.assertContains(r, "escala do F1 (nome do padrão)", count=5)
        self.assertContains(r, "LP F2 Padrão")  # onde aparece
        self.assertContains(r, 'aria-label="Projeto GO ISSN"')
        self.assertNotContains(r, "disabled")
        self.assertRedirects(self.client.get(reverse("ui_variaveis_inicio")), self.url)

    def test_so_leitura_sem_permissao(self):
        self.client.force_login(self.imp)
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Só leitura: seu perfil vê as variáveis")
        self.assertContains(r, "disabled")
        self.assertNotContains(r, "Salvar variáveis")
        self.assertNotContains(r, "Copiar de 2025")
        self.assertEqual(self.client.post(self.url, dados(r)).status_code, 403)
        copiar = reverse("ui_variaveis_copiar", args=[2026, self.projeto_go.pk])
        self.assertEqual(self.client.post(copiar).status_code, 403)
        self.client.force_login(get_user_model().objects.create(username="nada", is_staff=True))
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_post_grava_so_alteradas_e_pula_travado(self):
        d = dados(self.client.get(self.url))
        d["form-0-adjetivo_patrio_singular_masculino"] = "goiano"  # GO
        d["form-1-adjetivo_patrio_singular_masculino"] = "pernambucano"  # PE, travado
        Projeto.objects.filter(pk=self.projeto_go.pk).update(adjetivo_patrio_singular_feminino="goiana")  # outra pessoa
        self.travar(self.projeto_pe)
        r = self.client.post(self.url, d, follow=True)
        self.assertRedirects(r, self.url)
        go = Projeto.objects.get(pk=self.projeto_go.pk)
        self.assertEqual((go.adjetivo_patrio_singular_masculino, go.adjetivo_patrio_singular_feminino), ("goiano", "goiana"))
        self.assertEqual(Projeto.objects.get(pk=self.projeto_pe.pk).adjetivo_patrio_singular_masculino, "")
        self.assertEqual(mensagens(r), ["Variáveis salvas em 1 projeto(s).", "Pulados: Projeto PE (projeto em edição por outro)."])

    def test_erro_marca_a_celula_e_nada_grava(self):
        d = dados(self.client.get(self.url))
        d["form-0-adjetivo_patrio_singular_masculino"] = "x" * 201
        d["form-1-adjetivo_patrio_singular_masculino"] = "pernambucano"
        r = self.client.post(self.url, d)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Nada foi gravado: corrija os erros marcados.")
        self.assertContains(r, f'<ul id="erros-{self.projeto_go.pk}"><li>GO: Adjetivo pátrio masc. sing.: ')
        self.assertContains(r, 'aria-invalid="true"', count=1)
        self.assertContains(r, "x" * 201)  # o digitado continua na célula
        self.assertEqual(Projeto.objects.get(pk=self.projeto_pe.pk).adjetivo_patrio_singular_masculino, "")

    def test_copiar_htmx_devolve_a_linha(self):
        ano25 = Ano.objects.create(ano=2025)
        pa = ParceiroAno.objects.create(parceiro=self.projeto_go.parceiro_ano.parceiro, ano=ano25)
        Projeto.objects.create(parceiro_ano=pa, ano=ano25, nome="GO 2025", issn="1234-5678", adjetivo_patrio_plural_masculino="velho")
        url = reverse("ui_variaveis_copiar", args=[2026, self.projeto_go.pk]) + "?i=0"
        r = self.client.post(url, headers={"HX-Request": "true"})
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "ui/parciais/variaveis_linha.html")
        self.assertTemplateNotUsed(r, "ui/base.html")
        self.assertContains(r, f'<tbody id="projeto-{self.projeto_go.pk}"')
        self.assertContains(r, 'name="form-0-issn" value="1234-5678"')
        self.assertContains(r, 'name="initial-form-0-issn" value="1234-5678"')  # o original novo
        self.assertContains(r, 'hx-swap-oob="true"')
        self.assertContains(r, "Projeto GO: copiado de 2025: issn.")
        p = Projeto.objects.get(pk=self.projeto_go.pk)
        self.assertEqual((p.issn, p.adjetivo_patrio_plural_masculino), ("1234-5678", "goianos"))  # só vazias

    def test_copiar_sem_js_volta_a_pagina(self):
        url = reverse("ui_variaveis_copiar", args=[2026, self.projeto_pe.pk])
        r = self.client.post(url, follow=True)
        self.assertRedirects(r, self.url)
        self.assertIn("Projeto PE: não há projeto do parceiro em 2025; nada mudou.", mensagens(r))

    def test_copiar_travado_e_arquivado(self):
        url = reverse("ui_variaveis_copiar", args=[2026, self.projeto_go.pk])
        self.travar(self.projeto_go)
        r = self.client.post(url, follow=True)
        self.assertIn("Projeto GO: não copiado (projeto em edição por outro).", mensagens(r))
        Projeto.objects.filter(pk=self.projeto_go.pk).update(arquivado_em="2026-01-01T00:00:00Z")
        r = self.client.post(url + "?i=0", headers={"HX-Request": "true"})
        self.assertEqual(r["HX-Refresh"], "true")

    def test_anonimo_vai_para_o_login(self):
        self.client.logout()
        r = self.client.get(self.url)
        self.assertRedirects(r, f"{reverse('admin:login')}?next={self.url}", fetch_redirect_response=False)

    def test_ano_sem_projetos_mostra_vazio(self):
        Ano.objects.create(ano=2030)
        r = self.client.get(reverse("ui_variaveis", args=[2030]))
        self.assertContains(r, "Nenhum projeto ativo neste ano")
        self.assertContains(r, reverse("cortes", args=[2030]))
        self.assertNotContains(r, "Salvar variáveis")
