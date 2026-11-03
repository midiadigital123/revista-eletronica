"""Anos fora do admin (/ui/anos/, S3 de D-190): mesma regra do `AnoAdmin.abrir_view`."""

from django.urls import reverse

from nucleo.models import Ano, Componente, Etapa, Matriz
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
        n = len(self.e)  # índice da linha vazia ("Adicionar")
        dados = dados_da_tabela(resp, "etapas", **{f"etapas-{n}-codigo": "1EM", f"etapas-{n}-escala_max": "500", f"etapas-{n}-ordem": "9"})
        resp = self.client.post(self.url, dados, follow=True)
        self.assertRedirects(resp, self.url)
        self.assertContains(resp, "Etapas de 2026 salvas.")
        self.assertTrue(Etapa.objects.filter(ano=self.a26, codigo="1EM", escala_max=500, ordem=9).exists())

        lp = list(resp.context["componentes"].queryset).index(self.c["LP"])
        n = len(self.c)
        dados = dados_da_tabela(resp, "componentes", **{f"componentes-{lp}-nome": "Português", f"componentes-{n}-codigo": "ART", f"componentes-{n}-nome": "Arte"})
        self.assertContains(self.client.post(self.url, dados, follow=True), "Componentes de 2026 salvos.")
        self.assertEqual(Componente.objects.get(pk=self.c["LP"].pk).nome, "Português")
        self.assertTrue(Componente.objects.filter(ano=self.a26, codigo="ART", nome="Arte").exists())

    def test_codigo_repetido_da_mensagem(self):
        n = len(self.e)
        dados = dados_da_tabela(self.client.get(self.url), "etapas", **{f"etapas-{n}-codigo": "5EF", f"etapas-{n}-escala_max": "500", f"etapas-{n}-ordem": "9"})
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
