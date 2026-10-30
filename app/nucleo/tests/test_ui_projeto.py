"""Projeto fora do admin (/ui/projeto/<pk>/, T15/T16, opção B): testes pelo client.

Critérios de aceite em docs/telas/fichas/projeto.md.
"""

from django.urls import reverse
from django.utils import timezone

from nucleo.admin.bloqueio import CAMPO_SESSAO
from nucleo.variaveis import EDITAVEIS
from nucleo.models import Ano, Matriz, ParceiroAno, Projeto, ProjetoCor, ProjetoPasso
from nucleo.tests.test_admin_projeto import Base, mensagens
from nucleo.tests.test_resolver import usuario

HTMX = {"HTTP_HX_REQUEST": "true"}


class ProjetoUiTest(Base):
    def setUp(self):
        super().setUp()
        self.url = reverse("ui_projeto", args=[self.projeto_go.pk])

    def dados(self, resp, **extra):
        """POST do form como carregado: nome, variáveis, formsets vazios e a sessão do bloqueio."""
        p = self.projeto_go
        d = {"nome": p.nome, **{n: getattr(p, n) for n in EDITAVEIS}}
        for fs in ("passos", "cores"):
            d |= {f"{fs}-TOTAL_FORMS": 0, f"{fs}-INITIAL_FORMS": 0, f"{fs}-MIN_NUM_FORMS": 0, f"{fs}-MAX_NUM_FORMS": 1000}
        d[CAMPO_SESSAO] = resp.wsgi_request.bloqueio["sessao"]
        return d | extra

    def test_get_com_permissao(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "ui/base.html")
        self.assertContains(resp, "Salvar projeto")
        self.assertContains(resp, "<legend>Padrões de desempenho</legend>", html=True)
        self.assertContains(resp, 'placeholder="padrão do ano: Padrão 01"')  # D-175
        self.assertNotContains(resp, 'name="nome_parceiro"')  # automáticas não aparecem
        self.assertContains(resp, "Comunitária")
        self.assertContains(resp, "5EF LP: 25")  # passo da matriz como referência
        self.assertContains(resp, "--cor: #F72628")  # faixa com a cor do ano
        self.assertContains(resp, 'id="bloqueio-sessao"')
        self.assertContains(resp, reverse("ui_projeto_lista", args=[2026]))

    def test_so_leitura_sem_permissao(self):
        self.client.force_login(self.imp)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Só leitura: seu perfil vê o projeto")
        self.assertContains(resp, "disabled")
        self.assertNotContains(resp, "Salvar projeto")
        self.assertNotContains(resp, "Sobrescrever um passo")
        self.assertEqual(self.client.post(self.url, {"nome": "X"}).status_code, 403)
        self.client.force_login(usuario("nada"))
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_post_grava_nome_variavel_passo_e_cor(self):
        dados = self.dados(
            self.client.get(self.url), nome="Projeto GO novo", sigla_programa="SAEGO",
            **{"passos-TOTAL_FORMS": 1, "passos-0-etapa": self.e5.pk, "passos-0-componente": self.lp.pk, "passos-0-passo": "",
               "cores-TOTAL_FORMS": 1, "cores-0-padrao": 2, "cores-0-cor": "#123456"},
        )  # fmt: skip
        resp = self.client.post(self.url, dados, follow=True)
        self.assertRedirects(resp, self.url)
        self.assertIn("Projeto Projeto GO novo salvo.", mensagens(resp))
        p = Projeto.objects.get(pk=self.projeto_go.pk)
        self.assertEqual((p.nome, p.sigla_programa), ("Projeto GO novo", "SAEGO"))
        passo = ProjetoPasso.objects.get(projeto=p)
        self.assertEqual((passo.etapa, passo.componente, passo.passo, passo.ano_id), (self.e5, self.lp, None, self.ano.pk))
        self.assertEqual(ProjetoCor.objects.get(projeto=p, padrao=2).cor, "#123456")
        self.assertContains(resp, "--cor: #123456")  # a faixa mostra a cor do projeto

    def test_remover_cor_volta_a_paleta(self):
        cor = ProjetoCor.objects.create(projeto=self.projeto_go, padrao=1, cor="#000000")
        dados = self.dados(
            self.client.get(self.url),
            **{"cores-TOTAL_FORMS": 1, "cores-INITIAL_FORMS": 1, "cores-0-id": cor.pk, "cores-0-projeto": self.projeto_go.pk,
               "cores-0-padrao": 1, "cores-0-cor": "#000000", "cores-0-DELETE": "on"},
        )  # fmt: skip
        self.assertRedirects(self.client.post(self.url, dados), self.url)
        self.assertFalse(ProjetoCor.objects.filter(projeto=self.projeto_go).exists())

    def test_erro_mostra_mensagem_e_nao_grava(self):
        dados = self.dados(
            self.client.get(self.url), nome="x" * 201,
            **{"passos-TOTAL_FORMS": 1, "passos-0-etapa": self.e5.pk, "passos-0-componente": self.lp.pk, "passos-0-passo": 0},
        )  # fmt: skip
        resp = self.client.post(self.url, dados)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Nada foi gravado: corrija os erros marcados.", mensagens(resp))
        self.assertContains(resp, 'aria-invalid="true"', count=2)
        self.assertContains(resp, "pj-com-erro")
        self.assertEqual(Projeto.objects.get(pk=self.projeto_go.pk).nome, "Projeto GO")
        self.assertFalse(ProjetoPasso.objects.exists())

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
        self.assertNotContains(resp, "Salvar projeto")
        self.assertNotContains(resp, 'id="bloqueio-sessao"')  # arquivado não trava
        self.assertEqual(self.client.post(self.url, {"nome": "X"}).status_code, 403)

    def test_bloqueado_por_outro(self):
        self.travar(self.projeto_go)
        resp = self.client.get(self.url)
        self.assertTrue(any(m.startswith("Somente leitura: outro está editando") for m in mensagens(resp)))
        self.assertNotContains(resp, "Salvar projeto")
        dados = self.dados(self.client.get(reverse("ui_projeto", args=[self.projeto_pe.pk])), nome="Tomado")
        resp = self.client.post(self.url, dados, follow=True)
        self.assertIn("Não salvo: você perdeu o bloqueio de edição", mensagens(resp)[0])
        self.assertEqual(Projeto.objects.get(pk=self.projeto_go.pk).nome, "Projeto GO")

    def test_atribuir_matriz_pela_ficha(self):
        """Item 19 (D-190): a ficha grava a matriz com a sessão de bloqueio da própria ficha."""
        nova = Matriz.objects.create(ano=self.ano, nome="Nova")
        url = reverse("ui_projeto_matriz", args=[self.projeto_go.pk])
        resp = self.client.get(self.url)
        self.assertContains(resp, f'action="{url}"')
        sessao = resp.wsgi_request.bloqueio["sessao"]
        resp = self.client.post(url, {"matriz": nova.pk, CAMPO_SESSAO: sessao}, follow=True)
        self.assertIn("Matriz Nova escolhida para GO.", mensagens(resp))
        self.assertEqual(ParceiroAno.objects.get(pk=self.projeto_go.parceiro_ano_id).matriz, nova)
        self.assertEqual(ParceiroAno.objects.get(pk=self.projeto_pe.parceiro_ano_id).matriz, self.matriz)

    def test_matriz_de_outro_ano_e_recusada(self):
        velha = Matriz.objects.create(ano=Ano.objects.create(ano=2025), nome="Velha")
        sessao = self.client.get(self.url).wsgi_request.bloqueio["sessao"]
        resp = self.client.post(reverse("ui_projeto_matriz", args=[self.projeto_go.pk]), {"matriz": velha.pk, CAMPO_SESSAO: sessao}, follow=True)
        self.assertIn("Matriz não gravada: escolha uma matriz de 2026.", mensagens(resp))
        self.assertEqual(ParceiroAno.objects.get(pk=self.projeto_go.parceiro_ano_id).matriz, self.matriz)

    def test_matriz_sem_permissao_ou_arquivado(self):
        url = reverse("ui_projeto_matriz", args=[self.projeto_go.pk])
        self.client.force_login(self.imp)
        self.assertNotContains(self.client.get(self.url), f'action="{url}"')
        self.assertEqual(self.client.post(url, {"matriz": self.matriz.pk}).status_code, 403)
        self.client.force_login(self.ped)
        Projeto.objects.filter(pk=self.projeto_go.pk).update(arquivado_em=timezone.now())
        self.assertNotContains(self.client.get(self.url), f'action="{url}"')
        self.assertEqual(self.client.post(url, {"matriz": self.matriz.pk}).status_code, 403)

    def test_matriz_bloqueada_por_outro(self):
        self.travar(self.projeto_go)
        url = reverse("ui_projeto_matriz", args=[self.projeto_go.pk])
        resp = self.client.post(url, {"matriz": self.matriz.pk, CAMPO_SESSAO: "x"}, follow=True)
        self.assertIn("Não salvo: você perdeu o bloqueio de edição", mensagens(resp)[0])

    def test_htmx_linha_nova(self):
        sessao = self.client.get(self.url).wsgi_request.bloqueio["sessao"]
        ProjetoCor.objects.create(projeto=self.projeto_go, padrao=1, cor="#000000")
        url = reverse("ui_projeto_linha", args=[self.projeto_go.pk, "cores"])
        resp = self.client.get(url, {"cores-TOTAL_FORMS": 1, "cores-0-padrao": 1, CAMPO_SESSAO: sessao}, **HTMX)
        self.assertContains(resp, 'name="cores-1-padrao"')
        self.assertContains(resp, 'value="2"')  # primeiro padrão livre
        self.assertContains(resp, 'value="#FF8D43"')  # já com a cor do ano
        self.assertContains(resp, 'id="id_cores-TOTAL_FORMS" value="2" hx-swap-oob="true"')
        resp = self.client.get(url, {"cores-TOTAL_FORMS": 4, CAMPO_SESSAO: sessao}, **HTMX)
        self.assertContains(resp, "disabled")  # a 5ª cor desliga o botão (oob)
        url = reverse("ui_projeto_linha", args=[self.projeto_go.pk, "passos"])
        self.assertContains(resp, 'aria-label="Padrão"')  # o <th> não rotula o controle
        resp = self.client.get(url, {"passos-TOTAL_FORMS": 0, CAMPO_SESSAO: sessao}, **HTMX)
        self.assertContains(resp, 'name="passos-0-etapa"')
        self.assertContains(resp, 'aria-label="Passo"')
        self.assertContains(resp, ">5EF</option>")  # só o código: o ano é sempre o do projeto
        self.assertEqual(self.client.get(url, {"passos-TOTAL_FORMS": 0, CAMPO_SESSAO: "outra"}, **HTMX).status_code, 403)

    def test_etapa_de_outro_ano_nao_e_oferecida(self):
        ano25 = Ano.objects.create(ano=2025)
        velha = self.e5.__class__.objects.create(ano=ano25, codigo="5EF", escala_max=500, ordem=2)
        resp = self.client.get(self.url)
        self.assertNotIn(velha, resp.context["passos"].empty_form.fields["etapa"].queryset)


class ListaUiTest(Base):
    url = reverse("ui_projeto_lista", args=[2026])

    def test_lista_do_ano(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, reverse("ui_projeto", args=[self.projeto_go.pk]))
        self.assertContains(resp, "Projeto PE")
        self.assertContains(resp, "Escolher matriz")
        self.assertRedirects(self.client.get(reverse("ui_projeto_inicio")), self.url)
        self.client.force_login(self.imp)
        resp = self.client.get(self.url)
        self.assertContains(resp, "Projeto GO")
        self.assertNotContains(resp, "Escolher matriz")
        self.client.force_login(usuario("nada"))
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_ano_sem_projetos(self):
        Ano.objects.create(ano=2027)
        resp = self.client.get(reverse("ui_projeto_lista", args=[2027]))
        self.assertContains(resp, "Nenhum projeto neste ano")
