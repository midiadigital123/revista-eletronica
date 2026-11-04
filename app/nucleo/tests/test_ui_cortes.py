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
        # U10d: não existe mais "Salvar" na grade; a mensagem não manda salvar.
        self.assertContains(resp, "Parceiro SAEGO criado. Preencha os cortes da linha: cada célula salva sozinha ao sair dela.")
        self.assertNotContains(resp, "e salve")
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
    """Item 6 (D-190), U5: renomear inline na grade, pelo protocolo do autosave (U3). O nome entra no
    hash (`nome_parceiro`) e vale para todos os anos; revista validada que mudaria pede o modal antes."""

    def setUp(self):
        super().setUp()
        self.go_parceiro = self.projeto_go.parceiro_ano.parceiro
        self.url = reverse("cortes_renomear_parceiro", args=[2026, self.go_parceiro.pk])
        self.rev = self.go["LP"]
        Revista.objects.filter(pk=self.rev.pk).update(hash_validado=hash_validado(self.rev))

    def renomear(self, valor, **extra):
        return self.client.post(self.url, {"campo": "nome", "valor": valor, "original": "GO", **extra}, **JSON)

    def test_grade_tem_o_nome_inline(self):
        r = self.client.get(reverse("cortes", args=[2026]))
        self.assertContains(r, 'x-data="nomeInline"')
        self.assertContains(r, f'data-url="{self.url}"')
        self.assertContains(r, 'aria-label="Renomear GO"')
        self.assertNotContains(r, "<details")

    def test_sem_confirmar_devolve_impacto_e_nao_grava(self):
        r = self.renomear("Goiás")
        self.assertEqual(r.status_code, 200)
        corpo = r.json()
        self.assertFalse(corpo["ok"])
        self.assertEqual(corpo["impacto"]["perdem"], [str(self.rev)])
        self.assertIn("Renomear tira o “Validado” de 1 revista(s)", corpo["impacto"]["html"])
        self.assertEqual(Parceiro.objects.get(pk=self.go_parceiro.pk).nome, "GO")
        self.assertTrue(esta_validada(self.rev))

    def test_confirmado_grava_e_tira_validado(self):
        corpo = self.renomear("Goiás", confirmar_impacto="on").json()
        self.assertTrue(corpo["ok"])
        self.assertEqual((corpo["valor"], corpo["perderam"]), ("Goiás", 1))
        self.assertEqual(Parceiro.objects.get(pk=self.go_parceiro.pk).nome, "Goiás")
        self.assertFalse(esta_validada(self.rev))

    def test_sem_validada_grava_direto(self):
        Revista.objects.filter(pk=self.rev.pk).update(hash_validado=None)
        corpo = self.renomear("Goiás").json()
        self.assertTrue(corpo["ok"])
        self.assertEqual(Parceiro.objects.get(pk=self.go_parceiro.pk).nome, "Goiás")

    def test_422_vazio_ou_repetido(self):
        for valor in ("", "PE"):
            r = self.renomear(valor, confirmar_impacto="on")
            self.assertEqual(r.status_code, 422, valor)
            self.assertTrue(r.json()["erros"])
        self.assertEqual(Parceiro.objects.get(pk=self.go_parceiro.pk).nome, "GO")

    def test_impresso_nao_ve_e_recebe_403(self):
        self.client.force_login(self.imp)
        self.assertNotContains(self.client.get(reverse("cortes", args=[2026])), 'x-data="nomeInline"')
        self.assertEqual(self.renomear("X").status_code, 403)
        self.assertEqual(Parceiro.objects.get(pk=self.go_parceiro.pk).nome, "GO")
