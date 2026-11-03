"""Anos fora do admin (/ui/anos/, S3 de D-190): mesma regra do `AnoAdmin.abrir_view`."""

from django.test import TestCase
from django.urls import reverse

from nucleo.models import Ano, Componente, CorPadrao, Etapa, Matriz, Revista
from nucleo.tests.test_admin_cadastro import Base
from nucleo.tests.test_admin_padrao import esta_validada, validar
from nucleo.tests.test_admin_projeto import Base as BaseProjeto
from nucleo.tests.test_admin_projeto import mensagens
from nucleo.tests.test_resolver import usuario
from nucleo.ui_autosave import proxima_ordem
from nucleo.urls.ui_anos import EtapaForm, ordem_escolar


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
        self.assertNotContains(self.client.get(reverse("cortes", args=[2026])), f'href="{self.url}"')  # "Configurar" leva a /ui/anos/2026/
        self.assertEqual(self.client.post(self.url, {"ano": 2027}).status_code, 403)
        self.assertFalse(Ano.objects.filter(ano=2027).exists())
        self.client.force_login(usuario("nada"))  # sem view_ano
        self.assertEqual(self.client.get(self.url).status_code, 403)


def dados_da_tabela(resp, tabela, **mudar):
    """POST equivalente à tabela `tabela` renderizada ("etapas" ou "componentes"), com `mudar` por cima."""
    fs = resp.context[tabela]
    dados = {"tabela": tabela}
    for form in (fs.management_form, *fs.forms):
        for nome in form.fields:
            valor = form[nome].value()
            if valor is not None:
                dados[form.add_prefix(nome)] = valor
    dados.update(mudar)
    return dados


class CadastrosDoAnoTest(Base):
    """Etapas e componentes do ano fora do admin (S4 de D-190): mesmas regras de `EtapaAdmin`/`ComponenteAdmin`."""

    url = reverse("ui_ano", args=[2026])

    def setUp(self):
        self.client.force_login(usuario("ped", "Pedagógica"))

    def test_cria_e_edita(self):
        self.assertContains(self.client.get(reverse("ui_anos")), self.url)
        resp = self.client.get(self.url)
        n = len(self.e)  # índice da linha nova (o "+ Adicionar etapa" soma 1 ao TOTAL_FORMS)
        dados = dados_da_tabela(resp, "etapas", **{"etapas-TOTAL_FORMS": str(n + 1), f"etapas-{n}-codigo": "1EM", f"etapas-{n}-escala_max": "500"})
        resp = self.client.post(self.url, dados, follow=True)
        self.assertRedirects(resp, self.url)
        self.assertContains(resp, "Etapas de 2026 salvas.")
        self.assertTrue(Etapa.objects.filter(ano=self.a26, codigo="1EM", escala_max=500).exists())
        ordem = list(Etapa.objects.filter(ano=self.a26).order_by("ordem").values_list("codigo", flat=True))
        self.assertEqual(ordem, ["2EF", "5EF", "9EF", "1EM", "3EM"])  # U4: lógica escolar, não o fim da lista

        lp = list(resp.context["componentes"].queryset).index(self.c["LP"])
        n = len(self.c)
        dados = dados_da_tabela(resp, "componentes", **{
            f"componentes-{lp}-nome": "Português", "componentes-TOTAL_FORMS": str(n + 1),
            f"componentes-{n}-codigo": "ART", f"componentes-{n}-nome": "Arte",
        })  # fmt: skip
        self.assertContains(self.client.post(self.url, dados, follow=True), "Componentes de 2026 salvos.")
        self.assertEqual(Componente.objects.get(pk=self.c["LP"].pk).nome, "Português")
        self.assertTrue(Componente.objects.filter(ano=self.a26, codigo="ART", nome="Arte").exists())

    def test_codigo_repetido_da_mensagem(self):
        n = len(self.e)
        dados = dados_da_tabela(self.client.get(self.url), "etapas", **{"etapas-TOTAL_FORMS": str(n + 1), f"etapas-{n}-codigo": "5EF", f"etapas-{n}-escala_max": "500"})
        resp = self.client.post(self.url, dados)
        self.assertContains(resp, "Já existe a etapa 5EF em 2026.")
        self.assertEqual(Etapa.objects.filter(ano=self.a26, codigo="5EF").count(), 1)

    def test_codigo_repetido_no_mesmo_envio(self):
        n = len(self.c)
        dados = dados_da_tabela(self.client.get(self.url), "componentes", **{
            "componentes-TOTAL_FORMS": str(n + 2),
            f"componentes-{n}-codigo": "ART", f"componentes-{n}-nome": "Arte",
            f"componentes-{n + 1}-codigo": "ART", f"componentes-{n + 1}-nome": "Artes",
        })  # fmt: skip
        self.assertContains(self.client.post(self.url, dados), "Código repetido nesta tabela.")
        self.assertFalse(Componente.objects.filter(codigo="ART").exists())

    def test_escala_com_matriz_fica_so_leitura(self):
        resp = self.client.get(self.url)
        i = list(resp.context["etapas"].queryset).index(self.e["5EF"])
        self.assertTrue(resp.context["etapas"].forms[i].fields["escala_max"].disabled)
        self.assertTrue(resp.context["etapas"].forms[i].fields["codigo"].disabled)
        j = list(resp.context["etapas"].queryset).index(self.e["9EF"])
        self.assertFalse(resp.context["etapas"].forms[j].fields["escala_max"].disabled)  # sem corte nem matriz
        dados = dados_da_tabela(resp, "etapas", **{f"etapas-{i}-escala_max": "999", f"etapas-{i}-codigo": "XX"})
        self.client.post(self.url, dados)
        self.e["5EF"].refresh_from_db()
        self.assertEqual((self.e["5EF"].codigo, self.e["5EF"].escala_max), ("5EF", 500))

    def test_impresso_so_le(self):
        self.client.force_login(usuario("imp", "Impresso"))
        resp = self.client.get(self.url)
        self.assertContains(resp, "Língua Portuguesa")
        self.assertNotContains(resp, 'name="etapas-')
        self.assertNotContains(resp, 'name="componentes-')
        self.assertEqual(self.client.post(self.url, {"tabela": "componentes"}).status_code, 403)
        self.client.force_login(usuario("nada"))
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_ano_inexistente(self):
        self.assertEqual(self.client.get(reverse("ui_ano", args=[1999])).status_code, 404)


class PaletaDoAnoTest(BaseProjeto):
    """Padrões do ano fora do admin (S5 de D-190): mesma confirmação de impacto de `CorPadraoAdmin`."""

    def setUp(self):
        super().setUp()
        self.url = reverse("ui_ano", args=[2026])
        self.cp = CorPadrao.objects.get(ano=self.ano, padrao=3)
        self.projeto_pe.pd03 = "Adequado PE"  # PE sobrescreve o nome: fica fora da lista
        self.projeto_pe.save()
        validar(self.go["LP"])

    def post(self, follow=False, **troca):
        dados = {"tabela": "padroes", "padrao": self.cp.pk, "p3-nome": self.cp.nome, "p3-cor": self.cp.cor}
        dados.update({f"p3-{k}": v for k, v in troca.items()})
        return self.client.post(self.url, dados, follow=follow)

    def test_sem_confirmar_abre_modal_e_nao_grava(self):
        self.assertContains(self.client.get(self.url), 'name="p3-cor"')
        r = self.post(nome="Adequado")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "<dialog")
        self.assertContains(r, 'data-form="padrao-3" data-campo="p3-confirmar_impacto"')
        self.assertContains(r, "Salvar tira o “Validado” de 1 revista(s)")
        self.assertContains(r, f"<li>{self.go['LP']}</li>")
        self.assertContains(r, 'value="Adequado" data-original="Padrão 03"')
        self.assertEqual(CorPadrao.objects.get(pk=self.cp.pk).nome, "Padrão 03")
        self.assertTrue(esta_validada(self.go["LP"]))

    def test_afetada_sem_validada_grava_direto(self):
        Revista.objects.filter(pk=self.go["LP"].pk).update(hash_validado=None)
        self.assertEqual(self.post(nome="Adequado").status_code, 302)
        self.assertEqual(CorPadrao.objects.get(pk=self.cp.pk).nome, "Adequado")

    def test_confirmado_grava_e_tira_validado(self):
        r = self.post(follow=True, nome="Adequado", confirmar_impacto="on")
        self.assertRedirects(r, self.url)
        self.assertEqual(CorPadrao.objects.get(pk=self.cp.pk).nome, "Adequado")
        self.assertFalse(esta_validada(self.go["LP"]))
        aviso = next(m for m in mensagens(r) if "perderam" in m)
        self.assertIn(f"1 revista(s) perderam o “Validado”: {self.go['LP']}.", aviso)
        self.assertIn('href="/painel/2026/?falta=validado"', aviso)

    def test_sem_afetada_grava_direto(self):
        self.projeto_go.pd03 = "Adequado GO"
        self.projeto_go.save()
        r = self.post(nome="Adequado")
        self.assertEqual(r.status_code, 302)
        self.assertEqual(CorPadrao.objects.get(pk=self.cp.pk).nome, "Adequado")

    def test_salvar_sem_mudar_nao_mexe_na_cor(self):
        """O <input type=color> manda a cor em minúsculas; o banco pode ter maiúsculas (carga)."""
        CorPadrao.objects.filter(pk=self.cp.pk).update(cor="#B3CCFF")
        validar(self.go["LP"])
        r = self.post(cor="#b3ccff")
        self.assertEqual(r.status_code, 302)  # sem pedir confirmação
        self.assertEqual(CorPadrao.objects.get(pk=self.cp.pk).cor, "#B3CCFF")
        self.assertTrue(esta_validada(self.go["LP"]))

    def test_cor_invalida_e_padrao_de_outro_ano(self):
        self.assertContains(self.post(cor="#12", confirmar_impacto="on"), "Use o formato #RRGGBB.")
        self.assertEqual(CorPadrao.objects.get(pk=self.cp.pk).cor, self.cp.cor)
        outro = CorPadrao.objects.create(ano=Ano.objects.create(ano=2025), padrao=3, cor="#000000")
        r = self.client.post(self.url, {"tabela": "padroes", "padrao": outro.pk, "p3-nome": "x", "p3-cor": "#111111"})
        self.assertEqual(r.status_code, 404)

    def test_adiciona_padrao_que_falta(self):
        self.assertNotContains(self.client.get(self.url), "Adicionar padrão")  # já há 5
        CorPadrao.objects.filter(ano=self.ano, padrao=5).delete()
        r = self.client.get(self.url)
        self.assertContains(r, "Adicionar padrão")
        self.assertContains(r, '<details class="novo-padrao">')  # fechado até clicar (auditoria 03/11)
        self.assertContains(r, 'class="select"')
        self.assertContains(r, 'aria-label="Salvar Padrão 1"')  # cada "Salvar" diz de qual padrão
        dados = {"tabela": "novo_padrao", "novo-padrao": "5", "novo-nome": "Avançado", "novo-cor": "#00aa00"}
        self.assertEqual(self.client.post(self.url, dados).status_code, 302)
        self.assertTrue(CorPadrao.objects.filter(ano=self.ano, padrao=5, nome="Avançado").exists())

    def test_impresso_so_le(self):
        self.client.force_login(self.imp)
        r = self.client.get(self.url)
        self.assertContains(r, self.cp.cor)
        self.assertNotContains(r, 'name="p3-cor"')
        self.assertEqual(self.post(nome="X", confirmar_impacto="on").status_code, 403)
        self.assertEqual(CorPadrao.objects.get(pk=self.cp.pk).nome, "Padrão 03")


class LinhasDoAnoTest(Base):
    """U4: linha nova só pelo botão (formset sem linha vazia) e ordem automática. Etapa segue a
    lógica escolar (todo EF antes do EM; no mesmo ensino, pela série): não se digita nem se arrasta."""

    url = reverse("ui_ano", args=[2026])

    def setUp(self):
        self.client.force_login(usuario("ped", "Pedagógica"))

    def codigos(self):
        return list(Etapa.objects.filter(ano=self.a26).order_by("ordem").values_list("codigo", flat=True))

    def incluir(self, codigo):
        n = Etapa.objects.filter(ano=self.a26).count()
        dados = dados_da_tabela(self.client.get(self.url), "etapas", **{
            "etapas-TOTAL_FORMS": str(n + 1), f"etapas-{n}-codigo": codigo, f"etapas-{n}-escala_max": "500",
        })  # fmt: skip
        self.assertContains(self.client.post(self.url, dados, follow=True), "Etapas de 2026 salvas.")

    def test_form_sem_campo_ordem(self):
        self.assertNotIn("ordem", EtapaForm(ano=self.a26).fields)
        resp = self.client.get(self.url)
        self.assertNotContains(resp, "-ordem")
        self.assertNotContains(resp, ">Ordem<")

    def test_nova_etapa_entra_na_ordem_escolar(self):
        self.assertEqual(proxima_ordem(Etapa.objects.none()), 1)
        self.assertEqual(sorted(["3EM", "9EF", "1EM", "Z1", "10EF", "2EF"], key=ordem_escolar), ["2EF", "9EF", "10EF", "1EM", "3EM", "Z1"])
        antes = self.codigos()
        self.assertEqual(antes, sorted(antes, key=ordem_escolar))
        self.incluir("2EM")
        self.incluir("1EM")
        self.incluir("1EF")
        esperado = sorted([*antes, "2EM", "1EM", "1EF"], key=ordem_escolar)
        self.assertEqual(self.codigos(), esperado)
        self.assertEqual(esperado, ["1EF", "2EF", "5EF", "9EF", "1EM", "2EM", "3EM"])
        ordens = list(Etapa.objects.filter(ano=self.a26).order_by("ordem").values_list("ordem", flat=True))
        self.assertEqual(ordens, list(range(1, len(esperado) + 1)))

    def test_impresso_nao_ve_adicionar(self):
        self.client.force_login(usuario("imp", "Impresso"))
        resp = self.client.get(self.url)
        self.assertNotContains(resp, "Adicionar etapa")
        self.assertNotContains(resp, "Adicionar componente")
        self.assertNotContains(resp, "__prefix__")

    def test_sem_linha_vazia(self):
        resp = self.client.get(self.url)
        self.assertNotContains(resp, "Preencha a última linha")
        self.assertEqual(resp.context["etapas"].extra, 0)
        self.assertEqual(resp.context["componentes"].extra, 0)
        self.assertEqual(len(resp.context["etapas"].forms), len(self.e))  # só as gravadas
        self.assertContains(resp, "Adicionar etapa")
        self.assertContains(resp, "Adicionar componente")
        self.assertContains(resp, 'x-data="linhaNova"', count=2)
        self.assertNotContains(resp, 'x-data="ordenavel"')  # etapa: lógica escolar; componente: por código


class OrdemEscolarPorQualquerCaminhoTest(TestCase):
    """A ordem da etapa nasce do código em qualquer gravação (admin, criar_demo, abrir ano), não só na
    tela B: o preview ordena por ela e mostrava 9EF antes de 5EF."""

    def test_etapa_criada_pelo_orm_entra_na_ordem_escolar(self):
        from nucleo.models import Ano, Etapa

        ano = Ano.objects.create(ano=2031)
        for codigo in ["9EF", "3EM", "2EF", "5EF"]:  # fora de ordem, sem passar pela tela
            Etapa.objects.create(ano=ano, codigo=codigo, escala_max=500, ordem=99)
        self.assertEqual(list(Etapa.objects.filter(ano=ano).order_by("ordem").values_list("codigo", flat=True)),
                         ["2EF", "5EF", "9EF", "3EM"])
