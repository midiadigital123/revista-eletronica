"""Impresso B (/ui/impresso/<ano>/, T26/T27): critérios de aceite de docs/telas/fichas/impresso.md pelo client."""

from django.db import transaction
from django.urls import reverse

from nucleo.models import Ano, FotoRevista
from nucleo.models.revista import Motivo
from nucleo.servicos import validacao
from nucleo.servicos.resolver import carregar, hash_validado
from nucleo.tests.test_admin_projeto import Base, mensagens
from nucleo.tests.test_painel import SVG_B, completar, trocar_svg
from nucleo.tests.test_resolver import usuario

HTMX = {"HTTP_HX_REQUEST": "true"}


class ImpressoUiTest(Base):
    def setUp(self):
        super().setUp()
        self.rev = self.go["LP"]
        completar(self.rev)
        self.url = reverse("ui_impresso", args=[2026])
        self.marcar_url = reverse("ui_impresso_marcar", args=[2026, self.rev.pk])

    def validar(self):
        with transaction.atomic():
            self.assertIsNone(validacao.validar(self.rev.pk, hash_validado(carregar(self.rev.pk)), self.ped))

    def abrir(self, **extra):
        r = self.client.get(self.url, {"revista": self.rev.pk}, **extra)
        self.assertEqual(r.status_code, 200)
        return r

    def marcar(self, hash_visto=None):
        hash_visto = hash_visto or self.abrir().context["detalhe"]["hash"]
        return self.client.post(self.marcar_url, {"hash_visto": hash_visto}, follow=True)

    def test_get_com_permissao_mostra_lista_e_diff(self):
        r = self.abrir()
        self.assertTemplateUsed(r, "ui/base.html")
        self.assertEqual(r.context["secao"], "impresso")
        self.assertIn(self.rev.pk, [i["revista"].pk for i in r.context["itens"]])
        self.assertContains(r, "Primeira entrega")
        self.assertContains(r, "Copiar texto novo")
        self.assertContains(r, reverse("impresso_planilhas", args=[self.rev.pk]))
        self.assertContains(r, "Aguardando “Validado”")
        self.assertNotContains(r, 'id="botao-impressa"')  # sem "Validado"
        self.assertEqual(list(r.context["detalhe"]["mudancas"]), ["F1", "F2"])
        self.assertRedirects(self.client.get(reverse("ui_impresso")), self.url)

    def test_htmx_devolve_so_o_detalhe(self):
        r = self.abrir(**HTMX)
        self.assertTemplateUsed(r, "ui/parciais/impresso_detalhe.html")
        self.assertTemplateNotUsed(r, "ui/base.html")
        self.assertContains(r, str(self.rev))
        self.assertIn("HX-Request", r["Vary"])  # o Voltar não reaproveita o fragmento como página
        self.assertEqual(self.client.get(self.url, {"revista": 999999}, **HTMX).status_code, 404)
        # Revista de 2026 pedida por outro ano: 404 no detalhe e no marcar.
        Ano.objects.create(ano=2025)
        outro = reverse("ui_impresso", args=[2025])
        self.assertEqual(self.client.get(outro, {"revista": self.rev.pk}, **HTMX).status_code, 404)
        self.client.force_login(self.imp)
        self.assertEqual(self.client.post(reverse("ui_impresso_marcar", args=[2025, self.rev.pk])).status_code, 404)

    def test_restauracao_de_historico_devolve_a_pagina_inteira(self):
        r = self.abrir(**HTMX, HTTP_HX_HISTORY_RESTORE_REQUEST="true")
        self.assertTemplateUsed(r, "ui/base.html")
        self.assertIn("HX-Request", r["Vary"])

    def test_so_leitura_para_quem_nao_marca(self):
        self.validar()
        r = self.abrir()  # Pedagógica: vê, não marca
        self.assertContains(r, "Só leitura: seu perfil vê o que mudou, mas não marca a revista como impressa.")
        self.assertNotContains(r, 'id="botao-impressa"')
        self.assertEqual(self.client.post(self.marcar_url, {"hash_visto": r.context["detalhe"]["hash"]}).status_code, 403)
        self.client.force_login(usuario("nada"))  # sem view_revista
        self.assertEqual(self.client.get(self.url).status_code, 403)
        self.assertFalse(FotoRevista.objects.exists())

    def test_impresso_marca_pela_regra_e_fica_em_dia(self):
        self.validar()
        self.client.force_login(self.imp)
        self.assertContains(self.abrir(), 'id="botao-impressa"')
        r = self.marcar()
        self.assertRedirects(r, f"{self.url}?revista={self.rev.pk}")
        self.assertIn("Revista Impressa Atualizada: os avisos desta revista foram zerados.", mensagens(r))
        foto = FotoRevista.objects.get(revista=self.rev)
        self.assertEqual((foto.motivo, foto.criada_por), (Motivo.IMPRESSO, self.imp))
        self.assertContains(r, "Impresso em dia")
        self.assertNotContains(r, 'id="botao-impressa"')

    def test_hash_velho_recusa_com_mensagem(self):
        self.validar()
        self.client.force_login(self.imp)
        visto = self.abrir().context["detalhe"]["hash"]
        trocar_svg(self.rev, SVG_B)
        r = self.marcar(visto)
        self.assertIn("Impresso não atualizado: a revista mudou depois que a página abriu; confira de novo.", mensagens(r))
        self.assertFalse(FotoRevista.objects.exists())

    def test_projeto_em_edicao_recusa(self):
        self.validar()
        self.client.force_login(self.imp)
        visto = self.abrir().context["detalhe"]["hash"]
        self.travar(self.projeto_go)
        self.assertIn("Impresso não atualizado: projeto em edição por outro.", mensagens(self.marcar(visto)))
        self.assertFalse(FotoRevista.objects.exists())

    def test_anonimo_vai_ao_login(self):
        self.client.logout()
        for r in (self.client.get(self.url), self.client.post(self.marcar_url, {"hash_visto": "x"})):
            self.assertEqual(r.status_code, 302)
            self.assertTrue(r["Location"].startswith(reverse("admin:login")))

    def test_ano_sem_revistas_mostra_vazio(self):
        Ano.objects.create(ano=2030)
        r = self.client.get(reverse("ui_impresso", args=[2030]))
        self.assertContains(r, "Nenhuma revista ativa neste ano")
        self.assertContains(r, reverse("cortes", args=[2030]))

    def test_navegacao_aponta_para_a_tela_b(self):
        self.assertContains(self.client.get(reverse("cortes", args=[2026])), f'href="{self.url}"')
