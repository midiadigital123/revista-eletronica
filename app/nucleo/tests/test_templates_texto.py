"""Regra dos templates de texto comum ao admin e à tela B: seções do F2, rótulos, impacto e a migração 0023."""

import importlib

from django.apps import apps
from django.test import SimpleTestCase, TestCase

from nucleo import texto
from nucleo.models import RevistaFasciculo, RevistaInfografico, RevistaSecao, Template, TemplateVersao
from nucleo.servicos.resolver import versao_atual
from nucleo.templates_texto import impacto, rotulo, secoes_permitidas
from nucleo.tests.test_resolver import F2_LP, Mundo


class SecoesF2Test(SimpleTestCase):
    def test_secoes_permitidas_f2_sao_as_fixas_do_template(self):
        self.assertEqual(secoes_permitidas("F2"), {"fixas": list(texto.SECOES_F2), "repetiveis": {}})

    def test_rotulos_do_f2(self):
        self.assertEqual(rotulo("passo-tarefas"), "Passo: tarefas")
        self.assertEqual(rotulo("passo-descritor"), "Passo: descritor")
        self.assertEqual(rotulo("dlg-descritor"), "Diálogo do descritor")
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

    def test_template_ganha_a_versao_seguinte_com_as_8_secoes(self):
        self.migrar()
        for cc in ("LP", "MT"):
            versoes = TemplateVersao.objects.filter(template=self.templates[cc, "F2"]).order_by("numero")
            self.assertEqual([v.numero for v in versoes], [1, 2])
            self.assertEqual(list(texto.secoes(versoes[1].texto)), list(texto.SECOES_F2))
            texto.validar(versoes[1].texto, "F2")
        self.assertEqual(TemplateVersao.objects.get(template=self.tpl, numero=1).texto, F2_LP)

    def test_f1_e_outro_componente_ficam(self):
        outro = Template.objects.create(ano=self.ano, componente=self.mt, fasciculo="F2", nome="Outro")
        TemplateVersao.objects.create(template=outro, numero=1, texto=F2_LP)
        self.mt.codigo = "XX"
        self.mt.save()
        self.migrar()
        self.assertEqual(TemplateVersao.objects.filter(template=outro).count(), 1)
        self.assertEqual(TemplateVersao.objects.filter(template=self.templates["LP", "F1"]).count(), 1)

    def test_copias_dlg_p2_e_p3_viram_textos_do_infografico_outras(self):
        self.migrar()
        info = RevistaInfografico.objects.get(revista=self.rev, tipo="outras")
        self.assertEqual((info.texto_progressao, info.texto_habilidades), ("Progressão", "Habilidades"))

    def test_so_preenche_campo_vazio_e_cai_no_alfa_se_nao_ha_outras(self):
        RevistaInfografico.objects.filter(revista=self.rev, tipo="outras").update(texto_habilidades="Já escrito")
        self.migrar()
        info = RevistaInfografico.objects.get(revista=self.rev, tipo="outras")
        self.assertEqual((info.texto_progressao, info.texto_habilidades), ("Progressão", "Já escrito"))

        RevistaInfografico.objects.filter(revista=self.rev, tipo="outras").update(texto_progressao="", texto_habilidades="")
        RevistaSecao.objects.create(
            revista_fasciculo=self.rf, template=self.tpl, secao="dlg-p3", texto="Habilidades", template_versao=self.v1
        )
        RevistaInfografico.objects.filter(revista=self.rev, tipo="outras").delete()
        alfa = RevistaInfografico.objects.create(
            revista=self.rev, tipo="alfa", componente=self.lp, ano=self.ano
        )
        self.migrar()
        alfa.refresh_from_db()
        self.assertEqual(alfa.texto_habilidades, "Habilidades")

    def test_apaga_as_copias_fora_das_8_secoes_e_mantem_a_abertura(self):
        self.migrar()
        self.assertEqual(self.secoes(), {"abertura"})

    def test_idempotente(self):
        self.migrar()
        self.migrar()
        self.assertEqual(versao_atual(self.tpl.pk).numero, 2)
