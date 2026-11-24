"""importar_cortes (D-261, D-278): parceiros e etapas das Somativas + cortes da planilha, pela cascata."""

import tempfile
from io import StringIO
from pathlib import Path

from django.core.management import call_command
from django.test import TestCase
from openpyxl import Workbook

from nucleo.models import Corte, Etapa, Matriz, Parceiro, ParceiroAno, Revista, RevistaInfografico
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
                ["Municípios - Anchieta - Somativa 2026", 2, "LP, MT", "1EF, 4EF", "1EF, 4EF"],
                ["Santa Catarina - SEAESC 2026", 3, "LP, MT", "2EF", "2EF"],
            ],
        })
        cab = ["Grupo", "Parceiro", "Etapa"]
        self.cortes = xlsx(pasta, "c.xlsx", {
            "2EF - LP": [cab + ["LP"], [1, "GO", "2EF", "350, 400, 500"], [2, "SC", "2EF", "500, 600, 700"]],
            "2EF - MT": [cab + ["MT"], [1, "GO", "2EF", "400, 500, 625"]],  # SC sem MT: arbitrário
            "3EM - LP": [cab + ["LP"], [1, "GO", "3EM", "225, 275, 325"]],
            "3EM - MT": [cab + ["MT"], [1, "GO", "3EM", "250, 300, 350"], [2, "AM", "3EM", "100, 200, 300"]],
        })

    def rodar(self, *extra):
        saida = StringIO()
        call_command("importar_cortes", self.somativas, self.cortes, "--ano", "2026", "--usuario", "carga",
                     *extra, stdout=saida)
        return saida.getvalue()

    def cortes_de(self, nome, **filtro):
        return Corte.objects.filter(parceiro_ano__parceiro__nome=nome, **filtro)

    def test_alfa_e_regular_viram_um_parceiro_com_uma_revista_por_componente(self):
        self.rodar()
        self.assertEqual(sorted(Parceiro.objects.values_list("nome", flat=True)), ["Anchieta", "GO", "SC"])
        go = Parceiro.objects.get(nome="GO")
        self.assertEqual(self.cortes_de("GO").count(), 6)  # 2EF, 4EF e 3EM × LP e MT
        self.assertEqual(Revista.objects.filter(projeto__parceiro_ano__parceiro=go).count(), 2)  # LP e MT
        tipos = RevistaInfografico.objects.filter(revista__projeto__parceiro_ano__parceiro=go, arquivado_em=None)
        self.assertEqual(sorted(set(tipos.values_list("tipo", flat=True))), ["alfa", "outras"])

    def test_etapa_nao_canonica_e_criada_com_a_escala_certa(self):
        saida = self.rodar()
        self.assertEqual(
            list(Etapa.objects.order_by("ordem").values_list("codigo", "escala_max")),
            [("1EF", 1000), ("2EF", 1000), ("4EF", 500), ("5EF", 500), ("9EF", 500), ("3EM", 500)],
        )
        self.assertIn("etapas criadas: 1EF, 4EF", saida)

    def test_corte_que_falta_vira_arbitrario_e_sai_no_relatorio(self):
        saida = self.rodar()
        self.assertEqual(list(self.cortes_de("SC", componente__codigo="MT").get().valores), [100, 200, 300])
        self.assertEqual(list(self.cortes_de("SC", componente__codigo="LP").get().valores), [500, 600, 700])
        self.assertIn("SC: 2 corte(s); arbitrários 2EF-MT", saida)
        self.assertIn("GO: 6 corte(s); arbitrários 4EF-LP, 4EF-MT", saida)
        self.assertIn("3 parceiro(s), 12 corte(s) gravado(s), 7 arbitrário(s).", saida)

    def test_parceiro_so_com_nao_canonica_ganha_projeto_e_revistas(self):
        self.rodar()
        self.assertEqual(self.cortes_de("Anchieta").count(), 4)  # 1EF e 4EF × LP e MT
        revistas = Revista.objects.filter(projeto__parceiro_ano__parceiro__nome="Anchieta")
        self.assertEqual(revistas.count(), 2)
        tipos = RevistaInfografico.objects.filter(revista__in=revistas, arquivado_em=None)
        self.assertEqual(set(tipos.values_list("tipo", flat=True)), {"outras"})  # 1EF não é Alfa (D-230)

    def test_matriz_e_atribuida_a_todos(self):
        self.rodar()
        self.assertFalse(ParceiroAno.objects.filter(matriz__isnull=False).exists())  # sem --matriz, fica nula
        outra = Matriz.objects.create(ano=Etapa.objects.first().ano, nome="Própria")
        ParceiroAno.objects.filter(parceiro__nome="GO").update(matriz=outra)
        self.rodar("--matriz", "Comunitária")  # todos já têm corte: pulados, mas a matriz entra
        comunitaria = Matriz.objects.get(nome="Comunitária")
        self.assertEqual(
            dict(ParceiroAno.objects.values_list("parceiro__nome", "matriz__nome")),
            {"Anchieta": comunitaria.nome, "GO": "Própria", "SC": comunitaria.nome},  # quem já tem não troca
        )

    def test_simular_nao_grava_e_segunda_rodada_pula_quem_ja_tem_corte(self):
        self.assertIn("Simulação", self.rodar("--simular"))
        self.assertEqual(Parceiro.objects.count(), 0)
        self.rodar()
        Corte.objects.filter(parceiro_ano__parceiro__nome="GO", etapa__codigo="2EF").update(valores=[1, 2, 3])
        self.assertIn("GO: pulado (já tem cortes)", self.rodar())
        corte = Corte.objects.get(parceiro_ano__parceiro__nome="GO", etapa__codigo="2EF", componente__codigo="LP")
        self.assertEqual(list(corte.valores), [1, 2, 3])
