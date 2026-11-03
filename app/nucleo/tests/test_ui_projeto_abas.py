"""Página do projeto com abas (U7b): Dados, Matriz, Cortes, Passos e cores, Revistas (`?aba=`).

A aba Matriz é o único lugar da tela B que grava a matriz de um projeto, além da ação em massa da
Lista; as duas passam por `servicos.matriz.atribuir_matriz`.
"""

from unittest import mock

from django.urls import reverse

from nucleo.admin.bloqueio import CAMPO_SESSAO
from nucleo.models import Matriz, ParceiroAno
from nucleo.tests.test_admin_padrao import esta_validada, validar
from nucleo.tests.test_admin_projeto import Base

JSON = {"HTTP_ACCEPT": "application/json"}
ABAS = ["Dados", "Matriz", "Cortes", "Passos e cores", "Revistas"]


class AbasTest(Base):
    def setUp(self):
        super().setUp()
        self.url = reverse("ui_projeto", args=[self.projeto_go.pk])

    def test_cinco_abas_e_dados_por_padrao(self):
        r = self.client.get(self.url)
        for aba in ABAS:
            self.assertContains(r, f">{aba}</a>")
        self.assertContains(r, f'href="{self.url}?aba=dados" aria-current="page">Dados</a>')
        self.assertContains(r, 'id="nome"')
        self.assertContains(r, 'id="variaveis"')
        self.assertContains(r, 'id="passo" aria-labelledby="passo-titulo" hidden')  # na aba Passos e cores

    def test_aba_passos_e_cores(self):
        r = self.client.get(self.url + "?aba=passos")
        self.assertContains(r, 'aria-current="page">Passos e cores</a>')
        self.assertContains(r, 'id="nome" aria-labelledby="nome-titulo" hidden')
        self.assertContains(r, "Sobrescrever um passo")

    def test_aba_cortes_so_com_a_linha_do_parceiro(self):
        r = self.client.get(self.url + "?aba=cortes")
        self.assertContains(r, 'aria-label="GO 5EF LP"')
        self.assertNotContains(r, 'aria-label="PE 5EF LP"')
        self.assertContains(r, reverse("cortes_celula", args=[2026]))
        self.assertContains(r, reverse("cortes", args=[2026]))  # a grade do ano inteiro

    def test_aba_revistas_um_cartao_por_componente(self):
        lp, mt = self.go["LP"], self.go["MT"]
        r = self.client.get(self.url + "?aba=revistas")
        for rev in (lp, mt):
            self.assertContains(r, reverse("ui_revista_editar", args=[2026, rev.pk]))
            self.assertContains(r, reverse("preview", args=[rev.pk]))
        self.assertContains(r, "Template F1")
        self.assertContains(r, "Padrão")
        self.assertContains(r, "SVG do F2")
        self.assertContains(r, "Capa")
        self.assertContains(r, "Sem “Validado”")
        validar(lp)
        self.assertContains(self.client.get(self.url + "?aba=revistas"), "Validada")

    def test_nenhuma_acao_da_ficha_perdida(self):
        """Inventário da ficha antiga (uma página só) → aba que tem cada ação agora."""
        inventario = {
            "dados": ['name="nome"', 'name="sigla_programa"', "Planilha de variáveis de 2026"],
            "matriz": ['name="matriz"', reverse("ui_projeto_matriz", args=[self.projeto_go.pk])],
            "passos": ["Sobrescrever um passo", "Sobrescrever uma cor", "5EF LP: 25"],
        }
        for aba, acoes in inventario.items():
            r = self.client.get(f"{self.url}?aba={aba}")
            for acao in acoes:
                with self.subTest(aba=aba, acao=acao):
                    self.assertContains(r, acao)

    def test_aba_desconhecida_vira_dados(self):
        self.assertContains(self.client.get(self.url + "?aba=xyz"), 'aria-current="page">Dados</a>')


class AbaMatrizTest(Base):
    def setUp(self):
        super().setUp()
        self.url = reverse("ui_projeto", args=[self.projeto_go.pk])
        self.url_matriz = reverse("ui_projeto_matriz", args=[self.projeto_go.pk])
        self.nova = Matriz.objects.create(ano=self.ano, nome="Nova")
        self.pa = ParceiroAno.objects.get(pk=self.projeto_go.parceiro_ano_id)

    def abrir(self):
        r = self.client.get(self.url + "?aba=matriz")
        self.assertContains(r, f'data-url="{self.url_matriz}"')
        self.assertContains(r, 'x-data="campoAuto"')
        return r.wsgi_request.bloqueio["sessao"]

    def enviar(self, matriz, **extra):
        dados = {"campo": "matriz", "valor": matriz.pk, CAMPO_SESSAO: self.abrir(), **extra}
        return self.client.post(self.url_matriz, dados, **JSON)

    def test_autosave_sem_impacto_grava(self):
        r = self.enviar(self.nova)
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()["ok"])
        self.assertEqual(ParceiroAno.objects.get(pk=self.pa.pk).matriz, self.nova)
        self.assertEqual(ParceiroAno.objects.get(parceiro__nome="PE").matriz, self.matriz)

    def test_com_impacto_devolve_o_modal_e_so_grava_confirmado(self):
        validar(self.go["LP"])
        r = self.enviar(self.nova)
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.json()["ok"])
        self.assertEqual(r.json()["impacto"]["perdem"], [str(self.go["LP"])])
        self.assertEqual(ParceiroAno.objects.get(pk=self.pa.pk).matriz, self.matriz)
        self.assertTrue(esta_validada(self.go["LP"]))
        r = self.enviar(self.nova, confirmar_impacto="on")
        self.assertTrue(r.json()["ok"])
        self.assertEqual(ParceiroAno.objects.get(pk=self.pa.pk).matriz, self.nova)

    def test_matriz_de_outro_ano_422(self):
        velha = Matriz.objects.create(ano=type(self.ano).objects.create(ano=2025), nome="Velha")
        r = self.enviar(velha)
        self.assertEqual(r.status_code, 422)
        self.assertEqual(ParceiroAno.objects.get(pk=self.pa.pk).matriz, self.matriz)

    def test_bloqueio_perdido_409(self):
        self.travar(self.projeto_go)
        r = self.client.post(self.url_matriz, {"campo": "matriz", "valor": self.nova.pk, CAMPO_SESSAO: "x"}, **JSON)
        self.assertEqual(r.status_code, 409)

    def test_impresso_so_leitura_e_403(self):
        self.client.force_login(self.imp)
        r = self.client.get(self.url + "?aba=matriz")
        self.assertNotContains(r, f'data-url="{self.url_matriz}"')
        self.assertContains(r, "Comunitária")
        self.assertEqual(self.client.post(self.url_matriz, {"campo": "matriz", "valor": self.nova.pk}, **JSON).status_code, 403)

    def test_get_volta_a_aba(self):
        self.assertRedirects(self.client.get(self.url_matriz), self.url + "?aba=matriz", fetch_redirect_response=False)


class AtribuirMatrizUnicoServicoTest(Base):
    """A aba Matriz e a ação em massa da Lista gravam pelo mesmo serviço."""

    def test_aba_matriz_e_massa_chamam_atribuir_matriz(self):
        nova = Matriz.objects.create(ano=self.ano, nome="Nova")
        pa = ParceiroAno.objects.get(pk=self.projeto_go.parceiro_ano_id)
        url = reverse("ui_projeto", args=[self.projeto_go.pk])
        with mock.patch("nucleo.servicos.matriz.atribuir_matriz") as atribuir:
            sessao = self.client.get(url + "?aba=matriz").wsgi_request.bloqueio["sessao"]
            dados = {"campo": "matriz", "valor": nova.pk, CAMPO_SESSAO: sessao}
            self.assertEqual(self.client.post(reverse("ui_projeto_matriz", args=[self.projeto_go.pk]), dados, **JSON).status_code, 200)
            atribuir.assert_called_with(pa, nova, self.ped)
            atribuir.reset_mock()
            pe =ParceiroAno.objects.get(parceiro__nome="PE")
            self.client.post(reverse("ui_projeto_massa", args=[2026, "matriz"]), {"alvos": [pe.pk], "matriz": nova.pk})
            atribuir.assert_called_with(pe, nova, self.ped)

    def test_atribuir_matriz_grava_com_o_usuario_no_historico(self):
        from nucleo.servicos.matriz import atribuir_matriz

        nova = Matriz.objects.create(ano=self.ano, nome="Nova")
        pa = ParceiroAno.objects.get(pk=self.projeto_go.parceiro_ano_id)
        atribuir_matriz(pa, nova, self.ped)
        self.assertEqual(ParceiroAno.objects.get(pk=pa.pk).matriz, nova)
        self.assertEqual(pa.history.first().history_user, self.ped)
