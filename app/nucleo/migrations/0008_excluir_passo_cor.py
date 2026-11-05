# S11c (decisão do usuário): Pedagógica, Mídias Digitais e Admin excluem ProjetoPasso e
# ProjetoCor (excluir = voltar ao passo da matriz / à paleta do ano). Impresso não.
# Listas congeladas, como na 0007: migração não importa nucleo.permissoes.
from django.db import migrations

GRUPOS = ("Admin", "Pedagógica", "Mídias Digitais")
PERMISSOES = ("delete_projetopasso", "delete_projetocor")


def _grupos_e_perms(apps):
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    # get() falha alto se a 0007 não criou os grupos ou a permissão não existe.
    perms = [Permission.objects.get(content_type__app_label="nucleo", codename=c) for c in PERMISSOES]
    return [Group.objects.get(name=nome) for nome in GRUPOS], perms


def liberar(apps, schema_editor):
    grupos, perms = _grupos_e_perms(apps)
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
    dependencies = [("nucleo", "0007_perfis")]

    operations = [migrations.RunPython(liberar, recolher)]
