# D-233: permissões dos infográficos do F2. Pedagógica, Mídias Digitais e Admin: change/view do infográfico
# (nasce pela cascata) e add/change/view de etapa e item; Impresso só vê. Listas congeladas, como na 0016:
# migração não importa nucleo.permissoes.
from django.contrib.auth.management import create_permissions
from django.db import migrations

VER = ("view_revistainfografico", "view_revistainfograficoetapa", "view_revistainfograficoitem")
EDITA = (
    "change_revistainfografico", "add_revistainfograficoetapa", "change_revistainfograficoetapa",
    "add_revistainfograficoitem", "change_revistainfograficoitem",
)  # fmt: skip
POR_GRUPO = {"Admin": (*VER, *EDITA), "Pedagógica": (*VER, *EDITA), "Mídias Digitais": (*VER, *EDITA), "Impresso": VER}


def _permissoes(apps, codenames):
    Permission = apps.get_model("auth", "Permission")
    return Permission.objects.filter(content_type__app_label="nucleo", codename__in=codenames)


def liberar(apps, schema_editor):
    # Em banco novo, as permissões dos modelos novos só nasceriam no post_migrate: cria agora (como a 0007).
    config = apps.get_app_config("nucleo")
    config.models_module = True  # o stub da migração vem sem; create_permissions exige
    try:
        create_permissions(config, apps=apps, verbosity=0, using=schema_editor.connection.alias)
    finally:
        config.models_module = None

    Group = apps.get_model("auth", "Group")
    grupos = {g.name: g for g in Group.objects.filter(name__in=POR_GRUPO)}
    if not grupos:
        return  # banco sem os dados da 0007 (flush de TransactionTestCase): não há o que liberar
    if len(grupos) != len(POR_GRUPO):
        raise RuntimeError(f"Grupos da 0007 incompletos: {sorted(grupos)}")
    for nome, codenames in POR_GRUPO.items():
        perms = list(_permissoes(apps, codenames))
        if len(perms) != len(codenames):  # falha alto: tabela e modelos fora de sincronia
            raise RuntimeError(f"Permissões de infográfico faltando para {nome}")
        grupos[nome].permissions.add(*perms)


def recolher(apps, schema_editor):
    for grupo in apps.get_model("auth", "Group").objects.filter(name__in=POR_GRUPO):
        grupo.permissions.remove(*_permissoes(apps, POR_GRUPO[grupo.name]))


class Migration(migrations.Migration):
    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("contenttypes", "0002_remove_content_type_name"),
        ("nucleo", "0020_infograficos"),
    ]

    operations = [migrations.RunPython(liberar, recolher)]
