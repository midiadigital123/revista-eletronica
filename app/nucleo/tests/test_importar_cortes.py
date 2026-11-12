"""importar_cortes (D-261): parceiros das Somativas + cortes da planilha, pela cascata."""

import tempfile
from io import StringIO
from pathlib import Path

from django.core.management import call_command
from django.test import TestCase
from openpyxl import Workbook

from nucleo.models import Corte, Parceiro, Revista, RevistaInfografico
from nucleo.tests.test_importacao import cadastrar
from nucleo.tests.test_resolver import usuario


def xlsx(pasta, nome, abas):
    wb = Workbook()
    wb.remove(wb.active)
    for titulo, linhas in abas.items():
        ws = wb.create_sheet(titulo)
        for linha in linhas:
            ws.append(linha)
    caminho = Path(pasta) / nome
    wb.save(caminho)
    return str(caminho)


CAB_S = ["Subprograma", "Cód_Bizagi", "Disciplinas", "Etapas avaliadas", "Etapas para revista eletrônica"]


class ImportarCortesTest(TestCase):
    def setUp(self):
        cadastrar(2026)
        self.autor = usuario("carga")
        pasta = tempfile.mkdtemp()
        self.somativas = xlsx(pasta, "s.xlsx", {
            "REDES_ESTADUAIS": [
                CAB_S,
                ["Goiás - SAEGO ALFA 2026", 1, "LP, MT", "2EF", "2EF"],
                ["Goiás - SAEGO 2026", 1, "LP, MT", "3EM, 4EF", "4EF, 3EM"],
            ],
            "REDES_MUNICIPAIS": [
                CAB_S,
                ["Municípios - Anchieta - Somativa 2026", 2, "LP, MT", "4EF", "4EF"],
                ["Santa Catarina - SEAESC 2026", 3, "LP, MT", "2EF", "2EF"],
            ],
        })
        cab = ["Grupo", "Parceiro", "Etapa"]
        self.cortes = xlsx(pasta, "c.xlsx", {
            "2EF - LP": [cab + ["LP"], [1, "GO", "2EF", "350, 400, 500"], [2, "SC", "2EF", "500, 600, 700"]],
            "2EF - MT": [cab + ["MT"], [1, "GO", "2EF", "400, 500, 625"]],  # SC sem MT: lacuna
            "3EM - LP": [cab + ["LP"], [1, "GO", "3EM", "225, 275, 325"]],
            "3EM - MT": [cab + ["MT"], [1, "GO", "3EM", "250, 300, 350"], [2, "AM", "3EM", "100, 200, 300"]],
        })

    def rodar(self, *extra):
        saida = StringIO()
        call_command("importar_cortes", self.somativas, self.cortes, "--ano", "2026", "--usuario", "carga",
                     *extra, stdout=saida)
        return saida.getvalue()

    def test_alfa_e_regular_viram_um_parceiro_com_uma_revista_por_componente(self):
        self.rodar()
        self.assertEqual(sorted(Parceiro.objects.values_list("nome", flat=True)), ["Anchieta", "GO", "SC"])
        go = Parceiro.objects.get(nome="GO")
        self.assertEqual(Corte.objects.filter(parceiro_ano__parceiro=go).count(), 4)
        self.assertEqual(Revista.objects.filter(projeto__parceiro_ano__parceiro=go).count(), 2)  # LP e MT
        tipos = RevistaInfografico.objects.filter(revista__projeto__parceiro_ano__parceiro=go, arquivado_em=None)
        self.assertEqual(sorted(set(tipos.values_list("tipo", flat=True))), ["alfa", "outras"])
        self.assertFalse(Corte.objects.filter(parceiro_ano__parceiro__nome="Anchieta").exists())  # 4EF: fora
        self.assertEqual(Corte.objects.filter(parceiro_ano__parceiro__nome="SC").count(), 1)  # só LP

    def test_simular_nao_grava_e_segunda_rodada_pula_quem_ja_tem_corte(self):
        self.assertIn("Simulação", self.rodar("--simular"))
        self.assertEqual(Parceiro.objects.count(), 0)
        self.rodar()
        Corte.objects.filter(parceiro_ano__parceiro__nome="GO", etapa__codigo="2EF").update(valores=[1, 2, 3])
        self.assertIn("GO: pulado (já tem cortes)", self.rodar())
        corte = Corte.objects.get(parceiro_ano__parceiro__nome="GO", etapa__codigo="2EF", componente__codigo="LP")
        self.assertEqual(list(corte.valores), [1, 2, 3])
