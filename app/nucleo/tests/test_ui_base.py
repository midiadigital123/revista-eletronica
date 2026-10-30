"""Base comum das telas B: bloqueio para views próprias (ui_bloqueio), navegação (rota_b) e casca.

TransactionTestCase no bloqueio, como em test_bloqueio: o `now()` do banco precisa andar e
cada Client vê o commit do outro.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponse
from django.template import Context, RequestContext, Template as Tpl
from django.test import Client, SimpleTestCase, TestCase, TransactionTestCase, override_settings
from django.urls import include, path

from nucleo.admin.bloqueio import CAMPO_SESSAO
from nucleo.models import Ano, Bloqueio, Componente, Template
from nucleo.servicos import bloqueio
from nucleo.ui_bloqueio import com_bloqueio

PAGINA = Tpl(
    '{% extends "ui/base.html" %}{% block conteudo %}<form method="post">{% csrf_token %}'
    '{% include "ui/_componentes/bloqueio.html" %}<input name="nome" value="{{ tpl.nome }}"'
    '{% if not request.pode_gravar %} readonly{% endif %}></form>{% endblock %}'
)


@login_required(login_url="admin:login")
@com_bloqueio(lambda request, pk: get_object_or_404(Template, pk=pk), lambda u: u.has_perm("nucleo.change_template"))
def pagina(request, pk):
    tpl = Template.objects.get(pk=pk)
    if request.method == "POST":
        tpl.nome = request.POST["nome"]
        tpl.save()
        return redirect(request.path)
    return HttpResponse(PAGINA.render(RequestContext(request, {"tpl": tpl})))


urlpatterns = [path("teste-b/<int:pk>/", pagina), path("", include("sistema.urls"))]


@override_settings(ROOT_URLCONF=__name__)
class BloqueioUiTest(TransactionTestCase):
    def setUp(self):
        ano = Ano.objects.create(ano=2026)
        lp = Componente.objects.create(ano=ano, codigo="LP", nome="Língua Portuguesa")
        self.tpl = Template.objects.create(ano=ano, componente=lp, fasciculo="F1", nome="T")
        User = get_user_model()
        self.ana, self.bia = Client(), Client()
        self.ana.force_login(User.objects.create_superuser("ana", password="x", first_name="Ana"))
        self.bia.force_login(User.objects.create_superuser("bia", password="x"))
        self.url = f"/teste-b/{self.tpl.pk}/"

    def sessao(self, resp):
        return resp.wsgi_request.bloqueio["sessao"]

    def test_primeira_edita_segunda_so_le(self):
        r1 = self.ana.get(self.url)
        sessao = self.sessao(r1)
        self.assertContains(r1, f'value="{sessao}"')
        self.assertContains(r1, "nucleo/bloqueio.js")
        self.assertNotContains(r1, "readonly")
        r2 = self.bia.get(self.url)
        self.assertIsNone(r2.wsgi_request.bloqueio)
        self.assertNotContains(r2, "nucleo/bloqueio.js")
        self.assertContains(r2, "readonly")
        self.assertContains(r2, "Somente leitura: Ana está editando")

    def test_post_sem_bloqueio_e_recusado(self):
        sessao_ana = self.sessao(self.ana.get(self.url))
        for cliente, sessao in [(self.bia, sessao_ana), (self.bia, "falsa"), (self.ana, "outra")]:
            r = cliente.post(self.url, {"nome": "Invadido", CAMPO_SESSAO: sessao})
            self.assertRedirects(r, self.url, fetch_redirect_response=False)
        self.tpl.refresh_from_db()
        self.assertEqual(self.tpl.nome, "T")
        r = self.bia.post(self.url, {"nome": "X", CAMPO_SESSAO: "x"}, HTTP_HX_REQUEST="true")
        self.assertEqual(r["HX-Refresh"], "true")
        self.assertContains(self.bia.get(self.url), "perdeu o bloqueio de edição")

    def test_dona_salva_e_libera(self):
        sessao = self.sessao(self.ana.get(self.url))
        r = self.ana.post(self.url, {"nome": "Novo", CAMPO_SESSAO: sessao})
        self.assertEqual(r.status_code, 302)
        self.tpl.refresh_from_db()
        self.assertEqual(self.tpl.nome, "Novo")
        self.assertFalse(Bloqueio.objects.exists())

    def test_fragmento_htmx_nao_adquire_e_usa_a_sessao_da_aba(self):
        sessao = self.sessao(self.ana.get(self.url))
        r = self.ana.get(self.url, {CAMPO_SESSAO: sessao}, HTTP_HX_REQUEST="true")
        self.assertTrue(r.wsgi_request.pode_gravar)
        self.assertEqual(Bloqueio.objects.get().sessao_edicao, sessao)  # não trocou de sessão
        r = self.ana.get(self.url, {CAMPO_SESSAO: "outra"}, HTTP_HX_REQUEST="true")
        self.assertFalse(r.wsgi_request.pode_gravar)
        r = self.bia.get(self.url, HTTP_HX_REQUEST="true")
        self.assertFalse(r.wsgi_request.pode_gravar)

    def test_sem_permissao_so_le_sem_travar_e_post_403(self):
        c = Client()
        c.force_login(get_user_model().objects.create_user("imp", password="x", is_staff=True))
        r = c.get(self.url)
        self.assertContains(r, "readonly")
        self.assertFalse(Bloqueio.objects.exists())
        self.assertEqual(c.post(self.url, {"nome": "X"}).status_code, 403)

    def test_anonimo_vai_ao_login(self):
        r = Client().get(self.url)
        self.assertRedirects(r, f"/admin/login/?next={self.url}", fetch_redirect_response=False)

    def test_servico_e_o_mesmo_do_admin(self):
        self.ana.get(self.url)
        self.assertIsNotNone(bloqueio.quem_bloqueia(self.tpl))


@override_settings(ROOT_URLCONF="sistema.urls")
class RotaBTest(SimpleTestCase):
    def render(self, texto, **ctx):
        return Tpl("{% load ui %}" + texto).render(Context(ctx))

    def test_cai_para_vazio_sem_args_ou_com_args(self):
        self.assertEqual(self.render('{% rota_b "ui_nao_existe" 2026 %}'), "")
        self.assertEqual(self.render('{% rota_b "cortes" 2026 %}'), "/cortes/2026/")
        self.assertEqual(self.render('{% rota_b "cortes_inicio" 2026 %}'), "/cortes/")  # args a mais: sem args
        self.assertEqual(self.render('{% rota_b "cortes" ano %}', ano=None), "")  # sem ano e a rota exige


class CascaTest(TestCase):
    def test_casca_com_htmx_csrf_fonte_local_e_navegacao_com_reserva(self):
        Ano.objects.create(ano=2026)
        self.client.force_login(get_user_model().objects.create_superuser("ana", password="x"))
        r = self.client.get("/cortes/2026/")
        self.assertContains(r, "ui/htmx.min.js")
        self.assertContains(r, 'hx-headers=\'{"X-CSRFToken": "')
        self.assertContains(r, "ui/fontes/inter-latin-wght-normal.woff2")
        self.assertNotContains(r, "fonts.googleapis.com")
        # Telas B ainda vazias: a navegação cai no admin equivalente.
        self.assertContains(r, 'href="/painel/2026/"')
        self.assertContains(r, 'href="/ui/variaveis/2026/"')  # tela B de variáveis já entrou
        self.assertContains(r, 'href="/ui/matriz/2026/"')  # tela B de matrizes já registrada
        self.assertContains(r, 'href="/painel/2026/?falta=impresso"')
        self.assertContains(r, 'href="/ui/impresso/2026/"')
        self.assertContains(r, 'id="mensagens"')
