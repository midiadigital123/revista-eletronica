"""Exclusão do que não está em uso (D-205), ano inteiro (D-206), template com as versões (D-207) e
parceiro desativado (D-208): `servicos/exclusao.py` e a página `/ui/excluir/<modelo>/<pk>/`."""

from unittest import mock

from django.apps import apps
from django.db import IntegrityError, connection, models, transaction
from django.test import TestCase
from django.urls import reverse

from nucleo.models import (
    Ano, Bloqueio, Componente, CorPadrao, Corte, Descritor, Etapa, FotoRevista, Matriz, MatrizEtapaCC, Parceiro,
    ParceiroAno, Projeto, ProjetoCor, ProjetoPasso, Revista, RevistaFasciculo, RevistaSecao, Tarefa, Template,
    TemplateVersao,
)  # fmt: skip
from nucleo.models.revista import Motivo
from nucleo.servicos import bloqueio, exclusao
from nucleo.servicos.abrir_ano import abrir_ano
from nucleo.servicos.cascata import gravar_cortes
from nucleo.servicos.exclusao import EmUso, apagar_ano, excluir, impedimentos, resumo_ano
from nucleo.servicos.foto import fotografar
from nucleo.tests.test_resolver import Mundo, usuario

# FKs de nucleo que não são PROTECT, de propósito (D-205): trava efêmera, partes da matriz e da revista, e a
# origem só de consulta da matriz duplicada (D-113) e a base da etapa do projeto, que sobrevive à base apagada
# porque guarda a foto (D-227).
NAO_PROTECT = {
    "Bloqueio.matriz_etapa_cc", "Bloqueio.projeto", "Bloqueio.template", "Bloqueio.usuario",
    "Descritor.matriz_etapa_cc", "Tarefa.descritor", "RevistaFasciculo.revista", "RevistaSecao.revista_fasciculo",
    "Matriz.duplicada_de", "MatrizEtapaCC.base",
}  # fmt: skip


def rotulos(obj, usuario=None):
    return {i.rotulo: i.contagem for i in impedimentos(obj, usuario)}


def url(modelo, pk, **query):
    destino = reverse("ui_excluir", args=[modelo, pk])
    return destino + ("?" + "&".join(f"{k}={v}" for k, v in query.items()) if query else "")


class Base(TestCase):
    @classmethod
    def setUpTestData(cls):
        Mundo.montar(cls)
        cls.adm = usuario("adm", "Admin")
        cls.ped = usuario("ped", "Pedagógica")
        cls.mid = usuario("mid", "Mídias Digitais")
        cls.imp = usuario("imp", "Impresso")

    def livre(self, nome="Livre"):
        """Parceiro só com o ParceiroAno (parte): nada depende dele."""
        p = Parceiro.objects.create(nome=nome)
        ParceiroAno.objects.create(parceiro=p, ano=self.ano)
        return p


class FksTest(TestCase):
    def test_so_as_fks_permitidas_nao_sao_protect(self):
        """Trava: FK nova em nucleo nasce PROTECT, ou entra aqui com motivo (D-205)."""
        achadas = {
            f"{m.__name__}.{f.name}"
            for m in apps.get_app_config("nucleo").get_models()
            if not m.__name__.startswith("Historical")
            for f in m._meta.fields
            if f.is_relation and f.remote_field.on_delete is not models.PROTECT
        }
        self.assertEqual(achadas, NAO_PROTECT)


class ImpedimentosTest(Base):
    def test_parceiro_em_uso_por_corte_e_projeto_e_parceiroano_nao_conta(self):
        go = self.go["LP"].projeto.parceiro_ano.parceiro
        r = rotulos(go)
        self.assertEqual(r["cortes"], 3)
        self.assertEqual(r["projetos"], 1)
        self.assertEqual(len(r), 2)  # o ParceiroAno é parte

    def test_parceiro_livre_sai_com_o_parceiroano(self):
        p = self.livre()
        self.assertEqual(impedimentos(p), [])
        excluir(p, self.ped)
        self.assertFalse(Parceiro.objects.filter(pk=p.pk).exists())
        self.assertFalse(ParceiroAno.objects.filter(parceiro_id=p.pk).exists())
        ultimo = Parceiro.history.filter(id=p.pk).latest("history_date")
        self.assertEqual((ultimo.history_type, ultimo.history_user), ("-", self.ped))

    def test_etapa_em_uso_e_etapa_livre_renumera(self):
        r = rotulos(self.e5)
        self.assertEqual(set(r), {"cortes", "etapas × componente de matriz"})
        e1 = Etapa.objects.create(ano=self.ano, codigo="1EM", escala_max=500, ordem=0)
        e3 = Etapa.objects.create(ano=self.ano, codigo="3EM", escala_max=500, ordem=0)
        self.assertEqual(Etapa.objects.get(pk=e3.pk).ordem, 4)
        excluir(e1, self.ped)
        self.assertFalse(Etapa.objects.filter(pk=e1.pk).exists())
        self.assertEqual(Etapa.objects.get(pk=e3.pk).ordem, 3)  # Etapa.delete renumera

    def test_etapa_com_passo_de_projeto(self):
        e3 = Etapa.objects.create(ano=self.ano, codigo="3EM", escala_max=500, ordem=0)
        ProjetoPasso.objects.create(projeto=self.go["LP"].projeto, etapa=e3, componente=self.lp, ano=self.ano, passo=10)
        self.assertEqual(rotulos(e3), {"projetos com passo próprio": 1})

    def test_componente_em_uso_e_livre(self):
        r = rotulos(self.lp)
        self.assertLessEqual({"revistas", "templates", "cortes", "etapas × componente de matriz"}, set(r))
        self.assertEqual(r["revistas"], 2)  # GO e PE; os fascículos contam como a revista
        novo = Componente.objects.create(ano=self.ano, codigo="CI", nome="Ciências")
        self.assertEqual(impedimentos(novo), [])
        excluir(novo, self.ped)
        self.assertFalse(Componente.objects.filter(pk=novo.pk).exists())

    def test_matriz_em_uso_conta_parceiros_e_mostra_ate_5_links(self):
        for i in range(4):
            ParceiroAno.objects.create(parceiro=Parceiro.objects.create(nome=f"P{i}"), ano=self.ano, matriz=self.matriz)
        (imp,) = impedimentos(self.matriz)  # as 4 MECs são partes
        self.assertEqual((imp.rotulo, imp.contagem, len(imp.links)), ("parceiros que usam a matriz", 6, 5))
        self.assertTrue(all(u == reverse("ui_lotes_matriz", args=[2026]) for _, u in imp.links))

    def test_matriz_livre_sai_com_mec_descritores_e_tarefas(self):
        m = Matriz.objects.create(ano=self.ano, nome="Livre")
        mec = MatrizEtapaCC.objects.create(matriz=m, etapa=self.e5, componente=self.lp, ano=self.ano, passo=25)
        d = Descritor.objects.create(matriz_etapa_cc=mec, codigo="D01", descricao="x", ordem=1)
        Tarefa.objects.create(descritor=d, inicio=100, fim=150, texto="t", ordem=1)
        excluir(m, self.mid)
        self.assertFalse(Matriz.objects.filter(pk=m.pk).exists())
        self.assertFalse(MatrizEtapaCC.objects.filter(pk=mec.pk).exists())
        self.assertFalse(Descritor.objects.filter(pk=d.pk).exists())

    def test_mec_com_bloqueio_de_outra_pessoa_impede_a_matriz(self):
        m = Matriz.objects.create(ano=self.ano, nome="Livre")
        mec = MatrizEtapaCC.objects.create(matriz=m, etapa=self.e5, componente=self.lp, ano=self.ano)
        self.assertTrue(bloqueio.adquirir(mec, self.mid, "aba"))
        self.assertEqual(rotulos(m, self.ped), {"em edição por outra pessoa": 1})
        self.assertEqual(rotulos(m, self.mid), {})  # o próprio bloqueio não impede
        with self.assertRaises(EmUso):
            excluir(m, self.ped)
        excluir(m, self.mid)
        self.assertFalse(Bloqueio.objects.exists())

    def test_template_em_uso_lista_as_revistas(self):
        t = self.templates["LP", "F1"]
        (imp,) = impedimentos(t)
        self.assertEqual((imp.rotulo, imp.contagem), ("revistas", 2))
        self.assertIn(reverse("ui_revista_editar", args=[2026, self.go["LP"].pk]), [u for _, u in imp.links])

    def test_template_livre_sai_com_as_versoes(self):
        t = Template.objects.create(ano=self.ano, componente=self.lp, fasciculo="F1", nome="Livre")
        for n in (1, 2):
            TemplateVersao.objects.create(template=t, numero=n, texto="## introducao\nA\n\nB\n")
        excluir(t, self.ped)
        self.assertFalse(Template.objects.filter(pk=t.pk).exists())
        self.assertFalse(TemplateVersao.objects.filter(template_id=t.pk).exists())

    def test_template_com_bloqueio_de_outra_pessoa(self):
        t = Template.objects.create(ano=self.ano, componente=self.lp, fasciculo="F1", nome="Livre")
        bloqueio.adquirir(t, self.mid, "aba")
        self.assertEqual(rotulos(t, self.ped), {"em edição por outra pessoa": 1})


class TriggerTest(Base):
    """A chave `revista.apagar_versoes` só abre o DELETE, e só dentro de excluir/apagar_ano (D-206, D-207)."""

    def setUp(self):
        self.t = Template.objects.create(ano=self.ano, componente=self.lp, fasciculo="F1", nome="Livre")
        self.v = TemplateVersao.objects.create(template=self.t, numero=1, texto="x")

    def recusa(self, acao):
        with self.assertRaises(IntegrityError), transaction.atomic():
            acao()

    def test_fora_da_chave_recusa_delete_e_update(self):
        self.recusa(lambda: TemplateVersao.objects.filter(pk=self.v.pk).delete())
        self.recusa(lambda: TemplateVersao.objects.filter(pk=self.v.pk).update(texto="y"))

    def test_com_a_chave_update_continua_recusado(self):
        def update_com_chave():
            with connection.cursor() as c:
                c.execute("SET LOCAL revista.apagar_versoes = 'on'")
            TemplateVersao.objects.filter(pk=self.v.pk).update(texto="y")

        self.recusa(update_com_chave)

    def test_a_chave_desliga_depois_de_excluir(self):
        excluir(self.t, self.ped)
        outro = Template.objects.create(ano=self.ano, componente=self.lp, fasciculo="F2", nome="Livre")
        v = TemplateVersao.objects.create(template=outro, numero=1, texto="x")
        self.recusa(lambda: TemplateVersao.objects.filter(pk=v.pk).delete())


class CorridaTest(Base):
    def test_protectederror_vira_emuso(self):
        with mock.patch.object(exclusao, "impedimentos", return_value=[]), self.assertRaises(EmUso):
            excluir(self.e5, self.ped)
        self.assertTrue(Etapa.objects.filter(pk=self.e5.pk).exists())

    def test_integrityerror_do_banco_vira_emuso(self):
        """O app não viu o corte (gravado por outra transação); a FK do banco viu."""
        e3 = Etapa.objects.create(ano=self.ano, codigo="3EM", escala_max=500, ordem=0)
        Corte.objects.create(parceiro_ano=ParceiroAno.objects.get(parceiro__nome="GO"), etapa=e3, componente=self.lp, ano=self.ano, valores=[200])
        campo = Corte._meta.get_field("etapa").remote_field
        with (
            mock.patch.object(exclusao, "impedimentos", return_value=[]),
            mock.patch.object(campo, "on_delete", models.DO_NOTHING),
            self.assertRaises(EmUso),
        ):
            excluir(e3, self.ped)
        self.assertTrue(Etapa.objects.filter(pk=e3.pk).exists())
        Corte.objects.create(parceiro_ano=ParceiroAno.objects.get(parceiro__nome="PE"), etapa=e3, componente=self.lp, ano=self.ano, valores=[200])  # a transação segue usável


class ApagarAnoTest(Base):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        a27, _ = abrir_ano(2027, cls.usuario)
        etapa = {e.codigo: e for e in Etapa.objects.filter(ano=a27)}
        cc = {c.codigo: c for c in Componente.objects.filter(ano=a27)}
        go = Parceiro.objects.get(nome="GO")
        pa = ParceiroAno.objects.create(parceiro=go, ano=a27, matriz=Matriz.objects.get(ano=a27))
        gravar_cortes(pa, [(etapa["5EF"], cc["LP"], [200, 300])], cls.usuario)
        projeto = Projeto.objects.get(parceiro_ano=pa)
        ProjetoPasso.objects.create(projeto=projeto, etapa=etapa["5EF"], componente=cc["LP"], ano=a27, passo=10)
        ProjetoCor.objects.create(projeto=projeto, padrao=1, cor="#000000")
        revista = Revista.objects.get(projeto=projeto)
        for rf in RevistaFasciculo.objects.filter(revista=revista):
            rf.template = Template.objects.get(ano=a27, componente=cc["LP"], fasciculo=rf.fasciculo)
            rf.save()
        rf = RevistaFasciculo.objects.get(revista=revista, fasciculo="F1")
        RevistaSecao.objects.create(
            revista_fasciculo=rf, template=rf.template, secao="introducao", texto="cópia",
            template_versao=TemplateVersao.objects.get(template=rf.template),
        )  # fmt: skip
        fotografar(revista, Motivo.IMPRESSO, cls.usuario)
        bloqueio.adquirir(projeto, cls.ped, "aba")
        cls.a27 = a27

    def contagens(self, ano):
        return {r: n for r, n in resumo_ano(Ano.objects.get(ano=ano))}

    def test_resumo_conta_o_que_sai(self):
        r = self.contagens(2027)
        self.assertEqual((r["projetos"], r["revistas"], r["fotos de revista"], r["cortes"]), (1, 1, 1, 1))
        self.assertEqual(r["templates"], 4)
        self.assertEqual(r["versões de template"], 4)
        self.assertEqual(r["matrizes"], 1)

    def test_apaga_tudo_do_ano_e_deixa_os_outros(self):
        antes = self.contagens(2026)
        versoes_26 = TemplateVersao.objects.filter(template__ano__ano=2026).count()
        apagar_ano(self.a27, self.adm)
        self.assertFalse(Ano.objects.filter(ano=2027).exists())
        for modelo in (Etapa, Componente, CorPadrao, Matriz, MatrizEtapaCC, ParceiroAno, Corte, Projeto, Revista, RevistaFasciculo, Template):
            self.assertFalse(modelo.objects.filter(ano_id=self.a27.pk).exists(), modelo.__name__)
        self.assertFalse(FotoRevista.objects.filter(revista__ano_id=self.a27.pk).exists())
        self.assertFalse(TemplateVersao.objects.filter(template__ano_id=self.a27.pk).exists())
        self.assertFalse(Bloqueio.objects.exists())
        self.assertEqual(self.contagens(2026), antes)
        self.assertEqual(TemplateVersao.objects.filter(template__ano__ano=2026).count(), versoes_26)
        self.assertTrue(Parceiro.objects.filter(nome="GO").exists())
        self.assertEqual(Ano.history.filter(ano=2027).latest("history_date").history_user, self.adm)
        # a chave voltou a desligar
        livre = Template.objects.create(ano=self.ano, componente=self.lp, fasciculo="F1", nome="Livre")
        v = TemplateVersao.objects.create(template=livre, numero=1, texto="x")
        with self.assertRaises(IntegrityError), transaction.atomic():
            TemplateVersao.objects.filter(pk=v.pk).delete()


class ParceiroAtivoTest(Base):
    def test_desativar_e_reativar_com_historico(self):
        p = self.livre()
        exclusao.desativar_parceiro(p, self.ped)
        p.refresh_from_db()
        self.assertIsNotNone(p.desativado_em)
        self.assertEqual(Parceiro.history.filter(id=p.pk).latest("history_date").history_user, self.ped)
        exclusao.reativar_parceiro(p, self.mid)
        p.refresh_from_db()
        self.assertIsNone(p.desativado_em)

    def test_parceiros_do_ano(self):
        sem_dados = self.livre("Sem dados")
        go = Parceiro.objects.get(nome="GO")
        ativo = self.livre("Ativo")
        for p in (sem_dados, go):
            exclusao.desativar_parceiro(p, self.ped)
        lista = set(exclusao.parceiros_do_ano(self.ano))
        self.assertIn(ativo, lista)
        self.assertIn(go, lista)  # desativado, mas com corte em 2026
        self.assertNotIn(sem_dados, lista)

    def test_rota_desativa_e_impresso_403(self):
        p = self.livre()
        rota = reverse("ui_parceiro_ativo", args=[p.pk])
        self.client.force_login(self.imp)
        self.assertEqual(self.client.post(rota, {"acao": "desativar"}).status_code, 403)
        self.client.force_login(self.ped)
        self.assertEqual(self.client.post(rota, {"acao": "desativar"}).status_code, 302)
        self.assertIsNotNone(Parceiro.objects.get(pk=p.pk).desativado_em)
        self.client.post(rota, {"acao": "reativar"})
        self.assertIsNone(Parceiro.objects.get(pk=p.pk).desativado_em)

    def test_pagina_em_uso_oferece_desativar(self):
        go = Parceiro.objects.get(nome="GO")
        self.client.force_login(self.ped)
        r = self.client.get(url("parceiro", go.pk))
        self.assertContains(r, reverse("ui_parceiro_ativo", args=[go.pk]))
        self.assertContains(r, "Desativar")


class ViewTest(Base):
    def test_anonimo_vai_ao_login_e_modelo_desconhecido_404(self):
        self.assertEqual(self.client.get(url("parceiro", 1)).status_code, 302)
        self.client.force_login(self.adm)
        self.assertEqual(self.client.get(url("revista", self.go["LP"].pk)).status_code, 404)

    def test_impresso_403_em_tudo(self):
        self.client.force_login(self.imp)
        alvos = {
            "ano": 2026, "parceiro": self.livre().pk, "etapa": self.e5.pk, "componente": self.lp.pk,
            "matriz": self.matriz.pk, "template": self.templates["LP", "F1"].pk,
        }  # fmt: skip
        for modelo, pk in alvos.items():
            with self.subTest(modelo=modelo):
                self.assertEqual(self.client.get(url(modelo, pk)).status_code, 403)
                self.assertEqual(self.client.post(url(modelo, pk), {"confirmacao": "x"}).status_code, 403)

    def test_so_admin_apaga_ano(self):
        Ano.objects.create(ano=2030)
        for u in (self.ped, self.mid):
            self.client.force_login(u)
            self.assertEqual(self.client.get(url("ano", 2030)).status_code, 403)
            self.assertEqual(self.client.post(url("ano", 2030), {"confirmacao": "2030"}).status_code, 403)
        self.assertTrue(Ano.objects.filter(ano=2030).exists())

    def test_admin_apaga_ano_digitando_o_ano(self):
        abrir_ano(2027, self.usuario)
        self.client.force_login(self.adm)
        r = self.client.get(url("ano", 2027))
        self.assertContains(r, "Apagar o ano 2027")
        self.assertContains(r, "templates")
        self.client.post(url("ano", 2027), {"confirmacao": "2026"})
        self.assertTrue(Ano.objects.filter(ano=2027).exists())
        r = self.client.post(url("ano", 2027), {"confirmacao": "2027"})
        self.assertRedirects(r, reverse("ui_anos"), fetch_redirect_response=False)
        self.assertFalse(Ano.objects.filter(ano=2027).exists())

    def test_get_e_post_do_livre(self):
        p = self.livre("Parceiro Livre")
        self.client.force_login(self.ped)
        r = self.client.get(url("parceiro", p.pk))
        self.assertContains(r, 'data-confirmar="Parceiro Livre"')
        self.assertContains(r, "btn-destrutivo")
        r = self.client.post(url("parceiro", p.pk), {"confirmacao": "Parceiro"})
        self.assertContains(r, "Nada foi excluído")
        self.assertTrue(Parceiro.objects.filter(pk=p.pk).exists())
        r = self.client.post(url("parceiro", p.pk, voltar="/ui/anos/"), {"confirmacao": "Parceiro Livre"})
        self.assertRedirects(r, "/ui/anos/", fetch_redirect_response=False)
        self.assertFalse(Parceiro.objects.filter(pk=p.pk).exists())

    def test_em_uso_mostra_impedimento_e_post_nao_apaga(self):
        self.client.force_login(self.ped)
        r = self.client.get(url("componente", self.lp.pk))
        self.assertContains(r, "revistas")
        self.assertContains(r, reverse("ui_revista_editar", args=[2026, self.go["LP"].pk]))
        self.assertNotContains(r, "btn-destrutivo")
        self.client.post(url("componente", self.lp.pk), {"confirmacao": "LP"})
        self.assertTrue(Componente.objects.filter(pk=self.lp.pk).exists())

    def test_corrida_na_view_mostra_impedimento(self):
        e3 = Etapa.objects.create(ano=self.ano, codigo="3EM", escala_max=500, ordem=0)
        self.client.force_login(self.ped)
        with mock.patch.object(exclusao, "excluir", side_effect=EmUso([])):
            r = self.client.post(url("etapa", e3.pk), {"confirmacao": "3EM"})
        self.assertContains(r, "Nada foi excluído")
        self.assertNotContains(r, "btn-destrutivo")

    def test_voltar_de_fora_e_ignorado(self):
        p = self.livre()
        self.client.force_login(self.ped)
        r = self.client.get(url("parceiro", p.pk, voltar="https://exemplo.com/"))
        self.assertNotContains(r, "exemplo.com")
        r = self.client.post(url("parceiro", p.pk, voltar="https://exemplo.com/"), {"confirmacao": "Livre"})
        self.assertFalse(r["Location"].startswith("https://exemplo.com"))
