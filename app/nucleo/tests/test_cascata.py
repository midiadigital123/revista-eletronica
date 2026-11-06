import importlib
import threading
from unittest import mock

from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import connection
from django.test import TransactionTestCase

from nucleo.models import (
    Ano,
    Componente,
    Corte,
    Etapa,
    FotoRevista,
    Parceiro,
    ParceiroAno,
    Projeto,
    Revista,
    RevistaFasciculo,
    RevistaInfografico,
)
from nucleo.models.revista import Motivo, TipoInfografico
from nucleo.servicos.cascata import gravar_cortes
from nucleo.servicos.foto import fotografar
from nucleo.servicos.resolver import resolver, sha256



class CascataTest(TransactionTestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create(username="admin")
        ano = Ano.objects.create(ano=2026)
        self.lp = Componente.objects.create(ano=ano, codigo="LP", nome="Língua Portuguesa")
        self.mt = Componente.objects.create(ano=ano, codigo="MT", nome="Matemática")
        self.e2 = Etapa.objects.create(ano=ano, codigo="2EF", escala_max=500, ordem=1)
        self.e5 = Etapa.objects.create(ano=ano, codigo="5EF", escala_max=500, ordem=2)
        self.e9 = Etapa.objects.create(ano=ano, codigo="9EF", escala_max=500, ordem=3)
        self.pa = ParceiroAno.objects.create(parceiro=Parceiro.objects.create(nome="GO"), ano=ano)

    def gravar(self, *linhas):
        gravar_cortes(self.pa, linhas, self.usuario)

    def lp_e_mt(self):
        self.gravar((self.e5, self.lp, [125, 175, 225]), (self.e5, self.mt, [150, 200, 250]))

    def ativo(self):
        return Projeto.objects.get(parceiro_ano=self.pa, arquivado_em__isnull=True)

    # Validação (D-055): recusa antes de gravar.

    def recusa(self, valores, etapa=None):
        with self.assertRaises(ValidationError):
            self.gravar((etapa or self.e5, self.lp, valores))
        self.assertFalse(Corte.objects.exists())
        self.assertFalse(Projeto.objects.exists())

    def test_recusa_sem_valores(self):
        self.recusa([])

    def test_recusa_5_valores(self):
        self.recusa([100, 200, 300, 400, 450])

    def test_recusa_nao_crescente(self):
        self.recusa([200, 200, 300])
        self.recusa([300, 200])

    def test_recusa_acima_de_escala_max(self):
        self.recusa([100, 501])

    def test_recusa_negativo_e_nao_inteiro(self):
        self.recusa([-1, 100])
        self.recusa([100, "200"])

    def test_recusa_etapa_de_outro_ano(self):
        e5_27 = Etapa.objects.create(ano=Ano.objects.create(ano=2027), codigo="5EF", escala_max=500, ordem=2)
        self.recusa([100, 200], etapa=e5_27)

    def test_recusa_corte_nos_limites(self):  # D-153
        self.recusa([0, 100])
        self.recusa([100, 500])

    def test_aceita_dentro_dos_limites(self):
        self.gravar((self.e5, self.lp, [1, 499]))
        self.assertEqual(Corte.objects.get().valores, [1, 499])

    # Cascata.

    def test_so_lp_gera_1_revista_com_2_fasciculos(self):
        self.gravar((self.e5, self.lp, [125, 175, 225]), (self.e9, self.lp, [200, 275, 325]))
        projeto = self.ativo()
        self.assertEqual(projeto.nome, "GO - NOME DO PROJETO")
        revista = Revista.objects.get()
        self.assertEqual((revista.projeto, revista.componente), (projeto, self.lp))
        self.assertEqual(
            sorted(RevistaFasciculo.objects.filter(revista=revista).values_list("fasciculo", flat=True)),
            ["F1", "F2"],
        )

    def test_altera_valores_sem_mexer_na_revista(self):
        self.gravar((self.e5, self.lp, [125, 175, 225]))
        self.gravar((self.e5, self.lp, [100, 175]))
        self.assertEqual(Corte.objects.get().valores, [100, 175])
        self.assertEqual(Revista.objects.count(), 1)
        self.assertFalse(FotoRevista.objects.exists())

    def test_remover_mt_arquiva_mt_e_nao_mexe_na_lp(self):
        self.lp_e_mt()
        lp = Revista.objects.get(componente=self.lp)
        self.gravar((self.e5, self.lp, [125, 175, 225]))
        mt = Revista.objects.get(componente=self.mt)
        self.assertIsNotNone(mt.arquivada_em)
        foto = FotoRevista.objects.get()
        self.assertEqual((foto.revista, foto.motivo, foto.hash), (mt, "arquivamento", sha256(foto.conteudo)))
        # A foto viu os cortes do MT antes de serem apagados, e a revista arquivada devolve a foto (D-117).
        self.assertEqual(foto.conteudo["f1"]["dados"]["5ef"]["cortes"], {"padrao-1": 150, "padrao-2": 200, "padrao-3": 250})
        self.assertEqual(resolver(mt), foto.conteudo)
        lp_depois = Revista.objects.get(componente=self.lp)
        self.assertIsNone(lp_depois.arquivada_em)
        self.assertEqual(lp_depois.history.count(), lp.history.count())
        self.assertIsNone(self.ativo().arquivado_em)
        self.assertFalse(Corte.objects.filter(componente=self.mt).exists())

    def test_recolocar_mt_reativa_a_mesma_linha(self):
        self.lp_e_mt()
        mt = Revista.objects.get(componente=self.mt)
        self.gravar((self.e5, self.lp, [125, 175, 225]))
        self.lp_e_mt()
        self.assertEqual(Revista.objects.filter(componente=self.mt).get().pk, mt.pk)
        self.assertIsNone(Revista.objects.get(pk=mt.pk).arquivada_em)
        self.assertEqual(RevistaFasciculo.objects.filter(revista=mt).count(), 2)

    def test_remover_tudo_arquiva_o_projeto(self):
        self.lp_e_mt()
        projeto = self.ativo()
        self.gravar()
        projeto.refresh_from_db()
        self.assertIsNotNone(projeto.arquivado_em)
        self.assertFalse(Revista.objects.filter(arquivada_em__isnull=True).exists())
        self.assertEqual(FotoRevista.objects.filter(motivo="arquivamento").count(), 2)
        self.assertFalse(Corte.objects.exists())
        self.gravar()  # sem projeto ativo e sem cortes: nada a fazer
        self.assertEqual(Projeto.objects.count(), 1)

    def test_readicionar_gera_projeto_novo_e_herda_foto_de_impresso(self):
        self.gravar((self.e5, self.lp, [125, 175, 225]))
        antigo = self.ativo()
        lp_antiga = Revista.objects.get()
        impresso = fotografar(lp_antiga, Motivo.IMPRESSO, self.usuario)
        self.gravar()
        self.gravar((self.e5, self.lp, [125, 175, 225]), (self.e5, self.mt, [150, 200]))

        novo = self.ativo()
        self.assertNotEqual(novo.pk, antigo.pk)
        antigo.refresh_from_db()
        self.assertIsNotNone(antigo.arquivado_em)  # o arquivado fica como está
        lp_nova = Revista.objects.get(projeto=novo, componente=self.lp)
        herdada = FotoRevista.objects.get(revista=lp_nova)
        self.assertEqual(
            (herdada.motivo, herdada.herdada, herdada.hash, herdada.conteudo),
            ("impresso", True, impresso.hash, impresso.conteudo),
        )
        mt_nova = Revista.objects.get(projeto=novo, componente=self.mt)
        self.assertFalse(FotoRevista.objects.filter(revista=mt_nova).exists())  # MT nunca foi impressa

    def test_duas_threads_nao_duplicam_a_revista(self):
        barreira = threading.Barrier(2)
        erros = []

        def rodar():
            try:
                barreira.wait()
                self.lp_e_mt()
            except Exception as e:  # noqa: BLE001 — a thread não propaga a exceção
                erros.append(e)
            finally:
                connection.close()

        threads = [threading.Thread(target=rodar) for _ in range(2)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(erros, [])
        self.assertEqual(Projeto.objects.count(), 1)
        self.assertEqual(Revista.objects.count(), 2)
        self.assertEqual(RevistaFasciculo.objects.count(), 4)

    def test_foto_de_arquivamento_ve_os_cortes_ainda_gravados(self):
        self.lp_e_mt()
        cortes_na_foto = []

        def espiar(revista, motivo, usuario):
            cortes_na_foto.append(
                Corte.objects.filter(parceiro_ano=self.pa, componente=revista.componente).count()
            )
            return fotografar(revista, motivo, usuario)

        with mock.patch("nucleo.servicos.cascata.fotografar", side_effect=espiar):
            self.gravar((self.e5, self.lp, [125, 175, 225]))
        self.assertEqual(cortes_na_foto, [1])
        self.assertFalse(Corte.objects.filter(componente=self.mt).exists())

    def test_erro_na_foto_desfaz_tudo(self):
        self.lp_e_mt()
        antes = (
            list(Corte.objects.order_by("pk").values_list("componente", "valores")),
            list(Projeto.objects.values_list("pk", "arquivado_em")),
            list(Revista.objects.order_by("pk").values_list("pk", "arquivada_em")),
        )
        with mock.patch("nucleo.servicos.cascata.fotografar", side_effect=RuntimeError("falhou")):
            with self.assertRaises(RuntimeError):
                self.gravar()
        depois = (
            list(Corte.objects.order_by("pk").values_list("componente", "valores")),
            list(Projeto.objects.values_list("pk", "arquivado_em")),
            list(Revista.objects.order_by("pk").values_list("pk", "arquivada_em")),
        )
        self.assertEqual(depois, antes)
        self.assertFalse(FotoRevista.objects.exists())

    def test_remove_mt_depois_tudo_fotografa_cada_uma_uma_vez(self):
        self.lp_e_mt()
        self.gravar((self.e5, self.lp, [125, 175, 225]))
        self.gravar()
        fotos = FotoRevista.objects.filter(motivo="arquivamento")
        self.assertEqual(
            sorted(fotos.values_list("revista__componente__codigo", flat=True)), ["LP", "MT"]
        )

    def test_mesmo_conjunto_duas_vezes_nao_cria_historico(self):
        self.lp_e_mt()
        contagem = lambda: [m.history.count() for m in (Corte, Projeto, Revista, RevistaFasciculo)]  # noqa: E731
        antes = contagem()
        self.lp_e_mt()
        self.assertEqual(contagem(), antes)
        self.assertEqual(Corte.history.first().history_user, self.usuario)

    def test_heranca_nao_vem_de_outro_parceiro_ano(self):
        sc = ParceiroAno.objects.create(parceiro=Parceiro.objects.create(nome="SC"), ano=self.pa.ano)
        gravar_cortes(sc, [(self.e5, self.lp, [125, 175])], self.usuario)
        fotografar(Revista.objects.get(projeto__parceiro_ano=sc), Motivo.IMPRESSO, self.usuario)
        gravar_cortes(sc, [], self.usuario)
        self.gravar((self.e5, self.lp, [125, 175]))
        lp_go = Revista.objects.get(projeto__parceiro_ano=self.pa)
        self.assertFalse(FotoRevista.objects.filter(revista=lp_go).exists())

    # Infográficos do F2 (D-230): alfa <=> corte no 2EF; outras <=> corte em etapa != 2EF.

    def infograficos(self, componente):
        """{tipo: arquivado?} dos infográficos da revista do componente."""
        qs = RevistaInfografico.objects.filter(revista__componente=componente)
        return {i.tipo: i.arquivado_em is not None for i in qs}

    def test_so_2ef_gera_so_alfa(self):
        self.gravar((self.e2, self.lp, [200, 300]))
        self.assertEqual(self.infograficos(self.lp), {"alfa": False})

    def test_so_5ef_gera_so_outras(self):
        self.gravar((self.e5, self.lp, [200, 300]))
        self.assertEqual(self.infograficos(self.lp), {"outras": False})

    def test_2ef_e_5ef_geram_os_dois(self):
        self.gravar((self.e2, self.lp, [200, 300]), (self.e5, self.lp, [200, 300]))
        self.assertEqual(self.infograficos(self.lp), {"alfa": False, "outras": False})
        for inf in RevistaInfografico.objects.all():
            self.assertEqual((inf.componente_id, inf.ano_id), (self.lp.pk, self.pa.ano_id))

    def test_tirar_2ef_arquiva_alfa_e_mantem_outras(self):
        self.gravar((self.e2, self.lp, [200, 300]), (self.e5, self.lp, [200, 300]))
        self.gravar((self.e5, self.lp, [200, 300]))
        self.assertEqual(self.infograficos(self.lp), {"alfa": True, "outras": False})

    def test_voltar_2ef_desarquiva_o_mesmo_alfa(self):
        self.gravar((self.e2, self.lp, [200, 300]), (self.e5, self.lp, [200, 300]))
        alfa = RevistaInfografico.objects.get(tipo=TipoInfografico.ALFA)
        self.gravar((self.e5, self.lp, [200, 300]))
        self.gravar((self.e2, self.lp, [200, 300]), (self.e5, self.lp, [200, 300]))
        alfa_depois = RevistaInfografico.objects.get(tipo=TipoInfografico.ALFA)
        self.assertEqual(alfa_depois.pk, alfa.pk)
        self.assertIsNone(alfa_depois.arquivado_em)
        self.assertEqual(RevistaInfografico.objects.count(), 2)

    def test_infograficos_por_componente(self):
        self.gravar((self.e2, self.lp, [200, 300]), (self.e9, self.mt, [200, 300]))
        self.assertEqual(self.infograficos(self.lp), {"alfa": False})
        self.assertEqual(self.infograficos(self.mt), {"outras": False})

    def test_mesmo_conjunto_duas_vezes_nao_cria_historico_de_infografico(self):
        linhas = ((self.e2, self.lp, [200, 300]), (self.e5, self.lp, [200, 300]))
        self.gravar(*linhas)
        antes = RevistaInfografico.history.count()
        self.gravar(*linhas)
        self.assertEqual(RevistaInfografico.history.count(), antes)
        self.assertEqual(RevistaInfografico.history.first().history_user, self.usuario)

    def test_tirar_o_componente_nao_mexe_nos_infograficos_da_revista_arquivada(self):
        self.gravar((self.e2, self.lp, [200, 300]), (self.e5, self.mt, [200, 300]))
        self.gravar((self.e2, self.lp, [200, 300]))
        self.assertIsNotNone(Revista.objects.get(componente=self.mt).arquivada_em)
        self.assertEqual(self.infograficos(self.mt), {"outras": False})
        self.assertEqual(self.infograficos(self.lp), {"alfa": False})

    def test_revista_arquivada_que_volta_com_outros_cortes_sincroniza_depois_de_voltar(self):
        self.gravar((self.e2, self.lp, [200, 300]), (self.e5, self.mt, [200, 300]))
        self.gravar((self.e2, self.lp, [200, 300]))  # MT arquivada
        self.gravar((self.e2, self.lp, [200, 300]), (self.e2, self.mt, [200, 300]))  # MT volta só com 2EF
        self.assertIsNone(Revista.objects.get(componente=self.mt).arquivada_em)
        self.assertEqual(self.infograficos(self.mt), {"alfa": False, "outras": True})

    def test_codigo_da_etapa_nao_diferencia_maiusculas(self):
        e2 = Etapa.objects.create(ano=self.pa.ano, codigo="2ef", escala_max=500, ordem=4)
        self.gravar((e2, self.lp, [200, 300]))
        self.assertEqual(self.infograficos(self.lp), {"alfa": False})

    # Migração de dados 0022: revistas que já existiam ganham os infográficos.

    def migrar(self):
        mod = importlib.import_module("nucleo.migrations.0022_infograficos_existentes")
        mod.criar(apps, None)

    def test_migracao_cria_os_infograficos_que_faltam_sem_mudar_o_resolvido(self):
        self.gravar(
            (self.e2, self.lp, [200, 300]), (self.e5, self.lp, [200, 300]), (self.e9, self.mt, [200, 300])
        )
        RevistaInfografico.objects.all().delete()
        antes = {r.pk: resolver(r) for r in Revista.objects.all()}
        revistas = list(Revista.objects.values_list("pk", "hash_validado", "validado_em"))
        self.migrar()
        self.assertEqual(self.infograficos(self.lp), {"alfa": False, "outras": False})
        self.assertEqual(self.infograficos(self.mt), {"outras": False})
        self.migrar()  # idempotente
        self.assertEqual(RevistaInfografico.objects.count(), 3)
        self.assertEqual({r.pk: resolver(r) for r in Revista.objects.all()}, antes)
        self.assertEqual(list(Revista.objects.values_list("pk", "hash_validado", "validado_em")), revistas)

    def test_migracao_ignora_revista_arquivada(self):
        self.gravar((self.e2, self.lp, [200, 300]), (self.e5, self.mt, [200, 300]))
        self.gravar((self.e2, self.lp, [200, 300]))
        RevistaInfografico.objects.all().delete()
        self.migrar()
        self.assertEqual(self.infograficos(self.lp), {"alfa": False})
        self.assertEqual(self.infograficos(self.mt), {})
