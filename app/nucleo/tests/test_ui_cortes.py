"""Grade de cortes fora do admin (/cortes/<ano>/, protótipo da opção B): testes pelo client."""

from django.urls import reverse

from nucleo.models import Corte, Parceiro, ParceiroAno, Projeto, Revista
from nucleo.servicos.resolver import hash_validado
from nucleo.tests.test_admin_projeto import Base as ProjetoBase
from nucleo.tests.test_admin_cadastro import Base
from nucleo.tests.test_admin_padrao import esta_validada
from nucleo.tests.test_resolver import usuario


JSON = {"HTTP_ACCEPT": "application/json"}


class GradeUiTest(Base):
    """A grade só mostra; cada célula grava pela rota `cortes_celula` (U3, protocolo em test_ui_autosave)."""

    url = reverse("cortes", args=[2026])
    url_celula = reverse("cortes_celula", args=[2026])

    def celula(self, parceiro, etapa, cc):
        return f"c-{parceiro.pk}-{self.e[etapa].pk}-{self.c[cc].pk}"

    def postar(self, campo, valor, original=""):
        return self.client.post(self.url_celula, {"campo": campo, "valor": valor, "original": original}, **JSON)

    def test_get_com_permissao(self):
        Parceiro.objects.create(nome="GO")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "ui/base.html")
        self.assertContains(resp, f'data-url="{self.url_celula}"')
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
                self.assertContains(resp, f'data-url="{self.url_celula}"')
                self.assertNotContains(resp, "readonly")
                go = Parceiro.objects.get(nome="GO")
                self.assertEqual(self.postar(self.celula(go, "5EF", "MT"), "", "").status_code, 200)

    def test_adicionar_parceiro_cria_linha(self):
        url = reverse("cortes_novo_parceiro", args=[2026])
        self.client.force_login(usuario("md", "Mídias Digitais"))
        pagina = self.client.get(self.url)
        self.assertContains(pagina, "Adicionar parceiro")
        # U4: sem o form "Nova linha" sempre aberto; o botão abaixo da grade abre a linha (molde).
        self.assertNotContains(pagina, ">Nova linha<")
        self.assertContains(pagina, 'x-data="linhaNova"')
        self.assertLess(pagina.content.index(b"</table>"), pagina.content.index(b"Adicionar parceiro"))
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
        self.assertNotContains(resp, 'x-data="campoAuto"')
        go = Parceiro.objects.get(nome="GO")
        self.assertEqual(self.postar(self.celula(go, "5EF", "LP"), "125").status_code, 403)
        self.assertEqual(self.client.post(self.url, {}).status_code, 405)  # a grade inteira não grava mais
        self.client.force_login(usuario("nada"))  # sem view_corte
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_celula_grava_e_dispara_a_cascata(self):
        go = Parceiro.objects.create(nome="GO")
        self.assertEqual(self.postar(self.celula(go, "5EF", "LP"), "125, 175, 225").json()["ok"], True)
        pa = ParceiroAno.objects.get(parceiro=go, ano=self.a26)
        self.assertEqual(Corte.objects.get(parceiro_ano=pa).valores, [125, 175, 225])
        self.assertTrue(Revista.objects.filter(projeto=Projeto.objects.get(parceiro_ano=pa), componente__codigo="LP").exists())

    def test_celula_invalida_devolve_o_erro(self):
        go = Parceiro.objects.create(nome="GO")
        resp = self.postar(self.celula(go, "5EF", "LP"), "200, 150")
        self.assertEqual(resp.status_code, 422)
        self.assertEqual(resp.json()["erros"], ["5EF LP: cortes precisam ser crescentes."])
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
