from django.apps import apps
from django.contrib.auth.models import Group, Permission, User
from django.core.management import call_command
from django.test import TestCase, TransactionTestCase

from nucleo.permissoes import ADMIN_MARCA_IMPRESSA, MODELOS_NUCLEO, PAPEIS, permissoes
from nucleo.tests.test_resolver import usuario

CUSTOMIZADAS = ("abrir_ano", "validar_revista", "marcar_impressa")


def perms_do_grupo(nome):
    return {
        f"{app}.{codename}"
        for app, codename in Group.objects.get(name=nome).permissions.values_list(
            "content_type__app_label", "codename"
        )
    }


class GruposNoBancoTest(TestCase):
    """A migração 0007 (cópia congelada) bate com nucleo.permissoes."""

    def test_grupos_iguais_a_tabela(self):
        for papel in PAPEIS:
            with self.subTest(papel=papel):
                self.assertEqual(perms_do_grupo(papel), permissoes(papel))

    def test_modelos_nucleo_completo(self):
        registrados = {
            m._meta.model_name
            for m in apps.get_app_config("nucleo").get_models()
            if not m._meta.model_name.startswith("historical")
        }
        self.assertEqual(set(MODELOS_NUCLEO), registrados)

    def test_so_apaga_passo_cor_tarefa_e_descritor(self):
        """ProjetoPasso e ProjetoCor (0008), Tarefa e Descritor (D-181, 0014); Impresso nada."""
        so_esses = {
            "nucleo.delete_projetopasso", "nucleo.delete_projetocor",
            "nucleo.delete_tarefa", "nucleo.delete_descritor",
        }  # fmt: skip
        for papel in PAPEIS:
            with self.subTest(papel=papel):
                apaga = {p for p in permissoes(papel) if ".delete_" in p}
                self.assertEqual(apaga, set() if papel == "Impresso" else so_esses)


class PerfilTest(TestCase):
    def confere(self, papel, pode, nao_pode):
        user = usuario(papel, papel)
        for perm in pode:
            self.assertTrue(user.has_perm(perm), f"{papel} deveria ter {perm}")
        for perm in nao_pode:
            self.assertFalse(user.has_perm(perm), f"{papel} não deveria ter {perm}")

    PEDAGOGICA_PODE = (
        "nucleo.validar_revista", "nucleo.abrir_ano", "nucleo.change_matriz", "nucleo.add_matriz",
        "nucleo.change_corte", "nucleo.change_template", "nucleo.add_templateversao",
        "nucleo.change_corpadrao", "nucleo.change_projeto", "nucleo.change_revista",
        "nucleo.delete_projetopasso", "nucleo.delete_projetocor",
        "nucleo.delete_tarefa", "nucleo.delete_descritor",
    )  # fmt: skip
    PEDAGOGICA_NAO = (
        "nucleo.marcar_impressa", "auth.change_user", "auth.add_group",
        "nucleo.change_templateversao", "nucleo.add_ano", "nucleo.add_fotorevista",
        "nucleo.delete_revista", "nucleo.add_revista", "nucleo.delete_matrizetapacc",
        "nucleo.delete_matriz", "nucleo.delete_projeto",
    )  # fmt: skip

    def test_admin(self):
        impressa = ("nucleo.marcar_impressa",)
        self.confere(
            "Admin",
            pode=(
                *self.PEDAGOGICA_PODE, "auth.change_user", "auth.add_user", "auth.view_group",
                *(impressa if ADMIN_MARCA_IMPRESSA else ()),
            ),
            nao_pode=(
                "nucleo.change_templateversao", "nucleo.delete_revista",
                "auth.delete_user", "auth.add_group", "auth.change_group", "auth.delete_group",
                *(() if ADMIN_MARCA_IMPRESSA else impressa),
            ),
        )  # fmt: skip

    def test_pedagogica(self):
        self.confere("Pedagógica", self.PEDAGOGICA_PODE, self.PEDAGOGICA_NAO)

    def test_midias_digitais(self):
        self.confere("Mídias Digitais", self.PEDAGOGICA_PODE, self.PEDAGOGICA_NAO)

    def test_impresso(self):
        self.confere(
            "Impresso",
            pode=("nucleo.marcar_impressa", "nucleo.view_revista", "nucleo.view_matriz", "nucleo.view_projeto"),
            nao_pode=(
                "nucleo.validar_revista", "nucleo.abrir_ano", "nucleo.change_matriz",
                "nucleo.change_revista", "auth.change_user",
                "nucleo.delete_projetopasso", "nucleo.delete_projetocor",
                "nucleo.delete_tarefa", "nucleo.delete_descritor",
            ),
        )  # fmt: skip


def recriar_grupos():
    """Ida e volta pela 0007: recria os grupos que o flush de outro
    TransactionTestCase apagou. (serialized_rollback quebra com content type
    duplicado no setUp.)"""
    call_command("migrate", "nucleo", "0006", verbosity=0)
    call_command("migrate", "nucleo", verbosity=0)


class ReversaoTest(TransactionTestCase):
    def setUp(self):
        recriar_grupos()

    @classmethod
    def tearDownClass(cls):
        recriar_grupos()  # deixa o banco com grupos para quem rodar depois
        super().tearDownClass()

    def test_volta_para_0006_e_reaplica(self):
        user = User.objects.create_user("pessoa")
        user.groups.add(Group.objects.get(name="Pedagógica"))

        call_command("migrate", "nucleo", "0006", verbosity=0)
        self.assertFalse(Permission.objects.filter(codename__in=CUSTOMIZADAS).exists())
        self.assertTrue(user.groups.filter(name="Pedagógica").exists())  # grupo e vínculo ficam

        call_command("migrate", "nucleo", verbosity=0)
        for papel in PAPEIS:
            self.assertEqual(perms_do_grupo(papel), permissoes(papel))
        self.assertTrue(User.objects.get(pk=user.pk).has_perm("nucleo.validar_revista"))
