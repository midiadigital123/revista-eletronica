"""Página do projeto com abas (U7b): Dados, Matriz, Cortes, Passos e cores, Revistas (`?aba=`).

A aba Matriz é o único lugar da tela B que grava a matriz de um projeto, além da ação em massa da
Lista; as duas passam por `servicos.matriz.atribuir_matriz`.
"""

from unittest import mock

from django.urls import reverse

from nucleo.admin.bloqueio import CAMPO_SESSAO
from nucleo.models import Descritor, Etapa, Matriz, MatrizEtapaCC, ParceiroAno, ProjetoCor, ProjetoPasso
from nucleo.servicos import bloqueio
from nucleo.servicos.cascata import gravar_cortes
from nucleo.servicos.etapa_projeto import criar
from nucleo.servicos.pendencias import pendencias
from nucleo.servicos.resolver import carregar
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
        self.assertNotContains(r, 'id="passo"')  # só na aba Passos e cores

    def test_aba_passos_e_cores(self):
        r = self.client.get(self.url + "?aba=passos")
        self.assertContains(r, 'aria-current="page">Passos e cores</a>')
        self.assertContains(r, 'id="nome" aria-labelledby="nome-titulo" hidden')
        self.assertContains(r, 'id="passo" aria-labelledby="passo-titulo">')
        self.assertContains(r, 'id="cores" aria-labelledby="cores-titulo">')

    def test_aba_cortes_so_com_a_linha_do_parceiro(self):
        r = self.client.get(self.url + "?aba=cortes")
        self.assertContains(r, 'aria-label="GO 5EF LP"')
        self.assertNotContains(r, 'aria-label="PE 5EF LP"')
        self.assertContains(r, reverse("cortes_celula", args=[2026]))
        self.assertContains(r, reverse("cortes", args=[2026]))  # a grade do ano inteiro
        self.assertContains(r, 'class="pj-etapa"', count=2)  # um bloco por etapa, sem tabela
        self.assertNotContains(r, "<table")
        self.assertContains(r, "De 1 a 4 cortes", count=1)  # a regra uma vez só
        self.assertNotContains(r, "Cada célula salva sozinha")

    def test_aba_revistas_um_cartao_por_componente(self):
        lp, mt = self.go["LP"], self.go["MT"]
        r = self.client.get(self.url + "?aba=revistas")
        for rev in (lp, mt):
            self.assertContains(r, reverse("ui_revista_editar", args=[2026, rev.pk]))
            self.assertContains(r, reverse("preview", args=[rev.pk]))
        self.assertContains(r, "Template F1")
        self.assertContains(r, "Padrão")
        self.assertNotContains(r, "SVG do F2")  # o SVG enviado saiu (fase 4 do F2)
        self.assertContains(r, "Capa")
        self.assertContains(r, "Sem “Validado”")
        validar(lp)
        self.assertContains(self.client.get(self.url + "?aba=revistas"), "Validada")

    def test_nenhuma_acao_da_ficha_perdida(self):
        """Inventário da ficha antiga (uma página só) → aba que tem cada ação agora."""
        inventario = {
            "dados": ['name="nome"', 'name="sigla_programa"', "Ver a planilha de variáveis de 2026"],
            "matriz": ['name="matriz"', reverse("ui_projeto_matriz", args=[self.projeto_go.pk])],
            # sobrescrever passo/cor, "sem linhas vazias" e voltar ao herdado (antes: linhas com Remover)
            "passos": [f'name="passo-{self.e5.pk}-{self.lp.pk}"', f'name="sem-{self.e5.pk}-{self.lp.pk}"', 'name="cor-1"',
                       "Voltar ao passo da matriz", "Voltar à cor do ano", "Matriz: 25"],
        }
        for aba, acoes in inventario.items():
            r = self.client.get(f"{self.url}?aba={aba}")
            for acao in acoes:
                with self.subTest(aba=aba, acao=acao):
                    self.assertContains(r, acao)

    def test_aba_desconhecida_vira_dados(self):
        self.assertContains(self.client.get(self.url + "?aba=xyz"), 'aria-current="page">Dados</a>')


class CabecalhoTest(Base):
    def test_hierarquia_e_um_texto_de_ajuda_so(self):
        r = self.client.get(reverse("ui_projeto", args=[self.projeto_go.pk]) + "?aba=passos")
        self.assertContains(r, "<h1>Projeto GO</h1>", html=True)
        self.assertContains(r, "<div><dt>Parceiro</dt><dd>GO</dd></div>", html=True)
        self.assertContains(r, "<div><dt>Matriz</dt><dd>Comunitária</dd></div>", html=True)
        self.assertContains(r, "<div><dt>Revistas</dt><dd>LP, MT</dd></div>", html=True)
        self.assertNotContains(r, "Planilha de variáveis")  # o botão do cabeçalho saiu; o link fica na seção Variáveis
        self.assertContains(r, "Cada campo salva sozinho", count=1)  # no status, perto do salvamento


class SobrescritaPaginaTest(Base):
    """Aba Passos e cores: cada valor diz se vem do ano/da matriz ou se é sobrescrito aqui."""

    def setUp(self):
        super().setUp()
        self.url = reverse("ui_projeto", args=[self.projeto_go.pk]) + "?aba=passos"

    def celula(self, r, etapa, comp):
        return next(c for b in r.context["etapas_passo"] if b["etapa"] == etapa for c in b["celulas"] if c["componente"] == comp)

    def test_passo_herdado_aparece_como_herdado(self):
        r = self.client.get(self.url)
        c = self.celula(r, self.e5, self.lp)
        self.assertEqual((c["sobrescrito"], c["matriz"], c["passo"]), (False, 25, None))
        self.assertContains(r, f'name="passo-{self.e5.pk}-{self.lp.pk}" value="" placeholder="25"')

    def test_sem_linhas_vazias_e_diferente_de_herdar(self):
        ProjetoPasso.objects.create(projeto=self.projeto_go, etapa=self.e5, componente=self.lp, ano=self.ano, passo=None)
        r = self.client.get(self.url)
        c = self.celula(r, self.e5, self.lp)
        self.assertEqual((c["sobrescrito"], c["sem_vazias"]), (True, True))
        self.assertContains(r, f'name="sem-{self.e5.pk}-{self.lp.pk}" data-sem checked')
        self.assertFalse(self.celula(r, self.e9, self.lp)["sobrescrito"])

    def test_amostras_com_cor_e_nome_efetivos(self):
        ProjetoCor.objects.create(projeto=self.projeto_go, padrao=2, cor="#123456")
        r = self.client.get(self.url)
        amostras = {a["padrao"]: a for a in r.context["amostras"]}
        self.assertEqual(len(amostras), 5)
        self.assertEqual((amostras[1]["cor"], amostras[1]["sobrescrita"], amostras[1]["nome"]), ("#f72628", False, "Padrão 01"))
        self.assertEqual((amostras[2]["cor"], amostras[2]["sobrescrita"], amostras[2]["cor_ano"]), ("#123456", True, "#ff8d43"))
        self.assertContains(r, 'name="cor-2" id="cor-2" value="#123456"')
        self.assertContains(r, f'href="{reverse("ui_ano", args=[2026])}#padroes"')  # a paleta do ano

    def test_impresso_nao_ve_controles_e_recebe_403(self):
        self.client.force_login(self.imp)
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)
        for controle in ('name="passo-', 'name="sem-', 'name="cor-', "Voltar à cor do ano", "Editar as cores do ano"):
            self.assertNotContains(r, controle)
        url = reverse("ui_projeto_campo", args=[self.projeto_go.pk])
        for campo, valor in ((f"passo-{self.e5.pk}-{self.lp.pk}", "30"), ("cor-1", "#000000")):
            self.assertEqual(self.client.post(url, {"campo": campo, "valor": valor, CAMPO_SESSAO: "x"}, **JSON).status_code, 403)
        self.assertFalse(ProjetoPasso.objects.exists())
        self.assertFalse(ProjetoCor.objects.exists())


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


class EtapaNaoCanonica(Base):
    """GO com corte em 4EF LP, etapa que a Comunitária não tem."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.e4 = Etapa.objects.create(ano=cls.ano, codigo="4EF", escala_max=500, ordem=1)
        c = [100, 200, 250, 300]
        gravar_cortes(
            cls.projeto_go.parceiro_ano,
            [(cls.e5, cls.lp, c), (cls.e9, cls.lp, c), (cls.e5, cls.mt, c), (cls.e4, cls.lp, c)],
            cls.usuario,
        )
        cls.mec5 = MatrizEtapaCC.objects.get(matriz=cls.matriz, etapa=cls.e5, componente=cls.lp)

    def setUp(self):
        super().setUp()
        self.url = reverse("ui_projeto", args=[self.projeto_go.pk]) + "?aba=matriz"
        self.url_apontar = reverse("ui_projeto_etapa_apontar", args=[self.projeto_go.pk])

    def do_projeto(self):
        return MatrizEtapaCC.objects.filter(projeto=self.projeto_go)


class ApontarEtapaTest(EtapaNaoCanonica):
    """Etapa 7 (D-276): a etapa não canônica do projeto aponta para uma canônica pela aba Matriz."""

    def apontar(self, base, **extra):
        sessao = self.client.get(self.url).wsgi_request.bloqueio["sessao"]
        dados = {"etapa": self.e4.pk, "componente": self.lp.pk, "base": getattr(base, "pk", base), CAMPO_SESSAO: sessao, **extra}
        return self.client.post(self.url_apontar, dados, follow=True)

    def test_aba_matriz_mostra_o_form_de_apontar(self):
        mt5 = MatrizEtapaCC.objects.get(matriz=self.matriz, etapa=self.e5, componente=self.mt)
        r = self.client.get(self.url)
        self.assertContains(r, "Etapas do projeto")
        self.assertContains(r, 'name="base"', count=1)  # só 4EF LP escolhe a base; as outras têm a da matriz
        self.assertContains(r, '<optgroup label="Comunitária (2026)">')
        self.assertContains(r, f'<option value="{self.mec5.pk}">5EF</option>')
        self.assertNotContains(r, f'<option value="{mt5.pk}">')  # outro componente

    def test_aba_matriz_mostra_revisar_so_quando_a_base_mudou(self):
        """D-292: o selo e o link para a revisão aparecem na linha da cópia quando a base mudou, para todo perfil."""
        mec = criar(self.projeto_go, self.e4, self.lp, self.usuario, base=self.mec5)
        revisar = reverse("ui_revisao", args=[mec.pk])
        r = self.client.get(self.url)
        self.assertNotContains(r, "A base mudou")
        self.assertNotContains(r, revisar)
        Descritor.objects.filter(matriz_etapa_cc=self.mec5).update(descricao="Mudou na base")
        for quem in (self.ped, self.imp):
            self.client.force_login(quem)
            r = self.client.get(self.url)
            self.assertContains(r, "A base mudou", count=1)
            self.assertContains(r, f'<a class="link" href="{revisar}">Revisar mudanças da base<span class="sr-only"> de 4EF LP</span></a>', html=True)

    def test_apontar_pela_tela(self):
        r = self.apontar(self.mec5)
        self.assertRedirects(r, self.url)
        mec = self.do_projeto().get()
        self.assertEqual((mec.etapa, mec.componente, mec.base), (self.e4, self.lp, self.mec5))
        self.assertTrue(mec.base_foto)
        self.assertTrue(Descritor.objects.filter(matriz_etapa_cc=mec).exists())
        self.assertNotIn("etapa_sem_base", [p.codigo for p in pendencias(carregar(self.go["LP"].pk))])
        self.assertContains(r, "base: 5EF LP da Comunitária (2026)")
        self.assertContains(r, reverse("ui_matriz_mec", args=[mec.pk]))
        self.assertNotContains(r, 'name="base"')

    def test_apontar_recusa_sem_bloqueio_e_sem_permissao(self):
        self.client.get(self.url)
        dados = {"etapa": self.e4.pk, "componente": self.lp.pk, "base": self.mec5.pk}
        self.client.post(self.url_apontar, {**dados, CAMPO_SESSAO: "outra-aba"})
        self.assertFalse(self.do_projeto().exists())
        self.client.force_login(self.imp)
        self.assertNotContains(self.client.get(self.url), f'action="{self.url_apontar}"')
        self.assertEqual(self.client.post(self.url_apontar, dados).status_code, 403)
        self.assertFalse(self.do_projeto().exists())

    def test_recusa_do_servico_vira_mensagem(self):
        e3 = Etapa.objects.create(ano=self.ano, codigo="3EF", escala_max=500, ordem=0)
        nao_canonica = MatrizEtapaCC.objects.create(matriz=self.matriz, etapa=e3, componente=self.lp, ano=self.ano, passo=25)
        r = self.apontar(nao_canonica)
        self.assertContains(r, "Não apontado: a base precisa ser etapa canônica")
        self.assertContains(self.apontar("x"), "Não apontado: escolha a base.")
        self.assertFalse(self.do_projeto().exists())

    def test_get_volta_a_aba(self):
        self.assertRedirects(self.client.get(self.url_apontar), self.url, fetch_redirect_response=False)

    def test_revista_validada_abre_o_modal_e_so_grava_confirmado(self):
        """Apontar muda a revista: passa pelo modal de impacto, como toda gravação que tira o Validado (D-202)."""
        validar(self.go["LP"])
        r = self.apontar(self.mec5)
        self.assertRedirects(r, f"{self.url}&apontar={self.e4.pk}-{self.lp.pk}-{self.mec5.pk}")
        self.assertFalse(self.do_projeto().exists())
        self.assertTrue(esta_validada(self.go["LP"]))
        self.assertContains(r, f'data-form="apontar-{self.e4.pk}-{self.lp.pk}"')  # o modal, ligado ao form da linha
        self.assertContains(r, f"<li>{self.go['LP']}</li>")
        self.assertContains(r, f'<option value="{self.mec5.pk}" selected>5EF</option>')
        r = self.apontar(self.mec5, confirmar_impacto="on")
        self.assertRedirects(r, self.url)
        self.assertTrue(self.do_projeto().exists())
        self.assertFalse(esta_validada(self.go["LP"]))
        self.assertContains(r, "1 revista(s) perderam o “Validado”")

    def test_sem_revista_validada_grava_direto(self):
        validar(self.go["MT"])  # outro componente: apontar 4EF LP não muda a revista MT
        self.assertRedirects(self.apontar(self.mec5), self.url)
        self.assertTrue(self.do_projeto().exists())
        self.assertTrue(esta_validada(self.go["MT"]))

    def test_aba_passos_rotula_etapa_do_projeto(self):
        criar(self.projeto_go, self.e4, self.lp, self.ped, self.mec5)
        r = self.client.get(reverse("ui_projeto", args=[self.projeto_go.pk]) + "?aba=passos")
        chave = f"{self.e4.pk}-{self.lp.pk}"
        self.assertContains(r, f'id="passo-{chave}-matriz">Etapa do projeto: 25</p>')
        self.assertContains(r, f'id="passo-{self.e5.pk}-{self.lp.pk}-matriz">Matriz: 25</p>')


class DesfazerApontamentoTest(EtapaNaoCanonica):
    """Desfazer o apontamento pela aba Matriz: confirmação forte (D-181) e aviso do Validado (D-287)."""

    def setUp(self):
        super().setUp()
        self.mec = criar(self.projeto_go, self.e4, self.lp, self.ped, self.mec5)
        self.url_desfazer = reverse("ui_projeto_etapa_desfazer", args=[self.projeto_go.pk, self.mec.pk])

    def desfazer(self, confirmacao="4EF LP"):
        sessao = self.client.get(self.url_desfazer).wsgi_request.bloqueio["sessao"]
        return self.client.post(self.url_desfazer, {"confirmacao": confirmacao, CAMPO_SESSAO: sessao}, follow=True)

    def test_aba_matriz_tem_o_link_e_a_pagina_conta_o_que_sai(self):
        self.assertContains(self.client.get(self.url), f'href="{self.url_desfazer}"')
        r = self.client.get(self.url_desfazer)
        self.assertContains(r, "Desfazer o apontamento de 4EF LP")
        self.assertContains(r, "2 descritor(es) e 3 tarefa(s)")
        self.assertContains(r, 'data-confirmar="4EF LP"')
        self.assertNotContains(r, "Perde o “Validado”")

    def test_codigo_errado_nao_apaga(self):
        r = self.desfazer("4EF")
        self.assertContains(r, "o código não confere")
        self.assertTrue(self.do_projeto().exists())

    def test_desfaz_e_a_etapa_volta_a_ficar_sem_base(self):
        r = self.desfazer()
        self.assertRedirects(r, self.url)
        self.assertFalse(self.do_projeto().exists())
        self.assertFalse(Descritor.objects.filter(matriz_etapa_cc_id=self.mec.pk).exists())
        self.assertTrue(Descritor.objects.filter(matriz_etapa_cc=self.mec5).exists())  # a base fica
        self.assertIn("etapa_sem_base", [p.codigo for p in pendencias(carregar(self.go["LP"].pk))])
        self.assertContains(r, "Apontamento de 4EF LP desfeito")
        self.assertContains(r, 'name="base"')  # pode apontar de novo
        h = MatrizEtapaCC.history.filter(id=self.mec.pk).first()
        self.assertEqual((h.history_type, h.history_user), ("-", self.ped))

    def test_revista_validada_aparece_na_confirmacao_e_no_aviso(self):
        validar(self.go["LP"])
        self.assertContains(self.client.get(self.url_desfazer), "Perde o “Validado”", count=1)
        r = self.desfazer()
        self.assertFalse(esta_validada(self.go["LP"]))
        self.assertContains(r, "1 revista(s) perderam o “Validado”")

    def test_recusas(self):
        self.client.post(self.url_desfazer, {"confirmacao": "4EF LP", CAMPO_SESSAO: "outra-aba"})
        self.assertTrue(self.do_projeto().exists())  # sem o bloqueio da ficha
        # outra pessoa com a etapa aberta no editor da matriz
        self.assertTrue(bloqueio.adquirir(self.mec, self.outro, "editor-do-outro"))
        self.assertContains(self.desfazer(), "Não desfeito: outro está editando esta etapa")
        self.assertTrue(self.do_projeto().exists())
        # etapa de matriz ou de outro projeto: 404
        url = reverse("ui_projeto_etapa_desfazer", args=[self.projeto_go.pk, self.mec5.pk])
        self.assertEqual(self.client.get(url).status_code, 404)
        self.client.force_login(self.imp)
        self.assertNotContains(self.client.get(self.url), f'href="{self.url_desfazer}"')
        self.assertEqual(self.client.post(self.url_desfazer, {"confirmacao": "4EF LP"}).status_code, 403)
        self.assertTrue(self.do_projeto().exists())


class EditarSoNesteProjetoTest(EtapaNaoCanonica):
    """Etapa 7b (D-288): a etapa que a matriz tem ganha cópia do projeto pelo botão, e a cópia sempre vale."""

    def copiar(self, **extra):
        sessao = self.client.get(self.url).wsgi_request.bloqueio["sessao"]
        dados = {"etapa": self.e5.pk, "componente": self.lp.pk, CAMPO_SESSAO: sessao, **extra}
        return self.client.post(self.url_apontar, dados, follow=True)

    def test_linha_de_etapa_da_matriz_tem_editar_so_neste_projeto(self):
        r = self.client.get(self.url)
        self.assertContains(r, "usa a matriz Comunitária", count=3)  # 5EF LP, 9EF LP e 5EF MT
        self.assertContains(r, "Editar só neste projeto<span", count=3)
        self.client.force_login(self.imp)
        self.assertNotContains(self.client.get(self.url), "Editar só neste projeto<span")

    def test_editar_so_neste_projeto_cria_a_copia_e_abre_o_editor(self):
        antes = pendencias(carregar(self.go["LP"].pk))
        r = self.copiar()
        mec = self.do_projeto().get()
        self.assertEqual((mec.etapa, mec.componente, mec.base), (self.e5, self.lp, self.mec5))
        self.assertRedirects(r, reverse("ui_matriz_mec", args=[mec.pk]))
        self.assertContains(r, "5EF LP: cópia criada")
        self.assertEqual(pendencias(carregar(self.go["LP"].pk)), antes)  # nenhuma pendência nova
        r = self.client.get(self.url)
        self.assertContains(r, "cópia do projeto · base: 5EF LP da Comunitária (2026)")
        self.assertContains(r, "Desfazer a cópia")

    def test_copia_local_com_revista_validada_passa_pela_simulacao(self):
        """A cópia nasce igual à matriz: a simulação roda e ninguém perde o Validado, então grava direto."""
        gravar_cortes(self.projeto_go.parceiro_ano, [(self.e5, self.lp, [100, 200, 250, 300])], self.usuario)
        validar(self.go["LP"])
        self.copiar()
        self.assertTrue(self.do_projeto().exists())
        self.assertTrue(esta_validada(self.go["LP"]))

    def test_desfazer_copia_local_volta_a_usar_a_matriz(self):
        mec = criar(self.projeto_go, self.e5, self.lp, self.ped)
        Descritor.objects.filter(matriz_etapa_cc=mec, codigo="D01").update(descricao="Só do GO")
        url = reverse("ui_projeto_etapa_desfazer", args=[self.projeto_go.pk, mec.pk])
        r = self.client.get(url)
        self.assertContains(r, "a revista volta a usar a etapa da matriz")
        self.client.post(url, {"confirmacao": "5EF LP", CAMPO_SESSAO: r.wsgi_request.bloqueio["sessao"]})
        self.assertFalse(self.do_projeto().exists())
        from nucleo.servicos.resolver import resolver

        self.assertEqual(resolver(carregar(self.go["LP"].pk))["f1"]["dados"]["5ef"]["D01"]["description"], "Descritor 1 LP")
