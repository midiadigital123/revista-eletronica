"""Bloqueio de escrita (S10): serviço, rota de renovar e BloqueioAdminMixin.

TransactionTestCase (invariante 7): o `now()` do banco precisa andar entre
comandos e as threads precisam ver os commits umas das outras.
"""

import threading
import time
from datetime import timedelta

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.db import connection, transaction
from django.db.models.functions import Now
from django.test import Client, TransactionTestCase, override_settings
from django.urls import include, path

from nucleo.admin.bloqueio import CAMPO_SESSAO, BloqueioAdminMixin
from nucleo.models import (
    Ano,
    Bloqueio,
    Componente,
    Etapa,
    Matriz,
    MatrizEtapaCC,
    Parceiro,
    ParceiroAno,
    Projeto,
    Template,
    TemplateVersao,
)
from nucleo.servicos import bloqueio

# Admin de teste num AdminSite próprio: os admins reais só usam o mixin em S11.
site = admin.AdminSite(name="admin")


class VersaoInline(admin.TabularInline):
    model = TemplateVersao
    fields = ["numero", "texto"]
    extra = 1


class TemplateTesteAdmin(BloqueioAdminMixin, admin.ModelAdmin):
    fields = ["nome"]
    inlines = [VersaoInline]


site.register(Template, TemplateTesteAdmin)

urlpatterns = [path("admin/", site.urls), path("", include("nucleo.urls"))]
URL_RENOVAR = "/bloqueio/renovar"
URL_LIBERAR = "/bloqueio/liberar"
INLINE = "templateversao_set"


class Base(TransactionTestCase):
    def setUp(self):
        ano = Ano.objects.create(ano=2026)
        lp = Componente.objects.create(ano=ano, codigo="LP", nome="Língua Portuguesa")
        self.tpl = Template.objects.create(ano=ano, componente=lp, fasciculo="F1", nome="T")
        User = get_user_model()
        self.ana = User.objects.create_superuser("ana", password="x", first_name="Ana")
        self.bia = User.objects.create_superuser("bia", password="x")

    def expirar(self):
        Bloqueio.objects.update(expira_em=Now() - timedelta(seconds=1))


class ServicoTest(Base):
    def test_concorrentes_so_uma_adquire(self):
        n = 6
        barreira = threading.Barrier(n)
        resultados = []
        # Pessoas diferentes: a mesma pessoa em outra aba assume de propósito (D-191).
        pessoas = [get_user_model().objects.create_user(f"conc-{i}") for i in range(n)]

        def tentar(i):
            try:
                barreira.wait()
                resultados.append(bloqueio.adquirir(self.tpl, pessoas[i], f"aba-{i}"))
            finally:
                connection.close()  # cada thread tem a sua conexão

        threads = [threading.Thread(target=tentar, args=(i,)) for i in range(n)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(sorted(resultados), [False] * (n - 1) + [True])
        self.assertEqual(Bloqueio.objects.count(), 1)

    def test_outra_sessao_nao_adquire(self):
        self.assertTrue(bloqueio.adquirir(self.tpl, self.ana, "a"))
        self.assertFalse(bloqueio.adquirir(self.tpl, self.bia, "b"))
        self.assertEqual(bloqueio.quem_bloqueia(self.tpl).usuario, self.ana)

    def test_mesmo_usuario_em_outra_aba_assume(self):
        """D-191: a carga nova toma o bloqueio; a sessão anterior perde renovação e escrita."""
        self.assertTrue(bloqueio.adquirir(self.tpl, self.ana, "a"))
        self.assertTrue(bloqueio.adquirir(self.tpl, self.ana, "outra-aba"))
        self.assertEqual(bloqueio.quem_bloqueia(self.tpl).sessao_edicao, "outra-aba")
        self.assertFalse(bloqueio.renovar(self.tpl, self.ana, "a"))
        with transaction.atomic():
            self.assertFalse(bloqueio.conferir_na_transacao(self.tpl, self.ana, "a"))
        self.assertFalse(bloqueio.adquirir(self.tpl, self.bia, "b"))  # outra pessoa continua barrada

    def test_expirado_e_tomado(self):
        bloqueio.adquirir(self.tpl, self.ana, "a")
        self.expirar()
        self.assertIsNone(bloqueio.quem_bloqueia(self.tpl))
        self.assertTrue(bloqueio.adquirir(self.tpl, self.bia, "b"))
        b = Bloqueio.objects.get()
        self.assertEqual((b.usuario, b.sessao_edicao), (self.bia, "b"))
        self.assertFalse(bloqueio.renovar(self.tpl, self.ana, "a"))

    def test_alvos_matriz_etapa_cc_e_projeto(self):
        ano = self.tpl.ano
        mec = MatrizEtapaCC.objects.create(
            matriz=Matriz.objects.create(ano=ano, nome="M"),
            etapa=Etapa.objects.create(ano=ano, codigo="5EF", escala_max=500, ordem=1),
            componente=self.tpl.componente,
            ano=ano,
        )
        pa = ParceiroAno.objects.create(parceiro=Parceiro.objects.create(nome="GO"), ano=ano)
        projeto = Projeto.objects.create(parceiro_ano=pa, ano=ano, nome="GO")
        for alvo in (mec, projeto, self.tpl):  # mesmo pk possível: cada alvo tem a sua UNIQUE
            self.assertTrue(bloqueio.adquirir(alvo, self.ana, "a"))
            self.assertFalse(bloqueio.adquirir(alvo, self.bia, "b"))
        self.assertEqual(Bloqueio.objects.count(), 3)
        self.assertEqual(Bloqueio.objects.get(projeto=projeto).matriz_etapa_cc_id, None)

    def test_mesma_sessao_renova_e_readquire(self):
        bloqueio.adquirir(self.tpl, self.ana, "a")
        Bloqueio.objects.update(expira_em=Now() + timedelta(seconds=5))
        antes = Bloqueio.objects.get().expira_em
        self.assertTrue(bloqueio.renovar(self.tpl, self.ana, "a"))
        self.assertGreater(Bloqueio.objects.get().expira_em, antes)
        self.assertTrue(bloqueio.adquirir(self.tpl, self.ana, "a"))  # idempotente
        self.assertFalse(bloqueio.renovar(self.tpl, self.bia, "a"))

    def test_renovar_nao_readquire_expirado(self):
        bloqueio.adquirir(self.tpl, self.ana, "a")
        self.expirar()
        self.assertFalse(bloqueio.renovar(self.tpl, self.ana, "a"))

    def test_liberar_so_a_propria(self):
        bloqueio.adquirir(self.tpl, self.ana, "a")
        bloqueio.liberar(self.tpl, self.bia, "a")
        self.assertEqual(Bloqueio.objects.count(), 1)
        bloqueio.liberar(self.tpl, self.ana, "a")
        self.assertEqual(Bloqueio.objects.count(), 0)

    def test_conferir_na_transacao(self):
        bloqueio.adquirir(self.tpl, self.ana, "a")
        with self.assertRaises(RuntimeError):
            bloqueio.conferir_na_transacao(self.tpl, self.ana, "a")
        with transaction.atomic():
            self.assertTrue(bloqueio.conferir_na_transacao(self.tpl, self.ana, "a"))
            self.assertFalse(bloqueio.conferir_na_transacao(self.tpl, self.bia, "b"))
        self.expirar()
        with transaction.atomic():
            self.assertFalse(bloqueio.conferir_na_transacao(self.tpl, self.ana, "a"))

    def test_for_share_segura_a_tomada_ate_o_commit(self):
        """Com o bloqueio conferido numa escrita em curso, quem tenta tomar espera o commit."""
        bloqueio.adquirir(self.tpl, self.ana, "a")
        conferido, tentou = threading.Event(), threading.Event()
        resultado, durante = [], []

        def escrita():
            try:
                with transaction.atomic():
                    bloqueio.conferir_na_transacao(self.tpl, self.ana, "a")
                    conferido.set()
                    tentou.wait(5)
                    time.sleep(0.5)  # sem o FOR SHARE, a tomada já teria respondido False
                    durante.append(len(resultado))
                    # Expira antes do commit: a tomada, ao acordar, vê o expirado e toma.
                    Bloqueio.objects.update(expira_em=Now() - timedelta(seconds=1))
            finally:
                connection.close()

        def tomada():
            try:
                conferido.wait(5)
                tentou.set()
                resultado.append(bloqueio.adquirir(self.tpl, self.bia, "b"))
            finally:
                connection.close()

        threads = [threading.Thread(target=escrita), threading.Thread(target=tomada)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(10)
        self.assertEqual(durante, [0])  # esperou a escrita
        self.assertEqual(resultado, [True])  # e só tomou depois do commit


@override_settings(ROOT_URLCONF=__name__)
class RotaRenovarTest(Base):
    def post(self, cliente, sessao, **extra):
        dados = {"alvo": "template", "id": self.tpl.pk, "sessao": sessao, **extra}
        return cliente.post(URL_RENOVAR, dados)

    def test_200_com_bloqueio_409_sem(self):
        c = Client()
        c.force_login(self.ana)
        bloqueio.adquirir(self.tpl, self.ana, "a")
        r = self.post(c, "a")
        self.assertEqual((r.status_code, r.json()), (200, {"bloqueio": True}))
        self.assertEqual(self.post(c, "outra").status_code, 409)

    def test_exige_login(self):
        self.assertEqual(self.post(Client(), "a").status_code, 403)

    def test_exige_csrf(self):
        c = Client(enforce_csrf_checks=True)
        c.force_login(self.ana)
        bloqueio.adquirir(self.tpl, self.ana, "a")
        self.assertEqual(self.post(c, "a").status_code, 403)

    def test_pedido_invalido_e_get(self):
        c = Client()
        c.force_login(self.ana)
        self.assertEqual(self.post(c, "a", alvo="parceiro").status_code, 400)
        self.assertEqual(self.post(c, "").status_code, 400)
        self.assertEqual(self.post(c, "x" * 101).status_code, 400)
        for pk in ["²", "1" * 19, "-1", "1.0"]:
            self.assertEqual(self.post(c, "a", id=pk).status_code, 400, pk)
        self.assertEqual(c.get(URL_RENOVAR).status_code, 405)

    def test_liberar(self):
        dados = {"alvo": "template", "id": self.tpl.pk, "sessao": "a"}
        bloqueio.adquirir(self.tpl, self.ana, "a")
        sem_csrf = Client(enforce_csrf_checks=True)
        sem_csrf.force_login(self.ana)
        self.assertEqual(sem_csrf.post(URL_LIBERAR, dados).status_code, 403)
        bia = Client()
        bia.force_login(self.bia)
        self.assertEqual(bia.post(URL_LIBERAR, dados).status_code, 204)  # idempotente, não libera
        self.assertTrue(Bloqueio.objects.exists())
        c = Client()
        c.force_login(self.ana)
        self.assertEqual(c.post(URL_LIBERAR, dados).status_code, 204)
        self.assertFalse(Bloqueio.objects.exists())


@override_settings(ROOT_URLCONF=__name__)
class MixinTest(Base):
    def setUp(self):
        super().setUp()
        self.url = f"/admin/nucleo/template/{self.tpl.pk}/change/"
        self.c_ana, self.c_bia = Client(), Client()
        self.c_ana.force_login(self.ana)
        self.c_bia.force_login(self.bia)

    def dados(self, nome, sessao, **extra):
        return {
            "nome": nome,
            CAMPO_SESSAO: sessao,
            f"{INLINE}-TOTAL_FORMS": "0",
            f"{INLINE}-INITIAL_FORMS": "0",
            **extra,
        }

    def abrir(self, cliente):
        r = cliente.get(self.url)
        self.assertEqual(r.status_code, 200)
        return r

    def test_primeira_edita_segunda_so_le(self):
        r1 = self.abrir(self.c_ana)
        self.assertTrue(r1.context["has_change_permission"])
        sessao = r1.context["bloqueio"]["sessao"]
        self.assertContains(r1, f'value="{sessao}"')
        self.assertContains(r1, "nucleo/bloqueio.js")
        self.assertEqual(Bloqueio.objects.get().sessao_edicao, sessao)

        r2 = self.abrir(self.c_bia)
        self.assertFalse(r2.context["has_change_permission"])
        self.assertNotIn("bloqueio", r2.context)
        self.assertNotContains(r2, 'name="nome"')
        self.assertNotContains(r2, "nucleo/bloqueio.js")
        self.assertContains(r2, "Somente leitura: Ana está editando")

    def test_escrita_com_bloqueio_de_outra_sessao_e_recusada(self):
        sessao_ana = self.abrir(self.c_ana).context["bloqueio"]["sessao"]
        self.abrir(self.c_bia)
        for cliente, sessao in [(self.c_bia, "falsa"), (self.c_bia, sessao_ana), (self.c_ana, "x")]:
            r = cliente.post(self.url, self.dados("Invadido", sessao))
            self.assertRedirects(r, self.url, fetch_redirect_response=False)
        self.tpl.refresh_from_db()
        self.assertEqual(self.tpl.nome, "T")

    def test_dona_salva_e_libera(self):
        sessao = self.abrir(self.c_ana).context["bloqueio"]["sessao"]
        r = self.c_ana.post(self.url, self.dados("Novo", sessao, _continue="1"))
        self.assertEqual(r.status_code, 302)
        self.tpl.refresh_from_db()
        self.assertEqual(self.tpl.nome, "Novo")
        self.assertFalse(Bloqueio.objects.exists())
        # "Salvar e continuar" readquire com sessão nova.
        self.assertNotEqual(self.abrir(self.c_ana).context["bloqueio"]["sessao"], sessao)

    def test_form_invalido_mantem_bloqueio_e_sessao(self):
        sessao = self.abrir(self.c_ana).context["bloqueio"]["sessao"]
        r = self.c_ana.post(self.url, self.dados("", sessao))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context["bloqueio"]["sessao"], sessao)
        self.assertEqual(Bloqueio.objects.get().sessao_edicao, sessao)

    def test_expirado_e_tomado_pela_segunda(self):
        self.abrir(self.c_ana)
        self.expirar()
        self.assertTrue(self.abrir(self.c_bia).context["has_change_permission"])
        self.assertEqual(Bloqueio.objects.get().usuario, self.bia)

    def test_inlines_somente_leitura_para_a_segunda(self):
        TemplateVersao.objects.create(template=self.tpl, numero=1, texto="## a\n")
        r1 = self.abrir(self.c_ana)
        self.assertContains(r1, f'name="{INLINE}-0-texto"')
        r2 = self.abrir(self.c_bia)
        [inline] = r2.context["inline_admin_formsets"]
        self.assertEqual(
            (inline.has_add_permission, inline.has_change_permission, inline.has_delete_permission),
            (False, False, False),
        )
        self.assertNotContains(r2, f'name="{INLINE}-0-texto"')
        self.assertNotContains(r2, f'name="{INLINE}-1-texto"')  # sem linha extra

    def test_excluir_com_bloqueio_alheio_e_recusado(self):
        self.abrir(self.c_ana)
        url = f"/admin/nucleo/template/{self.tpl.pk}/delete/"
        self.assertEqual(self.c_bia.get(url).status_code, 403)
        self.assertEqual(self.c_bia.post(url, {"post": "yes"}).status_code, 403)
        self.assertTrue(Template.objects.filter(pk=self.tpl.pk).exists())
        self.assertEqual(self.c_ana.get(url).status_code, 200)  # o próprio usuário pode

    def test_f5_contra_si_mesmo(self):
        self.abrir(self.c_ana)
        r = self.abrir(self.c_ana)  # nova carga = sessão nova; assume o bloqueio (D-191)
        self.assertTrue(r.context["has_change_permission"])
