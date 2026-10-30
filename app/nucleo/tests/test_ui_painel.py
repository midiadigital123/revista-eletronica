"""Painel da temporada B (/ui/painel/<ano>/, T23): critérios de aceite de docs/telas/fichas/painel.md."""

from django.urls import reverse

from nucleo.models import Ano
from nucleo.tests.test_admin_projeto import Base
from nucleo.tests.test_painel import completar
from nucleo.tests.test_resolver import usuario


class PainelUiTest(Base):
    url = reverse("ui_painel", args=[2026])

    def pks(self, r):
        return [x["revista"].pk for x in r.context["linhas"]]

    def test_get_pedagogica_ve_tudo_e_pode_validar(self):
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "ui/base.html")
        self.assertTemplateUsed(r, "ui/painel/painel.html")
        self.assertEqual(len(r.context["linhas"]), 4)  # GO LP/MT e PE LP/MT
        rev = self.go["LP"]
        self.assertContains(r, f'name="revista" value="{rev.pk}"')
        self.assertContains(r, "Validar selecionadas")
        self.assertContains(r, f'action="{reverse("painel_validar", args=[2026])}"')  # ui_validar ainda não existe
        self.assertContains(r, f'href="{reverse("preview", args=[rev.pk])}" target="_blank"')
        self.assertContains(r, reverse("impresso", args=[rev.pk]))  # coluna Impresso leva à tela do impresso
        # Próxima tarefa da Pedagógica: revistas sem "Validado", com link para o filtro.
        self.assertContains(r, "<strong>4</strong> revista(s) sem “Validado” nesta versão")
        self.assertContains(r, 'href="?falta=validado"')
        self.assertContains(r, reverse("cortes", args=[2026]))
        self.assertNotContains(r, "Só leitura")

    def test_celula_falta_tem_dica_e_link(self):
        completar(self.go["LP"])
        r = self.client.get(self.url)
        mt = self.go["MT"]
        link = reverse("admin:nucleo_revista_change", args=[mt.pk])
        self.assertContains(r, f'<a class="status status-falta" href="{link}" title="Falta o SVG do F2.">')
        # Cabeçalho: quantas faltam por coluna (SVG: GO MT, PE LP, PE MT).
        svg = next(c for c in r.context["colunas"] if c["chave"] == "svg")
        self.assertEqual((svg["faltam"], svg["url"]), (3, "?falta=svg"))

    def test_so_leitura_impresso(self):
        self.client.force_login(self.imp)
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Só leitura: seu perfil vê o painel, mas não valida revistas.")
        self.assertNotContains(r, 'name="revista"')
        self.assertNotContains(r, "Validar selecionadas")
        self.assertContains(r, "revista(s) para atualizar no impresso")
        self.assertContains(r, 'href="?falta=impresso"')
        self.assertEqual(self.client.post(self.url).status_code, 405)  # o painel não grava

    def test_permissoes(self):
        self.client.force_login(usuario("nada"))  # sem view_revista
        self.assertEqual(self.client.get(self.url).status_code, 403)
        self.client.logout()
        self.assertRedirects(self.client.get(self.url), f"{reverse('admin:login')}?next={self.url}", fetch_redirect_response=False)
        self.client.force_login(self.ped)
        self.assertEqual(self.client.get(reverse("ui_painel", args=[1999])).status_code, 404)

    def test_filtros_iguais_ao_admin(self):
        go = self.go["LP"].projeto.parceiro_ano.parceiro_id
        self.assertEqual(len(self.client.get(self.url, {"falta": "svg"}).context["linhas"]), 4)
        completar(self.go["LP"])
        self.assertEqual(len(self.client.get(self.url, {"falta": "svg"}).context["linhas"]), 3)
        r = self.client.get(self.url, {"falta": "svg", "parceiro": go})
        self.assertEqual(self.pks(r), [self.go["MT"].pk])
        self.assertContains(r, f'<option value="{go}" selected>')
        # Falta e parceiro inválidos são ignorados, como no admin.
        self.assertEqual(len(self.client.get(self.url, {"falta": "x", "parceiro": "abc"}).context["linhas"]), 4)
        # Template: só as que usam; o link da coluna mantém o recorte.
        tpl = self.templates["LP", "F2"]
        r = self.client.get(self.url, {"template": tpl.pk})
        self.assertEqual(sorted(self.pks(r)), sorted([self.go["LP"].pk, self.pe["LP"].pk]))
        self.assertContains(r, f'name="template" value="{tpl.pk}"')
        self.assertEqual(next(c for c in r.context["colunas"] if c["chave"] == "svg")["url"], f"?template={tpl.pk}&falta=svg")

    def test_htmx_devolve_so_o_corpo(self):
        r = self.client.get(self.url, {"falta": "capa"}, headers={"HX-Request": "true"})
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "ui/parciais/painel_corpo.html")
        self.assertTemplateNotUsed(r, "ui/base.html")
        self.assertNotContains(r, "<html")
        self.assertContains(r, 'class="tabela painel-tabela"')

    def test_estados_vazios(self):
        completar(self.go["LP"])
        r = self.client.get(self.url, {"falta": "capa", "parceiro": self.go["LP"].projeto.parceiro_ano.parceiro_id})
        self.assertEqual(len(r.context["linhas"]), 1)
        completar(self.go["MT"])
        r = self.client.get(self.url, {"falta": "capa", "parceiro": self.go["LP"].projeto.parceiro_ano.parceiro_id})
        self.assertContains(r, "Nenhuma revista com esse filtro")
        self.assertContains(r, "Limpar filtro de falta")
        Ano.objects.create(ano=2027)
        r = self.client.get(reverse("ui_painel", args=[2027]))
        self.assertContains(r, "Nenhuma revista ativa neste ano")
        self.assertContains(r, reverse("cortes", args=[2027]))
        self.assertContains(r, f'href="{reverse("ui_painel", args=[2026])}"')  # seletor de ano
