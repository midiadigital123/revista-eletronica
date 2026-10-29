from django.db import connection
from django.test import TestCase


class BancoTest(TestCase):
    def test_postgres_17(self):
        with connection.cursor() as cursor:
            cursor.execute("SELECT version()")
            versao = cursor.fetchone()[0]
        self.assertTrue(versao.startswith("PostgreSQL 17"), versao)
