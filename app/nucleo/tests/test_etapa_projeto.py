"""Etapa do projeto (D-280): foto canônica e criação em branco ou por clone."""

import threading
import unittest
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import connection, transaction
from django.test import SimpleTestCase, TestCase, TransactionTestCase
from django.urls import reverse

from nucleo.management.commands.criar_demo import PNG
from nucleo.models import (
    Ano, Componente, Descritor, Etapa, Matriz, MatrizEtapaCC, Parceiro, ParceiroAno, Projeto, Revista, Tarefa,
)  # fmt: skip
from nucleo.servicos.cascata import gravar_cortes
from nucleo.servicos.empacotar import _itens
from nucleo.servicos.etapa_projeto import (
    CriacaoRecusada, Item, RevisaoIncompleta, RevisaoMudou, RevisaoRecusada, classificar, concluir, criar, derivadas,
    foto, hash_foto, pendente, revisao, textos_locais,
)  # fmt: skip
from nucleo.servicos.matriz import CAMPOS_DESCRITOR, impacto
from nucleo.servicos.planilhas import passos
from nucleo.servicos.pendencias import pendencias
from nucleo.servicos.resolver import carregar, hash_validado, resolver
from nucleo.servicos.validacao import validada, validar
from nucleo.urls.painel import link as link_painel
from nucleo.tests.test_resolver import MediaTemporaria, Mundo, preencher_infograficos, recarregar, usuario


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
        cls.mec5 = MatrizEtapaCC.objects.get(matriz=cls.matriz, etapa=cls.e5, componente=cls.lp)
        cls.lp_go = cls.go["LP"]

    def _outra_base(self):
        """Base 5EF LP de uma matriz que o GO não usa: mexer nela só muda a revista pela derivada."""
        outra = Matriz.objects.create(ano=self.ano, nome="Outra")
        base = MatrizEtapaCC.objects.create(matriz=outra, etapa=self.e5, componente=self.lp, ano=self.ano, passo=25)
        d = Descritor.objects.create(matriz_etapa_cc=base, codigo="D05", descricao="Da outra", ordem=1)
        Tarefa.objects.create(descritor=d, inicio=100, fim=150, texto="Compara.", ordem=1)
        return base

    def _pronta(self):
        preencher_infograficos(self.lp_go)  # o F2 sai dos infográficos (D-237), não de um SVG
        Revista.objects.filter(pk=self.lp_go.pk).update(capa="capas/x.png", capa_sha256="c" * 64)
        return recarregar(self.lp_go)


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
    def test_recusa_sem_base(self):  # D-276: não existe etapa em branco
        with self.assertRaisesMessage(CriacaoRecusada, "a etapa do projeto precisa de uma base"):
            criar(self.projeto, self.e4, self.lp, self.usuario, base=None)
        self.assertFalse(MatrizEtapaCC.objects.filter(projeto=self.projeto).exists())

    def test_canonica_que_a_matriz_nao_tem_continua_recusada(self):  # D-276: corrige-se na matriz
        MatrizEtapaCC.objects.filter(matriz=self.matriz, etapa=self.e9, componente=self.mt).delete()
        mt5 = MatrizEtapaCC.objects.get(matriz=self.matriz, etapa=self.e5, componente=self.mt)
        with self.assertRaisesMessage(CriacaoRecusada, "9EF é etapa canônica: corrija na matriz"):
            criar(self.projeto, self.e9, self.mt, self.usuario, base=mt5)

    def test_copia_local_usa_a_etapa_da_matriz_como_base(self):  # D-288: qualquer etapa da matriz
        mec = criar(self.projeto, self.e5, self.lp, self.usuario)
        self.assertEqual((mec.projeto, mec.base, mec.matriz), (self.projeto, self.mec5, None))
        self.assertEqual(mec.base_foto, foto(self.mec5))
        self.assertEqual(foto(mec), foto(self.mec5))
        self.assertEqual(criar(self.projeto, self.e9, self.lp, self.usuario, base=self.mec9).base, self.mec9)

    def test_copia_local_recusa_outra_base(self):
        with self.assertRaisesMessage(CriacaoRecusada, "a base da cópia local é a etapa da matriz do parceiro"):
            criar(self.projeto, self.e5, self.lp, self.usuario, base=self.mec9)
        self.assertFalse(MatrizEtapaCC.objects.filter(projeto=self.projeto).exists())

    def test_recusa_base_nao_canonica(self):  # D-276: a base é uma das 4 canônicas
        outra = Matriz.objects.create(ano=self.ano, nome="Outra")
        base = MatrizEtapaCC.objects.create(matriz=outra, etapa=self.e4, componente=self.lp, ano=self.ano, passo=25)
        e6 = Etapa.objects.create(ano=self.ano, codigo="6EF", escala_max=500, ordem=5)
        with self.assertRaisesMessage(CriacaoRecusada, "a base precisa ser etapa canônica (2EF, 5EF, 9EF ou 3EM)"):
            criar(self.projeto, e6, self.lp, self.usuario, base=base)

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

    def test_recusa_base_de_projeto_e_componente_diferente(self):
        propria = criar(self.projeto, self.e4, self.lp, self.usuario, base=self.mec9)
        outra = Etapa.objects.create(ano=self.ano, codigo="6EF", escala_max=500, ordem=5)
        with self.assertRaisesMessage(CriacaoRecusada, "a base precisa ser etapa de matriz"):
            criar(self.projeto, outra, self.lp, self.usuario, base=propria)
        mec_mt = MatrizEtapaCC.objects.get(matriz=self.matriz, etapa=self.e5, componente=self.mt)
        with self.assertRaisesMessage(CriacaoRecusada, "a base precisa ser do mesmo componente"):
            criar(self.projeto, outra, self.lp, self.usuario, base=mec_mt)

    def test_recusa_se_o_projeto_ja_tem_a_etapa(self):
        criar(self.projeto, self.e4, self.lp, self.usuario, base=self.mec9)
        with self.assertRaisesMessage(CriacaoRecusada, "o projeto já tem 4EF LP"):
            criar(self.projeto, self.e4, self.lp, self.usuario, base=self.mec9)

    def test_recusa_projeto_arquivado(self):
        Projeto.objects.filter(pk=self.projeto.pk).update(arquivado_em="2026-01-01T00:00:00Z")
        self.projeto.refresh_from_db()
        with self.assertRaisesMessage(CriacaoRecusada, "projeto arquivado"):
            criar(self.projeto, self.e4, self.lp, self.usuario, base=self.mec9)

    @unittest.skip(
        "premissa a decidir: corte_invalido só olha os cortes (problema_dos_cortes espelha o JS, D-131); "
        "tarefa fora da escala_max não vira pendência hoje"
    )
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


class RevistaTest(Base):
    """A revista com a etapa do projeto (GO LP 4EF): resolver, pendências e impacto."""

    def test_revista_usa_a_etapa_do_projeto(self):
        self.assertNotIn("D01", resolver(recarregar(self.lp_go))["f1"]["dados"]["4ef"])  # ainda sem MEC
        criar(self.projeto, self.e4, self.lp, self.usuario, base=self.mec5)
        r = resolver(recarregar(self.lp_go))
        self.assertEqual(r["f1"]["etapas"], ["4ef", "5ef", "9ef"])
        self.assertEqual(r["f1"]["dados"]["4ef"]["D01"], r["f1"]["dados"]["5ef"]["D01"])
        self.assertEqual(r["f1"]["dados"]["4ef"]["D01"]["description"], "Descritor 1 LP")
        self.assertEqual([lc for lc in r["lacunas"] if lc["tipo"] == "base"], [])

    def test_corte_sem_matriz_some_com_a_etapa_do_projeto(self):
        codigos = lambda: [x.codigo for x in pendencias(recarregar(self.lp_go))]  # noqa: E731
        p = [x for x in pendencias(recarregar(self.lp_go)) if x.codigo == "etapa_sem_base"]
        self.assertEqual(p[0].mensagem, "Etapa não canônica sem base: 4EF. Aponte cada uma para uma etapa canônica.")
        self.assertNotIn("corte_sem_matriz", codigos())  # a não canônica não é falta da matriz (D-276)
        # o link leva à aba Matriz do projeto (onde se aponta), não ao editor da matriz
        self.assertEqual(link_painel("etapa_sem_base", self.lp_go), reverse("ui_projeto", args=[self.projeto.pk]) + "?aba=matriz")
        self.client.force_login(usuario("ped-link", "Pedagógica"))
        r = self.client.get(reverse("ui_revista_editar", args=[2026, self.lp_go.pk]))
        self.assertContains(r, "Etapa não canônica sem base: 4EF.")
        criar(self.projeto, self.e4, self.lp, self.usuario, base=self.mec5)
        self.assertNotIn("etapa_sem_base", codigos())

    def test_etapa_sem_base_separa_da_canonica(self):
        MatrizEtapaCC.objects.filter(pk=self.mec9.pk).delete()  # a matriz perde o 9EF LP (canônica)
        self.assertEqual(
            [(x.codigo, x.mensagem) for x in pendencias(recarregar(self.lp_go)) if "sem" in x.codigo],
            [
                ("corte_sem_matriz", "A matriz não tem a etapa: 9EF."),
                ("etapa_sem_base", "Etapa não canônica sem base: 4EF. Aponte cada uma para uma etapa canônica."),
            ],
        )

    def test_editar_a_base_abre_lacuna_e_tira_o_validado(self):
        base = self._outra_base()
        criar(self.projeto, self.e4, self.lp, self.usuario, base=base)
        lp = self._pronta()
        self.assertEqual(pendencias(lp), [])
        self.assertIsNone(validar(lp.pk, hash_validado(lp), self.usuario))
        lp = recarregar(lp)
        antes = resolver(lp)
        self.assertTrue(validada(lp, hash_validado(lp)))

        Descritor.objects.filter(matriz_etapa_cc=base, codigo="D05").update(descricao="Da outra, revista")
        depois = resolver(lp)
        self.assertEqual(depois["f1"], antes["f1"])  # a cópia do projeto não muda sozinha
        self.assertIn({"tipo": "base", "etapa": "4ef"}, depois["lacunas"])
        self.assertFalse(validada(lp, hash_validado(lp)))
        self.assertIn(
            ("base", "A etapa 4EF tem mudanças da base para revisar."),
            [(p.codigo, p.mensagem) for p in pendencias(lp)],
        )

    def test_sem_base_nao_ha_lacuna(self):
        mec = criar(self.projeto, self.e4, self.lp, self.usuario, base=self.mec5)
        MatrizEtapaCC.objects.filter(pk=mec.pk).update(base=None)
        Descritor.objects.filter(matriz_etapa_cc=self.mec5, codigo="D01").update(descricao="Mudou na matriz")
        lp = recarregar(self.lp_go)
        self.assertNotIn("base", [lc["tipo"] for lc in resolver(lp)["lacunas"]])
        self.assertNotIn("base", [p.codigo for p in pendencias(lp)])

    def test_pendente_e_a_mesma_condicao_da_lacuna(self):
        base = self._outra_base()
        mec = criar(self.projeto, self.e4, self.lp, self.usuario, base=base)
        lacuna = {"tipo": "base", "etapa": "4ef"}
        self.assertFalse(pendente(mec))
        self.assertFalse(pendente(base))  # etapa de matriz não tem revisão
        self.assertNotIn(lacuna, resolver(recarregar(self.lp_go))["lacunas"])
        with patch("nucleo.servicos.etapa_projeto.pendente", return_value=True):  # o resolver pergunta a ela
            self.assertIn(lacuna, resolver(recarregar(self.lp_go))["lacunas"])

        Descritor.objects.filter(matriz_etapa_cc=base, codigo="D05").update(descricao="Da outra, revista")
        mec = MatrizEtapaCC.objects.get(pk=mec.pk)
        self.assertTrue(pendente(mec))
        self.assertIn(lacuna, resolver(recarregar(self.lp_go))["lacunas"])
        MatrizEtapaCC.objects.filter(pk=mec.pk).update(base=None)
        self.assertFalse(pendente(MatrizEtapaCC.objects.get(pk=mec.pk)))  # cópia solta

    def test_copia_vale_sobre_a_matriz_sem_pendencia(self):  # D-288: sai a pendência de escolha
        criar(self.projeto, self.e4, self.lp, self.usuario, base=self.mec5)
        da_matriz = MatrizEtapaCC.objects.create(matriz=self.matriz, etapa=self.e4, componente=self.lp, ano=self.ano, passo=25)
        Descritor.objects.create(matriz_etapa_cc=da_matriz, codigo="D09", descricao="Da matriz", ordem=1)
        lp = recarregar(self.lp_go)
        r = resolver(lp)
        self.assertEqual([k for k in r["f1"]["dados"]["4ef"] if k.startswith("D")], ["D01", "D02"])
        self.assertEqual(r["lacunas"], resolver(recarregar(self.pe["LP"]))["lacunas"])  # nenhuma lacuna a mais
        self.assertEqual(pendencias(lp), pendencias(recarregar(self.pe["LP"])))

    def test_afetadas_inclui_a_revista_derivada(self):
        base = self._outra_base()
        self.assertEqual(impacto(base), [])
        mec = criar(self.projeto, self.e4, self.lp, self.usuario, base=base)
        self.assertEqual(list(derivadas(base)), [mec])
        self.assertEqual([r for r, _ in impacto(base)], [self.lp_go])  # só o LP: o MT não tem a etapa

    def test_afetadas_inclui_derivada_de_base_de_outro_ano(self):
        # Componente e etapa são por ano: a derivada (2026) não tem o componente_id da base (2025).
        ano = Ano.objects.create(ano=2025)
        lp = Componente.objects.create(ano=ano, codigo="LP", nome="Língua Portuguesa")
        e5 = Etapa.objects.create(ano=ano, codigo="5EF", escala_max=500, ordem=2)
        base = MatrizEtapaCC.objects.create(
            matriz=Matriz.objects.create(ano=ano, nome="Comunitária 2025"), etapa=e5, componente=lp, ano=ano, passo=25
        )
        Descritor.objects.create(matriz_etapa_cc=base, codigo="D01", descricao="De 2025", ordem=1)
        criar(self.projeto, self.e4, self.lp, self.usuario, base=base)
        afetadas = [r for r, _ in impacto(base)]
        self.assertIn(self.lp_go, afetadas)
        self.assertNotIn(self.go["MT"], afetadas)


class EdicaoLocalTest(Base):
    """Critérios de aceite de docs/edicao-local-por-projeto.md (§10, D-288): GO edita a cópia do 5EF LP."""

    def setUp(self):
        self.copia = criar(self.projeto, self.e5, self.lp, self.usuario)
        self.pe_lp = self.pe["LP"]

    def _d01(self, revista):
        return resolver(recarregar(revista))["f1"]["dados"]["5ef"]["D01"]["description"]

    def test_edicao_local_so_muda_o_proprio_projeto(self):
        antes = foto(self.mec5)
        Descritor.objects.filter(matriz_etapa_cc=self.copia, codigo="D01").update(descricao="Só do GO")
        Descritor.objects.filter(matriz_etapa_cc=self.copia, codigo="D02").delete()
        self.assertEqual(self._d01(self.lp_go), "Só do GO")
        self.assertNotIn("D02", resolver(recarregar(self.lp_go))["f1"]["dados"]["5ef"])
        self.assertEqual(self._d01(self.pe_lp), "Descritor 1 LP")  # 1: o outro projeto vê o original
        self.assertEqual(foto(self.mec5), antes)  # 2: nenhuma linha da Comunitária muda
        self.assertEqual(Descritor.objects.filter(matriz_etapa_cc=self.mec5).count(), 2)

    def test_mudar_a_matriz_abre_revisao_so_em_quem_tem_copia(self):
        sem_copia = resolver(recarregar(self.pe_lp))["lacunas"]  # 3: PE segue pela matriz, sem pendência nova
        Descritor.objects.filter(matriz_etapa_cc=self.mec5, codigo="D01").update(descricao="Mudou na Comunitária")
        self.assertEqual(self._d01(self.pe_lp), "Mudou na Comunitária")
        self.assertEqual(resolver(recarregar(self.pe_lp))["lacunas"], sem_copia)
        self.assertEqual(self._d01(self.lp_go), "Descritor 1 LP")  # 4: o GO fica com a cópia até revisar
        go = recarregar(self.lp_go)
        self.assertIn({"tipo": "base", "etapa": "5ef"}, resolver(go)["lacunas"])
        self.assertIn("base", [p.codigo for p in pendencias(go)])

    def test_ordem_do_editor_vai_para_a_revista_e_muda_o_hash(self):  # D-291
        lp = recarregar(self.lp_go)
        self.assertEqual(resolver(lp)["f1"]["dados"]["5ef"]["ordem"], ["D01", "D02"])
        antes = hash_validado(lp)
        Descritor.objects.filter(matriz_etapa_cc=self.copia, codigo="D01").update(ordem=3)
        lp = recarregar(self.lp_go)
        self.assertEqual(resolver(lp)["f1"]["dados"]["5ef"]["ordem"], ["D02", "D01"])
        self.assertNotEqual(hash_validado(lp), antes)

    def test_bloqueio_da_copia_nao_trava_a_matriz(self):  # 6
        from nucleo.servicos import bloqueio

        outro = get_user_model().objects.create(username="outro")
        self.assertTrue(bloqueio.adquirir(self.mec5, self.usuario, "aba-da-matriz"))
        self.assertTrue(bloqueio.adquirir(self.copia, outro, "aba-da-copia"))


class CascataTest(Base):
    """D-281: o projeto que a cascata recria herda as etapas do projeto arquivado."""

    def _arquiva_e_volta(self, no_meio=lambda: None):
        pa, cortes = self.projeto.parceiro_ano, [100, 200, 250, 300]
        gravar_cortes(pa, [], self.usuario)  # sem corte nenhum, o projeto é arquivado
        no_meio()
        gravar_cortes(pa, [(self.e4, self.lp, cortes), (self.e5, self.lp, cortes)], self.usuario)
        novo = Projeto.objects.get(parceiro_ano=pa, arquivado_em__isnull=True)
        return novo, Revista.objects.get(projeto=novo, componente=self.lp)

    def test_projeto_recriado_herda_a_etapa_do_projeto(self):
        mec = criar(self.projeto, self.e4, self.lp, self.usuario, base=self.mec5)
        foto_antes = mec.base_foto
        novo, lp = self._arquiva_e_volta()
        self.assertNotEqual(novo.pk, self.projeto.pk)
        mec.refresh_from_db()  # a mesma linha: transfere, não copia
        self.assertEqual((mec.projeto_id, mec.base_id, mec.base_foto), (novo.pk, self.mec5.pk, foto_antes))
        self.assertIn("D01", resolver(lp)["f1"]["dados"]["4ef"])
        self.assertNotIn("etapa_sem_base", [p.codigo for p in pendencias(lp)])
        h = mec.history.first()
        self.assertEqual((h.history_user, h.history_change_reason), (self.usuario, "projeto recriado pela cascata"))

    def test_base_editada_com_o_projeto_arquivado_abre_a_revisao_ao_herdar(self):
        criar(self.projeto, self.e4, self.lp, self.usuario, base=self.mec5)
        _, lp = self._arquiva_e_volta(
            lambda: Descritor.objects.filter(matriz_etapa_cc=self.mec5, codigo="D01").update(descricao="Mudou")
        )
        self.assertIn({"tipo": "base", "etapa": "4ef"}, resolver(lp)["lacunas"])


class RestoDoSistemaTest(MediaTemporaria, Base):
    """Fluxos antigos com a etapa do projeto (GO LP 4EF) e um parceiro sem matriz com corte 4EF LP:
    `filter(matriz_id=None)` casaria a etapa do projeto do GO."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.mec = criar(cls.projeto, cls.e4, cls.lp, cls.usuario, base=cls.mec9)
        pa = ParceiroAno.objects.create(parceiro=Parceiro.objects.create(nome="SEM"), ano=cls.ano)
        gravar_cortes(pa, [(cls.e4, cls.lp, [100, 200, 250, 300])], cls.usuario)
        cls.sem = Revista.objects.get(projeto__parceiro_ano=pa)
        cls.lp_go = cls.go["LP"]

    def test_admin_lista_descritores_da_etapa_do_projeto(self):
        self.client.force_login(get_user_model().objects.create_superuser("su", password="x"))
        self.assertContains(self.client.get(reverse("admin:nucleo_descritor_changelist")), "Projeto GO · 4EF LP")

    def test_admin_abre_a_etapa_do_projeto(self):  # o admin diz de quem é a etapa sem matriz (D-277)
        self.client.force_login(get_user_model().objects.create_superuser("su", password="x"))
        self.assertContains(self.client.get(reverse("admin:nucleo_matrizetapacc_changelist")), "Projeto GO")
        self.assertContains(self.client.get(reverse("admin:nucleo_matrizetapacc_change", args=[self.mec.pk])), "Projeto GO")

    def test_item_da_etapa_do_projeto_no_zip_e_no_preview(self):
        caminho = default_storage.save("itens/do-projeto.png", ContentFile(PNG))
        Tarefa.objects.filter(descritor__matriz_etapa_cc=self.mec, inicio=100).update(arquivo=caminho)
        rev, erros = carregar(self.lp_go.pk), []
        self.assertEqual(_itens(rev, resolver(rev), erros), {"do-projeto.png": caminho})
        self.assertEqual(erros, [])
        self.client.force_login(usuario("ped", "Pedagógica"))
        self.assertEqual(self.client.get(reverse("preview_item", args=[rev.pk, "do-projeto.png"])).status_code, 200)
        self.assertEqual(self.client.get(reverse("preview_item", args=[self.sem.pk, "do-projeto.png"])).status_code, 404)

    def test_passo_da_planilha_vem_da_etapa_do_projeto(self):
        MatrizEtapaCC.objects.filter(pk=self.mec.pk).update(passo=10)
        self.assertEqual(passos(self.lp_go)["4ef"], 10)
        self.assertEqual(passos(self.sem), {})

    def test_projeto_sem_matriz_nao_mostra_passo_de_etapa_de_outro_projeto(self):
        self.client.force_login(usuario("ped", "Pedagógica"))
        resp = self.client.get(reverse("ui_projeto", args=[self.sem.projeto_id]) + "?aba=passos")
        self.assertEqual(list(resp.context["passos_matriz"]), [])
        (bloco,) = [b for b in resp.context["etapas_passo"] if b["etapa"] == self.e4]
        (celula,) = [c for c in bloco["celulas"] if c["componente"] == self.lp]
        self.assertEqual(celula["da_matriz"], "fora da matriz")

    def test_aba_passos_herda_o_passo_da_etapa_do_projeto(self):  # o mesmo passo que a revista usa
        MatrizEtapaCC.objects.filter(pk=self.mec.pk).update(passo=10)
        self.client.force_login(usuario("ped", "Pedagógica"))
        resp = self.client.get(reverse("ui_projeto", args=[self.projeto.pk]) + "?aba=passos")
        (bloco,) = [b for b in resp.context["etapas_passo"] if b["etapa"] == self.e4]
        (celula,) = [c for c in bloco["celulas"] if c["componente"] == self.lp]
        self.assertEqual((celula["da_matriz"], celula["matriz"]), (10, 10))

    def test_impacto_da_etapa_do_projeto_e_so_a_revista_do_projeto(self):
        self.assertEqual([r for r, _ in impacto(self.mec)], [self.lp_go])


class ConcluirTest(MediaTemporaria, Base):
    """Concluir a revisão em 3 vias e escolher a etapa preferida (D-284): a base mudou, o projeto decide."""

    def _derivada(self, base=None):
        base = base or self._outra_base()
        return base, criar(self.projeto, self.e4, self.lp, self.usuario, base=base)

    def _d05(self, mec):
        return Descritor.objects.get(matriz_etapa_cc=mec, codigo="D05")

    def _t05(self, mec):
        return Tarefa.objects.get(descritor__matriz_etapa_cc=mec, descritor__codigo="D05", inicio=100)

    def _validada(self):
        lp = recarregar(self.lp_go)
        return validada(lp, hash_validado(lp))

    def test_concluir_aplica_o_que_entra_e_avanca_a_foto(self):
        base, mec = self._derivada()
        lp = self._pronta()
        self.assertIsNone(validar(lp.pk, hash_validado(lp), self.usuario))
        self.assertTrue(self._validada())
        # a foto junta espaços e quebras; o projeto recebe o texto bruto da base
        Descritor.objects.filter(matriz_etapa_cc=base, codigo="D05").update(descricao="  Da base,   nova\n")
        Tarefa.objects.filter(descritor__matriz_etapa_cc=base).update(texto="Compara melhor.")
        MatrizEtapaCC.objects.filter(pk=base.pk).update(passo=30)
        self.assertIn({"tipo": "base", "etapa": "4ef"}, resolver(recarregar(self.lp_go))["lacunas"])

        mec.refresh_from_db()  # `revisao` usa a base em cache do `mec`: leia o mec de novo
        itens, visto = revisao(mec)
        self.assertEqual(
            [(i.chave, i.campo, i.situacao) for i in itens],
            [("passo", "passo", "entra"), ("D05", "descricao", "entra"), ("D05/100-150#1", "texto", "entra")],
        )
        self.assertEqual(concluir(mec, {}, visto, self.usuario), 3)

        mec.refresh_from_db()
        base.refresh_from_db()
        self.assertEqual(mec.passo, 30)
        self.assertEqual(self._d05(mec).descricao, "  Da base,   nova\n")
        self.assertEqual(self._t05(mec).texto, "Compara melhor.")
        self.assertEqual(mec.base_foto, foto(base))
        self.assertEqual(revisao(mec)[0], [])
        self.assertNotIn("base", [lc["tipo"] for lc in resolver(recarregar(self.lp_go))["lacunas"]])
        self.assertFalse(self._validada())  # o conteúdo mudou: a revista tem de ser revalidada
        h = mec.history.first()
        self.assertEqual(
            (h.history_user, h.history_change_reason), (self.usuario, "revisão da base: aplicou 3, manteve 0")
        )
        self.assertEqual(self._d05(mec).history.first().history_change_reason, "revisão da base")
        self.assertEqual(self._d05(mec).history.first().history_user, self.usuario)

    def test_manter_o_meu_nao_grava_e_nao_volta_a_perguntar(self):
        base, mec = self._derivada()
        Descritor.objects.filter(matriz_etapa_cc=mec, codigo="D05").update(descricao="Do projeto")
        lp = self._pronta()
        self.assertIsNone(validar(lp.pk, hash_validado(lp), self.usuario))
        Descritor.objects.filter(matriz_etapa_cc=base, codigo="D05").update(descricao="Da base, nova")  # conflito
        Tarefa.objects.filter(descritor__matriz_etapa_cc=base).update(texto="Compara melhor.")  # entra
        self.assertFalse(self._validada())  # a lacuna `base` tira o validado

        itens, visto = revisao(mec)
        self.assertEqual([i.situacao for i in itens], ["conflito", "entra"])
        escolhas = {(i.chave, i.campo): "local" for i in itens}
        self.assertEqual(concluir(mec, escolhas, visto, self.usuario), 0)

        mec.refresh_from_db()
        self.assertEqual(self._d05(mec).descricao, "Do projeto")
        self.assertEqual(self._t05(mec).texto, "Compara.")
        self.assertEqual(mec.base_foto, foto(base))
        self.assertEqual(revisao(mec)[0], [])
        self.assertTrue(self._validada())  # o conteúdo voltou a ser o validado (D-094)
        self.assertEqual(mec.history.first().history_change_reason, "revisão da base: aplicou 0, manteve 2")

    def test_texto_editado_a_mao(self):
        base, mec = self._derivada()
        Descritor.objects.filter(matriz_etapa_cc=base, codigo="D05").update(descricao="Da base, nova")
        Descritor.objects.filter(matriz_etapa_cc=mec, codigo="D05").update(descricao="Do projeto")
        itens, visto = revisao(mec)
        self.assertEqual([(i.campo, i.situacao) for i in itens], [("descricao", "conflito")])
        self.assertEqual(concluir(mec, {("D05", "descricao"): ("texto", "  Meu\ntexto ")}, visto, self.usuario), 1)
        self.assertEqual(self._d05(mec).descricao, "  Meu\ntexto ")  # como digitado
        mec.refresh_from_db()
        self.assertEqual(revisao(mec)[0], [])

    def test_textos_locais_devolve_o_texto_com_as_quebras(self):  # a foto junta as quebras (`_norm`)
        base, mec = self._derivada()
        Descritor.objects.filter(matriz_etapa_cc=base, codigo="D05").update(descricao="Da base, nova", ordem=3)
        Descritor.objects.filter(matriz_etapa_cc=mec, codigo="D05").update(descricao="Do projeto,\n\nem duas linhas ")
        Tarefa.objects.filter(descritor__matriz_etapa_cc=base).update(texto="Compara melhor.")
        MatrizEtapaCC.objects.filter(pk=base.pk).update(passo=30)
        mec.refresh_from_db()
        itens, _ = revisao(mec)
        self.assertEqual([i.local for i in itens if i.campo == "descricao"], ["Do projeto, em duas linhas"])
        self.assertEqual(
            textos_locais(mec, itens),  # sem o passo e sem a ordem: só campo de texto
            {("D05", "descricao"): "Do projeto,\n\nem duas linhas ", ("D05/100-150#1", "texto"): "Compara."},
        )

    def test_texto_so_vale_em_campo_de_texto(self):
        base, mec = self._derivada()
        Descritor.objects.filter(matriz_etapa_cc=base, codigo="D05").update(ordem=3)
        antes = MatrizEtapaCC.objects.get(pk=mec.pk).base_foto
        _, visto = revisao(mec)
        with self.assertRaisesMessage(RevisaoRecusada, "ordem não é campo de texto"):
            concluir(mec, {("D05", "ordem"): ("texto", "3")}, visto, self.usuario)
        self.assertEqual(self._d05(mec).ordem, 1)
        self.assertEqual(MatrizEtapaCC.objects.get(pk=mec.pk).base_foto, antes)

    def test_escolha_malformada_e_recusada_sem_gravar(self):
        base, mec = self._derivada()
        Descritor.objects.filter(matriz_etapa_cc=base, codigo="D05").update(descricao="Da base, nova")
        Tarefa.objects.filter(descritor__matriz_etapa_cc=base, inicio=100).update(texto_alternativo="Alt da base")
        _, visto = revisao(mec)
        for chave, escolha in [
            (("D05", "descricao"), ("texto",)),
            (("D05", "descricao"), ("texto", None)),
            (("D05", "descricao"), "outra"),
            (("D05/100-150#1", "texto_alternativo"), ("texto", "x" * 1001)),
        ]:
            with self.subTest(escolha=escolha), self.assertRaises(RevisaoRecusada):
                concluir(mec, {chave: escolha}, visto, self.usuario)
        self.assertEqual(self._d05(mec).descricao, "Da outra")

    def test_descritor_apagado_leva_o_usuario_no_historico_das_tarefas(self):
        base, mec = self._derivada()
        tarefa = self._t05(mec)
        self._d05(base).delete()
        _, visto = revisao(mec)
        self.assertEqual(concluir(mec, {}, visto, self.usuario), 1)
        apagada = Tarefa.history.filter(id=tarefa.pk, history_type="-").get()
        self.assertEqual(apagada.history_user, self.usuario)

    def test_conflito_sem_escolha_e_recusado(self):
        base, mec = self._derivada()
        Descritor.objects.filter(matriz_etapa_cc=base, codigo="D05").update(descricao="Da base, nova")  # conflito
        Descritor.objects.filter(matriz_etapa_cc=mec, codigo="D05").update(descricao="Do projeto")
        Tarefa.objects.filter(descritor__matriz_etapa_cc=base).update(texto="Compara melhor.")  # entra
        antes = MatrizEtapaCC.objects.get(pk=mec.pk).base_foto
        _, visto = revisao(mec)
        with self.assertRaises(RevisaoIncompleta):
            concluir(mec, {}, visto, self.usuario)
        self.assertEqual(self._d05(mec).descricao, "Do projeto")
        self.assertEqual(self._t05(mec).texto, "Compara.")  # nem o que entra foi gravado
        self.assertEqual(MatrizEtapaCC.objects.get(pk=mec.pk).base_foto, antes)

    def test_visto_velho_e_recusado_base_mudou(self):
        base, mec = self._derivada()
        Descritor.objects.filter(matriz_etapa_cc=base, codigo="D05").update(descricao="Da base, nova")
        _, visto = revisao(mec)
        Descritor.objects.filter(matriz_etapa_cc=base, codigo="D05").update(descricao="Da base, outra vez")
        with self.assertRaises(RevisaoMudou):
            concluir(mec, {}, visto, self.usuario)
        with self.assertRaises(RevisaoMudou):
            concluir(mec, {}, "", self.usuario)
        self.assertEqual(self._d05(mec).descricao, "Da outra")

    def test_visto_velho_e_recusado_local_mudou(self):
        base, mec = self._derivada()
        Descritor.objects.filter(matriz_etapa_cc=base, codigo="D05").update(descricao="Da base, nova")
        _, visto = revisao(mec)
        Descritor.objects.filter(matriz_etapa_cc=mec, codigo="D05").update(descricao="Editado no meio")
        with self.assertRaises(RevisaoMudou):  # "usar o da base" apagaria um texto que ninguém viu
            concluir(mec, {}, visto, self.usuario)
        self.assertEqual(self._d05(mec).descricao, "Editado no meio")

    def test_escolha_de_chave_que_nao_esta_nos_itens_e_ignorada(self):
        base, mec = self._derivada()
        Descritor.objects.filter(matriz_etapa_cc=base, codigo="D05").update(descricao="Da base, nova")
        _, visto = revisao(mec)
        escolhas = {("D99", "descricao"): "local", ("D05", "ordem"): ("texto", "x")}
        self.assertEqual(concluir(mec, escolhas, visto, self.usuario), 1)
        self.assertEqual(self._d05(mec).descricao, "Da base, nova")

    def test_descritor_com_codigo_passo_aplica_o_campo_e_nao_o_passo(self):  # o código é livre (D-290)
        base = self._outra_base()
        Descritor.objects.create(matriz_etapa_cc=base, codigo="passo", descricao="Antes", ordem=2)
        _, mec = self._derivada(base)
        MatrizEtapaCC.objects.filter(pk=mec.pk).update(passo=40)  # só o projeto mudou o passo: não é item
        Descritor.objects.filter(matriz_etapa_cc=base, codigo="passo").update(descricao="Da base, nova")
        mec.refresh_from_db()
        itens, visto = revisao(mec)
        self.assertEqual([(i.chave, i.campo) for i in itens], [("passo", "descricao")])
        self.assertEqual(concluir(mec, {}, visto, self.usuario), 1)
        mec.refresh_from_db()
        self.assertEqual(Descritor.objects.get(matriz_etapa_cc=mec, codigo="passo").descricao, "Da base, nova")
        self.assertEqual(mec.passo, 40)

    def test_descritor_com_barra_no_codigo_conclui(self):  # campo de descritor, campo de tarefa e "existe"
        base = self._outra_base()
        d = Descritor.objects.create(matriz_etapa_cc=base, codigo="EF05/LP", descricao="Antes", ordem=2)
        Tarefa.objects.create(descritor=d, inicio=100, fim=150, texto="Um.", ordem=1)
        sai = Tarefa.objects.create(descritor=d, inicio=200, fim=250, texto="Dois.", ordem=2)
        _, mec = self._derivada(base)
        Descritor.objects.filter(pk=d.pk).update(descricao="Da base, nova")
        Tarefa.objects.filter(descritor=d, inicio=100).update(texto="Um, novo.")
        sai.delete()
        Tarefa.objects.create(descritor=d, inicio=300, fim=350, texto="Três.", ordem=3)
        novo = Descritor.objects.create(matriz_etapa_cc=base, codigo="EF06/LP", descricao="Novo", ordem=3)
        Tarefa.objects.create(descritor=novo, inicio=100, fim=150, texto="Do novo.", ordem=1)

        itens, visto = revisao(mec)
        self.assertEqual(
            [(i.chave, i.campo) for i in itens],
            [
                ("EF05/LP", "descricao"),
                ("EF05/LP/100-150#1", "texto"),
                ("EF05/LP/200-250#1", "existe"),
                ("EF05/LP/300-350#1", "existe"),
                ("EF06/LP", "existe"),
            ],
        )
        self.assertEqual(concluir(mec, {}, visto, self.usuario), 5)
        mec.refresh_from_db()
        self.assertEqual(foto(mec), foto(base))
        self.assertEqual(revisao(mec)[0], [])

    def test_base_acrescentou_e_apagou_descritor_e_tarefa(self):
        base = self._outra_base()
        d05 = self._d05(base)
        Tarefa.objects.create(descritor=d05, inicio=300, fim=350, texto="Terceira.", ordem=2)
        d06 = Descritor.objects.create(matriz_etapa_cc=base, codigo="D06", descricao="Seis", ordem=2)
        Tarefa.objects.create(descritor=d06, inicio=100, fim=150, texto="Seis.", ordem=1)
        _, mec = self._derivada(base)
        # a base apaga D06 e a tarefa 300-350 do D05, e acrescenta o D07 e a tarefa 400-450 do D05
        d06.delete()
        Tarefa.objects.get(descritor=d05, inicio=300).delete()
        Tarefa.objects.create(descritor=d05, inicio=400, fim=450, texto="Quarta.", ordem=3)
        d07 = Descritor.objects.create(matriz_etapa_cc=base, codigo="D07", descricao="Sete", ordem=3)
        Tarefa.objects.create(descritor=d07, inicio=110, fim=160, texto="Sete.", ordem=1)

        itens, visto = revisao(mec)
        self.assertEqual(
            [(i.chave, i.campo, i.situacao) for i in itens],
            [
                ("D05/300-350#1", "existe", "entra"),
                ("D05/400-450#1", "existe", "entra"),
                ("D07", "existe", "entra"),
                ("D06", "existe", "entra"),
            ],
        )
        self.assertEqual(concluir(mec, {}, visto, self.usuario), 4)

        mec.refresh_from_db()
        self.assertEqual(foto(mec), foto(base))
        self.assertEqual(sorted(Descritor.objects.filter(matriz_etapa_cc=mec).values_list("codigo", flat=True)), ["D05", "D07"])
        self.assertEqual(Tarefa.objects.filter(descritor__matriz_etapa_cc=mec, descritor__codigo="D07").count(), 1)
        self.assertEqual(Tarefa.objects.filter(descritor__matriz_etapa_cc=base).count(), 3)  # a base não mexe
        self.assertEqual(mec.base_foto, foto(base))
        self.assertEqual(revisao(mec)[0], [])
        self.assertEqual(self._d05(mec).tarefa_set.get(inicio=400).history.get().history_user, self.usuario)

    def test_existe_em_conflito_vale_a_escolha(self):
        base = self._outra_base()
        d06 = Descritor.objects.create(matriz_etapa_cc=base, codigo="D06", descricao="Seis", ordem=2)
        _, mec = self._derivada(base)
        d06.delete()  # a base apaga o D06 que o projeto editou
        Descritor.objects.filter(matriz_etapa_cc=mec, codigo="D06").update(descricao="Seis editado")
        d07 = Descritor.objects.create(matriz_etapa_cc=base, codigo="D07", descricao="Sete da base", ordem=3)
        Tarefa.objects.create(descritor=d07, inicio=110, fim=160, texto="Da base.", ordem=1)
        d07p = Descritor.objects.create(matriz_etapa_cc=mec, codigo="D07", descricao="Sete do projeto", ordem=3)
        Tarefa.objects.create(descritor=d07p, inicio=120, fim=170, texto="Do projeto.", ordem=1)

        itens, visto = revisao(mec)
        self.assertEqual([(i.chave, i.situacao) for i in itens], [("D07", "conflito"), ("D06", "conflito")])
        with self.assertRaises(RevisaoIncompleta):
            concluir(mec, {("D07", "existe"): "base"}, visto, self.usuario)
        escolhas = {("D07", "existe"): "base", ("D06", "existe"): "local"}
        self.assertEqual(concluir(mec, escolhas, visto, self.usuario), 1)

        self.assertEqual(Descritor.objects.get(matriz_etapa_cc=mec, codigo="D06").descricao, "Seis editado")
        self.assertEqual(Descritor.objects.get(matriz_etapa_cc=mec, codigo="D07").descricao, "Sete da base")
        self.assertEqual(
            list(Tarefa.objects.filter(descritor__matriz_etapa_cc=mec, descritor__codigo="D07").values_list("texto", flat=True)),
            ["Da base."],
        )
        mec.refresh_from_db()
        self.assertEqual(revisao(mec)[0], [])

    def test_usar_o_da_base_troca_o_arquivo_e_apaga_o_orfao(self):
        velho = default_storage.save("itens/velho.png", ContentFile(PNG))
        novo = default_storage.save("itens/novo.png", ContentFile(PNG))
        sumiu = default_storage.save("itens/sumiu.png", ContentFile(PNG))
        base = self._outra_base()
        Tarefa.objects.filter(descritor__matriz_etapa_cc=base).update(arquivo=velho)
        Tarefa.objects.create(descritor=self._d05(base), inicio=300, fim=350, texto="Outra.", ordem=2, arquivo=sumiu)
        _, mec = self._derivada(base)  # o clone copia os caminhos: arquivo compartilhado (D-150)
        Tarefa.objects.filter(descritor__matriz_etapa_cc=base, inicio=100).update(arquivo=novo)
        Tarefa.objects.get(descritor__matriz_etapa_cc=base, inicio=300).delete()

        itens, visto = revisao(mec)
        self.assertEqual([(i.chave, i.campo) for i in itens], [("D05/100-150#1", "arquivo"), ("D05/300-350#1", "existe")])
        with self.captureOnCommitCallbacks(execute=True):
            self.assertEqual(concluir(mec, {}, visto, self.usuario), 2)

        self.assertEqual(self._t05(mec).arquivo, novo)
        self.assertFalse(default_storage.exists(velho))  # ninguém mais aponta para ele
        self.assertFalse(default_storage.exists(sumiu))  # saiu com a tarefa apagada
        self.assertTrue(default_storage.exists(novo))

    def test_manter_o_arquivo_do_projeto_nao_apaga_nada(self):
        velho = default_storage.save("itens/velho.png", ContentFile(PNG))
        novo = default_storage.save("itens/novo.png", ContentFile(PNG))
        base = self._outra_base()
        Tarefa.objects.filter(descritor__matriz_etapa_cc=base).update(arquivo=velho)
        _, mec = self._derivada(base)
        Tarefa.objects.filter(descritor__matriz_etapa_cc=base).update(arquivo=novo)
        _, visto = revisao(mec)
        with self.captureOnCommitCallbacks(execute=True):
            concluir(mec, {("D05/100-150#1", "arquivo"): "local"}, visto, self.usuario)
        self.assertEqual(self._t05(mec).arquivo, velho)
        self.assertTrue(default_storage.exists(velho))

    def test_recusa_copia_solta_e_projeto_arquivado(self):
        with self.assertRaisesMessage(RevisaoRecusada, "só a etapa do projeto tem revisão"):
            concluir(self.mec5, {}, "x", self.usuario)
        base, solta = self._derivada()
        e6 = Etapa.objects.create(ano=self.ano, codigo="6EF", escala_max=500, ordem=5)
        _, visto = revisao(solta)
        MatrizEtapaCC.objects.filter(pk=solta.pk).update(base=None)  # a base saiu (SET NULL)
        with self.assertRaisesMessage(RevisaoRecusada, "etapa sem base"):
            concluir(solta, {}, visto, self.usuario)

        mec = criar(self.projeto, e6, self.lp, self.usuario, base=base)
        Descritor.objects.filter(matriz_etapa_cc=base, codigo="D05").update(descricao="Da base, nova")
        _, visto = revisao(mec)
        Projeto.objects.filter(pk=self.projeto.pk).update(arquivado_em="2026-01-01T00:00:00Z")
        with self.assertRaisesMessage(RevisaoRecusada, "projeto arquivado"):
            concluir(mec, {}, visto, self.usuario)
        self.assertEqual(self._d05(mec).descricao, "Da outra")


class ConcluirConcorrenteTest(TransactionTestCase):
    """A trava da MEC do projeto faz o `concluir` esperar quem está gravando nela e recalcular."""

    def test_espera_a_edicao_local_em_andamento_e_recusa(self):
        Mundo.montar(self)
        e4 = Etapa.objects.create(ano=self.ano, codigo="4EF", escala_max=500, ordem=4)
        projeto = Projeto.objects.get(parceiro_ano__parceiro__nome="GO", arquivado_em__isnull=True)
        outra = Matriz.objects.create(ano=self.ano, nome="Outra")
        base = MatrizEtapaCC.objects.create(matriz=outra, etapa=self.e5, componente=self.lp, ano=self.ano, passo=25)
        Descritor.objects.create(matriz_etapa_cc=base, codigo="D05", descricao="Da outra", ordem=1)
        mec = criar(projeto, e4, self.lp, self.usuario, base=base)
        Descritor.objects.filter(matriz_etapa_cc=base, codigo="D05").update(descricao="Da base, nova")
        _, visto = revisao(mec)  # a tela mostrou 1 item "entra"
        travou, solta = threading.Event(), threading.Event()

        def outra_aba():  # trava só a MEC do projeto e edita o mesmo texto, sem commit ainda
            try:
                with transaction.atomic():
                    MatrizEtapaCC.objects.select_for_update().get(pk=mec.pk)
                    Descritor.objects.filter(matriz_etapa_cc=mec, codigo="D05").update(descricao="Do projeto")
                    travou.set()
                    solta.wait(10)
            finally:
                connection.close()

        t = threading.Thread(target=outra_aba)
        t.start()
        self.assertTrue(travou.wait(10))
        threading.Timer(0.5, solta.set).start()
        # Sem a trava, o concluir leria o texto antigo (a outra aba não commitou) e gravaria por cima.
        with self.assertRaises(RevisaoMudou):
            concluir(MatrizEtapaCC.objects.get(pk=mec.pk), {}, visto, self.usuario)
        t.join()
        self.assertEqual(Descritor.objects.get(matriz_etapa_cc=mec, codigo="D05").descricao, "Do projeto")

    def test_so_uma_aplica_e_a_outra_leva_revisao_mudou(self):
        Mundo.montar(self)
        e4 = Etapa.objects.create(ano=self.ano, codigo="4EF", escala_max=500, ordem=4)
        projeto = Projeto.objects.get(parceiro_ano__parceiro__nome="GO", arquivado_em__isnull=True)
        outra = Matriz.objects.create(ano=self.ano, nome="Outra")
        base = MatrizEtapaCC.objects.create(matriz=outra, etapa=self.e5, componente=self.lp, ano=self.ano, passo=25)
        Descritor.objects.create(matriz_etapa_cc=base, codigo="D05", descricao="Da outra", ordem=1)
        mec = criar(projeto, e4, self.lp, self.usuario, base=base)
        Descritor.objects.filter(matriz_etapa_cc=base, codigo="D05").update(descricao="Da base, nova")
        _, visto = revisao(mec)
        largada, resultados = threading.Event(), []

        def conclui():
            try:
                largada.wait(10)
                resultados.append(concluir(MatrizEtapaCC.objects.get(pk=mec.pk), {}, visto, self.usuario))
            except Exception as e:  # noqa: BLE001 - o teste confere o tipo
                resultados.append(e)
            finally:
                connection.close()

        threads = [threading.Thread(target=conclui) for _ in range(2)]
        for t in threads:
            t.start()
        largada.set()
        for t in threads:
            t.join()
        self.assertEqual(sorted(type(r).__name__ for r in resultados), ["RevisaoMudou", "int"])
        self.assertIn(1, resultados)
        self.assertEqual(Descritor.objects.get(matriz_etapa_cc=mec, codigo="D05").descricao, "Da base, nova")


def _tarefa(texto="t", arquivo=None, alt="", ordem=1):
    return {"texto": texto, "arquivo": arquivo, "texto_alternativo": alt, "ordem": ordem}


def _desc(descricao="x", ordem=1, tarefas=None):
    campos = {c: None for c in CAMPOS_DESCRITOR}
    return {**campos, "ordem": ordem, "descricao": descricao, "tarefas": tarefas or {}}


def _f(descritores, passo=None):
    return {"passo": passo, "descritores": descritores}


class ClassificarTest(SimpleTestCase):
    def test_so_base_mudou_entra(self):
        a, b, l = (_f({"D01": _desc(x)}) for x in ("x", "y", "x"))
        self.assertEqual(classificar(a, b, l), [Item("D01", "descricao", "x", "y", "x", "entra")])

    def test_so_local_mudou_nao_aparece(self):
        a, b, l = (_f({"D01": _desc(x)}) for x in ("x", "x", "z"))
        self.assertEqual(classificar(a, b, l), [])

    def test_os_dois_iguais_nao_aparece(self):
        a, b, l = (_f({"D01": _desc(x)}) for x in ("x", "y", "y"))
        self.assertEqual(classificar(a, b, l), [])

    def test_os_dois_diferentes_e_conflito(self):
        a, b, l = (_f({"D01": _desc(x)}) for x in ("x", "y", "z"))
        self.assertEqual(classificar(a, b, l), [Item("D01", "descricao", "x", "y", "z", "conflito")])

    def test_base_apagou_e_local_editou_e_conflito(self):
        a = _f({"D01": _desc(), "D02": _desc("x", 2)})
        b = _f({"D01": _desc()})
        l = _f({"D01": _desc(), "D02": _desc("editado", 2)})
        self.assertEqual(
            classificar(a, b, l),
            [Item("D02", "existe", _desc("x", 2), None, _desc("editado", 2), "conflito")],
        )

    def test_base_apagou_e_local_nao_mexeu_entra(self):
        a = _f({"D01": _desc(), "D02": _desc("x", 2)})
        b = _f({"D01": _desc()})
        self.assertEqual(
            classificar(a, b, a),
            [Item("D02", "existe", _desc("x", 2), None, _desc("x", 2), "entra")],
        )

    def test_base_acrescentou_descritor_entra(self):
        a = _f({"D01": _desc()})
        b = _f({"D01": _desc(), "D02": _desc("novo", 2)})
        self.assertEqual(
            classificar(a, b, a),
            [Item("D02", "existe", None, _desc("novo", 2), None, "entra")],
        )

    def test_dois_acrescentaram_o_mesmo_descritor_com_conteudo_diferente_e_conflito(self):
        a = _f({})
        b = _f({"D01": _desc("y")})
        l = _f({"D01": _desc("z")})
        self.assertEqual(
            classificar(a, b, l),
            [Item("D01", "existe", None, _desc("y"), _desc("z"), "conflito")],
        )

    def test_passo(self):
        a, b, l = _f({}, 1), _f({}, 2), _f({}, 1)
        self.assertEqual(classificar(a, b, l), [Item("passo", "passo", 1, 2, 1, "entra")])

    def test_arquivo_da_tarefa_entra_na_comparacao(self):
        def com(arquivo):
            return _f({"D01": _desc(tarefas={"100-150#1": _tarefa(arquivo=arquivo)})})

        self.assertEqual(
            classificar(com(None), com("novo.png"), com(None)),
            [Item("D01/100-150#1", "arquivo", None, "novo.png", None, "entra")],
        )

    def test_tarefa_nova_na_base_entra(self):
        a = _f({"D01": _desc()})
        b = _f({"D01": _desc(tarefas={"100-150#1": _tarefa()})})
        self.assertEqual(
            classificar(a, b, a),
            [Item("D01/100-150#1", "existe", None, _tarefa(), None, "entra")],
        )
    def test_ordem_de_saida(self):
        # Ordem natural das tarefas: "2-3#1" < "10-20#1" < "100-150#2" < "100-150#10"
        # (a lexicográfica daria "10-20#1", "100-150#10", "100-150#2", "2-3#1").
        chaves = ["100-150#10", "2-3#1", "100-150#2", "10-20#1"]

        def f(sufixo, ordens, passo):
            return _f({
                cod: _desc("x" + sufixo, ordem, {c: _tarefa("t" + sufixo) for c in chaves})
                for cod, ordem in ordens.items()
            }, passo)

        ordens = {"D01": 2, "D02": 1}
        a, b = f("", ordens, 2), f("!", ordens, 1)
        # D08 e D07 só existem em antes/local (a base apagou): vêm depois dos da base, na ordem de local.
        a["descritores"] = {"D08": _desc("a8", 8), "D07": _desc("a7", 7), **a["descritores"]}
        l = f("", ordens, 2)
        l["descritores"] = {"D07": _desc("l7", 7), "D08": _desc("l8", 8), **l["descritores"]}
        tarefas = ["2-3#1", "10-20#1", "100-150#2", "100-150#10"]
        self.assertEqual(
            [(i.chave, i.campo) for i in classificar(a, b, l)],
            [("passo", "passo")]
            + [item for cod in ("D02", "D01")
               for item in [(cod, "descricao")] + [(f"{cod}/{c}", "texto") for c in tarefas]]
            + [("D07", "existe"), ("D08", "existe")],
        )

    def test_fotos_vazias_e_passo_nulo_dao_lista_vazia(self):
        vazia = {"passo": None, "descritores": {}}
        self.assertEqual(classificar(vazia, vazia, vazia), [])

    def test_prerequisitos_e_ordem_do_descritor_tambem_entram(self):
        a = _f({"D01": {**_desc(ordem=1), "prerequisitos": ["p1"]}})
        b = _f({"D01": {**_desc(ordem=3), "prerequisitos": ["p1", "p2"]}})
        self.assertEqual(
            classificar(a, b, a),
            [
                Item("D01", "prerequisitos", ["p1"], ["p1", "p2"], ["p1"], "entra"),
                Item("D01", "ordem", 1, 3, 1, "entra"),
            ],
        )
