"""criar_usuarios (S17): CSV usuario,grupo → usuário sem senha + link do Django para definir."""
import re
import tempfile
from io import StringIO
from pathlib import Path

from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase


class CriarUsuariosTest(TestCase):
    def rodar(self, conteudo):
        with tempfile.TemporaryDirectory() as pasta:
            arquivo = Path(pasta) / "u.csv"
            arquivo.write_text(conteudo, encoding="utf-8")
            saida = StringIO()
            call_command("criar_usuarios", str(arquivo), url="http://testserver/", stdout=saida)
        return saida.getvalue()

    def test_cria_sem_senha_e_o_link_define_a_senha(self):
        saida = self.rodar("usuario,grupo\nped1,Pedagógica\nimp1,Impresso\n")
        ped = User.objects.get(username="ped1")
        self.assertFalse(ped.has_usable_password())
        self.assertTrue(ped.is_staff)
        self.assertFalse(ped.is_superuser)
        self.assertEqual(list(ped.groups.values_list("name", flat=True)), ["Pedagógica"])
        link = re.search(r"ped1 http://testserver(/\S+)", saida)[1]

        r = self.client.get(link, follow=True)  # o Django troca o token por um da sessão
        self.assertEqual(r.status_code, 200)
        r = self.client.post(r.redirect_chain[-1][0], {"new_password1": "Xq9!senha-longa", "new_password2": "Xq9!senha-longa"})
        self.assertRedirects(r, "/conta/senha/pronto/")
        ped.refresh_from_db()
        self.assertTrue(ped.check_password("Xq9!senha-longa"))
        self.assertEqual(self.client.get(link, follow=True).context["validlink"], False)  # link usado não vale mais

        self.assertIn("já existe, mantido: ped1", self.rodar("usuario,grupo\nped1,Admin\n"))
        self.assertFalse(ped.groups.filter(name="Admin").exists())

    def test_linha_invalida_nao_cria_nada(self):
        with self.assertRaisesMessage(CommandError, "x: grupo 'Chefe'"):
            self.rodar("usuario,grupo\nok,Pedagógica\nx,Chefe\n")
        self.assertFalse(User.objects.exists())
