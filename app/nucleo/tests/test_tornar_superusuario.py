"""tornar_superusuario (D-219): promove quem existe; um nome errado e nada muda."""
from io import StringIO

from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase


class TornarSuperusuarioTest(TestCase):
    def rodar(self, *nomes):
        saida = StringIO()
        call_command("tornar_superusuario", *nomes, stdout=saida)
        return saida.getvalue()

    def test_promove_e_recusa_nome_errado_sem_mudar_nada(self):
        ana = User.objects.create_user("ana")
        bia = User.objects.create_user("bia", is_active=False)
        with self.assertRaisesMessage(CommandError, "usuário não encontrado: nao-existe"):
            self.rodar("ana", "nao-existe")
        ana.refresh_from_db()
        self.assertFalse(ana.is_superuser)

        saida = self.rodar("ana", "bia")
        self.assertIn("agora é superusuário: ana", saida)
        self.assertIn("agora é superusuário: bia (está desativado", saida)
        for u in (ana, bia):
            u.refresh_from_db()
            self.assertTrue(u.is_superuser and u.is_staff)
        self.assertIn("já era superusuário: ana", self.rodar("ana"))
