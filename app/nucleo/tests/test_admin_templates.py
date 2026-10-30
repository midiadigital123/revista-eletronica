"""Admin de templates (S11b1): validar, tela de impacto, versão nova, bloqueio, preview e perfis.

TestCase na maioria: os grupos da migração 0007 só existem antes do flush dos
TransactionTestCase. A dupla confirmação (concorrência) é TransactionTestCase com superusuário.
"""

import threading
import time

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import connection, transaction
from django.test import Client, TestCase, TransactionTestCase

from nucleo.admin.bloqueio import CAMPO_SESSAO
from nucleo.management.commands.carregar_templates import AVISO
from nucleo.models import Bloqueio, FotoRevista, RevistaFasciculo, RevistaSecao, Template, TemplateVersao
from nucleo.models.revista import Motivo
from nucleo.servicos.resolver import versao_atual
from nucleo.tests.test_resolver import F1, F2_LP, Mundo, usuario
from nucleo.texto import TEXTO_MAX

# F2_LP com um passo2 a mais: as revistas com SVG só até passo1 ficariam sem o id.
F2_NOVO = F2_LP + "\n## passo2\nPasso dois\n\nNovo {{ano}}.\n"
IMPACTO = "nucleo/template_impacto.html"


class Base(TestCase):
    def setUp(self):
        Mundo.montar(self)
        self.tpl = self.templates["LP", "F2"]
        self.url = f"/admin/nucleo/template/{self.tpl.pk}/change/"
        self.ped = Client()
        self.ped.force_login(usuario("ped", "Pedagógica"))

    def abrir(self, cliente=None):
        r = (cliente or self.ped).get(self.url)
        self.assertEqual(r.status_code, 200)
        return r

    def dados(self, sessao, texto, **extra):
        return {"nome": "Padrão", "texto": texto, CAMPO_SESSAO: sessao, **extra}

    def confirmar(self, impacto, cliente=None, **troca):
        """POST do botão "Confirmar" da tela de impacto (hidden + sessão), com `troca` aplicada."""
        self.assertTemplateUsed(impacto, IMPACTO)
        dados = dict(impacto.context["dados"])
        dados.update({CAMPO_SESSAO: impacto.context["bloqueio"]["sessao"], "_confirmar": "1", **troca})
        return (cliente or self.ped).post(self.url, dados)

    def versoes(self):
        return TemplateVersao.objects.filter(template=self.tpl).count()


class SalvarTest(Base):
    def test_variavel_fora_da_lista_e_recusada(self):
        sessao = self.abrir().context["bloqueio"]["sessao"]
        ruim = F2_LP + "\n## passo2\nT\n\nOi {{x}}.\n"
        r = self.ped.post(self.url, self.dados(sessao, ruim))
        self.assertEqual(r.status_code, 200)
        self.assertTemplateNotUsed(r, IMPACTO)
        self.assertIn("{{x}}", str(r.context["adminform"].form.errors["texto"]))
        # Nem o _confirmar com assinatura válida passa: o form revalida no POST final.
        impacto = self.ped.post(self.url, self.dados(sessao, F2_NOVO))
        r = self.confirmar(impacto, texto=ruim)
        self.assertEqual(r.status_code, 200)
        self.assertTemplateNotUsed(r, IMPACTO)
        self.assertEqual(self.versoes(), 1)

    def test_impacto_e_depois_versao_nova(self):
        sessao = self.abrir().context["bloqueio"]["sessao"]
        r = self.ped.post(self.url, self.dados(sessao, F2_NOVO, _continue="1"))
        self.assertTemplateUsed(r, IMPACTO)
        self.assertEqual(self.versoes(), 1)  # nada gravado
        self.assertContains(r, f'value="{sessao}"')
        self.assertContains(r, 'name="_continue"')  # o POST original volta nos hidden

        r = self.confirmar(r, texto=F2_NOVO.replace("\n", "\r\n"))  # textarea manda CRLF
        self.assertRedirects(r, self.url, fetch_redirect_response=False)
        v1, v2 = TemplateVersao.objects.filter(template=self.tpl).order_by("numero")
        self.assertEqual(v1.texto, F2_LP)  # versão antiga intacta
        self.assertEqual((v2.numero, v2.texto, v2.criada_por.username), (2, F2_NOVO, "ped"))
        self.assertFalse(Bloqueio.objects.exists())  # salvou e liberou

    def test_texto_igual_salva_nome_sem_impacto_nem_versao(self):
        sessao = self.abrir().context["bloqueio"]["sessao"]
        r = self.ped.post(self.url, {**self.dados(sessao, F2_LP), "nome": "Outro"})
        self.assertEqual(r.status_code, 302)
        self.tpl.refresh_from_db()
        self.assertEqual(self.tpl.nome, "Outro")
        self.assertEqual(self.versoes(), 1)

    def test_seed_do_banco_volta_igual_pelo_textarea(self):
        seed = (settings.BASE_DIR / "templates_seed" / "2026" / "f2-lp.hbs").read_text(encoding="utf-8-sig")
        seed = AVISO.sub("", seed)  # como o carregar_templates grava
        TemplateVersao.objects.create(template=self.tpl, numero=2, texto=seed)
        r = self.abrir()
        self.assertEqual(r.context["adminform"].form["texto"].value(), seed)
        sessao = r.context["bloqueio"]["sessao"]
        r = self.ped.post(self.url, self.dados(sessao, seed.replace("\n", "\r\n")))
        self.assertEqual(r.status_code, 302)  # sem tela de impacto nem versão nova
        self.assertEqual(self.versoes(), 2)

    def test_voltar_reabre_o_form_com_o_texto(self):
        sessao = self.abrir().context["bloqueio"]["sessao"]
        r = self.ped.post(self.url, self.dados(sessao, F2_NOVO, _voltar="1"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Novo {{ano}}")
        self.assertEqual(Bloqueio.objects.get().sessao_edicao, sessao)
        self.assertEqual(self.versoes(), 1)

    def test_confirmar_sem_o_bloqueio_e_recusado(self):
        self.abrir()
        r = self.ped.post(self.url, self.dados("outra", F2_NOVO))
        self.assertTemplateNotUsed(r, IMPACTO)
        r = self.ped.post(self.url, self.dados("outra", F2_NOVO, _confirmar="1"))
        self.assertRedirects(r, self.url, fetch_redirect_response=False)
        self.assertEqual(self.versoes(), 1)

    def test_bloqueio_de_outro_usuario(self):
        outro = Client()
        outro.force_login(usuario("mid", "Mídias Digitais"))
        sessao_mid = self.abrir(outro).context["bloqueio"]["sessao"]
        r = self.abrir()  # ped chega depois: só leitura, sem o editor
        self.assertNotContains(r, 'name="texto"')
        self.assertNotContains(r, 'class="editor-template"')
        self.assertContains(r, "Para os {{adjetivo_patrio_plural_masculino}}.")
        for extra in ({}, {"_confirmar": "1"}):
            r = self.ped.post(self.url, self.dados(sessao_mid, F2_NOVO, **extra))
            self.assertRedirects(r, self.url, fetch_redirect_response=False)
        self.assertEqual(self.versoes(), 1)

    def test_assinatura_adulterada_ou_texto_trocado_reabre_o_impacto(self):
        sessao = self.abrir().context["bloqueio"]["sessao"]
        impacto = self.ped.post(self.url, self.dados(sessao, F2_NOVO))
        outro = F2_NOVO + "\n## passo3\nTrês\n\nMais.\n"
        for troca in ({"_impacto": "adulterada"}, {"_impacto": ""}, {"texto": outro}):
            with self.subTest(troca):
                r = self.confirmar(impacto, **troca)
                self.assertTemplateUsed(r, IMPACTO)
                self.assertContains(r, "mudou desde a tela de impacto")
        self.assertEqual(self.versoes(), 1)
        # A tela reaberta assina o texto novo: confirmar por ela grava.
        r = self.confirmar(self.confirmar(impacto, texto=outro))
        self.assertEqual(r.status_code, 302)
        self.assertEqual(versao_atual(self.tpl.pk).texto, outro)

    def test_versao_base_mudou_reabre_o_impacto(self):
        sessao = self.abrir().context["bloqueio"]["sessao"]
        impacto = self.ped.post(self.url, self.dados(sessao, F2_NOVO))
        TemplateVersao.objects.create(template=self.tpl, numero=2, texto=F2_LP + "\n")  # outro caminho gravou
        r = self.confirmar(impacto)
        self.assertTemplateUsed(r, IMPACTO)
        self.assertEqual(self.versoes(), 2)


class ImpactoTest(Base):
    def test_lista_svg_incompleto_impresso_e_copia(self):
        go, pe = self.go["LP"], self.pe["LP"]
        go.svg_f2, go.svg_sha256, go.svg_ids = "f2/go.svg", "a" * 64, ["passo1", "btn-action-p2"]
        go.save()
        FotoRevista.objects.create(revista=pe, motivo=Motivo.IMPRESSO, conteudo={}, hash="b" * 64, criada_por=self.usuario)
        rf = RevistaFasciculo.objects.get(revista=pe, fasciculo="F2")
        RevistaSecao.objects.create(
            revista_fasciculo=rf, template=self.tpl, secao="passo1", texto="Cópia.",
            template_versao=TemplateVersao.objects.get(template=self.tpl),
        )
        sessao = self.abrir().context["bloqueio"]["sessao"]
        r = self.ped.post(self.url, self.dados(sessao, F2_NOVO))
        linhas = {x["revista"].pk: x for x in r.context["revistas"]}
        self.assertEqual(set(linhas), {go.pk, pe.pk})  # MT usa outro template
        self.assertEqual(linhas[go.pk]["ids_faltando"], ["passo2"])
        self.assertEqual(linhas[pe.pk]["ids_faltando"], [])  # sem SVG: a pendência é outra
        self.assertTrue(linhas[pe.pk]["impresso"])
        self.assertEqual(linhas[pe.pk]["copias"], ["passo1"])
        self.assertContains(r, "SVG incompleto: passo2")
        self.assertContains(r, "Já tem foto do impresso")

    def test_impacto_de_f1(self):
        self.tpl = self.templates["LP", "F1"]
        self.url = f"/admin/nucleo/template/{self.tpl.pk}/change/"
        sessao = self.abrir().context["bloqueio"]["sessao"]
        novo = F1.replace("Fim.", "Fim de novo.")
        r = self.ped.post(self.url, self.dados(sessao, novo))
        self.assertEqual({x["revista"].pk for x in r.context["revistas"]}, {self.go["LP"].pk, self.pe["LP"].pk})
        self.assertTrue(all(x["ids_faltando"] == [] for x in r.context["revistas"]))
        self.assertEqual(self.confirmar(r).status_code, 302)
        self.assertEqual(versao_atual(self.tpl.pk).texto, novo)

    def test_lista_mostra_usado_por(self):
        rf = RevistaFasciculo.objects.get(revista=self.pe["LP"], fasciculo="F2")
        v1 = TemplateVersao.objects.get(template=self.tpl)
        for secao in ("passo1", "abertura"):
            RevistaSecao.objects.create(
                revista_fasciculo=rf, template=self.tpl, secao=secao, texto="A", template_versao=v1
            )
        r = self.ped.get("/admin/nucleo/template/?fasciculo__exact=F2")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, f'href="/painel/2026/?template={self.tpl.pk}">usado por 2 (1 com cópia)')
        self.assertContains(r, 'aria-current="page">Textos F2')


class PreviewTest(Base):
    def test_preview_colore_variavel_e_mostra_erros(self):
        r = self.ped.post("/templates/preview", {"texto": "## passo1\nOi\n\nPara {{ano}}.\n", "fasciculo": "F2"})
        json = r.json()
        self.assertIn('<span class="variavel-vazia">{{ano}}</span>', json["html"])
        self.assertIn("Seções obrigatórias faltando: abertura.", json["erros"])

    def test_preview_escapa_id_e_titulo(self):
        r = self.ped.post("/templates/preview", {"texto": "## <img/onerror=1>\nA < B <script>\n\nC.\n"})
        html = r.json()["html"]
        self.assertIn("## &lt;img/onerror=1&gt;", html)
        self.assertIn("A &lt; B &lt;script&gt;", html)
        self.assertNotIn("<img", html)
        self.assertNotIn("<script", html)

    def test_preview_exige_login_permissao_csrf_e_teto(self):
        self.assertEqual(Client().post("/templates/preview", {"texto": "x"}).status_code, 403)
        sem = Client()
        sem.force_login(get_user_model().objects.create_user("sem", is_staff=True))
        self.assertEqual(sem.post("/templates/preview", {"texto": "x"}).status_code, 403)
        csrf = Client(enforce_csrf_checks=True)
        csrf.force_login(get_user_model().objects.get(username="ped"))
        self.assertEqual(csrf.post("/templates/preview", {"texto": "x"}).status_code, 403)
        grande = self.ped.post("/templates/preview", {"texto": "a" * (TEXTO_MAX + 1)})
        self.assertEqual(grande.status_code, 400)

    def test_validar_e_linear_com_muitas_secoes(self):
        # Era ids.count(i) (O(n²)): 40 mil seções levavam ~23 s.
        corpo = "".join(f"## passo{i}\n" for i in range(1, 20_000))[:TEXTO_MAX]
        inicio = time.monotonic()
        r = self.ped.post("/templates/preview", {"texto": corpo, "fasciculo": "F2"})
        self.assertEqual(r.status_code, 200)
        self.assertLess(time.monotonic() - inicio, 5)


class PerfisTest(Base):
    def test_quem_edita(self):
        for papel in ("Pedagógica", "Mídias Digitais", "Admin"):
            with self.subTest(papel):
                Bloqueio.objects.all().delete()
                c = Client()
                c.force_login(usuario(f"u-{papel}", papel))
                r = self.abrir(c)
                self.assertContains(r, 'name="texto"')
                self.assertContains(r, "nucleo/template_editor.js")
                self.assertEqual(c.get("/admin/nucleo/template/add/").status_code, 200)

    def test_impresso_so_ve(self):
        c = Client()
        c.force_login(usuario("imp", "Impresso"))
        r = self.abrir(c)
        self.assertNotContains(r, 'name="texto"')
        self.assertContains(r, "Para os {{adjetivo_patrio_plural_masculino}}.")  # texto só leitura
        self.assertEqual(c.post(self.url, self.dados("x", F2_NOVO, _confirmar="1")).status_code, 403)
        self.assertEqual(c.post(self.url, self.dados("x", F2_NOVO)).status_code, 403)
        self.assertEqual(c.get("/admin/nucleo/template/add/").status_code, 403)
        self.assertEqual(c.post("/templates/preview", {"texto": "x"}).status_code, 200)  # ver pode
        self.assertEqual(self.versoes(), 1)

    def test_criar_template_nasce_com_versao_1(self):
        r = self.ped.post(
            "/admin/nucleo/template/add/",
            {"ano": self.ano.pk, "componente": self.lp.pk, "fasciculo": "F1", "nome": "Novo",
             "texto": "## introducao\nI\n\nA.\n\n## fechamento\nF\n\nB.\n"},
        )  # fmt: skip
        self.assertEqual(r.status_code, 302)
        v = TemplateVersao.objects.get(template__nome="Novo")
        self.assertEqual((v.numero, v.criada_por.username), (1, "ped"))


class DuplaConfirmacaoTest(TransactionTestCase):
    """Duplo "Confirmar" da mesma aba: os dois passam pelo FOR SHARE do bloqueio; a trava do
    template no save_model serializa e o segundo vê a versão do primeiro (sem IntegrityError)."""

    def test_segundo_confirmar_nao_duplica_a_versao(self):
        Mundo.montar(self)
        tpl = self.templates["LP", "F2"]
        url = f"/admin/nucleo/template/{tpl.pk}/change/"
        c = Client()
        c.force_login(get_user_model().objects.create_superuser("su", password="x"))
        sessao = c.get(url).context["bloqueio"]["sessao"]
        impacto = c.post(url, {"nome": "Padrão", "texto": F2_NOVO, CAMPO_SESSAO: sessao})
        dados = {**dict(impacto.context["dados"]), CAMPO_SESSAO: sessao, "_confirmar": "1"}

        travou, solta = threading.Event(), threading.Event()

        def primeiro():  # o 1º confirmar no meio da transação: travou, gravou a v2, não commitou
            try:
                with transaction.atomic():
                    Template.objects.select_for_update().get(pk=tpl.pk)
                    TemplateVersao.objects.create(template=tpl, numero=2, texto=F2_NOVO)
                    travou.set()
                    solta.wait(10)
            finally:
                connection.close()

        t = threading.Thread(target=primeiro)
        t.start()
        self.assertTrue(travou.wait(10))
        threading.Timer(0.5, solta.set).start()  # o 2º fica esperando a trava e só então relê
        r = c.post(url, dados)
        t.join()
        self.assertEqual(r.status_code, 302)
        numeros = TemplateVersao.objects.filter(template=tpl).order_by("numero").values_list("numero", flat=True)
        self.assertEqual(list(numeros), [1, 2])
