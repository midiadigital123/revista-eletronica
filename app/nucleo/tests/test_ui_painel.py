"""Painel da temporada B (/painel/<ano>/, T23): critérios de aceite de docs/telas/fichas/painel.md."""

from unittest.mock import patch

from django.db import transaction
from django.urls import reverse

from nucleo.models import Ano, Matriz, MatrizEtapaCC, ParceiroAno
from nucleo.servicos import validacao
from nucleo.servicos.resolver import carregar, hash_validado
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
        self.assertContains(r, 'hx-get="?falta=validado"')  # contador da coluna Validado
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
        self.assertContains(r, 'hx-get="?falta=impresso"')
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
        self.assertContains(r, f'<option value="{tpl.pk}" selected>')
        r = self.client.get(self.url, {"template": tpl.pk, "falta": "svg", "parceiro": go})
        self.assertEqual(r.context["sem_falta"], f"?parceiro={go}&template={tpl.pk}")  # o contador ativo desliga só a falta
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
        self.assertContains(r, f'aria-pressed="false" hx-get="?parceiro={go}&amp;falta=svg"')
        self.assertNotContains(r, "painel-limpar\"")  # "Limpar filtro" da falta; o "Limpar filtros" geral aparece
        self.assertNotContains(r, 'id="filtro-falta"')  # o contador substitui o select de falta
        r = self.client.get(self.url, {"parceiro": go, "falta": "svg"})
        self.assertContains(r, 'aria-pressed="true"')  # contador ativo destacado
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


class PainelFiltrosTest(Base):
    """Contador que liga e desliga; filtros parceiro, componente, template, matriz e situação."""

    url = reverse("painel", args=[2026])

    def pks(self, **params):
        return sorted(x["revista"].pk for x in self.client.get(self.url, params).context["linhas"])

    def todas(self, *pares):
        return sorted(getattr(self, p)[c].pk for p, c in pares)

    def contador(self, r, chave):
        return next(c for c in r.context["colunas"] if c["chave"] == chave)

    def test_contador_ativo_volta_ao_estado_inicial(self):
        go = self.go["LP"].projeto.parceiro_ano.parceiro_id
        r = self.client.get(self.url, {"parceiro": go, "falta": "svg"})
        svg = self.contador(r, "svg")
        self.assertEqual(svg["url"], r.context["sem_falta"])  # o mesmo que "Limpar filtro"
        self.assertEqual(svg["url"], f"?parceiro={go}")
        self.assertEqual(self.contador(r, "capa")["url"], f"?parceiro={go}&falta=capa")  # os outros trocam a falta
        self.assertContains(r, f'aria-pressed="true" hx-get="?parceiro={go}"')
        self.assertContains(r, 'aria-pressed="false"')
        # Sem nenhum outro filtro: o contador ativo volta à página limpa.
        r = self.client.get(self.url, {"falta": "svg"})
        self.assertEqual(self.contador(r, "svg")["url"], self.url)

    def test_cada_filtro_sozinho(self):
        go = self.go["LP"].projeto.parceiro_ano.parceiro_id
        lp = self.go["LP"].componente_id
        self.assertEqual(self.pks(parceiro=go), self.todas(("go", "LP"), ("go", "MT")))
        self.assertEqual(self.pks(componente=lp), self.todas(("go", "LP"), ("pe", "LP")))
        self.assertEqual(self.pks(template=self.templates["LP", "F2"].pk), self.todas(("go", "LP"), ("pe", "LP")))
        nova = Matriz.objects.create(ano=self.ano, nome="Nova")
        ParceiroAno.objects.filter(parceiro__nome="PE").update(matriz=nova)
        self.assertEqual(self.pks(matriz=nova.pk), self.todas(("pe", "LP"), ("pe", "MT")))
        self.assertEqual(self.pks(matriz=self.matriz.pk), self.todas(("go", "LP"), ("go", "MT")))
        # Situação: nada completo nem validado no Mundo; validar uma revista a põe em "validada".
        quatro = self.todas(("go", "LP"), ("go", "MT"), ("pe", "LP"), ("pe", "MT"))
        self.assertEqual(self.pks(situacao="incompleta"), quatro)
        self.assertEqual(self.pks(situacao="completa"), [])
        completar(self.go["LP"])  # validar pede revista sem pendência
        rev = carregar(self.go["LP"].pk)
        with transaction.atomic():
            self.assertIsNone(validacao.validar(rev.pk, hash_validado(rev), self.ped))
        self.assertEqual(self.pks(situacao="validada"), [self.go["LP"].pk])
        patch("nucleo.urls.painel.completa", lambda x: x["revista"].pk == self.pe["MT"].pk).start()
        self.addCleanup(patch.stopall)
        self.assertEqual(self.pks(situacao="completa"), [self.pe["MT"].pk])

    def test_selects_preenchidos_e_limpar_filtros(self):
        tpl = self.templates["LP", "F2"]
        r = self.client.get(self.url)
        self.assertNotContains(r, "Limpar filtros")
        for campo in ("parceiro", "componente", "template", "matriz", "situacao"):
            self.assertContains(r, f'id="filtro-{campo}" name="{campo}"')
        self.assertContains(r, f'<option value="{tpl.pk}">LP · {tpl}</option>')
        r = self.client.get(self.url, {"template": tpl.pk})  # o link "usado por N" cai no select preenchido
        self.assertContains(r, f'<option value="{tpl.pk}" selected>')
        self.assertNotContains(r, "painel-chip")
        self.assertContains(r, f'href="{self.url}" hx-get="{self.url}"')  # Limpar filtros: volta à página limpa
        self.assertContains(r, "Limpar filtros")
        self.assertContains(self.client.get(self.url, {"situacao": "validada"}), '<option value="validada" selected>')
        self.assertContains(self.client.get(self.url, {"falta": "svg"}), "Limpar filtros")

    def test_combinacao_e_contadores_do_recorte(self):
        go = self.go["LP"].projeto.parceiro_ano.parceiro_id
        mt = self.go["MT"].componente_id
        r = self.client.get(self.url, {"parceiro": go, "componente": mt})
        self.assertEqual([x["revista"].pk for x in r.context["linhas"]], [self.go["MT"].pk])
        self.assertEqual(self.contador(r, "svg")["faltam"], 1)  # só o recorte conta
        self.assertEqual(self.contador(r, "svg")["url"], f"?parceiro={go}&componente={mt}&falta=svg")
        completar(self.go["LP"])
        r = self.client.get(self.url, {"parceiro": go, "componente": mt, "falta": "svg", "situacao": "incompleta"})
        self.assertEqual([x["revista"].pk for x in r.context["linhas"]], [self.go["MT"].pk])
        self.assertEqual(r.context["sem_falta"], f"?parceiro={go}&componente={mt}&situacao=incompleta")
        self.assertContains(r, 'name="falta" value="svg"')  # trocar um select mantém a falta
        r = self.client.get(self.url, {"componente": self.go["LP"].componente_id, "falta": "svg"})
        self.assertEqual([x["revista"].pk for x in r.context["linhas"]], [self.pe["LP"].pk])
        # Template de MT com componente LP: recorte vazio, sem erro.
        r = self.client.get(self.url, {"componente": self.go["LP"].componente_id, "template": self.templates["MT", "F2"].pk})
        self.assertEqual(r.context["linhas"], [])
        self.assertContains(r, "Nenhuma revista com esse filtro")

    def test_valor_invalido_e_ignorado(self):
        quatro = self.todas(("go", "LP"), ("go", "MT"), ("pe", "LP"), ("pe", "MT"))
        velha = Matriz.objects.create(ano=Ano.objects.create(ano=2025), nome="Velha")
        for params in (
            {"parceiro": "abc"},
            {"componente": "999999"},
            {"template": "-1"},
            {"matriz": velha.pk},
            {"situacao": "talvez"},
            {"falta": "x", "componente": "", "matriz": "1 OR 1=1"},
        ):
            with self.subTest(params=params):
                r = self.client.get(self.url, params)
                self.assertEqual(r.status_code, 200)
                self.assertEqual(sorted(x["revista"].pk for x in r.context["linhas"]), quatro)
                self.assertNotContains(r, "Limpar filtros")

    def test_etapa_sem_matriz_leva_a_matriz(self):
        """"A matriz não tem a etapa" se corrige na matriz (a aba Matriz do projeto só escolhe a matriz)."""
        MatrizEtapaCC.objects.filter(matriz=self.matriz, componente=self.go["LP"].componente).delete()
        url = reverse("ui_matriz_detalhe", args=[self.matriz.pk])
        r = self.client.get(self.url)
        self.assertContains(r, f'href="{url}" title="A matriz não tem a etapa:')
        r = self.client.get(reverse("ui_revista_editar", args=[2026, self.go["LP"].pk]))
        self.assertContains(r, f'href="{url}"')
        # Sem matriz escolhida, a pendência é outra e continua na aba Matriz do projeto.
        ParceiroAno.objects.filter(parceiro__nome="GO").update(matriz=None)
        r = self.client.get(self.url)
        self.assertContains(r, f'href="{reverse("ui_projeto", args=[self.projeto_go.pk])}?aba=matriz" title="Falta escolher a matriz')

    def test_impresso_filtra_sem_validar(self):
        self.client.force_login(self.imp)
        r = self.client.get(self.url, {"componente": self.go["LP"].componente_id, "situacao": "incompleta", "falta": "svg"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.context["linhas"]), 2)
        self.assertNotContains(r, 'name="revista"')
        self.assertNotContains(r, "Validar selecionadas")
