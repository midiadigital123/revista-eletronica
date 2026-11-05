# D-181: Pedagógica, Mídias Digitais e Admin excluem Tarefa e Descritor (só pela tela de
# confirmação forte do admin). Impresso não. Listas congeladas, como na 0007/0008:
# migração não importa nucleo.permissoes.
from django.db import migrations

GRUPOS = ("Admin", "Pedagógica", "Mídias Digitais")
PERMISSOES = ("delete_tarefa", "delete_descritor")


def liberar(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    grupos = list(Group.objects.filter(name__in=GRUPOS))
    if not grupos:
        # Banco sem os dados da 0007 (o flush de um TransactionTestCase apaga grupos e
        # permissões e o teste migra de novo a partir da 0009): não há o que liberar.
        return
    # Com os grupos, falha alto se faltar um deles ou a permissão (tabela fora de sincronia).
    if len(grupos) != len(GRUPOS):
        raise RuntimeError(f"Grupos da 0007 incompletos: {sorted(g.name for g in grupos)}")
    perms = [Permission.objects.get(content_type__app_label="nucleo", codename=c) for c in PERMISSOES]
    for grupo in grupos:
        grupo.permissions.add(*perms)


def recolher(apps, schema_editor):
    # Tolerante: sem os grupos (banco esvaziado) não há o que tirar.
    perms = apps.get_model("auth", "Permission").objects.filter(
        content_type__app_label="nucleo", codename__in=PERMISSOES
    )
    for grupo in apps.get_model("auth", "Group").objects.filter(name__in=GRUPOS):
        grupo.permissions.remove(*perms)


class Migration(migrations.Migration):
    dependencies = [("nucleo", "0013_tarefa_texto_alternativo")]

    operations = [migrations.RunPython(liberar, recolher)]
