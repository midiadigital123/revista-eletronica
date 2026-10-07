"""Checa a extração contra valores conferidos na revista.
Uso: python3 scripts/test_extrair_descritores.py  (outro PDF: REVISTA_PDF=<pdf> python3 ...)
"""
import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent))
import extrair_descritores  # noqa: E402
from extrair_descritores import extrair  # noqa: E402

PDF = os.environ.get(
    "REVISTA_PDF", str(Path.home() / "Documentos/SAEGO_2025_RE_Alfa_2EF_5EF Web.pdf")
)


@unittest.skipUnless(Path(PDF).exists(), f"PDF não encontrado: {PDF}")
class TestExtrair(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        r = extrair(PDF)
        cls.lp, cls.mt = r["lingua-portuguesa"], r["matematica"]

    def test_contagens(self):
        contar = lambda ano: len(ano) - 2  # tira scaleRange e cortes
        self.assertEqual(
            {a: contar(d) for a, d in self.lp.items()} | {f"mt{a}": contar(d) for a, d in self.mt.items()},
            {"2ef": 8, "5ef": 15, "mt2ef": 33, "mt5ef": 28},
        )

    def test_lp_2ef_d01(self):
        self.assertEqual(self.lp["2ef"]["cortes"], {"padrao-1": 350, "padrao-2": 400, "padrao-3": 500})
        self.assertEqual(self.lp["2ef"]["scaleRange"], {"min": 0, "max": 1000})
        d = self.lp["2ef"]["D01"]
        self.assertEqual(d["description"], "Relacionar elementos sonoros das palavras com sua representação escrita.")
        self.assertEqual(len(d["prerequisites"]), 13)
        self.assertEqual(d["prerequisites"][6], "Reconhecer letras do alfabeto.")  # fim da coluna esquerda
        niveis = [n["level"] for p in ("padrao-4", "padrao-3", "padrao-2", "padrao-1") for n in d["scale"][p]]
        self.assertEqual(niveis, [782, 732, 675, 616, 556, 503, 446, 390])
        self.assertTrue(d["scale"]["padrao-4"][0]["content"].startswith('Reconhecer o som da letra "C" inicial'))
        self.assertIn("/ʒ/ e /g/", d["scale"]["padrao-4"][5]["content"])  # glifo deslocado no PDF

    def test_lp_2ef_d02_tracos_e_bncc(self):
        d = self.lp["2ef"]["D02"]
        self.assertEqual([n["content"] for n in d["scale"]["padrao-4"][:2]], ["---", "---"])
        self.assertTrue(d["bncc"]["skills"][1].startswith("(EF12LP01)"))

    def test_mt_2ef_d06_rotulos_trocados(self):
        d = self.mt["2ef"]["D06"]
        self.assertEqual(d["bncc"]["skills"][0], "EF02MA01")
        self.assertTrue(d["description"].endswith("(ou valor relativo) em um número natural de até 3 ordens."))
        self.assertEqual(self.mt["2ef"]["cortes"], {"padrao-1": 400, "padrao-2": 500, "padrao-3": 625})


class TestStdout(unittest.TestCase):
    """--stdout (usado pela API): JSON no stdout, nenhum arquivo gravado. Não precisa do PDF."""

    def test_imprime_json_sem_gravar(self):
        dados = {"matematica": {"2ef": {"scaleRange": {"min": 0, "max": 1000}}}, "lingua-portuguesa": {}}
        with tempfile.TemporaryDirectory() as pasta, mock.patch.object(
            extrair_descritores, "extrair", return_value=dados
        ) as falso:
            saida = io.StringIO()
            with redirect_stdout(saida):
                extrair_descritores.main(["x.pdf", pasta, "--stdout"])
            falso.assert_called_once_with("x.pdf")
            self.assertEqual(json.loads(saida.getvalue()), dados)
            self.assertEqual(os.listdir(pasta), [])


if __name__ == "__main__":
    unittest.main()
