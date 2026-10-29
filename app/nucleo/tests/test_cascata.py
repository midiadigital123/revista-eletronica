import threading
from unittest import mock

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
)
from nucleo.models.revista import Motivo
from nucleo.servicos.cascata import gravar_cortes
from nucleo.servicos.foto import fotografar

SHA256_DE_VAZIO = "44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a"  # sha256("{}")


class CascataTest(TransactionTestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create(username="admin")
        ano = Ano.objects.create(ano=2026)
        self.lp = Componente.objects.create(ano=ano, codigo="LP", nome="Língua Portuguesa")
        self.mt = Componente.objects.create(ano=ano, codigo="MT", nome="Matemática")
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

    def test_aceita_limites(self):
        self.gravar((self.e5, self.lp, [0, 500]))
        self.assertEqual(Corte.objects.get().valores, [0, 500])

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
        self.assertEqual((foto.revista, foto.motivo, foto.hash), (mt, "arquivamento", SHA256_DE_VAZIO))
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
