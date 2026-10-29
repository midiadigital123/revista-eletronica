from django.apps import apps
from django.db import IntegrityError, connection, transaction
from django.test import TestCase

from nucleo.models import Ano, Componente, CorPadrao, Etapa, Matriz, MatrizEtapaCC

# Atualize junto com cada migração que criar FK composta, CHECK ou UNIQUE (D-124).
FKS_COMPOSTAS = {
    "fk_matriz_etapa_cc_matriz_ano": "FOREIGN KEY (matriz_id, ano_id) REFERENCES matriz(id, ano_id)",
    "fk_matriz_etapa_cc_etapa_ano": "FOREIGN KEY (etapa_id, ano_id) REFERENCES etapa(id, ano_id)",
    "fk_matriz_etapa_cc_componente_ano": "FOREIGN KEY (componente_id, ano_id) REFERENCES componente(id, ano_id)",
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
}


def constraints(tipo):
    """Constraints do tipo dado ('f', 'c', 'u') nas tabelas do app nucleo."""
    tabelas = [m._meta.db_table for m in apps.get_app_config("nucleo").get_models()]
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT c.conname, pg_get_constraintdef(c.oid)
            FROM pg_constraint c JOIN pg_namespace n ON n.oid = c.connamespace
            JOIN pg_class t ON t.oid = c.conrelid
            WHERE n.nspname = current_schema() AND c.contype = %s AND t.relname = ANY(%s)
            """,
            [tipo, tabelas],
        )
        return dict(cursor.fetchall())


class CatalogoTest(TestCase):
    def test_fks_compostas(self):
        fks = {k: v for k, v in constraints("f").items() if k.startswith("fk_")}
        self.assertEqual(fks, FKS_COMPOSTAS)

    def test_indice_proprio_por_fk_composta(self):
        with connection.cursor() as cursor:
            cursor.execute("SELECT indexname FROM pg_indexes WHERE indexname LIKE 'ix\\_%'")
            indices = {r[0] for r in cursor.fetchall()}
        self.assertEqual(indices, {"ix_" + n.removeprefix("fk_") for n in FKS_COMPOSTAS})

    def test_checks(self):
        self.assertEqual(set(constraints("c")), CHECKS)

    def test_uniques(self):
        # Inclui também os UNIQUE de coluna única (ano.ano, parceiro.nome), com nome gerado.
        self.assertLessEqual(UNIQUES, set(constraints("u")))


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
