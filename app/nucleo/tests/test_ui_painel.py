"""Painel da temporada B (/painel/<ano>/, T23): critérios de aceite de docs/telas/fichas/painel.md."""

from unittest.mock import patch

from django.urls import reverse

from nucleo.models import Ano
from nucleo.tests.test_admin_projeto import Base
from nucleo.tests.test_painel import completar
from nucleo.tests.test_resolver import usuario


class PainelUiTest(Base):
    url = reverse("painel", args=[2026])

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
        self.assertContains(r, f'action="{reverse("ui_validar", args=[2026])}"')  # lote vai à tela B de validar
        self.assertContains(r, f'href="{reverse("preview", args=[rev.pk])}" target="_blank"')
        self.assertContains(r, f'href="{reverse("ui_revista_editar", args=[2026, rev.pk])}"')  # o nome abre a revista B
        self.assertContains(r, f'{reverse("ui_impresso", args=[2026])}?revista={rev.pk}')  # coluna Impresso leva à tela B
        self.assertContains(r, 'href="?falta=validado"')  # contador da coluna Validado
        self.assertNotContains(r, "Só leitura")

    def test_celula_falta_tem_dica_e_link(self):
        completar(self.go["LP"])
        r = self.client.get(self.url)
        mt = self.go["MT"]
        link = reverse("ui_revista_editar", args=[2026, mt.pk])
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
        self.assertContains(r, 'href="?falta=impresso"')
        self.assertEqual(self.client.post(self.url).status_code, 405)  # o painel não grava

    def test_permissoes(self):
        self.client.force_login(usuario("nada"))  # sem view_revista
        self.assertEqual(self.client.get(self.url).status_code, 403)
        self.client.logout()
        self.assertRedirects(self.client.get(self.url), f"{reverse('admin:login')}?next={self.url}", fetch_redirect_response=False)
        self.client.force_login(self.ped)
        self.assertEqual(self.client.get(reverse("painel", args=[1999])).status_code, 404)

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
        r = self.client.get(self.url, {"template": tpl.pk, "falta": "svg", "parceiro": go})
        self.assertContains(r, f'href="?falta=svg&amp;parceiro={go}" hx-get=')  # Limpar só tira o template
        r = self.client.get(self.url, {"template": tpl.pk})
        self.assertEqual(next(c for c in r.context["colunas"] if c["chave"] == "svg")["url"], f"?template={tpl.pk}&falta=svg")

    def test_htmx_devolve_so_o_corpo(self):
        r = self.client.get(self.url, {"falta": "capa"}, headers={"HX-Request": "true"})
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "ui/parciais/painel_corpo.html")
        self.assertTemplateNotUsed(r, "ui/base.html")
        self.assertNotContains(r, "<html")
        self.assertContains(r, 'class="tabela painel-tabela"')
        self.assertIn("HX-Request", r["Vary"])  # o cache do navegador não troca página por fragmento
        # Restauração de histórico do htmx (Voltar com o cache vazio): página inteira.
        r = self.client.get(self.url, {"falta": "capa"}, headers={"HX-Request": "true", "HX-History-Restore-Request": "true"})
        self.assertTemplateUsed(r, "ui/base.html")
        self.assertIn("HX-Request", r["Vary"])

    def test_sem_card_proxima_tarefa(self):
        from django.contrib.auth import get_user_model

        self.client.force_login(get_user_model().objects.create_superuser("raiz", "r@x.br", "x"))
        r = self.client.get(self.url)
        self.assertNotContains(r, "Próxima tarefa")
        self.assertNotContains(r, 'aria-label="Montagem"')  # atalhos ficam no menu
        self.assertNotContains(r, "painel-tarefa")
        self.assertTemplateNotUsed(r, "ui/_componentes/painel_tarefa.html")

    def test_agrupa_por_parceiro(self):
        completar(self.go["LP"])
        # Completa de verdade pede Validado e impresso; aqui só a conta do grupo importa.
        patch("nucleo.urls.ui_painel.completa", lambda x: x["revista"] == self.go["LP"]).start()
        self.addCleanup(patch.stopall)
        r = self.client.get(self.url)
        grupos = r.context["grupos"]
        self.assertEqual([g["parceiro"].nome for g in grupos], ["GO", "PE"])
        self.assertEqual([[x["revista"].componente.codigo for x in g["linhas"]] for g in grupos], [["LP", "MT"], ["LP", "MT"]])
        self.assertEqual([(g["completas"], g["total"]) for g in grupos], [(1, 2), (0, 2)])
        html = r.content.decode()
        self.assertEqual(html.count('class="painel-grupo"'), 2)  # uma linha de grupo por parceiro
        self.assertContains(r, "1 de 2 revistas completas")
        self.assertContains(r, f'href="{reverse("ui_projeto", args=[self.projeto_go.pk])}"')
        # As sublinhas vêm na ordem dos componentes, logo abaixo da linha do grupo.
        go = html.index('data-grupo-linha="%d"' % self.projeto_go.pk)
        lp, mt = (html.index(f'data-revista="{self.go[c].pk}"') for c in ("LP", "MT"))
        self.assertLess(go, lp)
        self.assertLess(lp, mt)
        self.assertLess(mt, html.index('data-grupo-linha="%d"' % self.projeto_pe.pk))
        # Com filtro de falta o grupo mostra só as revistas filtradas, mas a contagem é do parceiro.
        r = self.client.get(self.url, {"falta": "svg"})
        g = r.context["grupos"][0]
        self.assertEqual(([x["revista"] for x in g["linhas"]], g["completas"], g["total"]), ([self.go["MT"]], 1, 2))

    def test_selecao_por_grupo(self):
        r = self.client.get(self.url)
        go = self.projeto_go.pk
        self.assertContains(r, f'data-grupo="{go}" aria-label="Selecionar as revistas de GO"')
        for c in ("LP", "MT"):
            self.assertContains(r, f'name="revista" value="{self.go[c].pk}" data-de="{go}"')
        self.assertContains(r, "Nenhuma selecionada")
        self.client.force_login(self.imp)  # sem validar: nem caixa de grupo
        self.assertNotContains(self.client.get(self.url), "data-grupo=")

    def test_filtro_por_contador(self):
        go = self.go["LP"].projeto.parceiro_ano.parceiro_id
        r = self.client.get(self.url, {"parceiro": go})
        # Resumo: um contador por coluna, link-filtro (HTMX) que mantém o recorte.
        self.assertContains(r, f'href="?parceiro={go}&amp;falta=svg" hx-get="?parceiro={go}&amp;falta=svg"')
        self.assertNotContains(r, "Limpar filtro")
        self.assertNotContains(r, 'id="filtro-falta"')  # o contador substitui o select de falta
        r = self.client.get(self.url, {"parceiro": go, "falta": "svg"})
        self.assertContains(r, 'aria-current="true"')  # contador ativo destacado
        self.assertContains(r, f'href="?parceiro={go}" hx-get="?parceiro={go}"')  # Limpar filtro mantém o parceiro
        self.assertContains(r, "Limpar filtro")
        self.assertContains(r, 'name="falta" value="svg"')  # trocar o parceiro mantém a falta

    def test_estados_vazios(self):
        completar(self.go["LP"])
        r = self.client.get(self.url, {"falta": "capa", "parceiro": self.go["LP"].projeto.parceiro_ano.parceiro_id})
        self.assertEqual(len(r.context["linhas"]), 1)
        completar(self.go["MT"])
        r = self.client.get(self.url, {"falta": "capa", "parceiro": self.go["LP"].projeto.parceiro_ano.parceiro_id})
        self.assertContains(r, "Nenhuma revista com esse filtro")
        self.assertContains(r, "Limpar filtro")
        Ano.objects.create(ano=2027)
        r = self.client.get(reverse("painel", args=[2027]))
        self.assertContains(r, "Nenhuma revista ativa neste ano")
        self.assertContains(r, reverse("cortes", args=[2027]))
        self.assertContains(r, f'href="{reverse("painel", args=[2026])}"')  # seletor de ano
