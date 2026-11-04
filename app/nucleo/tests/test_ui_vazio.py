"""Estados vazios que ensinam (U10b): título, causa + o que fazer e o botão da ação só para quem pode.

Uma tela por teste. Quem grava (Pedagógica) vê o botão dentro do `.vazio`; o Impresso vê só o texto
e continua recebendo 403 na gravação correspondente.
"""

import re

from django.test import TestCase
from django.urls import reverse

from nucleo.models import Ano, Componente, Etapa, Matriz, MatrizEtapaCC, Parceiro, ParceiroAno, Projeto
from nucleo.tests.test_resolver import usuario

VAZIO = re.compile(r'<div class="vazio"[^>]*>.*?</div>', re.S)


class Perfis:
    @classmethod
    def setUpTestData(cls):
        cls.ped = usuario("ped", "Pedagógica")
        cls.imp = usuario("imp", "Impresso")

    def vazio(self, user, url, titulo="Nenhum", **get):
        """O único bloco `.vazio` da página com `titulo`."""
        self.client.force_login(user)
        r = self.client.get(url, get)
        self.assertEqual(r.status_code, 200)
        blocos = [b for b in VAZIO.findall(r.content.decode()) if titulo in b]
        self.assertEqual(len(blocos), 1, blocos)
        return blocos[0]

    def assertBotao(self, bloco, rotulo, href=None):
        self.assertRegex(bloco, rf'class="btn btn-outline"[^>]*>(?:<svg.*?</svg>)?\s*{re.escape(rotulo)}')
        if href:
            self.assertIn(f'href="{href}"', bloco)

    def assertSemBotao(self, bloco):
        self.assertNotIn("btn", bloco)

    def assert403(self, url, dados=None):
        self.client.force_login(self.imp)
        self.assertEqual(self.client.post(url, dados or {}).status_code, 403)


class AnoVazioTest(Perfis, TestCase):
    """Ano 2025 aberto e vazio (sem parceiro, projeto, revista, matriz ou template)."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.ano = Ano.objects.create(ano=2025)

    def test_projetos_mostra_novo_projeto_so_para_quem_cadastra_parceiro(self):
        url = reverse("ui_projeto_lista", args=[2025])
        bloco = self.vazio(self.ped, url)
        self.assertIn("Nenhum projeto em 2025", bloco)
        self.assertBotao(bloco, "Novo projeto", reverse("cortes", args=[2025]))
        bloco = self.vazio(self.imp, url)
        self.assertIn("Nenhum projeto em 2025", bloco)
        self.assertSemBotao(bloco)
        self.assert403(reverse("cortes_novo_parceiro", args=[2025]), {"nome": "X"})

    def test_cortes_sem_parceiro_ensina_a_adicionar_e_o_impresso_nao_ve_o_botao(self):
        url = reverse("cortes", args=[2025])
        bloco = self.vazio(self.ped, url)
        self.assertIn("Nenhum parceiro cadastrado", bloco)
        self.assertIn("adicionar parceiro, logo abaixo", bloco)
        self.assertContains(self.client.get(url), "data-abrir-linha")
        bloco = self.vazio(self.imp, url)
        self.assertNotIn("adicionar parceiro", bloco)
        self.assertNotContains(self.client.get(url), "data-abrir-linha")
        self.assert403(reverse("cortes_novo_parceiro", args=[2025]), {"nome": "X"})

    def test_painel_variaveis_e_impresso_mostram_abrir_cortes_so_para_quem_lanca(self):
        cortes = reverse("cortes", args=[2025])
        for url in (reverse("painel", args=[2025]), reverse("ui_variaveis", args=[2025]), reverse("ui_impresso", args=[2025])):
            with self.subTest(url):
                self.assertBotao(self.vazio(self.ped, url), "Abrir cortes", cortes)
                bloco = self.vazio(self.imp, url)
                self.assertIn("Nenhum", bloco)
                self.assertSemBotao(bloco)
        self.assert403(reverse("cortes_celula", args=[2025]), {"campo": "c-1-1-1", "valor": "1"})

    def test_matrizes_mostra_abrir_origem_so_para_quem_duplica(self):
        origem = Matriz.objects.create(ano=Ano.objects.create(ano=2026), nome="SAEGO")
        url = reverse("ui_matriz", args=[2025])
        self.assertBotao(self.vazio(self.ped, url), "Abrir SAEGO", reverse("ui_matriz_detalhe", args=[origem.pk]))
        bloco = self.vazio(self.imp, url)
        self.assertIn("Nenhuma matriz em 2025", bloco)
        self.assertSemBotao(bloco)
        self.assert403(reverse("ui_matriz_duplicar", args=[origem.pk]), {"nome": "X", "ano": self.ano.pk})

    def test_templates_mostra_novo_template_so_para_quem_cria(self):
        url = reverse("ui_templates", args=[2025])
        self.assertBotao(self.vazio(self.ped, url), "Novo template", reverse("admin:nucleo_template_add"))
        bloco = self.vazio(self.imp, url)
        self.assertIn("Nenhum template F1 neste ano", bloco)
        self.assertSemBotao(bloco)
        self.assertNotIn("use Novo template", bloco)
        self.assert403(reverse("admin:nucleo_template_add"), {"nome": "X"})


class SemAnoTest(Perfis, TestCase):
    """Nenhum ano aberto: Projetos, Matrizes e Templates mandam abrir um ano (só quem abre vê o botão)."""

    def test_sem_ano_mostra_abrir_anos_so_para_quem_abre(self):
        for rota in ("ui_projeto_inicio", "ui_matriz_inicio", "ui_templates_inicio"):
            with self.subTest(rota):
                bloco = self.vazio(self.ped, reverse(rota))
                self.assertIn("Nenhum ano aberto", bloco)
                self.assertBotao(bloco, "Abrir anos", reverse("ui_anos"))
                bloco = self.vazio(self.imp, reverse(rota))
                self.assertIn("Nenhum ano aberto", bloco)
                self.assertSemBotao(bloco)
        self.assert403(reverse("ui_anos"), {"ano": "2025"})


class DentroDoAnoTest(Perfis, TestCase):
    """Vazios dentro de uma página de detalhe: MEC sem descritor e projeto sem etapa."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        ano = Ano.objects.create(ano=2025)
        etapa = Etapa.objects.create(ano=ano, codigo="5EF", escala_max=500, ordem=1)
        cc = Componente.objects.create(ano=ano, codigo="LP", nome="Língua Portuguesa")
        cls.mec = MatrizEtapaCC.objects.create(matriz=Matriz.objects.create(ano=ano, nome="SAEGO"), etapa=etapa, componente=cc, ano=ano)
        sem_etapa = Ano.objects.create(ano=2024)
        pa = ParceiroAno.objects.create(parceiro=Parceiro.objects.create(nome="GO"), ano=sem_etapa)
        cls.projeto = Projeto.objects.create(parceiro_ano=pa, ano=sem_etapa, nome="SAEGO")

    def test_mec_sem_descritor_abre_novo_descritor_so_para_quem_edita_a_matriz(self):
        url = reverse("ui_matriz_mec", args=[self.mec.pk])
        bloco = self.vazio(self.ped, url, "Nenhum descritor<")
        self.assertIn('data-abrir="dlg-novo"', bloco)
        self.assertBotao(bloco, "Novo descritor")
        bloco = self.vazio(self.imp, url, "Nenhum descritor<")
        self.assertSemBotao(bloco)
        self.assertNotIn("Crie", bloco)
        self.assert403(reverse("ui_matriz_novo", args=[self.mec.pk]), {"codigo": "D01"})

    def test_mec_busca_sem_resultado_oferece_limpar_a_busca(self):
        url = reverse("ui_matriz_mec", args=[self.mec.pk])
        bloco = self.vazio(self.imp, url, "Nenhum descritor com “zzz”", q="zzz")
        self.assertBotao(bloco, "Limpar busca", url)

    def test_projeto_sem_etapa_leva_ao_ano_so_quem_cadastra_etapa(self):
        url = reverse("ui_projeto", args=[self.projeto.pk]) + "?aba=passos"
        self.assertBotao(self.vazio(self.ped, url, "Nenhuma etapa"), "Cadastrar etapas", reverse("ui_ano", args=[2024]))
        bloco = self.vazio(self.imp, url, "Nenhuma etapa")
        self.assertSemBotao(bloco)
        self.assert403(reverse("ui_ano", args=[2024]), {"tabela": "etapas"})
