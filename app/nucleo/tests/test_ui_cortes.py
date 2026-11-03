"""Grade de cortes fora do admin (/cortes/<ano>/, protótipo da opção B): testes pelo client."""

from django.urls import reverse

from nucleo.models import Corte, Parceiro, ParceiroAno, Projeto, Revista
from nucleo.servicos.resolver import hash_validado
from nucleo.tests.test_admin_projeto import Base as ProjetoBase
from nucleo.tests.test_admin_cadastro import Base, dados_da_grade
from nucleo.tests.test_admin_padrao import esta_validada, validar
from nucleo.tests.test_resolver import usuario


class GradeUiTest(Base):
    url = reverse("cortes", args=[2026])

    def celula(self, parceiro, etapa, cc):
        return f"c-{parceiro.pk}-{self.e[etapa].pk}-{self.c[cc].pk}"

    def test_get_com_permissao(self):
        Parceiro.objects.create(nome="GO")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "ui/base.html")
        self.assertContains(resp, "Salvar cortes")
        self.assertContains(resp, reverse("admin:nucleo_corte_exportar") + "?ano=2026")
        self.assertContains(resp, reverse("painel", args=[2026]))
        self.assertNotContains(resp, "readonly")
        self.assertRedirects(self.client.get(reverse("cortes_inicio")), self.url)

    def test_todos_os_grupos_menos_impresso_gravam(self):
        Parceiro.objects.create(nome="GO")
        for grupo in ("Admin", "Pedagógica", "Mídias Digitais"):
            with self.subTest(grupo):
                self.client.force_login(usuario(f"u-{grupo}", grupo))
                resp = self.client.get(self.url)
                self.assertContains(resp, "Salvar cortes")
                self.assertNotContains(resp, "readonly")

    def test_adicionar_parceiro_cria_linha(self):
        url = reverse("cortes_novo_parceiro", args=[2026])
        self.client.force_login(usuario("md", "Mídias Digitais"))
        self.assertContains(self.client.get(self.url), "Adicionar parceiro")
        resp = self.client.post(url, {"nome": "SAEGO"}, follow=True)
        self.assertContains(resp, 'data-parceiro="SAEGO"')
        self.assertContains(self.client.post(url, {"nome": "SAEGO"}, follow=True), "Parceiro não criado")
        self.assertEqual(Parceiro.objects.filter(nome="SAEGO").count(), 1)
        self.client.force_login(usuario("imp2", "Impresso"))
        self.assertNotContains(self.client.get(self.url), "Adicionar parceiro")
        self.assertEqual(self.client.post(url, {"nome": "X"}).status_code, 403)

    def test_so_leitura_sem_permissao(self):
        Parceiro.objects.create(nome="GO")
        self.client.force_login(usuario("imp", "Impresso"))
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Só leitura")
        self.assertContains(resp, "readonly")
        self.assertNotContains(resp, "Salvar cortes")
        self.assertEqual(self.client.post(self.url, dados_da_grade(resp)).status_code, 403)
        self.client.force_login(usuario("nada"))  # sem view_corte
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_post_grava_e_dispara_a_cascata(self):
        go = Parceiro.objects.create(nome="GO")
        dados = dados_da_grade(self.client.get(self.url))
        dados[self.celula(go, "5EF", "LP")] = "125, 175, 225"
        resp = self.client.post(self.url, dados, follow=True)
        self.assertRedirects(resp, self.url)
        self.assertContains(resp, "Cortes gravados (1 parceiro(s) alterado(s)).")
        pa = ParceiroAno.objects.get(parceiro=go, ano=self.a26)
        self.assertEqual(Corte.objects.get(parceiro_ano=pa).valores, [125, 175, 225])
        self.assertTrue(Revista.objects.filter(projeto=Projeto.objects.get(parceiro_ano=pa), componente__codigo="LP").exists())

    def test_celula_invalida_mostra_erro_na_linha(self):
        go = Parceiro.objects.create(nome="GO")
        dados = dados_da_grade(self.client.get(self.url))
        dados[self.celula(go, "5EF", "LP")] = "200, 150"
        resp = self.client.post(self.url, dados)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, f'<ul id="erros-{go.pk}"><li>GO: 5EF LP: cortes precisam ser crescentes.</li></ul>', html=False)
        self.assertContains(resp, 'value="200, 150" aria-label="GO 5EF LP" aria-invalid="true"')
        self.assertContains(resp, 'aria-invalid="true"', count=1)  # só a célula errada, não a linha
        self.assertContains(resp, "Nada foi gravado")
        self.assertFalse(Corte.objects.exists())

    def test_anonimo_vai_para_o_login(self):
        self.client.logout()
        resp = self.client.get(self.url)
        self.assertRedirects(resp, f"{reverse('admin:login')}?next={self.url}", fetch_redirect_response=False)


class RenomearParceiroTest(ProjetoBase):
    """Item 6 (D-190): renomear pela grade. O nome entra no hash (`nome_parceiro`) e vale para todos
    os anos; revista validada que mudaria pede confirmação antes."""

    def setUp(self):
        super().setUp()
        self.go_parceiro = self.projeto_go.parceiro_ano.parceiro
        self.url = reverse("cortes_renomear_parceiro", args=[2026, self.go_parceiro.pk])
        self.rev = self.go["LP"]
        Revista.objects.filter(pk=self.rev.pk).update(hash_validado=hash_validado(self.rev))

    def test_sem_confirmar_abre_modal_e_nao_grava(self):
        self.assertContains(self.client.get(reverse("cortes", args=[2026])), f'action="{self.url}"')
        r = self.client.post(self.url, {"nome": "Goiás"})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "<dialog")
        self.assertContains(r, "data-abrir-ao-carregar")
        self.assertContains(r, "Renomear tira o “Validado” de 1 revista(s)")
        self.assertContains(r, f'data-form="renomear-{self.go_parceiro.pk}"')
        self.assertContains(r, str(self.rev))
        self.assertContains(r, 'value="Goiás" data-original="GO"')
        self.assertEqual(Parceiro.objects.get(pk=self.go_parceiro.pk).nome, "GO")
        self.assertTrue(esta_validada(self.rev))

    def test_confirmado_grava_e_tira_validado(self):
        r = self.client.post(self.url, {"nome": "Goiás", "confirmar_impacto": "on"}, follow=True)
        self.assertContains(r, "Parceiro renomeado para Goiás. 1 revista(s) perderam o “Validado”.")
        self.assertEqual(Parceiro.objects.get(pk=self.go_parceiro.pk).nome, "Goiás")
        self.assertFalse(esta_validada(self.rev))

    def test_sem_validada_grava_direto(self):
        Revista.objects.filter(pk=self.rev.pk).update(hash_validado=None)
        r = self.client.post(self.url, {"nome": "Goiás"})
        self.assertRedirects(r, reverse("cortes", args=[2026]), fetch_redirect_response=False)
        self.assertEqual(Parceiro.objects.get(pk=self.go_parceiro.pk).nome, "Goiás")

    def test_nome_repetido_e_impresso(self):
        r = self.client.post(self.url, {"nome": "PE", "confirmar_impacto": "on"}, follow=True)
        self.assertContains(r, "Parceiro não renomeado")
        self.client.force_login(self.imp)
        self.assertNotContains(self.client.get(reverse("cortes", args=[2026])), f'action="{self.url}"')
        self.assertEqual(self.client.post(self.url, {"nome": "X", "confirmar": "1"}).status_code, 403)


class GradeImpactoTest(ProjetoBase):
    """U2: a grade B grava cortes que mudam revista validada só depois do modal de impacto."""

    url = reverse("cortes", args=[2026])

    def setUp(self):
        super().setUp()
        self.rev = self.go["LP"]
        validar(self.rev)
        corte = Corte.objects.get(parceiro_ano__parceiro__nome="GO", etapa=self.e5, componente=self.lp)
        self.chave = f"c-{self.projeto_go.parceiro_ano.parceiro_id}-{self.e5.pk}-{self.lp.pk}"
        self.antes = corte.valores
        self.dados = dados_da_grade(self.client.get(self.url))
        self.dados[self.chave] = "110, 200, 250, 300"

    def test_sem_confirmar_abre_modal_e_nao_grava(self):
        r = self.client.post(self.url, self.dados)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "<dialog")
        self.assertContains(r, 'data-form="grade"')
        self.assertContains(r, "Salvar cortes tira o “Validado” de 1 revista(s)")
        self.assertContains(r, str(self.rev))
        self.assertContains(r, 'value="110, 200, 250, 300" data-original="100, 200, 250, 300"')
        self.assertEqual(Corte.objects.get(parceiro_ano__parceiro__nome="GO", etapa=self.e5, componente=self.lp).valores, self.antes)
        self.assertTrue(esta_validada(self.rev))

    def test_confirmado_grava_e_tira_validado(self):
        r = self.client.post(self.url, {**self.dados, "confirmar_impacto": "on"}, follow=True)
        self.assertRedirects(r, self.url)
        self.assertContains(r, "Cortes gravados (1 parceiro(s) alterado(s)).")
        self.assertContains(r, "1 revista(s) perderam o “Validado”")
        self.assertContains(r, "/painel/2026/?falta=validado")
        self.assertEqual(Corte.objects.get(parceiro_ano__parceiro__nome="GO", etapa=self.e5, componente=self.lp).valores,
                         [110, 200, 250, 300])  # fmt: skip
        self.assertFalse(esta_validada(self.rev))

    def test_sem_validada_grava_direto(self):
        Revista.objects.filter(pk=self.rev.pk).update(hash_validado=None)
        self.assertEqual(self.client.post(self.url, self.dados).status_code, 302)
