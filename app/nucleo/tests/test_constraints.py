from django.apps import apps
from django.core.management import call_command
from django.db import IntegrityError, connection, transaction
from django.test import TestCase, TransactionTestCase

from nucleo.models import Ano, Componente, CorPadrao, Etapa, Matriz, MatrizEtapaCC

# Atualize junto com cada migração que criar FK composta, CHECK ou UNIQUE (D-124).
FKS_COMPOSTAS = {
    "fk_matriz_etapa_cc_matriz_ano": "FOREIGN KEY (matriz_id, ano_id) REFERENCES matriz(id, ano_id)",
    "fk_matriz_etapa_cc_etapa_ano": "FOREIGN KEY (etapa_id, ano_id) REFERENCES etapa(id, ano_id)",
    "fk_matriz_etapa_cc_componente_ano": "FOREIGN KEY (componente_id, ano_id) REFERENCES componente(id, ano_id)",
    "fk_parceiro_ano_matriz_ano": "FOREIGN KEY (matriz_id, ano_id) REFERENCES matriz(id, ano_id)",
    "fk_corte_parceiro_ano_ano": "FOREIGN KEY (parceiro_ano_id, ano_id) REFERENCES parceiro_ano(id, ano_id)",
    "fk_corte_etapa_ano": "FOREIGN KEY (etapa_id, ano_id) REFERENCES etapa(id, ano_id)",
    "fk_corte_componente_ano": "FOREIGN KEY (componente_id, ano_id) REFERENCES componente(id, ano_id)",
    "fk_projeto_parceiro_ano_ano": "FOREIGN KEY (parceiro_ano_id, ano_id) REFERENCES parceiro_ano(id, ano_id)",
    "fk_projeto_passo_projeto_ano": "FOREIGN KEY (projeto_id, ano_id) REFERENCES projeto(id, ano_id)",
    "fk_projeto_passo_etapa_ano": "FOREIGN KEY (etapa_id, ano_id) REFERENCES etapa(id, ano_id)",
    "fk_projeto_passo_componente_ano": "FOREIGN KEY (componente_id, ano_id) REFERENCES componente(id, ano_id)",
    "fk_template_componente_ano": "FOREIGN KEY (componente_id, ano_id) REFERENCES componente(id, ano_id)",
    "fk_revista_projeto_ano": "FOREIGN KEY (projeto_id, ano_id) REFERENCES projeto(id, ano_id)",
    "fk_revista_componente_ano": "FOREIGN KEY (componente_id, ano_id) REFERENCES componente(id, ano_id)",
    "fk_revista_fasciculo_revista_ano": "FOREIGN KEY (revista_id, ano_id, componente_id) "
    "REFERENCES revista(id, ano_id, componente_id)",
    "fk_revista_fasciculo_template_ano": "FOREIGN KEY (template_id, ano_id, componente_id, fasciculo) "
    "REFERENCES template(id, ano_id, componente_id, fasciculo)",
    "fk_revista_secao_fasciculo_template": "FOREIGN KEY (revista_fasciculo_id, template_id) "
    "REFERENCES revista_fasciculo(id, template_id)",
    "fk_revista_secao_versao_template": "FOREIGN KEY (template_versao_id, template_id) "
    "REFERENCES template_versao(id, template_id)",
}
# Colunas de FK composta que podem ser nulas (MATCH SIMPLE desliga a checagem).
ANULAVEIS = {("parceiro_ano", "matriz_id"), ("revista_fasciculo", "template_id")}
# Toda FK que o Django não cria: compostas e as com ação de banco (D-124).
FKS_MANUAIS = {
    **FKS_COMPOSTAS,
    "fk_matriz_duplicada_de": "FOREIGN KEY (duplicada_de_id) REFERENCES matriz(id) ON DELETE SET NULL",
}
CHECKS = {
    "componente_codigo_tamanho",
    "componente_nome_tamanho",
    "cor_padrao_cor_hex",
    "cor_padrao_padrao_1a5",
    "descritor_codigo_tamanho",
    "etapa_codigo_tamanho",
    "matriz_duplicada_de_outra",
    "matriz_nome_tamanho",
    "parceiro_nome_tamanho",
    "tarefa_arquivo_tamanho",
    "tarefa_inicio_menor_fim",
    "bloqueio_sessao_edicao_tamanho",
    "bloqueio_um_alvo",
    "corte_valores_1a4",
    "corte_valores_sem_nulo",
    "foto_revista_hash_sha256",
    "foto_revista_motivo",
    "projeto_cor_cor_hex",
    "projeto_cor_padrao_1a5",
    "projeto_gentilico_fem_plur_tamanho",
    "projeto_gentilico_fem_sing_tamanho",
    "projeto_gentilico_masc_plur_tamanho",
    "projeto_gentilico_masc_sing_tamanho",
    "projeto_nome_tamanho",
    "revista_capa_com_hash",
    "revista_capa_sha256_sha256",
    "revista_capa_tamanho",
    "revista_fasciculo_fasciculo_f1_f2",
    "revista_hash_validado_sha256",
    "revista_secao_secao_tamanho",
    "revista_svg_f2_com_hash",
    "revista_svg_f2_tamanho",
    "revista_svg_sha256_sha256",
    "template_fasciculo_f1_f2",
    "template_nome_tamanho",
    "template_origem_tamanho",
}
UNIQUES = {
    "componente_ano_codigo_uniq",
    "componente_id_ano_uniq",
    "cor_padrao_ano_padrao_uniq",
    "descritor_mecc_codigo_uniq",
    "etapa_ano_codigo_uniq",
    "etapa_id_ano_uniq",
    "matriz_ano_nome_uniq",
    "matriz_etapa_cc_uniq",
    "matriz_id_ano_uniq",
    "corte_uniq",
    "parceiro_ano_id_ano_uniq",
    "parceiro_ano_parceiro_ano_uniq",
    "projeto_cor_uniq",
    "projeto_id_ano_uniq",
    "projeto_passo_uniq",
    "revista_alvo_uniq",
    "revista_fasciculo_alvo_uniq",
    "revista_fasciculo_uniq",
    "revista_secao_uniq",
    "revista_uniq",
    "template_alvo_uniq",
    "template_nome_uniq",
    "template_versao_alvo_uniq",
    "template_versao_uniq",
}
# UNIQUE parciais viram índice único, não constraint.
UNIQUES_PARCIAIS = {
    "projeto_um_ativo_por_parceiro_ano",
    "bloqueio_matriz_etapa_cc_uniq",
    "bloqueio_projeto_uniq",
    "bloqueio_template_uniq",
}


def constraints(tipo, filtro="true"):
    """Constraints do tipo dado ('f', 'c', 'u') nas tabelas do app nucleo."""
    tabelas = [m._meta.db_table for m in apps.get_app_config("nucleo").get_models()]
    with connection.cursor() as cursor:
        cursor.execute(
            f"""
            SELECT c.conname, pg_get_constraintdef(c.oid)
            FROM pg_constraint c JOIN pg_namespace n ON n.oid = c.connamespace
            JOIN pg_class t ON t.oid = c.conrelid
            WHERE n.nspname = current_schema() AND c.contype = %s AND t.relname = ANY(%s)
              AND {filtro}
            """,
            [tipo, tabelas],
        )
        return dict(cursor.fetchall())


def fks_manuais():
    # O Django só cria FK de uma coluna e NO ACTION; o resto veio de RunSQL.
    return constraints("f", "(cardinality(c.conkey) > 1 OR c.confdeltype <> 'a')")


def indices_ix():
    with connection.cursor() as cursor:
        cursor.execute("SELECT indexname FROM pg_indexes WHERE indexname LIKE 'ix\\_%'")
        return {r[0] for r in cursor.fetchall()}


class CatalogoTest(TestCase):
    def test_fks_manuais(self):
        self.assertEqual(fks_manuais(), FKS_MANUAIS)

    def test_indice_proprio_por_fk_composta(self):
        self.assertEqual(indices_ix(), {"ix_" + n.removeprefix("fk_") for n in FKS_COMPOSTAS})

    def test_checks(self):
        self.assertEqual(set(constraints("c")), CHECKS)

    def test_uniques(self):
        # Inclui também os UNIQUE de coluna única (ano.ano, parceiro.nome), com nome gerado.
        self.assertLessEqual(UNIQUES, set(constraints("u")))
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT indexname FROM pg_indexes WHERE indexname = ANY(%s) "
                "AND indexdef LIKE 'CREATE UNIQUE INDEX%%WHERE%%'",
                [list(UNIQUES_PARCIAIS)],
            )
            self.assertEqual({r[0] for r in cursor.fetchall()}, UNIQUES_PARCIAIS)

    def test_colunas_de_fk_composta_not_null(self):
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT DISTINCT t.relname, a.attname
                FROM pg_constraint c
                JOIN pg_class t ON t.oid = c.conrelid
                JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = ANY(c.conkey)
                WHERE c.conname = ANY(%s) AND NOT a.attnotnull
                """,
                [list(FKS_COMPOSTAS)],
            )
            self.assertEqual(set(cursor.fetchall()), ANULAVEIS)


class RecusaTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.a26 = Ano.objects.create(ano=2026)
        cls.a27 = Ano.objects.create(ano=2027)
        cls.matriz = Matriz.objects.create(ano=cls.a26, nome="Comunitária")
        cls.lp = Componente.objects.create(ano=cls.a26, codigo="LP", nome="Língua Portuguesa")
        cls.e5 = Etapa.objects.create(ano=cls.a26, codigo="5EF", escala_max=500, ordem=2)
        cls.e5_27 = Etapa.objects.create(ano=cls.a27, codigo="5EF", escala_max=500, ordem=2)

    def recusa(self, criar):
        with self.assertRaises(IntegrityError), transaction.atomic():
            criar()

    def test_mec_do_mesmo_ano_passa(self):
        MatrizEtapaCC.objects.create(matriz=self.matriz, etapa=self.e5, componente=self.lp, ano=self.a26)

    def test_mec_com_etapa_de_outro_ano(self):
        self.recusa(lambda: MatrizEtapaCC.objects.create(
            matriz=self.matriz, etapa=self.e5_27, componente=self.lp, ano=self.a26
        ))

    def test_mec_com_ano_diferente_da_matriz(self):
        self.recusa(lambda: MatrizEtapaCC.objects.create(
            matriz=self.matriz, etapa=self.e5_27, componente=self.lp, ano=self.a27
        ))

    def test_mec_com_componente_de_outro_ano(self):
        mt27 = Componente.objects.create(ano=self.a27, codigo="MT", nome="Matemática")
        self.recusa(lambda: MatrizEtapaCC.objects.create(
            matriz=self.matriz, etapa=self.e5, componente=mt27, ano=self.a26
        ))

    def test_cor_fora_do_formato(self):
        for cor in ("#FFF", "FFFFFF", "#GGGGGG", "#FFFFFF0"):
            with self.subTest(cor=cor):
                self.recusa(lambda: CorPadrao.objects.create(ano=self.a26, padrao=1, cor=cor))

    def test_padrao_fora_de_1a5(self):
        CorPadrao.objects.create(ano=self.a26, padrao=5, cor="#FFFFFF")
        for padrao in (0, 6):
            with self.subTest(padrao=padrao):
                self.recusa(lambda: CorPadrao.objects.create(ano=self.a26, padrao=padrao, cor="#AABBCC"))

    def test_matriz_duplicada_de_si_mesma(self):
        self.recusa(lambda: Matriz.objects.filter(pk=self.matriz.pk).update(duplicada_de=self.matriz))

    def test_matriz_duplicada_de_outro_ano_passa(self):
        Matriz.objects.create(ano=self.a27, nome="Comunitária", duplicada_de=self.matriz)

    def test_apagar_origem_anula_duplicada_de_no_banco(self):
        copia = Matriz.objects.create(ano=self.a27, nome="Cópia", duplicada_de=self.matriz)
        with connection.cursor() as cursor:  # SQL direto: sem o SET_NULL do ORM
            cursor.execute("DELETE FROM matriz WHERE id = %s", [self.matriz.pk])
            cursor.execute("SELECT duplicada_de_id FROM matriz WHERE id = %s", [copia.pk])
            self.assertIsNone(cursor.fetchone()[0])


def triggers():
    with connection.cursor() as cursor:
        cursor.execute("SELECT tgname FROM pg_trigger WHERE NOT tgisinternal")
        return {r[0] for r in cursor.fetchall()}


TRIGGERS = {"template_versao_so_insert"}


class ReverseSqlTest(TransactionTestCase):
    """Desfaz e refaz as migrações com RunSQL: prova cada reverse_sql."""

    def test_migrate_ida_e_volta(self):
        call_command("migrate", "nucleo", "0001", verbosity=0)
        self.assertEqual(fks_manuais(), {})
        self.assertEqual(indices_ix(), set())
        self.assertEqual(triggers(), set())
        call_command("migrate", "nucleo", verbosity=0)
        self.assertEqual(triggers(), TRIGGERS)
        self.assertEqual(fks_manuais(), FKS_MANUAIS)
        self.assertEqual(indices_ix(), {"ix_" + n.removeprefix("fk_") for n in FKS_COMPOSTAS})
