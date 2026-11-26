"""A cascata dos cortes preenche pelo seed o infográfico de LP que ela cria (D-298); desarquivar não preenche."""

import json
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from nucleo.models import (
    Ano,
    Componente,
    Etapa,
    Parceiro,
    ParceiroAno,
    RevistaInfografico,
    RevistaInfograficoEtapa,
    RevistaInfograficoItem,
)
from nucleo.servicos import seed_infografico
from nucleo.servicos.cascata import gravar_cortes
from nucleo.tests.test_resolver import MediaTemporaria

SEED = seed_infografico.seeds(2026)


@override_settings(INFOGRAFICOS_DO_SEED=True)
class CascataInfograficoTest(MediaTemporaria, TestCase):
    def setUp(self):
        super().setUp()  # a mídia temporária vem antes de qualquer cascata: as imagens vão para lá
        self.usuario = get_user_model().objects.create(username="admin")
        ano = self.ano = Ano.objects.create(ano=2026)
        self.lp = Componente.objects.create(ano=ano, codigo="LP", nome="Língua Portuguesa")
        self.mt = Componente.objects.create(ano=ano, codigo="MT", nome="Matemática")
        self.e2 = Etapa.objects.create(ano=ano, codigo="2EF", escala_max=1000, ordem=1)
        self.e5 = Etapa.objects.create(ano=ano, codigo="5EF", escala_max=500, ordem=2)
        self.pa = ParceiroAno.objects.create(parceiro=Parceiro.objects.create(nome="GO"), ano=ano)

    def cortes(self, *linhas):
        gravar_cortes(self.pa, [(e, c, [100, 200, 300]) for e, c in linhas], self.usuario)

    def alfa(self, componente):
        return RevistaInfografico.objects.get(revista__componente=componente, tipo="alfa")

    def test_alfa_de_lp_nasce_com_o_seed_e_a_de_mt_vazia(self):
        self.cortes((self.e5, self.lp), (self.e2, self.lp), (self.e2, self.mt))
        inf, seed = self.alfa(self.lp), SEED["LP", "alfa"]
        self.assertEqual(inf.habilidade, seed["habilidade"])
        self.assertEqual(inf.texto_habilidades, seed["texto_habilidades"])
        self.assertEqual(RevistaInfograficoEtapa.objects.filter(infografico=inf).count(), 12)
        self.assertEqual(
            list(RevistaInfograficoItem.objects.filter(infografico=inf, imagem__isnull=False).values_list("posicao", flat=True)),
            [1, 2, 3, 4],
        )
        self.assertEqual(inf.history.first().history_user, self.usuario)
        outras = RevistaInfografico.objects.get(revista__componente=self.lp, tipo="outras")
        self.assertEqual(outras.habilidade, SEED["LP", "outras"]["habilidade"])
        self.assertEqual(self.alfa(self.mt).habilidade, "")
        self.assertFalse(RevistaInfograficoItem.objects.filter(infografico__componente=self.mt).exists())

    def test_desarquivar_nao_preenche(self):
        self.cortes((self.e5, self.lp), (self.e2, self.lp))
        self.cortes((self.e5, self.lp))  # sem 2EF: a Alfa é arquivada
        inf = self.alfa(self.lp)
        self.assertIsNotNone(inf.arquivado_em)
        RevistaInfografico.objects.filter(pk=inf.pk).update(habilidade="")
        self.cortes((self.e5, self.lp), (self.e2, self.lp))  # volta: a mesma linha é desarquivada
        inf.refresh_from_db()
        self.assertIsNone(inf.arquivado_em)
        self.assertEqual(inf.habilidade, "")

    def test_seed_invalido_nao_impede_os_cortes(self):
        pasta = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, pasta)
        for arquivo in seed_infografico.pasta(2026).iterdir():
            shutil.copy(arquivo, pasta)
        quebrado = json.loads((pasta / "lp-alfa.json").read_text(encoding="utf-8"))
        quebrado["etapas"]["1EF"]["marca"] = "X"
        (pasta / "lp-alfa.json").write_text(json.dumps(quebrado), encoding="utf-8")
        with patch.object(seed_infografico, "pasta", return_value=pasta), self.assertLogs("nucleo.servicos.cascata", "WARNING") as log:
            self.cortes((self.e5, self.lp), (self.e2, self.lp))
        self.assertIn("lp-alfa.json inválido", log.output[0])
        self.assertEqual(self.alfa(self.lp).habilidade, "")  # a Alfa nasceu vazia
        self.assertEqual(  # as Outras, de seed válido, nasceram preenchidas
            RevistaInfografico.objects.get(revista__componente=self.lp, tipo="outras").habilidade,
            SEED["LP", "outras"]["habilidade"],
        )

    @override_settings(INFOGRAFICOS_DO_SEED=False)
    def test_chave_desligada_nasce_vazio(self):
        self.cortes((self.e2, self.lp))
        self.assertEqual(self.alfa(self.lp).habilidade, "")
