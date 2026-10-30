"""Grade de cortes fora do admin (/cortes/<ano>/, protótipo da opção B): testes pelo client."""

from django.urls import reverse

from nucleo.models import Corte, Parceiro, ParceiroAno, Projeto, Revista
from nucleo.tests.test_admin_cadastro import Base, dados_da_grade
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
