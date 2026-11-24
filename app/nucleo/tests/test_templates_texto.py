"""Regra dos templates de texto comum ao admin e à tela B: seções do F2, rótulos, impacto e as migrações 0023 e 0025."""

import importlib

from django.apps import apps
from django.conf import settings
from django.test import SimpleTestCase, TestCase

from nucleo import texto
from nucleo.management.commands.carregar_templates import AVISO
from nucleo.models import Revista, RevistaFasciculo, RevistaInfografico, RevistaSecao, Template, TemplateVersao
from nucleo.servicos.resolver import versao_atual
from nucleo.templates_texto import impacto, rotulo
from nucleo.tests.test_resolver import F2_LP, Mundo

SEED = settings.BASE_DIR / "templates_seed" / "2026"


class SecoesF2Test(SimpleTestCase):
    def test_rotulos_do_f2(self):
        self.assertEqual(rotulo("passo-tarefas"), "Passo: tarefas")
        self.assertEqual(rotulo("passo-descritor"), "Passo: descritor")
        self.assertEqual(rotulo("dlg-descritor"), "Diálogo do descritor")
        self.assertEqual(rotulo("dlg-tarefas"), "Diálogo das tarefas")
        self.assertEqual(rotulo("tarefas-fechamento"), "Fechamento das tarefas")
        self.assertEqual(rotulo("fechamento"), "Fechamento")


class ImpactoTest(TestCase):
    def test_impacto_nao_tem_mais_ids_faltando(self):
        Mundo.montar(self)
        linhas = impacto(self.templates["LP", "F2"], "## abertura\nA\n\nx\n")
        self.assertTrue(linhas)
        self.assertTrue(all("ids_faltando" not in x for x in linhas))


class Migracao0023Test(TestCase):
    """Molde: test_migracao_cria_os_infograficos... (test_cascata.py). Importa a função da migração."""

    def setUp(self):
        Mundo.montar(self)
        self.mod = importlib.import_module("nucleo.migrations.0023_template_f2_secoes")
        self.rev = self.go["LP"]
        self.rf = RevistaFasciculo.objects.get(revista=self.rev, fasciculo="F2")
        self.tpl = self.templates["LP", "F2"]
        self.v1 = versao_atual(self.tpl.pk)
        for secao, corpo in (("abertura", "A"), ("passo2", "P2"), ("dlg-p2", "Progressão"), ("dlg-p3", "Habilidades")):
            RevistaSecao.objects.create(
                revista_fasciculo=self.rf, template=self.tpl, secao=secao, texto=corpo, template_versao=self.v1
            )

    def migrar(self):
        self.mod.criar(apps, None)

    def secoes(self):
        return set(RevistaSecao.objects.filter(revista_fasciculo=self.rf).values_list("secao", flat=True))

    def test_template_ganha_a_versao_seguinte_com_as_9_secoes(self):
        self.migrar()
        for cc in ("LP", "MT"):
            versoes = TemplateVersao.objects.filter(template=self.templates[cc, "F2"]).order_by("numero")
            self.assertEqual([v.numero for v in versoes], [1, 2])
            self.assertEqual(list(texto.secoes(versoes[1].texto)), list(texto.SECOES_F2))
            texto.validar(versoes[1].texto, "F2")
        self.assertEqual(TemplateVersao.objects.get(template=self.tpl, numero=1).texto, F2_LP)

    def test_f1_e_outro_componente_ficam(self):
        outro = Template.objects.create(ano=self.ano, componente=self.mt, fasciculo="F2", nome="Outro")
        v1_outro = TemplateVersao.objects.create(template=outro, numero=1, texto=F2_LP)
        rf_outro = RevistaFasciculo.objects.get(revista=self.pe["MT"], fasciculo="F2")
        rf_outro.template = outro
        rf_outro.save()
        for secao in ("passo2", "dlg-p3"):
            RevistaSecao.objects.create(
                revista_fasciculo=rf_outro, template=outro, secao=secao, texto="Cópia.", template_versao=v1_outro
            )
        self.mt.codigo = "XX"
        self.mt.save()
        self.migrar()
        self.assertEqual(TemplateVersao.objects.filter(template=outro).count(), 1)
        self.assertEqual(TemplateVersao.objects.filter(template=self.templates["LP", "F1"]).count(), 1)
        copias = RevistaSecao.objects.filter(revista_fasciculo=rf_outro, template=outro)
        self.assertEqual(set(copias.values_list("secao", flat=True)), {"passo2", "dlg-p3"})
        info = RevistaInfografico.objects.filter(revista=self.pe["MT"]).first()
        self.assertEqual((info.texto_progressao, info.texto_habilidades), ("", ""))

    def test_copias_dlg_p2_e_p3_viram_textos_do_infografico_outras(self):
        self.migrar()
        info = RevistaInfografico.objects.get(revista=self.rev, tipo="outras")
        self.assertEqual((info.texto_progressao, info.texto_habilidades), ("Progressão", "Habilidades"))

    def test_so_preenche_campo_vazio(self):
        RevistaInfografico.objects.filter(revista=self.rev, tipo="outras").update(texto_habilidades="Já escrito")
        self.migrar()
        info = RevistaInfografico.objects.get(revista=self.rev, tipo="outras")
        self.assertEqual((info.texto_progressao, info.texto_habilidades), ("Progressão", "Já escrito"))

    def test_revista_so_com_alfa_recebe_no_alfa(self):
        RevistaInfografico.objects.filter(revista=self.rev, tipo="outras").delete()
        alfa = RevistaInfografico.objects.create(revista=self.rev, tipo="alfa", componente=self.lp, ano=self.ano)
        self.migrar()
        alfa.refresh_from_db()
        self.assertEqual((alfa.texto_progressao, alfa.texto_habilidades), ("Progressão", "Habilidades"))

    def test_texto_congelado_e_o_do_seed(self):
        seed = AVISO.sub("", (SEED / "f2-lp.hbs").read_text(encoding="utf-8-sig"))
        m25 = importlib.import_module("nucleo.migrations.0025_tarefas_fechamento_sem_lp")
        self.assertEqual(
            self.mod.TEXTO_F2.replace(m25.RETIRAR, ""), seed,  # a 0025 tirou um parágrafo do seed
            "A migração 0023 é histórica: não a altere. Se o seed do F2 mudou de propósito, ajuste este teste.",
        )

    def test_apaga_as_copias_fora_das_8_secoes_e_mantem_a_abertura(self):
        self.migrar()
        self.assertEqual(self.secoes(), {"abertura"})

    def test_idempotente(self):
        self.migrar()
        self.migrar()
        self.assertEqual(versao_atual(self.tpl.pk).numero, 2)


class Migracao0025Test(TestCase):
    """Molde: Migracao0023Test. Importa a função da migração."""

    def setUp(self):
        self.m23 = importlib.import_module("nucleo.migrations.0023_template_f2_secoes")
        self.mod = importlib.import_module("nucleo.migrations.0025_tarefas_fechamento_sem_lp")
        Mundo.montar(self, f2_lp=self.m23.TEXTO_F2)
        self.tpl = self.templates["LP", "F2"]
        self.v1 = versao_atual(self.tpl.pk)
        self.corpo = texto.secoes(self.m23.TEXTO_F2)["tarefas-fechamento"][1]

    def copia(self, revista, corpo):
        rf = RevistaFasciculo.objects.get(revista=revista, fasciculo="F2")
        return RevistaSecao.objects.create(
            revista_fasciculo=rf, template=self.tpl, secao="tarefas-fechamento", texto=corpo, template_versao=self.v1
        )

    def migrar(self):
        self.mod.frente(apps, None)

    def test_template_ganha_versao_sem_o_paragrafo_e_a_anterior_fica(self):
        self.migrar()
        self.migrar()  # idempotente
        v2 = versao_atual(self.tpl.pk)
        self.assertEqual(v2.numero, 2)
        self.assertNotIn(self.mod.PARAGRAFO, v2.texto)
        self.assertEqual(v2.texto, self.m23.TEXTO_F2.replace(self.mod.RETIRAR, ""))
        self.assertIn("Fechamento das tarefas\n\nEssa trajetória", v2.texto)
        self.assertEqual(TemplateVersao.objects.get(pk=self.v1.pk).texto, self.m23.TEXTO_F2)
        self.assertEqual(TemplateVersao.objects.filter(template=self.templates["LP", "F1"]).count(), 1)
        self.assertEqual(TemplateVersao.objects.filter(template=self.templates["MT", "F2"]).count(), 1)  # sem o parágrafo

    def test_copia_com_o_paragrafo_perde_o_paragrafo(self):
        c = self.copia(self.go["LP"], self.corpo)
        self.migrar()
        c.refresh_from_db()
        self.assertEqual(c.texto, self.corpo.replace(self.mod.RETIRAR, ""))
        self.assertTrue(c.texto.startswith("Essa trajetória"))
        self.assertEqual(c.template_versao_id, versao_atual(self.tpl.pk).pk)  # já tem a mudança: não fica desatualizada

    def test_copia_de_versao_mais_antiga_continua_desatualizada(self):
        TemplateVersao.objects.create(template=self.tpl, numero=2, texto=self.m23.TEXTO_F2 + "\n")  # outra mudança depois da cópia
        c = self.copia(self.go["LP"], self.corpo)
        self.migrar()
        c.refresh_from_db()
        self.assertNotIn(self.mod.PARAGRAFO, c.texto)
        self.assertEqual(c.template_versao_id, self.v1.pk)  # falta a mudança da versão 2: o aviso continua

    def test_copia_editada_fica(self):
        editado = self.corpo.replace("tirinha", "tira", 1)
        c = self.copia(self.go["LP"], editado)
        self.migrar()
        c.refresh_from_db()
        self.assertEqual(c.texto, editado)

    def test_revista_arquivada_fica(self):
        c = self.copia(self.pe["LP"], self.corpo)
        Revista.objects.filter(pk=self.pe["LP"].pk).update(arquivada_em="2026-10-29T12:00:00Z")
        self.migrar()
        c.refresh_from_db()
        self.assertEqual(c.texto, self.corpo)
