"""S12: painel da temporada, "Validado" na revista e validação em lote (D-074, D-089, D-094, D-120)."""

import re
from unittest import mock

from django.contrib.auth import get_user_model
from django.db import connection, transaction
from django.test.utils import CaptureQueriesContext
from django.test import TransactionTestCase
from django.urls import reverse

from nucleo.admin.bloqueio import CAMPO_SESSAO
from nucleo.models import Bloqueio, Revista, RevistaFasciculo, RevistaSecao, TemplateVersao
from nucleo.servicos import bloqueio, resolver, validacao
from nucleo.servicos.resolver import carregar, hash_validado
from nucleo.tests.test_admin_projeto import Base, mensagens
from nucleo.tests.test_resolver import F1, Mundo

SVG_A, SVG_B = "a" * 64, "b" * 64


def completar(revista, svg=SVG_A):
    """Sem pendências: SVG com os ids do F2 e capa (só os campos; o resolver não lê o arquivo)."""
    Revista.objects.filter(pk=revista.pk).update(
        svg_f2="f2/x.svg", svg_sha256=svg, svg_ids=["passo1", "btn-action-p2"], capa="capas/x.png", capa_sha256="c" * 64
    )


def trocar_svg(revista, svg):
    Revista.objects.filter(pk=revista.pk).update(svg_sha256=svg)


class ValidadoTest(Base):
    def setUp(self):
        super().setUp()
        self.rev = self.go["LP"]
        completar(self.rev)
        self.url = reverse("admin:nucleo_revista_change", args=[self.rev.pk])
        self.painel = reverse("painel", args=[2026])

    def abrir(self):
        Bloqueio.objects.all().delete()  # o pagehide da carga anterior
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)
        return r

    def validar(self, aberta=None, **troca):
        aberta = aberta or self.abrir()
        dados = {CAMPO_SESSAO: aberta.context["bloqueio"]["sessao"], "hash_visto": aberta.context["validacao"]["hash"]}
        dados.update(troca)
        return self.client.post(reverse("admin:nucleo_revista_validar", args=[self.rev.pk]), dados, follow=True)

    def celula(self, coluna, revista=None):
        r = self.client.get(self.painel)
        linha = next(x for x in r.context["linhas"] if x["revista"].pk == (revista or self.rev).pk)
        return linha["faltas"][coluna]

    def test_valida_e_grava(self):
        r = self.abrir()
        self.assertContains(r, 'id="botao-validado"')
        self.assertContains(r, f'name="hash_visto" value="{r.context["validacao"]["hash"]}"')
        sessao = r.context["bloqueio"]["sessao"]
        r = self.validar(r)
        self.assertIn("Revista validada.", mensagens(r))
        self.assertFalse(Bloqueio.objects.filter(sessao_edicao=sessao).exists())  # liberou para a próxima carga
        rev = Revista.objects.get(pk=self.rev.pk)
        self.assertEqual(rev.hash_validado, hash_validado(carregar(rev.pk)))
        self.assertEqual(rev.validado_por, self.ped)
        self.assertIsNotNone(rev.validado_em)
        self.assertContains(r, "✓ Validado")
        self.assertTrue(self.celula("validado")["ok"])

    def test_hash_velho_recusado(self):
        aberta = self.abrir()
        trocar_svg(self.rev, SVG_B)  # mudou depois que a página abriu
        r = self.validar(aberta)
        self.assertIn("Não validada: a revista mudou depois que a página abriu; confira de novo.", mensagens(r))
        self.assertIsNone(Revista.objects.get(pk=self.rev.pk).hash_validado)

    def test_pendencia_recusa(self):
        Revista.objects.filter(pk=self.rev.pk).update(capa=None, capa_sha256=None)
        aberta = self.abrir()
        self.assertContains(aberta, "Falta a imagem de capa.")
        r = self.validar(aberta)
        self.assertIn("Não validada: pendências: Falta a imagem de capa.", mensagens(r))
        self.assertIsNone(Revista.objects.get(pk=self.rev.pk).hash_validado)

    def test_sem_bloqueio_recusa(self):
        aberta = self.abrir()
        Bloqueio.objects.all().delete()
        bloqueio.adquirir(self.rev.projeto, self.outro, "aba-do-outro")  # outro abriu o projeto
        r = self.validar(aberta)
        self.assertIn("Não validada: você não tem o bloqueio de edição desta revista; recarregue a página.", mensagens(r))
        self.assertIsNone(Revista.objects.get(pk=self.rev.pk).hash_validado)
        self.assertTrue(bloqueio.quem_bloqueia(self.rev.projeto).usuario == self.outro)  # não liberou o do outro

    def test_somente_leitura_sem_botao(self):
        bloqueio.adquirir(self.rev.projeto, self.outro, "aba-do-outro")
        r = self.client.get(self.url)
        self.assertNotContains(r, 'id="botao-validado"')

    def test_trocar_svg_derruba_e_desfazer_volta(self):
        self.validar()
        self.assertTrue(self.celula("validado")["ok"])
        trocar_svg(self.rev, SVG_B)
        self.assertFalse(self.celula("validado")["ok"])
        self.assertContains(self.abrir(), "a revista mudou depois do último")
        trocar_svg(self.rev, SVG_A)  # desfez: o hash volta e o "Validado" volta (D-094)
        self.assertTrue(self.celula("validado")["ok"])
        self.assertContains(self.abrir(), "✓ Validado")

    def test_secao_desatualizada_so_avisa(self):
        rf = RevistaFasciculo.objects.get(revista=self.rev, fasciculo="F1")
        v1 = TemplateVersao.objects.get(template=rf.template, numero=1)
        RevistaSecao.objects.create(revista_fasciculo=rf, template=rf.template, secao="fechamento", texto="Meu fim.", template_versao=v1)
        TemplateVersao.objects.create(template=rf.template, numero=2, texto=F1.replace("Fim.", "Fim novo."))
        aberta = self.abrir()
        self.assertContains(aberta, "seções desatualizadas (F1 fechamento)")
        self.assertIn("Revista validada.", mensagens(self.validar(aberta)))

    def test_permissoes(self):
        # Impresso vê o painel, mas não valida (nem o botão, nem o POST, nem o lote).
        self.client.force_login(self.imp)
        r = self.client.get(self.painel)
        self.assertEqual(r.status_code, 200)
        self.assertNotContains(r, "Validar selecionadas")
        self.assertNotContains(self.client.get(self.url), 'id="botao-validado"')
        url = reverse("admin:nucleo_revista_validar", args=[self.rev.pk])
        self.assertEqual(self.client.post(url, {"hash_visto": hash_validado(carregar(self.rev.pk))}).status_code, 403)
        self.assertEqual(self.client.get(reverse("painel_validar", args=[2026])).status_code, 403)
        self.assertIsNone(Revista.objects.get(pk=self.rev.pk).hash_validado)
        # Pedagógica valida; anônimo vai ao login; o validar só aceita POST.
        self.client.force_login(self.ped)
        self.assertContains(self.client.get(self.painel), "Validar selecionadas")
        self.assertEqual(self.client.get(url).status_code, 405)
        self.client.logout()
        self.assertRedirects(self.client.get(self.painel), f"{reverse('admin:login')}?next={self.painel}")

    def test_painel_colunas_links_e_filtros(self):
        r = self.client.get(self.painel)
        rotulos = [str(x["revista"]) for x in r.context["linhas"]]
        self.assertEqual(len(rotulos), 4)  # GO LP/MT e PE LP/MT
        go_mt = self.go["MT"]
        falta_svg = self.celula("svg", go_mt)
        self.assertEqual((falta_svg["ok"], falta_svg["dica"]), (False, "Falta o SVG do F2."))
        self.assertEqual(falta_svg["link"], reverse("ui_revista_editar", args=[2026, go_mt.pk]))
        self.assertTrue(self.celula("svg")["ok"])
        self.assertContains(r, f'<a class="status status-falta" href="{falta_svg["link"]}" title="Falta o SVG do F2.">')
        # Filtro por pendência: só as sem SVG (GO MT, PE LP, PE MT).
        r = self.client.get(self.painel, {"falta": "svg"})
        self.assertEqual(len(r.context["linhas"]), 3)
        # Pendência + parceiro.
        r = self.client.get(self.painel, {"falta": "svg", "parceiro": self.go["LP"].projeto.parceiro_ano.parceiro_id})
        self.assertEqual([x["revista"].pk for x in r.context["linhas"]], [go_mt.pk])
        # Variáveis: nome padrão do projeto aponta para o projeto.
        self.projeto_go.nome = "GO - NOME DO PROJETO"
        self.projeto_go.save()
        self.assertEqual(self.celula("variaveis")["link"], reverse("ui_projeto", args=[self.projeto_go.pk]))

    def test_resolvido_uma_vez_por_linha(self):
        with mock.patch.object(resolver, "resolver", wraps=resolver.resolver) as espiao:
            r = self.client.get(self.painel)
        self.assertEqual(espiao.call_count, len(r.context["linhas"]))

    def test_teto_de_queries_por_linha(self):
        def consultas(**filtro):
            with CaptureQueriesContext(connection) as c:
                r = self.client.get(self.painel, filtro)
            return len(c.captured_queries), len(r.context["linhas"])

        todas, n_todas = consultas()
        go, n_go = consultas(parceiro=self.go["LP"].projeto.parceiro_ano.parceiro_id)
        por_linha = (todas - go) / (n_todas - n_go)
        self.assertLessEqual(por_linha, 16, por_linha)  # medido no S12: 15 (resolver + pendências + foto); +1 nomes do ano (D-175)


class LoteTest(TransactionTestCase):
    """Cada par (revista, hash) é gravado ou recusado sozinho; commits reais (escrever_travado)."""

    def setUp(self):
        Mundo.montar(self)
        self.admin = get_user_model().objects.create(username="chefe", is_staff=True, is_superuser=True)
        self.client.force_login(self.admin)
        self.alvos = [self.go["LP"], self.go["MT"], self.pe["LP"]]
        for r in self.alvos:
            completar(r)
        self.url = reverse("painel_validar", args=[2026])

    def pares(self):
        r = self.client.get(self.url, {"revista": [r.pk for r in self.alvos]})
        self.assertEqual(len(r.context["itens"]), 3)
        self.assertContains(r, "Sem foto do impresso para comparar")
        return re.findall(r'name="par" value="([^"]+)"', r.content.decode())

    def test_lote_de_3_com_1_alterado_no_meio_grava_2(self):
        pares = self.pares()
        trocar_svg(self.pe["LP"], SVG_B)  # mudou entre ver o diff e enviar
        r = self.client.post(self.url, {"par": pares}, follow=True)
        msgs = mensagens(r)
        self.assertIn("Validadas 2 revista(s).", msgs)
        self.assertTrue(any("Projeto PE · LP (a revista mudou depois que a página abriu" in m for m in msgs), msgs)
        validadas = set(Revista.objects.filter(hash_validado__isnull=False).values_list("pk", flat=True))
        self.assertEqual(validadas, {self.go["LP"].pk, self.go["MT"].pk})

    def test_lote_com_ja_validada_mantem_quem_validou(self):
        outro = get_user_model().objects.create(username="outro")
        rev = carregar(self.go["LP"].pk)
        with transaction.atomic():
            self.assertIsNone(validacao.validar(rev.pk, hash_validado(rev), outro))
        antes = Revista.objects.get(pk=rev.pk)
        r = self.client.get(self.url, {"revista": [x.pk for x in self.alvos]})
        self.assertNotContains(r, f'value="{rev.pk}:{antes.hash_validado}" checked')
        pares = re.findall(r'name="par" value="([^"]+)"', r.content.decode())
        msgs = mensagens(self.client.post(self.url, {"par": pares + ["999999:x"]}, follow=True))
        depois = Revista.objects.get(pk=rev.pk)
        self.assertEqual((depois.validado_por, depois.validado_em), (outro, antes.validado_em))
        self.assertIn("Validadas 3 revista(s).", msgs)
        self.assertTrue(any("revista 999999 (não encontrada ou arquivada)" in m for m in msgs), msgs)

    def test_lote_pula_projeto_em_edicao(self):
        pares = self.pares()
        outro = get_user_model().objects.create(username="outro")
        bloqueio.adquirir(self.pe["LP"].projeto, outro, "aba-do-outro")
        msgs = mensagens(self.client.post(self.url, {"par": pares}, follow=True))
        self.assertIn("Validadas 2 revista(s).", msgs)
        self.assertTrue(any("Projeto PE · LP (projeto em edição por outro)" in m for m in msgs), msgs)
