"""Lotes B (/ui/lotes/<ano>/matriz/ e /template/): critérios de aceite de docs/telas/fichas/lotes.md.

U7a: o GET destas rotas vai à Lista de Projetos (testes da tela em test_ui_projetos.py); aqui fica o
POST, que continua gravando pela mesma regra."""

from django.test import Client, TransactionTestCase
from django.urls import reverse

from nucleo.models import (
    Ano,
    Matriz,
    Parceiro,
    ParceiroAno,
    Projeto,
    RevistaFasciculo,
    RevistaSecao,
    TemplateVersao,
)
from nucleo.tests import test_admin_projeto
from nucleo.tests.test_admin_padrao import esta_validada, validar
from nucleo.tests.test_admin_projeto import ARQUIVADO, Base, mensagens
from nucleo.tests.test_resolver import usuario

HTMX = {"HTTP_HX_REQUEST": "true"}
LISTA = reverse("ui_projeto_lista", args=[2026])


class LoteMatrizUiTest(Base):
    url = reverse("ui_lotes_matriz", args=[2026])

    def test_post_grava_pela_regra_e_pula_travado(self):
        nova = Matriz.objects.create(ano=self.ano, nome="Nova")
        self.travar(self.projeto_go)
        pas = ParceiroAno.objects.filter(ano=self.ano)
        r = self.client.post(self.url, {"alvos": [pa.pk for pa in pas], "matriz": nova.pk}, follow=True)
        self.assertRedirects(r, LISTA)
        self.assertEqual(ParceiroAno.objects.get(parceiro__nome="PE").matriz, nova)
        self.assertEqual(ParceiroAno.objects.get(parceiro__nome="GO").matriz, self.matriz)
        self.assertIn("Matriz Nova escolhida para 1 parceiro(s).", mensagens(r))
        self.assertIn("Pulados: GO (projeto em edição por outro).", mensagens(r))

    def test_sem_projeto_ativo_grava_e_avisa(self):
        Projeto.objects.filter(pk=self.projeto_pe.pk).update(arquivado_em=ARQUIVADO)
        nova = Matriz.objects.create(ano=self.ano, nome="Nova")
        pe = ParceiroAno.objects.get(parceiro__nome="PE")
        self.client.post(self.url, {"alvos": [pe.pk], "matriz": nova.pk})
        self.assertEqual(ParceiroAno.objects.get(pk=pe.pk).matriz, nova)

    def test_erro_sem_marcar_e_matriz_de_outro_ano(self):
        r = self.client.post(self.url, {"matriz": ""})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Nada foi gravado: corrija os erros marcados.")
        self.assertContains(r, "Marque ao menos um parceiro.")
        self.assertContains(r, "Escolha a matriz.")
        velha = Matriz.objects.create(ano=Ano.objects.create(ano=2025), nome="Velha")
        pe = ParceiroAno.objects.get(parceiro__nome="PE")
        r = self.client.post(self.url, {"alvos": [pe.pk], "matriz": velha.pk})
        self.assertContains(r, "Escolha uma opção da lista; a lista mudou desde que a página abriu.")
        self.assertContains(r, f'value="{pe.pk}" id="alvo-{pe.pk}" checked')  # a seleção fica
        self.assertEqual(ParceiroAno.objects.get(pk=pe.pk).matriz, self.matriz)

    def test_htmx_devolve_o_form_com_valores_novos_e_mensagens_oob(self):
        nova = Matriz.objects.create(ano=self.ano, nome="Nova")
        pe = ParceiroAno.objects.get(parceiro__nome="PE")
        r = self.client.post(self.url, {"alvos": [pe.pk], "matriz": nova.pk}, **HTMX)
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "ui/parciais/lotes_matriz.html")
        self.assertTemplateNotUsed(r, "ui/base.html")
        self.assertContains(r, 'id="mensagens" class="mensagens-area" hx-swap-oob="true"')
        self.assertContains(r, "Matriz Nova escolhida para 1 parceiro(s).")
        self.assertNotContains(r, "checked")  # seleção limpa
        self.assertEqual(ParceiroAno.objects.get(pk=pe.pk).matriz, nova)

    def test_so_leitura_403_e_anonimo(self):
        self.client.force_login(self.imp)
        pe = ParceiroAno.objects.get(parceiro__nome="PE")
        self.assertEqual(self.client.post(self.url, {"alvos": [pe.pk], "matriz": self.matriz.pk}).status_code, 403)
        self.client.force_login(usuario("nada"))
        self.assertEqual(self.client.post(self.url, {"alvos": [pe.pk], "matriz": self.matriz.pk}).status_code, 403)
        self.client.logout()
        self.assertRedirects(self.client.get(self.url), f"{reverse('entrar')}?next={self.url}", fetch_redirect_response=False)

class LoteTemplateUiTest(Base):
    novo_template = test_admin_projeto.LoteTemplateTest.novo_template

    def url(self, componente=None):
        return reverse("ui_lotes_template", args=[2026]) + (f"?componente={componente.pk}" if componente else "")

    def test_post_troca_pula_copias_e_travado(self):
        f1 = self.novo_template(self.lp, "F1")
        f2 = self.novo_template(self.lp, "F2", nome="Outro F2")
        self.travar(self.projeto_pe)
        rf_go = RevistaFasciculo.objects.get(revista=self.go["LP"], fasciculo="F1")
        RevistaSecao.objects.create(
            revista_fasciculo=rf_go, template=rf_go.template, secao="introducao", texto="editado",
            template_versao=TemplateVersao.objects.get(template=rf_go.template, numero=1),
        )  # fmt: skip
        alvos = [self.go["LP"].pk, self.pe["LP"].pk]
        r = self.client.post(self.url(self.lp), {"alvos": alvos, "template_f1": f1.pk, "template_f2": f2.pk}, follow=True)
        self.assertRedirects(r, LISTA)
        self.assertEqual(RevistaFasciculo.objects.get(pk=rf_go.pk).template, self.templates["LP", "F1"])
        self.assertEqual(RevistaFasciculo.objects.get(revista=self.pe["LP"], fasciculo="F2").template, self.templates["LP", "F2"])
        aviso = next(m for m in mensagens(r) if m.startswith("Pulados"))
        self.assertIn("Projeto GO · LP (F1 tem cópias de seção; troque o template pela revista)", aviso)
        self.assertIn("Projeto PE · LP (projeto em edição por outro)", aviso)

    def test_nao_mudar_fica_e_erro_sem_template(self):
        f2 = self.novo_template(self.lp, "F2")
        alvo = {"alvos": [self.go["LP"].pk]}
        r = self.client.post(self.url(self.lp), alvo)
        self.assertContains(r, "Escolha o template do F1, do F2 ou dos dois.")
        self.assertContains(r, "Nada foi gravado")
        r = self.client.post(self.url(self.lp), {**alvo, "template_f1": self.templates["MT", "F1"].pk})
        self.assertContains(r, "Escolha uma opção da lista")
        self.client.post(self.url(self.lp), {**alvo, "template_f2": f2.pk})
        self.assertEqual(RevistaFasciculo.objects.get(revista=self.go["LP"], fasciculo="F2").template, f2)
        self.assertEqual(RevistaFasciculo.objects.get(revista=self.go["LP"], fasciculo="F1").template, self.templates["LP", "F1"])

    def test_arquivada_e_recusada(self):
        self.go["LP"].__class__.objects.filter(pk=self.go["LP"].pk).update(arquivada_em=ARQUIVADO)
        f2 = self.novo_template(self.lp, "F2")
        r = self.client.post(self.url(self.lp), {"alvos": [self.go["LP"].pk], "template_f2": f2.pk})
        self.assertContains(r, "Escolha uma opção da lista")

    def test_htmx_e_so_leitura(self):
        f2 = self.novo_template(self.lp, "F2")
        r = self.client.post(self.url(self.lp), {"alvos": [self.go["LP"].pk], "template_f2": f2.pk}, **HTMX)
        self.assertTemplateUsed(r, "ui/parciais/lotes_template.html")
        self.assertContains(r, "Template escolhido em 1 revista(s).")
        self.assertContains(r, 'hx-swap-oob="true"')
        self.client.force_login(self.imp)
        self.assertEqual(self.client.post(self.url(self.lp), {"alvos": [self.go["LP"].pk], "template_f2": f2.pk}).status_code, 403)

class LoteUiConcorrenteTest(TransactionTestCase):
    """Bloqueio efetivado por outra conexão (o editor abriu o projeto no admin)."""

    def test_pula_projeto_aberto_pelo_editor(self):
        ano = Ano.objects.create(ano=2026)
        matriz = Matriz.objects.create(ano=ano, nome="M")
        pa = ParceiroAno.objects.create(parceiro=Parceiro.objects.create(nome="GO"), ano=ano)
        projeto = Projeto.objects.create(parceiro_ano=pa, ano=ano, nome="P")
        editor = Client()
        editor.force_login(usuario("editor", is_superuser=True, first_name="Ana"))
        editor.get(reverse("admin:nucleo_projeto_change", args=[projeto.pk]))
        self.client.force_login(usuario("lote", is_superuser=True))
        url = reverse("ui_lotes_matriz", args=[2026])
        self.assertContains(self.client.get(reverse("ui_projeto_lista", args=[2026])), "Em edição por Ana: será pulado")
        r = self.client.post(url, {"alvos": [pa.pk], "matriz": matriz.pk}, follow=True)
        self.assertIn("Pulados: GO (projeto em edição por Ana).", mensagens(r))
        self.assertIsNone(ParceiroAno.objects.get(pk=pa.pk).matriz)


class LoteImpactoUiTest(Base):
    """U2: lote que tira o "Validado" de GO LP só grava depois do modal de impacto."""

    novo_template = test_admin_projeto.LoteTemplateTest.novo_template

    def setUp(self):
        super().setUp()
        self.rev = self.go["LP"]
        validar(self.rev)
        self.nova = Matriz.objects.create(ano=self.ano, nome="Nova")
        self.go_pa = ParceiroAno.objects.get(parceiro__nome="GO")
        self.url_matriz = reverse("ui_lotes_matriz", args=[2026])
        self.url_template = reverse("ui_lotes_template", args=[2026]) + f"?componente={self.lp.pk}"

    def assertModal(self, r):
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "<dialog")
        self.assertContains(r, 'data-abrir-ao-carregar data-form="lote"')
        self.assertContains(r, "Aplicar tira o “Validado” de 1 revista(s)")
        self.assertContains(r, f"<li>{self.rev}</li>")
        self.assertTrue(esta_validada(self.rev))

    def test_matriz_sem_confirmar_abre_modal_e_nao_grava(self):
        r = self.client.post(self.url_matriz, {"alvos": [self.go_pa.pk], "matriz": self.nova.pk}, **HTMX)
        self.assertModal(r)
        self.assertContains(r, f'value="{self.go_pa.pk}" id="alvo-{self.go_pa.pk}" checked')  # a seleção fica
        self.assertEqual(ParceiroAno.objects.get(pk=self.go_pa.pk).matriz, self.matriz)

    def test_matriz_confirmado_grava_e_tira_validado(self):
        dados = {"alvos": [self.go_pa.pk], "matriz": self.nova.pk, "confirmar_impacto": "on"}
        r = self.client.post(self.url_matriz, dados, follow=True)
        self.assertEqual(ParceiroAno.objects.get(pk=self.go_pa.pk).matriz, self.nova)
        self.assertTrue(any("1 revista(s) perderam o “Validado”" in m and "?falta=validado" in m for m in mensagens(r)))
        self.assertFalse(esta_validada(self.rev))

    def test_template_sem_confirmar_abre_modal_e_nao_grava(self):
        f2 = self.novo_template(self.lp, "F2", nome="Outro F2")
        r = self.client.post(self.url_template, {"alvos": [self.rev.pk], "template_f2": f2.pk}, **HTMX)
        self.assertModal(r)
        self.assertEqual(RevistaFasciculo.objects.get(revista=self.rev, fasciculo="F2").template, self.templates["LP", "F2"])

    def test_template_confirmado_grava_e_tira_validado(self):
        f2 = self.novo_template(self.lp, "F2", nome="Outro F2")
        dados = {"alvos": [self.rev.pk], "template_f2": f2.pk, "confirmar_impacto": "on"}
        r = self.client.post(self.url_template, dados, follow=True)
        self.assertEqual(RevistaFasciculo.objects.get(revista=self.rev, fasciculo="F2").template, f2)
        self.assertTrue(any("1 revista(s) perderam o “Validado”" in m for m in mensagens(r)))
        self.assertFalse(esta_validada(self.rev))
