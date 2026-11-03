"""Base comum das telas B: bloqueio para views próprias (ui_bloqueio), navegação e casca.

TransactionTestCase no bloqueio, como em test_bloqueio: o `now()` do banco precisa andar e
cada Client vê o commit do outro.
"""

import re
from pathlib import Path

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponse
from django.template import RequestContext, Template as Tpl
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


def menu(resp):
    """Itens do menu principal: (href, nome, ativo)."""
    nav = re.search(r'<nav class="nav" aria-label="Principal">(.*?)</nav>', resp.content.decode(), re.S).group(1)
    return [(h, n.strip(), bool(a)) for h, a, n in re.findall(r'<a href="([^"]+)"( aria-current="page")?>([^<]+)</a>', nav)]


class CascaTest(TestCase):
    def test_casca_com_htmx_csrf_fonte_local_e_navegacao_com_reserva(self):
        Ano.objects.create(ano=2026)
        self.client.force_login(get_user_model().objects.create_superuser("ana", password="x"))
        r = self.client.get("/ui/projeto/ano/2026/cortes/")
        self.assertContains(r, "ui/htmx.min.js")
        self.assertContains(r, 'hx-headers=\'{"X-CSRFToken": "')
        self.assertContains(r, "ui/fontes/inter-latin-wght-normal.woff2")
        self.assertNotContains(r, "fonts.googleapis.com")
        # Navegação só por telas B (U6: 5 itens; Cortes, Variáveis, Revistas e Lotes ficam sob Projetos).
        self.assertEqual(menu(r), [
            ("/painel/2026/", "Painel", False), ("/ui/projeto/ano/2026/", "Projetos", True),
            ("/ui/matriz/2026/", "Matrizes", False), ("/ui/templates/2026/", "Templates", False),
            ("/ui/impresso/2026/", "Impresso", False),
        ])
        self.assertContains(r, 'id="mensagens"')

    def test_menu_tem_5_itens(self):
        Ano.objects.create(ano=2026)
        self.client.force_login(get_user_model().objects.create_superuser("ana", password="x"))
        nomes = ["Painel", "Projetos", "Matrizes", "Templates", "Impresso"]
        for url, ativo in [("/painel/2026/", "Painel"), ("/ui/projeto/ano/2026/variaveis/", "Projetos"),
                           ("/ui/projeto/ano/2026/cortes/", "Projetos"), ("/ui/projeto/ano/2026/", "Projetos"), ("/ui/matriz/2026/", "Matrizes"),
                           ("/ui/templates/2026/", "Templates"), ("/ui/impresso/2026/", "Impresso"),
                           ("/ui/validar/2026/", "Painel"), ("/ui/anos/2026/", None)]:
            with self.subTest(url=url):
                itens = menu(self.client.get(url))
                self.assertEqual([n for _, n, _ in itens], nomes)
                self.assertEqual([n for _, n, a in itens if a], [ativo] if ativo else [])

    def test_alpine_csp_e_sortable_com_sri_na_ordem(self):
        # D-195: Sortable e componentes.js antes do Alpine, para o alpine:init achar os registros.
        Ano.objects.create(ano=2026)
        self.client.force_login(get_user_model().objects.create_superuser("bia", password="x"))
        html = self.client.get("/ui/projeto/ano/2026/cortes/").content.decode()
        ordem = ["ui/htmx.min.js", "ui/ui.js", "sortablejs@1.15.6/Sortable.min.js",
                 "ui/componentes.js", "ui/componentes/autosave.js", "@alpinejs/csp@3.14.9/dist/cdn.min.js"]
        posicoes = [html.index(x) for x in ordem]
        self.assertEqual(posicoes, sorted(posicoes))
        self.assertEqual(html.count('integrity="sha384-'), 2)
        self.assertEqual(html.count('crossorigin="anonymous"'), 2)



class SemSeletorNasPaginasTest(SimpleTestCase):
    """U6: o seletor de ano (e o "Abrir ano") mora só no cabeçalho da base."""

    def test_nenhuma_pagina_inclui_abrir_ano(self):
        raiz = Path(__file__).resolve().parent.parent / "templates" / "ui"
        achados = [
            str(arquivo.relative_to(raiz))
            for arquivo in sorted(raiz.rglob("*.html"))
            if arquivo.name not in ("base.html", "anos.html")
            and ("_componentes/anos.html" in (t := arquivo.read_text()) or "Abrir ano</a>" in t)
        ]
        self.assertEqual(achados, [])


class SemCheckboxConfirmoTest(SimpleTestCase):
    """U2: confirmação de impacto nas telas B é o modal (_componentes/impacto.html), nunca checkbox."""

    def test_nenhum_checkbox_confirmo(self):
        raiz = Path(__file__).resolve().parent.parent / "templates" / "ui"
        achados = []
        for arquivo in sorted(raiz.rglob("*.html")):
            texto = arquivo.read_text()
            if "Confirmo:" in texto:
                achados.append(f"{arquivo.relative_to(raiz)}: Confirmo:")
            for tag in re.findall(r"<input\b[^>]*>", texto):
                if 'type="checkbox"' in tag and re.search(r'name="[^"]*confirmar', tag):
                    achados.append(f"{arquivo.relative_to(raiz)}: {tag}")
        self.assertEqual(achados, [])


class EstaticosComVersaoTest(SimpleTestCase):
    """CSS/JS com ?v=<mtime>: arquivo mudou, URL muda, o navegador não usa o CSS velho do cache."""

    def test_static_leva_versao(self):
        from django.templatetags.static import static

        self.assertRegex(static("ui/ui.css"), r"/static/ui/ui\.css\?v=\d+$")

    def test_arquivo_inexistente_fica_sem_versao(self):
        from django.templatetags.static import static

        self.assertTrue(static("ui/nao-existe.css").endswith("/static/ui/nao-existe.css"))

    def test_pasta_fica_sem_versao(self):
        """O preview monta `static("revista/") + "styles.css"`: versão no meio quebrava o CSS da revista."""
        from django.templatetags.static import static

        self.assertTrue(static("revista/").endswith("/static/revista/"))


class MenuPorPerfilTest(TestCase):
    """Impresso só no menu de quem marca revista como impressa; Admin só para o superusuário."""

    def setUp(self):
        Ano.objects.create(ano=2026)

    def test_pedagogica_nao_ve_impresso_nem_admin(self):
        from nucleo.tests.test_resolver import usuario

        self.client.force_login(usuario("ped", "Pedagógica"))
        r = self.client.get("/painel/2026/")
        self.assertEqual([n for _, n, _ in menu(r)], ["Painel", "Projetos", "Matrizes", "Templates"])
        self.assertNotContains(r, ">Admin</a>")

    def test_impresso_ve_impresso_sem_admin(self):
        from nucleo.tests.test_resolver import usuario

        self.client.force_login(usuario("imp", "Impresso"))
        r = self.client.get("/painel/2026/")
        self.assertIn("Impresso", [n for _, n, _ in menu(r)])
        self.assertNotContains(r, ">Admin</a>")

    def test_superusuario_ve_tudo(self):
        self.client.force_login(get_user_model().objects.create_superuser("ana", password="x"))
        r = self.client.get("/painel/2026/")
        self.assertIn("Impresso", [n for _, n, _ in menu(r)])
        self.assertContains(r, ">Admin</a>")
