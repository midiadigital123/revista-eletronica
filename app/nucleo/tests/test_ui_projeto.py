"""Projeto fora do admin (/ui/projeto/<pk>/, T15/T16, opção B): testes pelo client.

Critérios de aceite em docs/telas/fichas/projeto.md.
"""

from django.urls import reverse
from django.utils import timezone

from nucleo.admin.bloqueio import CAMPO_SESSAO
from nucleo.variaveis import EDITAVEIS
from nucleo.models import Ano, Projeto
from nucleo.tests.test_admin_projeto import Base, mensagens
from nucleo.tests.test_resolver import usuario

class ProjetoUiTest(Base):
    def setUp(self):
        super().setUp()
        self.url = reverse("ui_projeto", args=[self.projeto_go.pk])

    def dados(self, resp, **extra):
        """POST do form como carregado: nome, variáveis e a sessão do bloqueio."""
        p = self.projeto_go
        d = {"nome": p.nome, **{n: getattr(p, n) for n in EDITAVEIS}}
        d[CAMPO_SESSAO] = resp.wsgi_request.bloqueio["sessao"]
        return d | extra

    def test_get_com_permissao(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "ui/base.html")
        self.assertContains(resp, 'x-data="campoAuto"')  # U3: autosave no lugar do Salvar
        self.assertContains(resp, "<legend>Padrões de desempenho</legend>", html=True)
        self.assertContains(resp, 'placeholder="padrão do ano: Padrão 01"')  # D-175
        self.assertNotContains(resp, 'name="nome_parceiro"')  # automáticas não aparecem
        self.assertContains(resp, "Comunitária")
        self.assertContains(resp, 'id="bloqueio-sessao"')
        self.assertContains(resp, reverse("ui_projeto_lista", args=[2026]))

    def test_so_leitura_sem_permissao(self):
        self.client.force_login(self.imp)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Só leitura: seu perfil vê o projeto")
        self.assertContains(resp, "disabled")
        self.assertNotContains(resp, 'x-data="campoAuto"')  # U3: autosave no lugar do Salvar
        resp = self.client.get(self.url + "?aba=passos")
        self.assertNotContains(resp, 'name="passo-')  # sem controles de gravar
        self.assertNotContains(resp, 'name="cor-')
        self.assertNotContains(resp, "Voltar ao passo da matriz")
        self.assertNotContains(resp, "Editar as cores do ano")
        self.assertContains(resp, "--cor: #f72628")  # vê as cores, sem seletor
        self.assertEqual(self.client.post(self.url, {"nome": "X"}).status_code, 403)
        self.client.force_login(usuario("nada"))
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_post_grava_nome_e_variavel(self):
        dados = self.dados(self.client.get(self.url), nome="Projeto GO novo", sigla_programa="SAEGO")
        resp = self.client.post(self.url, dados, follow=True)
        self.assertRedirects(resp, self.url)
        self.assertIn("Projeto Projeto GO novo salvo.", mensagens(resp))
        p = Projeto.objects.get(pk=self.projeto_go.pk)
        self.assertEqual((p.nome, p.sigla_programa), ("Projeto GO novo", "SAEGO"))

    def test_erro_mostra_mensagem_e_nao_grava(self):
        resp = self.client.post(self.url, self.dados(self.client.get(self.url), nome="x" * 201))
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Nada foi gravado: corrija os erros marcados.", mensagens(resp))
        self.assertContains(resp, 'aria-invalid="true"', count=1)
        self.assertEqual(Projeto.objects.get(pk=self.projeto_go.pk).nome, "Projeto GO")

    def test_anonimo_vai_para_o_login(self):
        self.client.logout()
        for url in (self.url, reverse("ui_projeto_lista", args=[2026])):
            resp = self.client.get(url)
            self.assertRedirects(resp, f"{reverse('admin:login')}?next={url}", fetch_redirect_response=False)

    def test_arquivado_so_leitura(self):
        Projeto.objects.filter(pk=self.projeto_go.pk).update(arquivado_em=timezone.now())
        resp = self.client.get(self.url)
        self.assertContains(resp, "Só leitura: este projeto foi arquivado")
        self.assertContains(resp, "Arquivado")
        self.assertNotContains(resp, 'x-data="campoAuto"')  # U3: autosave no lugar do Salvar
        self.assertNotContains(resp, 'id="bloqueio-sessao"')  # arquivado não trava
        self.assertEqual(self.client.post(self.url, {"nome": "X"}).status_code, 403)

    def test_bloqueado_por_outro(self):
        self.travar(self.projeto_go)
        resp = self.client.get(self.url)
        self.assertTrue(any(m.startswith("Somente leitura: outro está editando") for m in mensagens(resp)))
        self.assertNotContains(resp, 'x-data="campoAuto"')  # U3: autosave no lugar do Salvar
        dados = self.dados(self.client.get(reverse("ui_projeto", args=[self.projeto_pe.pk])), nome="Tomado")
        resp = self.client.post(self.url, dados, follow=True)
        self.assertIn("Não salvo: você perdeu o bloqueio de edição", mensagens(resp)[0])
        self.assertEqual(Projeto.objects.get(pk=self.projeto_go.pk).nome, "Projeto GO")

    def test_matriz_sem_permissao_ou_arquivado(self):
        url = reverse("ui_projeto_matriz", args=[self.projeto_go.pk])
        self.client.force_login(self.imp)
        # U7b: a matriz é a aba Matriz, com autosave (data-url); casos de gravação em test_ui_projeto_abas.py
        self.assertNotContains(self.client.get(self.url + "?aba=matriz"), f'data-url="{url}"')
        self.assertEqual(self.client.post(url, {"matriz": self.matriz.pk}).status_code, 403)
        self.client.force_login(self.ped)
        self.assertContains(self.client.get(self.url + "?aba=matriz"), f'data-url="{url}"')
        Projeto.objects.filter(pk=self.projeto_go.pk).update(arquivado_em=timezone.now())
        self.assertNotContains(self.client.get(self.url + "?aba=matriz"), f'data-url="{url}"')
        self.assertEqual(self.client.post(url, {"matriz": self.matriz.pk}).status_code, 403)

    def test_matriz_bloqueada_por_outro(self):
        self.travar(self.projeto_go)
        url = reverse("ui_projeto_matriz", args=[self.projeto_go.pk])
        resp = self.client.post(url, {"matriz": self.matriz.pk, CAMPO_SESSAO: "x"}, follow=True)
        self.assertIn("Não salvo: você perdeu o bloqueio de edição", mensagens(resp)[0])

    def test_etapa_de_outro_ano_nao_entra_na_grade_de_passo(self):
        ano25 = Ano.objects.create(ano=2025)
        velha = self.e5.__class__.objects.create(ano=ano25, codigo="5EF", escala_max=500, ordem=2)
        resp = self.client.get(self.url + "?aba=passos")
        self.assertNotIn(velha, [b["etapa"] for b in resp.context["etapas_passo"]])


class ListaUiTest(Base):
    url = reverse("ui_projeto_lista", args=[2026])

    def test_lista_do_ano(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, reverse("ui_projeto", args=[self.projeto_go.pk]))
        self.assertContains(resp, "Projeto PE")
        self.assertContains(resp, "Atribuir matriz…")
        self.assertRedirects(self.client.get(reverse("ui_projeto_inicio")), self.url)
        self.client.force_login(self.imp)
        resp = self.client.get(self.url)
        self.assertContains(resp, "Projeto GO")
        self.assertNotContains(resp, "Atribuir matriz…")
        self.client.force_login(usuario("nada"))
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_ano_sem_projetos(self):
        Ano.objects.create(ano=2027)
        resp = self.client.get(reverse("ui_projeto_lista", args=[2027]))
        self.assertContains(resp, "Nenhum projeto em 2027")
