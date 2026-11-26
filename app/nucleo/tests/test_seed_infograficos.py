"""O seed dos infográficos de LP (D-298), gerado dos Word por `scripts/docx_infografico.py`, passa pela
mesma validação da ficha da revista: falha se alguém editar o JSON à mão e quebrar um campo."""

from django.test import TestCase

from nucleo.servicos import seed_infografico


class SeedInfograficosTest(TestCase):
    def test_seeds_de_2026_validos(self):
        seeds = seed_infografico.seeds(2026)
        self.assertEqual(set(seeds), {("LP", "alfa"), ("LP", "outras")})
        for chave, seed in seeds.items():
            with self.subTest(seed=chave):
                self.assertEqual(seed_infografico.validar(seed), [])

    def test_seed_quebrado_tem_erros(self):
        seed = seed_infografico.seeds(2026)[("LP", "alfa")]
        quebrado = {**seed, "texto_descritor": "# título", "itens": seed["itens"][:3]}
        erros = seed_infografico.validar(quebrado)
        self.assertTrue(any("texto_descritor: recurso não permitido" in e for e in erros), erros)
        self.assertIn("os itens precisam ser as posições 1 a 4", erros)
