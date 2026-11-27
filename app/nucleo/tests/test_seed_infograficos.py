"""O seed dos infográficos (D-298; MT Alfa, D-311), gerado dos Word por `scripts/docx_infografico.py`, passa pela
mesma validação da ficha da revista: falha se alguém editar o JSON à mão e quebrar um campo."""

from django.test import TestCase

from nucleo.servicos import seed_infografico


class SeedInfograficosTest(TestCase):
    def test_seeds_de_2026_validos(self):
        seeds = seed_infografico.seeds(2026)
        self.assertEqual(set(seeds), {("LP", "alfa"), ("LP", "outras"), ("MT", "alfa")})
        for chave, seed in seeds.items():
            with self.subTest(seed=chave):
                self.assertEqual(seed_infografico.validar(seed), [])

    def test_seed_quebrado_tem_erros(self):
        seed = seed_infografico.seeds(2026)[("LP", "alfa")]
        quebrado = {**seed, "texto_descritor": "# título", "itens": seed["itens"][:3]}
        erros = seed_infografico.validar(quebrado)
        self.assertTrue(any("texto_descritor: recurso não permitido" in e for e in erros), erros)
        self.assertIn("os itens precisam ser as posições 1 a 4", erros)

    def test_seed_mt_alfa(self):
        seed = seed_infografico.seeds(2026)[("MT", "alfa")]
        self.assertEqual(len(seed["etapas"]), 12)
        self.assertEqual(seed["etapas"]["3EM"], {"marca": "R", "codigo": "", "texto": "", "junta_marca": False,
                                                 "junta_habilidade": False})  # fmt: skip
        self.assertTrue(all(i["habilidade"] and (seed["_pasta"] / i["imagem"]).is_file() for i in seed["itens"]))
        sem = {**seed, "itens": [{**seed["itens"][0], "habilidade": ""}, *seed["itens"][1:]]}
        self.assertIn("item 1: habilidade: vazia (obrigatória nas tarefas por nível, D-305)", seed_infografico.validar(sem))
