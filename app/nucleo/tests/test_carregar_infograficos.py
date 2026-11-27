"""carregar_infograficos (D-298, D-311): copia o seed dos Word para os infográficos de LP e de MT Alfa, só onde está vazio."""

import hashlib
import json
import shutil
import tempfile
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from django.core.files.storage import default_storage
from django.core.management import CommandError, call_command
from django.test import TestCase
from django.utils import timezone

from nucleo.models import Revista, RevistaInfografico, RevistaInfograficoEtapa, RevistaInfograficoItem
from nucleo.servicos import arquivos, resolver, seed_infografico
from nucleo.tests.test_resolver import MediaTemporaria, Mundo

SEED = seed_infografico.seeds(2026)
PNG_PROPRIO = b"\x89PNG\r\n\x1a\n" + b"\x01" * 32  # imagem que a revista enviou na ficha


def arquivos_no_storage():
    _, nomes = default_storage.listdir("infograficos") if default_storage.exists("infograficos") else ([], [])
    return set(nomes)


class CarregarInfograficosTest(MediaTemporaria, TestCase):
    @classmethod
    def setUpTestData(cls):
        Mundo.montar(cls)  # GO e PE com cortes em 5EF e 9EF: só "outras", de LP e de MT
        cls.lp_go, cls.lp_pe, cls.mt_go = cls.go["LP"], cls.pe["LP"], cls.go["MT"]
        cls.alfa_go = RevistaInfografico.objects.create(revista=cls.lp_go, componente=cls.lp, ano=cls.ano, tipo="alfa")
        cls.alfa_pe_arquivado = RevistaInfografico.objects.create(
            revista=cls.lp_pe, componente=cls.lp, ano=cls.ano, tipo="alfa", arquivado_em=timezone.now()
        )

    def carregar(self):
        saida = StringIO()
        call_command("carregar_infograficos", ano=2026, usuario="admin", stdout=saida)
        return saida.getvalue()

    def inf(self, revista, tipo):
        return RevistaInfografico.objects.get(revista=revista, tipo=tipo)

    def test_preenche_lp_com_o_seed(self):
        self.carregar()
        for revista, tipo in ((self.lp_go, "alfa"), (self.lp_go, "outras"), (self.lp_pe, "outras")):
            seed, inf = SEED["LP", tipo], self.inf(revista, tipo)
            self.assertEqual(
                [getattr(inf, c) for c in seed_infografico.CAMPOS_INF], [seed[c] for c in seed_infografico.CAMPOS_INF]
            )
            etapas = {e.etapa: {c: getattr(e, c) for c in seed_infografico.CAMPOS_ETAPA}
                      for e in RevistaInfograficoEtapa.objects.filter(infografico=inf)}  # fmt: skip
            self.assertEqual(etapas, seed["etapas"])
            itens = RevistaInfograficoItem.objects.filter(infografico=inf).order_by("posicao")
            self.assertEqual([(i.etapa, i.descritor, i.analise) for i in itens],
                             [(i["etapa"], i["descritor"], i["analise"]) for i in seed["itens"]])  # fmt: skip
            for item, valores in zip(itens, seed["itens"]):
                dados = (seed_infografico.pasta(2026) / valores["imagem"]).read_bytes()
                self.assertEqual(item.imagem_sha256, hashlib.sha256(dados).hexdigest())
                self.assertTrue(default_storage.exists(item.imagem))
            self.assertEqual(inf.history.first().history_user, self.usuario)
        # Um arquivo por revista: as imagens das revistas não dividem caminho.
        caminhos = list(RevistaInfograficoItem.objects.values_list("imagem", flat=True))
        self.assertEqual(len(caminhos), len(set(caminhos)))

    def test_nao_toca_mt_nem_arquivados(self):
        Revista.objects.filter(pk=self.lp_pe.pk).update(arquivada_em=timezone.now())
        self.carregar()
        self.assertEqual(self.inf(self.mt_go, "outras").habilidade, "")
        self.assertEqual(self.inf(self.lp_pe, "outras").habilidade, "")  # revista arquivada
        self.alfa_pe_arquivado.refresh_from_db()
        self.assertEqual(self.alfa_pe_arquivado.habilidade, "")
        self.assertFalse(RevistaInfograficoItem.objects.filter(infografico__revista__componente=self.mt).exists())

    def test_mantem_o_que_ja_tem_valor(self):
        inf = self.inf(self.lp_go, "outras")
        RevistaInfografico.objects.filter(pk=inf.pk).update(habilidade="Escrita do projeto")
        RevistaInfograficoEtapa.objects.create(infografico=inf, ano=self.ano, etapa="1EF", marca="R")
        saida = self.carregar()
        inf.refresh_from_db()
        self.assertEqual(inf.habilidade, "Escrita do projeto")
        self.assertEqual(inf.texto_descritor, SEED["LP", "outras"]["texto_descritor"])  # o vazio foi preenchido
        etapa = RevistaInfograficoEtapa.objects.get(infografico=inf, etapa="1EF")
        self.assertEqual((etapa.marca, etapa.codigo), ("R", "EF15LP18"))
        self.assertIn("2 mantidos", saida)

    def test_segunda_rodada_nao_muda_nada(self):
        self.carregar()
        arquivos, historicos = arquivos_no_storage(), RevistaInfografico.history.count()
        saida = self.carregar()
        self.assertEqual(arquivos_no_storage(), arquivos)
        self.assertEqual(RevistaInfografico.history.count(), historicos)
        self.assertEqual(saida.count("0 preenchidos, 0 atualizados, 0 mantidos"), len(SEED))  # uma linha por seed

    def test_conta_quem_perdeu_o_validado(self):
        revista = Revista.objects.get(pk=self.lp_go.pk)
        Revista.objects.filter(pk=revista.pk).update(hash_validado=resolver.hash_validado(revista))
        saida = self.carregar()
        self.assertIn("1 revistas perderam o Validado", saida)

    def test_seed_invalido_nao_grava_nada(self):
        pasta = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, pasta)
        for arquivo in seed_infografico.pasta(2026).iterdir():
            shutil.copy(arquivo, pasta)
        quebrado = json.loads((pasta / "lp-alfa.json").read_text(encoding="utf-8"))
        quebrado["etapas"]["1EF"]["marca"] = "X"
        (pasta / "lp-alfa.json").write_text(json.dumps(quebrado), encoding="utf-8")
        with patch.object(seed_infografico, "pasta", return_value=pasta):
            with self.assertRaisesMessage(CommandError, "lp-alfa.json: etapa 1EF: marca"):
                self.carregar()
        self.assertFalse(RevistaInfograficoItem.objects.exists())
        self.assertEqual(self.inf(self.lp_go, "outras").habilidade, "")

    def test_usuario_inexistente(self):
        with self.assertRaisesMessage(CommandError, "usuário 'ninguem' não existe"):
            call_command("carregar_infograficos", ano=2026, usuario="ninguem")


class RecargaInfograficosTest(MediaTemporaria, TestCase):
    """--anterior (D-298): o campo ainda igual ao seed anterior recebe o novo; o editado na revista fica."""

    @classmethod
    def setUpTestData(cls):
        Mundo.montar(cls)
        cls.lp_go, cls.lp_pe = cls.go["LP"], cls.pe["LP"]

    def setUp(self):
        super().setUp()
        call_command("carregar_infograficos", ano=2026, usuario="admin", stdout=StringIO())  # 1ª carga: o seed real
        # Seed "corrigido": progressão, código da 1EF e análise do item 2 trocados; imagem do item 1 = a do item 2.
        self.novo = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.novo)
        for arquivo in seed_infografico.pasta(2026).iterdir():
            shutil.copy(arquivo, self.novo)
        seed = json.loads((self.novo / "lp-outras.json").read_text(encoding="utf-8"))
        seed["texto_progressao"] += "\n\nParágrafo corrigido."
        seed["etapas"]["1EF"]["codigo"] = "EF15LP99"
        seed["itens"][1]["analise"] = "Análise corrigida."
        (self.novo / "lp-outras-item-1.png").write_bytes((self.novo / "lp-outras-item-2.png").read_bytes())
        (self.novo / "lp-outras.json").write_text(json.dumps(seed, ensure_ascii=False), encoding="utf-8")
        self.seed_novo = seed

    def recarregar(self, anterior=None):
        saida = StringIO()
        anterior = anterior or str(seed_infografico.pasta(2026))
        with patch.object(seed_infografico, "pasta", return_value=self.novo):
            call_command("carregar_infograficos", ano=2026, usuario="admin", anterior=anterior, stdout=saida)
        return saida.getvalue()

    def outras(self, revista):
        return RevistaInfografico.objects.get(revista=revista, tipo="outras")

    def test_atualiza_o_que_ninguem_editou_e_mantem_o_editado(self):
        inf_go, inf_pe = self.outras(self.lp_go), self.outras(self.lp_pe)
        RevistaInfografico.objects.filter(pk=inf_pe.pk).update(texto_progressao="Texto do PE.")
        RevistaInfograficoEtapa.objects.filter(infografico=inf_pe, etapa="1EF").update(codigo="EF00PE00")
        RevistaInfograficoItem.objects.filter(infografico=inf_pe, posicao=2).update(analise="Análise do PE.")
        with self.captureOnCommitCallbacks(execute=True):
            saida = self.recarregar()
        inf_go.refresh_from_db(), inf_pe.refresh_from_db()
        self.assertEqual(inf_go.texto_progressao, self.seed_novo["texto_progressao"])
        self.assertEqual(inf_pe.texto_progressao, "Texto do PE.")
        etapa = lambda inf: RevistaInfograficoEtapa.objects.get(infografico=inf, etapa="1EF").codigo  # noqa: E731
        self.assertEqual((etapa(inf_go), etapa(inf_pe)), ("EF15LP99", "EF00PE00"))
        analise = lambda inf: RevistaInfograficoItem.objects.get(infografico=inf, posicao=2).analise  # noqa: E731
        self.assertEqual((analise(inf_go), analise(inf_pe)), ("Análise corrigida.", "Análise do PE."))
        # GO: 3 campos + imagem do item 1 (nas duas revistas) atualizados; PE: 3 editados mantidos.
        self.assertIn("lp-outras.json: 2 infográficos, 0 preenchidos, 5 atualizados, 3 mantidos", saida)
        self.assertIn("lp-alfa.json", saida)  # o Mundo não tem Alfa: 0 infográficos, sem erro

    def test_imagem_igual_a_anterior_e_trocada_e_a_editada_fica(self):
        item_go = RevistaInfograficoItem.objects.get(infografico=self.outras(self.lp_go), posicao=1)
        item_pe = RevistaInfograficoItem.objects.get(infografico=self.outras(self.lp_pe), posicao=1)
        arquivos.receber_imagem_item(item_pe, PNG_PROPRIO)  # o PE trocou a imagem na ficha
        antigo_go, sha_pe = item_go.imagem, RevistaInfograficoItem.objects.get(pk=item_pe.pk).imagem_sha256
        with self.captureOnCommitCallbacks(execute=True):
            self.recarregar()
        item_go.refresh_from_db(), item_pe.refresh_from_db()
        novo = hashlib.sha256((self.novo / "lp-outras-item-1.png").read_bytes()).hexdigest()
        self.assertEqual(item_go.imagem_sha256, novo)
        self.assertNotEqual(item_go.imagem, antigo_go)
        self.assertFalse(default_storage.exists(antigo_go))  # o antigo era só desta revista
        self.assertEqual(item_pe.imagem_sha256, sha_pe)

    def test_anterior_inexistente_ou_invalido_nao_grava(self):
        with self.assertRaisesMessage(CommandError, "nenhum seed anterior"):
            self.recarregar(anterior="templates_seed/2026/nao-existe")
        quebrado = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, quebrado)
        shutil.copy(seed_infografico.pasta(2026) / "lp-outras.json", quebrado)  # sem as imagens
        with self.assertRaisesMessage(CommandError, "anterior lp-outras.json: item 1: imagem"):
            self.recarregar(anterior=str(quebrado))
        self.assertEqual(self.outras(self.lp_go).texto_progressao, seed_infografico.seeds(2026)["LP", "outras"]["texto_progressao"])
