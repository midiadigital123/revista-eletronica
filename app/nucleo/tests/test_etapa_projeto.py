"""Etapa do projeto (D-227): foto canônica e criação em branco ou por clone."""

import unittest

from django.test import TestCase

from nucleo.models import Descritor, Etapa, MatrizEtapaCC, Projeto, Revista, Tarefa
from nucleo.servicos.cascata import gravar_cortes
from nucleo.servicos.etapa_projeto import CriacaoRecusada, criar, foto, hash_foto
from nucleo.servicos.resolver import pendencias
from nucleo.tests.test_resolver import Mundo


class Base(TestCase):
    @classmethod
    def setUpTestData(cls):
        Mundo.montar(cls)
        cls.e4 = Etapa.objects.create(ano=cls.ano, codigo="4EF", escala_max=500, ordem=4)
        cls.projeto = Projeto.objects.get(parceiro_ano__parceiro__nome="GO", arquivado_em__isnull=True)
        cls.mec9 = MatrizEtapaCC.objects.get(matriz=cls.matriz, etapa=cls.e9, componente=cls.lp)
        gravar_cortes(
            cls.projeto.parceiro_ano,
            [
                (cls.e5, cls.lp, [100, 200, 250, 300]),
                (cls.e9, cls.lp, [100, 200, 250, 300]),
                (cls.e5, cls.mt, [100, 200, 250, 300]),
                (cls.e4, cls.lp, [100, 200, 250, 300]),
            ],
            cls.usuario,
        )


class FotoTest(Base):
    def test_foto_e_por_codigo_e_nao_por_id(self):
        antes = foto(self.mec9)
        d01 = Descritor.objects.get(matriz_etapa_cc=self.mec9, codigo="D01")
        tarefas = list(d01.tarefa_set.order_by("pk").values("inicio", "fim", "texto", "arquivo", "texto_alternativo", "ordem"))
        campos = {c: getattr(d01, c) for c in ("descricao", "prerequisitos", "praticas", "conhecimento",
                                                "habilidades_relacionadas", "habilidade_correspondente", "ordem")}
        d01.delete()
        novo = Descritor.objects.create(matriz_etapa_cc=self.mec9, codigo="D01", **campos)
        for t in tarefas:
            Tarefa.objects.create(descritor=novo, **t)
        self.assertNotEqual(novo.pk, d01.pk)
        self.assertEqual(foto(self.mec9), antes)
        self.assertEqual(hash_foto(foto(self.mec9)), hash_foto(antes))
        self.assertEqual(set(antes["descritores"]["D01"]["tarefas"]), {"100-150#1", "225-275#1"})
        self.assertEqual(antes["passo"], 25)

    def test_foto_normaliza_espacos(self):
        antes = foto(self.mec9)
        Descritor.objects.filter(matriz_etapa_cc=self.mec9, codigo="D01").update(
            descricao="  Descritor 1   LP\n", prerequisitos=["Pré  1;", "Pré 2.\n"]
        )
        Tarefa.objects.filter(descritor__matriz_etapa_cc=self.mec9, inicio=100).update(texto="Lê,  interpreta.\n")
        d = foto(self.mec9)["descritores"]["D01"]
        self.assertEqual(d["descricao"], antes["descritores"]["D01"]["descricao"])
        self.assertEqual(d["prerequisitos"], ["Pré 1;", "Pré 2."])
        self.assertEqual(d["tarefas"]["100-150#1"]["texto"], "Lê, interpreta.")

    def test_tarefas_da_mesma_faixa_ganham_n_pela_ordem(self):
        d02 = Descritor.objects.get(matriz_etapa_cc=self.mec9, codigo="D02")
        Tarefa.objects.create(descritor=d02, inicio=300, fim=350, texto="Outra.", ordem=2)
        t = foto(self.mec9)["descritores"]["D02"]["tarefas"]
        self.assertEqual([(k, v["texto"]) for k, v in t.items()], [("300-350#1", "Infere."), ("300-350#2", "Outra.")])


class CriarTest(Base):
    def test_criar_em_branco(self):
        mec = criar(self.projeto, self.e4, self.lp, self.usuario)
        self.assertEqual((mec.projeto, mec.matriz, mec.base, mec.base_foto), (self.projeto, None, None, None))
        self.assertEqual((mec.etapa, mec.componente, mec.ano_id), (self.e4, self.lp, self.projeto.ano_id))
        self.assertEqual(Descritor.objects.filter(matriz_etapa_cc=mec).count(), 0)

    def test_criar_clone_copia_e_guarda_foto(self):
        mec = criar(self.projeto, self.e4, self.lp, self.usuario, base=self.mec9)
        self.assertEqual(mec.base, self.mec9)
        self.assertEqual(mec.base_foto, foto(self.mec9))
        self.assertEqual(foto(mec), foto(self.mec9))
        self.assertEqual(Descritor.objects.filter(matriz_etapa_cc=mec).count(), 2)
        self.assertEqual(Tarefa.objects.filter(descritor__matriz_etapa_cc=mec).count(), 3)
        h = mec.history.get()
        self.assertEqual((h.history_type, h.history_user, h.history_change_reason), ("+", self.usuario, f"clone de {self.mec9}"))
        self.assertEqual(Descritor.objects.get(matriz_etapa_cc=mec, codigo="D01").history.get().history_type, "+")
        # A base de matriz não muda.
        self.assertEqual(Descritor.objects.filter(matriz_etapa_cc=self.mec9).count(), 2)

    def test_recusa_se_matriz_ja_tem_a_etapa(self):
        with self.assertRaisesMessage(CriacaoRecusada, "a matriz do parceiro já tem 5EF LP"):
            criar(self.projeto, self.e5, self.lp, self.usuario)

    def test_recusa_base_de_projeto_e_componente_diferente(self):
        propria = criar(self.projeto, self.e4, self.lp, self.usuario, base=self.mec9)
        outra = Etapa.objects.create(ano=self.ano, codigo="3EM", escala_max=500, ordem=5)
        with self.assertRaisesMessage(CriacaoRecusada, "a base precisa ser etapa de matriz"):
            criar(self.projeto, outra, self.lp, self.usuario, base=propria)
        mec_mt = MatrizEtapaCC.objects.get(matriz=self.matriz, etapa=self.e5, componente=self.mt)
        with self.assertRaisesMessage(CriacaoRecusada, "a base precisa ser do mesmo componente"):
            criar(self.projeto, outra, self.lp, self.usuario, base=mec_mt)

    def test_recusa_se_o_projeto_ja_tem_a_etapa(self):
        criar(self.projeto, self.e4, self.lp, self.usuario)
        with self.assertRaisesMessage(CriacaoRecusada, "o projeto já tem 4EF LP"):
            criar(self.projeto, self.e4, self.lp, self.usuario)

    def test_recusa_projeto_arquivado(self):
        Projeto.objects.filter(pk=self.projeto.pk).update(arquivado_em="2026-01-01T00:00:00Z")
        self.projeto.refresh_from_db()
        with self.assertRaisesMessage(CriacaoRecusada, "projeto arquivado"):
            criar(self.projeto, self.e4, self.lp, self.usuario)

    @unittest.skip("depende da tarefa 4: resolver lê a MEC do projeto")
    def test_clone_fora_da_escala_vira_corte_invalido(self):
        e7 = Etapa.objects.create(ano=self.ano, codigo="7EF", escala_max=400, ordem=6)
        Tarefa.objects.filter(descritor__matriz_etapa_cc=self.mec9, inicio=300).update(inicio=450, fim=480)
        gravar_cortes(
            self.projeto.parceiro_ano,
            [
                (self.e5, self.lp, [100, 200, 250, 300]),
                (self.e9, self.lp, [100, 200, 250, 300]),
                (self.e5, self.mt, [100, 200, 250, 300]),
                (e7, self.lp, [100, 200, 250, 300]),
            ],
            self.usuario,
        )
        criar(self.projeto, e7, self.lp, self.usuario, base=self.mec9)
        revista = Revista.objects.get(projeto=self.projeto, componente=self.lp)
        self.assertIn("corte_invalido", [p.codigo for p in pendencias(revista)])
