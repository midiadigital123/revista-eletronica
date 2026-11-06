"""Etapa do projeto (D-227): foto canônica e criação em branco ou por clone."""

import unittest

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from nucleo.management.commands.criar_demo import PNG
from nucleo.models import (
    Ano, Componente, Descritor, Etapa, Matriz, MatrizEtapaCC, Parceiro, ParceiroAno, Projeto, Revista, Tarefa,
)  # fmt: skip
from nucleo.servicos.cascata import gravar_cortes
from nucleo.servicos.empacotar import _itens
from nucleo.servicos.etapa_projeto import CriacaoRecusada, Item, classificar, criar, derivadas, foto, hash_foto
from nucleo.servicos.matriz import CAMPOS_DESCRITOR, impacto
from nucleo.servicos.planilhas import passos
from nucleo.servicos.resolver import carregar, hash_validado, pendencias, resolver
from nucleo.servicos.validacao import validada, validar
from nucleo.tests.test_resolver import MediaTemporaria, Mundo, recarregar, usuario


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

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.mec5 = MatrizEtapaCC.objects.get(matriz=cls.matriz, etapa=cls.e5, componente=cls.lp)
        cls.lp_go = cls.go["LP"]

    def _outra_base(self):
        """Base 4EF LP de uma matriz que o GO não usa: mexer nela só muda a revista pela derivada."""
        outra = Matriz.objects.create(ano=self.ano, nome="Outra")
        base = MatrizEtapaCC.objects.create(matriz=outra, etapa=self.e4, componente=self.lp, ano=self.ano, passo=25)
        d = Descritor.objects.create(matriz_etapa_cc=base, codigo="D05", descricao="Da outra", ordem=1)
        Tarefa.objects.create(descritor=d, inicio=100, fim=150, texto="Compara.", ordem=1)
        return base

    def _pronta(self):
        Revista.objects.filter(pk=self.lp_go.pk).update(
            svg_f2="f2/x.svg", svg_sha256="a" * 64, svg_ids=["passo1", "btn-action-p2"],
            capa="capas/x.png", capa_sha256="c" * 64,
        )  # fmt: skip
        return recarregar(self.lp_go)

    def test_revista_usa_a_etapa_do_projeto(self):
        self.assertNotIn("D01", resolver(recarregar(self.lp_go))["f1"]["dados"]["4ef"])  # ainda sem MEC
        criar(self.projeto, self.e4, self.lp, self.usuario, base=self.mec5)
        r = resolver(recarregar(self.lp_go))
        self.assertEqual(r["f1"]["etapas"], ["4ef", "5ef", "9ef"])
        self.assertEqual(r["f1"]["dados"]["4ef"]["D01"], r["f1"]["dados"]["5ef"]["D01"])
        self.assertEqual(r["f1"]["dados"]["4ef"]["D01"]["description"], "Descritor 1 LP")
        self.assertEqual([lc for lc in r["lacunas"] if lc["tipo"] in ("base", "etapa_em_dobro")], [])

    def test_corte_sem_matriz_some_com_a_etapa_do_projeto(self):
        p = [x for x in pendencias(recarregar(self.lp_go)) if x.codigo == "corte_sem_matriz"]
        self.assertEqual(p[0].mensagem, "A matriz não tem a etapa: 4EF.")
        criar(self.projeto, self.e4, self.lp, self.usuario, base=self.mec5)
        self.assertNotIn("corte_sem_matriz", [x.codigo for x in pendencias(recarregar(self.lp_go))])

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

    def test_matriz_ganha_a_etapa_vira_pendencia_de_escolha(self):
        mec = criar(self.projeto, self.e4, self.lp, self.usuario, base=self.mec5)
        da_matriz = MatrizEtapaCC.objects.create(matriz=self.matriz, etapa=self.e4, componente=self.lp, ano=self.ano, passo=25)
        Descritor.objects.create(matriz_etapa_cc=da_matriz, codigo="D09", descricao="Da matriz", ordem=1)
        lp = recarregar(self.lp_go)
        r = resolver(lp)
        self.assertIn({"tipo": "etapa_em_dobro", "etapa": "4ef"}, r["lacunas"])
        self.assertIn("D01", r["f1"]["dados"]["4ef"])  # até escolher, vale a do projeto
        self.assertIn(
            ("etapa_em_dobro", "A matriz agora tem 4EF: escolha qual usar."),
            [(p.codigo, p.mensagem) for p in pendencias(lp)],
        )

        MatrizEtapaCC.objects.filter(pk=mec.pk).update(preferida="matriz")
        r = resolver(lp)
        self.assertEqual([k for k in r["f1"]["dados"]["4ef"] if k.startswith("D")], ["D09"])
        self.assertNotIn("etapa_em_dobro", [lc["tipo"] for lc in r["lacunas"]])
        self.assertNotIn("etapa_em_dobro", [p.codigo for p in pendencias(lp)])

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

    def test_preferida_projeto_mantem_a_do_projeto_e_tira_a_lacuna(self):
        mec = criar(self.projeto, self.e4, self.lp, self.usuario, base=self.mec5)
        da_matriz = MatrizEtapaCC.objects.create(matriz=self.matriz, etapa=self.e4, componente=self.lp, ano=self.ano, passo=25)
        Descritor.objects.create(matriz_etapa_cc=da_matriz, codigo="D09", descricao="Da matriz", ordem=1)
        MatrizEtapaCC.objects.filter(pk=mec.pk).update(preferida="projeto")
        lp = recarregar(self.lp_go)
        r = resolver(lp)
        self.assertEqual([k for k in r["f1"]["dados"]["4ef"] if k.startswith("D")], ["D01", "D02"])
        self.assertNotIn("etapa_em_dobro", [lc["tipo"] for lc in r["lacunas"]])
        self.assertNotIn("etapa_em_dobro", [p.codigo for p in pendencias(lp)])


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

    def test_impacto_da_etapa_do_projeto_e_so_a_revista_do_projeto(self):
        self.assertEqual([r for r, _ in impacto(self.mec)], [self.lp_go])


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
