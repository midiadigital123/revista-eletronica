# D-205/D-206/D-207: Pedagógica, Mídias Digitais e Admin excluem parceiro, etapa, componente, matriz e
# template sem uso; só o Admin apaga o ano inteiro. Impresso nada. Listas congeladas, como na 0014:
# migração não importa nucleo.permissoes.
from django.db import migrations

SEM_USO = ("delete_parceiro", "delete_etapa", "delete_componente", "delete_matriz", "delete_template")
POR_GRUPO = {"Admin": (*SEM_USO, "delete_ano"), "Pedagógica": SEM_USO, "Mídias Digitais": SEM_USO}


def liberar(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    grupos = {g.name: g for g in Group.objects.filter(name__in=POR_GRUPO)}
    if not grupos:
        return  # banco sem os dados da 0007 (flush de TransactionTestCase): não há o que liberar
    if len(grupos) != len(POR_GRUPO):
        raise RuntimeError(f"Grupos da 0007 incompletos: {sorted(grupos)}")
    for nome, codenames in POR_GRUPO.items():
        grupos[nome].permissions.add(
            *(Permission.objects.get(content_type__app_label="nucleo", codename=c) for c in codenames)
        )


def recolher(apps, schema_editor):
    Permission = apps.get_model("auth", "Permission")
    for grupo in apps.get_model("auth", "Group").objects.filter(name__in=POR_GRUPO):
        grupo.permissions.remove(
            *Permission.objects.filter(content_type__app_label="nucleo", codename__in=POR_GRUPO[grupo.name])
        )


class Migration(migrations.Migration):
    dependencies = [("nucleo", "0015_etapa_ordem_escolar")]

    operations = [migrations.RunPython(liberar, recolher)]
