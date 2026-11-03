"""Autosave por campo (U3): o protocolo JSON de `ui_autosave.responder_campo` em cada rota.

200 ok / 200 impacto (não grava) / 422 erros / 409 conflito ou bloqueio perdido / 403.
"""

import json

from django.urls import reverse

from nucleo.admin.bloqueio import CAMPO_SESSAO
from nucleo.models import Ano, Componente, Corte, Descritor, Etapa, Projeto, ProjetoCor, ProjetoPasso, Tarefa
from nucleo.servicos import bloqueio
from nucleo.tests.test_admin_padrao import esta_validada, validar
from nucleo.tests.test_admin_projeto import Base
from nucleo.tests.test_item import Base as BaseMundo
from nucleo.tests.test_resolver import usuario

JSON = {"HTTP_ACCEPT": "application/json"}


class Protocolo:
    """Asserts do protocolo (mixin dos TestCase abaixo)."""

    def postar(self, url, **dados):
        return self.client.post(url, dados, **JSON)

    def assertSalvo(self, r):
        self.assertEqual(r.status_code, 200, r.content)
        corpo = r.json()
        self.assertTrue(corpo["ok"])
        self.assertRegex(corpo["salvo_em"], r"^\d\d:\d\d$")
        return corpo

    def assertNaoSalvo(self, r, status, chave):
        self.assertEqual(r.status_code, status, r.content)
        corpo = json.loads(r.content)
        self.assertFalse(corpo["ok"])
        self.assertNotIn("salvo_em", corpo)  # o campo não pode aparecer como "Salvo"
        self.assertTrue(corpo[chave])
        return corpo


class ProjetoCampoTest(Protocolo, Base):
    """U3a: a ficha do projeto (com a sessão de bloqueio) e a planilha de variáveis (sem sessão:
    cada envio trava o projeto na hora, como a planilha já fazia) gravam pela mesma rota."""

    def setUp(self):
        super().setUp()
        self.p = self.projeto_go
        self.url = reverse("ui_projeto_campo", args=[self.p.pk])
        self.rev = self.go["LP"]

    def sessao(self):
        r = self.client.get(reverse("ui_projeto", args=[self.p.pk]))
        return r.wsgi_request.bloqueio["sessao"]

    def test_200_grava_um_campo_da_ficha(self):
        self.assertSalvo(self.postar(self.url, campo="sigla_programa", valor="SAEGO", **{CAMPO_SESSAO: self.sessao()}))
        self.assertEqual(Projeto.objects.get(pk=self.p.pk).sigla_programa, "SAEGO")

    def test_200_planilha_sem_sessao_trava_na_hora(self):
        self.assertSalvo(self.postar(self.url, campo="sigla_programa", valor="SAEGO"))
        self.assertEqual(Projeto.objects.get(pk=self.p.pk).sigla_programa, "SAEGO")
        self.assertIsNone(bloqueio.quem_bloqueia(self.p))  # soltou depois de gravar

    def test_422_valor_invalido_e_campo_desconhecido(self):
        sessao = self.sessao()
        corpo = self.assertNaoSalvo(self.postar(self.url, campo="nome", valor="x" * 201, **{CAMPO_SESSAO: sessao}), 422, "erros")
        self.assertIn("200", corpo["erros"][0])
        self.assertNaoSalvo(self.postar(self.url, campo="nome_parceiro", valor="X", **{CAMPO_SESSAO: sessao}), 422, "erros")
        self.assertNaoSalvo(self.postar(self.url, campo="nome", valor="X"), 422, "erros")  # planilha: só variáveis
        self.assertEqual(Projeto.objects.get(pk=self.p.pk).nome, self.p.nome)

    def test_409_bloqueio_perdido_nao_grava(self):
        sessao = self.sessao()
        self.sessao()  # outra aba da mesma pessoa toma o bloqueio (D-191)
        corpo = self.assertNaoSalvo(self.postar(self.url, campo="sigla_programa", valor="X", **{CAMPO_SESSAO: sessao}), 409, "conflito")
        self.assertIn("perdeu o bloqueio", corpo["conflito"])
        self.assertNotEqual(Projeto.objects.get(pk=self.p.pk).sigla_programa, "X")

    def test_409_planilha_com_projeto_em_edicao(self):
        self.travar(self.p)
        corpo = self.assertNaoSalvo(self.postar(self.url, campo="sigla_programa", valor="X"), 409, "conflito")
        self.assertIn("em edição por outro", corpo["conflito"])
        self.assertNotEqual(Projeto.objects.get(pk=self.p.pk).sigla_programa, "X")

    def test_403_impresso_e_arquivado(self):
        self.client.force_login(self.imp)
        self.assertEqual(self.postar(self.url, campo="sigla_programa", valor="X").status_code, 403)
        self.assertEqual(self.postar(self.url, campo="sigla_programa", valor="X", **{CAMPO_SESSAO: "x"}).status_code, 403)
        self.client.force_login(self.ped)
        arquivado = Projeto.objects.filter(arquivado_em__isnull=False).first()
        if arquivado:
            url = reverse("ui_projeto_campo", args=[arquivado.pk])
            self.assertIn(self.postar(url, campo="sigla_programa", valor="X").status_code, (403, 409))

    def test_impacto_nao_grava_e_confirmado_grava(self):
        validar(self.rev)
        sessao = self.sessao()
        corpo = self.assertNaoSalvo(self.postar(self.url, campo="nome", valor="GO novo", **{CAMPO_SESSAO: sessao}), 200, "impacto")
        self.assertIn(str(self.rev), corpo["impacto"]["perdem"])
        self.assertGreaterEqual(corpo["impacto"]["afetadas"], 1)
        self.assertIn("tira o “Validado” de 1 revista(s)", corpo["impacto"]["html"])
        self.assertEqual(Projeto.objects.get(pk=self.p.pk).nome, self.p.nome)
        self.assertTrue(esta_validada(self.rev))

        self.assertSalvo(self.postar(self.url, campo="nome", valor="GO novo", confirmar_impacto="on", **{CAMPO_SESSAO: sessao}))
        self.assertEqual(Projeto.objects.get(pk=self.p.pk).nome, "GO novo")
        self.assertFalse(esta_validada(self.rev))

    def test_linha_de_passo_cria_edita_e_remove(self):
        sessao = self.sessao()
        linha = {CAMPO_SESSAO: sessao, "passos-7-id": "", "passos-7-etapa": self.e9.pk, "passos-7-componente": self.lp.pk}
        corpo = self.assertSalvo(self.postar(self.url, campo="passos-7-passo", valor="30", **linha, **{"passos-7-passo": "30"}))
        passo = ProjetoPasso.objects.get(projeto=self.p, etapa=self.e9, componente=self.lp)
        self.assertEqual((corpo["id"], passo.passo), (passo.pk, 30))

        linha["passos-7-id"] = passo.pk
        self.assertSalvo(self.postar(self.url, campo="passos-7-passo", valor="", **linha, **{"passos-7-passo": ""}))
        self.assertIsNone(ProjetoPasso.objects.get(pk=passo.pk).passo)

        corpo = self.assertSalvo(self.postar(self.url, campo="passos-7-DELETE", valor="on", **linha, **{"passos-7-DELETE": "on"}))
        self.assertTrue(corpo["removida"])
        self.assertFalse(ProjetoPasso.objects.filter(pk=passo.pk).exists())

    def test_linha_de_cor_incompleta_e_repetida(self):
        sessao = self.sessao()
        linha = {CAMPO_SESSAO: sessao, "cores-0-id": "", "cores-0-padrao": "", "cores-0-cor": "#112233"}
        self.assertNaoSalvo(self.postar(self.url, campo="cores-0-cor", valor="#112233", **linha), 422, "erros")
        linha["cores-0-padrao"] = "2"
        self.assertSalvo(self.postar(self.url, campo="cores-0-padrao", valor="2", **linha))
        linha["cores-1-id"], linha["cores-1-padrao"], linha["cores-1-cor"] = "", "2", "#445566"
        self.assertNaoSalvo(self.postar(self.url, campo="cores-1-padrao", valor="2", **linha), 422, "erros")
        self.assertEqual(ProjetoCor.objects.filter(projeto=self.p).count(), 1)

    def test_paginas_sem_salvar_e_com_autosave(self):
        r = self.client.get(reverse("ui_projeto", args=[self.p.pk]))
        self.assertNotContains(r, "Salvar projeto")
        self.assertContains(r, 'x-data="campoAuto"')
        self.assertContains(r, f'data-url="{self.url}"')
        self.assertContains(r, "data-status-salvo")
        r = self.client.get(reverse("ui_variaveis", args=[2026]))
        self.assertNotContains(r, "Salvar variáveis")
        self.assertNotContains(r, "alteração não salva")
        self.assertNotContains(r, "beforeunload")
        self.assertContains(r, 'x-data="campoAuto"')
        self.assertContains(r, f'data-url="{self.url}"')
        self.client.force_login(self.imp)
        self.assertNotContains(self.client.get(reverse("ui_variaveis", args=[2026])), "data-status-salvo")


class CortesCelulaTest(Protocolo, Base):
    """U3b: a grade de Cortes salva por célula. Sem bloqueio: o conflito é otimista pelo `original`
    (o texto que a célula tinha na tela)."""

    url = reverse("cortes_celula", args=[2026])

    def setUp(self):
        super().setUp()
        self.parceiro = self.projeto_go.parceiro_ano.parceiro
        self.chave = f"c-{self.parceiro.pk}-{self.e5.pk}-{self.lp.pk}"
        self.rev = self.go["LP"]

    def corte(self, etapa=None, cc=None):
        c = Corte.objects.filter(parceiro_ano__parceiro=self.parceiro, etapa=etapa or self.e5, componente=cc or self.lp).first()
        return c and c.valores

    def test_200_grava_a_celula_e_normaliza(self):
        corpo = self.assertSalvo(self.postar(self.url, campo=self.chave, valor="100 200 250 310", original="100, 200, 250, 300"))
        self.assertEqual(corpo["valor"], "100, 200, 250, 310")
        self.assertEqual(self.corte(), [100, 200, 250, 310])

    def test_200_celula_vazia_cria_e_apaga_o_corte(self):
        chave = f"c-{self.parceiro.pk}-{self.e9.pk}-{self.mt.pk}"
        self.assertSalvo(self.postar(self.url, campo=chave, valor="120, 240", original=""))
        self.assertEqual(self.corte(self.e9, self.mt), [120, 240])
        self.assertSalvo(self.postar(self.url, campo=chave, valor="", original="120, 240"))
        self.assertIsNone(self.corte(self.e9, self.mt))

    def test_422_texto_e_ordem(self):
        for valor, erro in (("abc", "inteiros"), ("300, 200", "crescentes"), ("600", "entre 1 e 499")):
            with self.subTest(valor):
                corpo = self.assertNaoSalvo(self.postar(self.url, campo=self.chave, valor=valor, original="100, 200, 250, 300"), 422, "erros")
                self.assertIn(erro, " ".join(corpo["erros"]))
        self.assertNaoSalvo(self.postar(self.url, campo="c-0-0-0", valor="1", original=""), 422, "erros")
        self.assertEqual(self.corte(), [100, 200, 250, 300])

    def test_409_duas_abas_original_diferente(self):
        # A aba 1 grava; a aba 2 ainda tem o valor antigo na tela e não pode gravar por cima.
        self.assertSalvo(self.postar(self.url, campo=self.chave, valor="110, 200, 250, 300", original="100, 200, 250, 300"))
        corpo = self.assertNaoSalvo(
            self.postar(self.url, campo=self.chave, valor="120, 200, 250, 300", original="100, 200, 250, 300"), 409, "conflito"
        )
        self.assertEqual(corpo["atual"], "110, 200, 250, 300")
        self.assertEqual(self.corte(), [110, 200, 250, 300])
        # "Tentar de novo" manda o atual como original: sobrescreve de propósito.
        self.assertSalvo(self.postar(self.url, campo=self.chave, valor="120, 200, 250, 300", original=corpo["atual"]))
        self.assertEqual(self.corte(), [120, 200, 250, 300])

    def test_403_impresso(self):
        self.client.force_login(self.imp)
        self.assertEqual(self.postar(self.url, campo=self.chave, valor="1", original="100, 200, 250, 300").status_code, 403)
        self.assertEqual(self.corte(), [100, 200, 250, 300])

    def test_impacto_nao_grava_e_confirmado_grava(self):
        validar(self.rev)
        dados = {"campo": self.chave, "valor": "110, 200, 250, 300", "original": "100, 200, 250, 300"}
        corpo = self.assertNaoSalvo(self.postar(self.url, **dados), 200, "impacto")
        self.assertIn(str(self.rev), corpo["impacto"]["perdem"])
        self.assertEqual(self.corte(), [100, 200, 250, 300])
        self.assertTrue(esta_validada(self.rev))
        self.assertSalvo(self.postar(self.url, confirmar_impacto="on", **dados))
        self.assertEqual(self.corte(), [110, 200, 250, 300])
        self.assertFalse(esta_validada(self.rev))

    def test_pagina_sem_salvar_nem_contador(self):
        r = self.client.get(reverse("cortes", args=[2026]))
        self.assertNotContains(r, "Salvar cortes")
        self.assertNotContains(r, "alteração não salva")
        self.assertNotContains(r, "beforeunload")
        self.assertContains(r, f'data-url="{self.url}"')
        self.assertContains(r, "data-status-salvo")


class AnoCampoTest(Protocolo, Base):
    """U3b: na página do ano salvam sozinhos a escala máxima (sem corte nem matriz), a ordem da
    etapa e o nome do componente. Código é imutável; a linha nova ainda grava pelo botão (U4)."""

    def setUp(self):
        super().setUp()
        self.livre = Etapa.objects.create(ano=self.ano, codigo="1EM", escala_max=500, ordem=9)

    def url(self, tabela, pk):
        return reverse("ui_ano_campo", args=[2026, tabela, pk])

    def test_200_escala_ordem_e_nome(self):
        self.assertSalvo(self.postar(self.url("etapas", self.livre.pk), campo="escala_max", valor="1000"))
        self.assertSalvo(self.postar(self.url("etapas", self.livre.pk), campo="ordem", valor="4"))
        self.livre.refresh_from_db()
        self.assertEqual((self.livre.escala_max, self.livre.ordem), (1000, 4))
        self.assertSalvo(self.postar(self.url("componentes", self.mt.pk), campo="nome", valor="Matemática E2E"))
        self.assertEqual(Componente.objects.get(pk=self.mt.pk).nome, "Matemática E2E")

    def test_422_codigo_escala_travada_e_valor_ruim(self):
        self.assertNaoSalvo(self.postar(self.url("etapas", self.livre.pk), campo="codigo", valor="XX"), 422, "erros")
        self.assertNaoSalvo(self.postar(self.url("etapas", self.e5.pk), campo="escala_max", valor="999"), 422, "erros")
        self.assertNaoSalvo(self.postar(self.url("etapas", self.livre.pk), campo="escala_max", valor="abc"), 422, "erros")
        self.assertNaoSalvo(self.postar(self.url("componentes", self.mt.pk), campo="nome", valor=""), 422, "erros")
        self.e5.refresh_from_db()
        self.assertEqual((self.e5.codigo, self.e5.escala_max), ("5EF", 500))

    def test_403_impresso_e_404_de_outro_ano(self):
        self.client.force_login(self.imp)
        self.assertEqual(self.postar(self.url("componentes", self.mt.pk), campo="nome", valor="X").status_code, 403)
        self.client.force_login(self.ped)
        outro = Componente.objects.create(ano=Ano.objects.create(ano=2027), codigo="LP", nome="LP")
        self.assertEqual(self.postar(self.url("componentes", outro.pk), campo="nome", valor="X").status_code, 404)

    def test_impacto_e_simulado_e_nome_fora_do_hash_grava_direto(self):
        # O nome do componente não entra no hash da revista: a simulação não acha quem perca o
        # "Validado" e grava sem modal. (Escala e código, que mudariam a revista, não editam aqui.)
        rev = self.go["LP"]
        validar(rev)
        self.assertSalvo(self.postar(self.url("componentes", self.lp.pk), campo="nome", valor="Português"))
        self.assertEqual(Componente.objects.get(pk=self.lp.pk).nome, "Português")
        self.assertTrue(esta_validada(rev))

    def test_pagina_sem_salvar_e_linha_nova_pelo_botao(self):
        r = self.client.get(reverse("ui_ano", args=[2026]))
        self.assertNotContains(r, "Salvar etapas")
        self.assertNotContains(r, "Salvar componentes")
        self.assertContains(r, "Adicionar etapa")
        self.assertContains(r, "Adicionar componente")
        self.assertContains(r, f'data-url="{self.url("componentes", self.lp.pk)}"')
        self.assertContains(r, "data-manual")


class DescritorCampoTest(Protocolo, BaseMundo):
    """U3b: o descritor e as tarefas salvas salvam sozinhos, sob o bloqueio da MEC."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.imp = usuario("imp", "Impresso")

    def setUp(self):
        super().setUp()
        self.d = self.tarefa.descritor
        self.mec = self.d.matriz_etapa_cc
        self.url = reverse("ui_matriz_campo", args=[self.mec.pk, self.d.pk])
        self.pagina = reverse("ui_matriz_descritor", args=[self.mec.pk, self.d.pk])

    def sessao(self):
        return self.client.get(self.pagina).wsgi_request.bloqueio["sessao"]

    def linha(self, sessao, **mudar):
        t = self.tarefa
        dados = {CAMPO_SESSAO: sessao, "tarefas-0-id": t.pk, "tarefas-0-inicio": t.inicio, "tarefas-0-fim": t.fim,
                 "tarefas-0-texto": t.texto, "tarefas-0-ordem": t.ordem}  # fmt: skip
        return {**dados, **{f"tarefas-0-{k}": v for k, v in mudar.items()}}

    def test_200_campo_e_tarefa(self):
        sessao = self.sessao()
        self.assertSalvo(self.postar(self.url, campo="descricao", valor="Descrição E2E", **{CAMPO_SESSAO: sessao}))
        self.assertSalvo(self.postar(self.url, campo="prerequisitos", valor="a\nb", **{CAMPO_SESSAO: sessao}))
        self.d.refresh_from_db()
        self.assertEqual((self.d.descricao, self.d.prerequisitos), ("Descrição E2E", ["a", "b"]))
        self.assertSalvo(self.postar(self.url, campo="tarefas-0-texto", valor="Tarefa E2E", **self.linha(sessao, texto="Tarefa E2E")))
        self.assertEqual(Tarefa.objects.get(pk=self.tarefa.pk).texto, "Tarefa E2E")

    def test_422_codigo_repetido_e_faixa_invertida(self):
        sessao = self.sessao()
        outro = Descritor.objects.filter(matriz_etapa_cc=self.mec).exclude(pk=self.d.pk).first()
        self.assertNaoSalvo(self.postar(self.url, campo="codigo", valor=outro.codigo, **{CAMPO_SESSAO: sessao}), 422, "erros")
        self.assertNaoSalvo(self.postar(self.url, campo="codigo", valor="", **{CAMPO_SESSAO: sessao}), 422, "erros")
        linha = self.linha(sessao, inicio=400, fim=100)
        self.assertNaoSalvo(self.postar(self.url, campo="tarefas-0-inicio", valor="400", **linha), 422, "erros")
        self.assertEqual(Tarefa.objects.get(pk=self.tarefa.pk).inicio, self.tarefa.inicio)

    def test_409_bloqueio_perdido(self):
        sessao = self.sessao()
        self.assertTrue(bloqueio.adquirir(self.mec, self.root, "outra-aba"))  # a mesma pessoa em outra aba
        corpo = self.assertNaoSalvo(self.postar(self.url, campo="descricao", valor="X", **{CAMPO_SESSAO: sessao}), 409, "conflito")
        self.assertIn("perdeu o bloqueio", corpo["conflito"])
        self.assertNotEqual(Descritor.objects.get(pk=self.d.pk).descricao, "X")

    def test_403_impresso(self):
        self.client.force_login(self.imp)
        self.assertEqual(self.postar(self.url, campo="descricao", valor="X", **{CAMPO_SESSAO: "x"}).status_code, 403)

    def test_impacto_nao_grava_e_confirmado_grava(self):
        rev = self.go["LP"]
        validar(rev)
        sessao = self.sessao()
        dados = {"campo": "descricao", "valor": "Nova", "form_id": "form-descritor", CAMPO_SESSAO: sessao}
        corpo = self.assertNaoSalvo(self.postar(self.url, **dados), 200, "impacto")
        self.assertIn(str(rev), corpo["impacto"]["perdem"])
        self.assertIn('data-form="form-descritor"', corpo["impacto"]["html"])
        self.assertNotEqual(Descritor.objects.get(pk=self.d.pk).descricao, "Nova")
        self.assertSalvo(self.postar(self.url, confirmar_impacto="on", **dados))
        self.assertEqual(Descritor.objects.get(pk=self.d.pk).descricao, "Nova")
        self.assertFalse(esta_validada(rev))

    def test_painel_sem_salvar_e_tarefa_nova_pelo_botao(self):
        r = self.client.get(self.pagina)
        self.assertNotContains(r, "Salvar descritor")
        self.assertContains(r, 'x-data="campoAuto"')
        self.assertContains(r, f'data-url="{self.url}"')
        self.assertContains(r, "Incluir tarefa")
