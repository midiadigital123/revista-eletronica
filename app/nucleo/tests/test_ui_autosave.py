"""Autosave por campo (U3): o protocolo JSON de `ui_autosave.responder_campo` em cada rota.

200 ok / 200 impacto (não grava) / 422 erros / 409 conflito ou bloqueio perdido / 403.
"""

import json

from django.urls import reverse

from nucleo.admin.bloqueio import CAMPO_SESSAO
from nucleo.models import Projeto, ProjetoCor, ProjetoPasso, Revista
from nucleo.servicos import bloqueio
from nucleo.tests.test_admin_padrao import esta_validada, validar
from nucleo.tests.test_admin_projeto import Base

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
