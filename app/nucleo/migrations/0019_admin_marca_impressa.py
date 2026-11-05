# D-220: o Admin marca "Revista Impressa Atualizada" (ADMIN_MARCA_IMPRESSA = True) e atribui o grupo
# Impresso. Lista congelada, como na 0016: migração não importa nucleo.permissoes.
from django.db import migrations

CODENAME = "marcar_impressa"


def _grupo_e_perm(apps):
    grupo = apps.get_model("auth", "Group").objects.filter(name="Admin").first()
    perm = apps.get_model("auth", "Permission").objects.filter(content_type__app_label="nucleo", codename=CODENAME).first()
    return grupo, perm


def liberar(apps, schema_editor):
    grupo, perm = _grupo_e_perm(apps)
    if grupo is None:
        return  # banco sem os dados da 0007 (flush de TransactionTestCase): não há o que liberar
    if perm is None:
        raise RuntimeError(f"Permissão nucleo.{CODENAME} não existe (0007 incompleta?)")
    grupo.permissions.add(perm)


def recolher(apps, schema_editor):
    grupo, perm = _grupo_e_perm(apps)
    if grupo is not None and perm is not None:
        grupo.permissions.remove(perm)


class Migration(migrations.Migration):
    dependencies = [("nucleo", "0018_parceiro_desativado_em")]

    operations = [migrations.RunPython(liberar, recolher)]
