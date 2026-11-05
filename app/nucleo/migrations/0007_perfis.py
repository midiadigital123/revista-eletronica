# Perfis e permissões (S14; D-073, D-079, D-083, D-102).
# As listas abaixo são uma cópia congelada de nucleo.permissoes (migração não
# importa código que muda depois). Mudou a tabela? Migração nova.
# Nenhum usuário é criado aqui: só grupos e permissões.
from django.contrib.auth.management import create_permissions
from django.db import migrations

PEDAGOGICA = """
nucleo.abrir_ano nucleo.add_componente nucleo.add_corpadrao nucleo.add_corte
nucleo.add_descritor nucleo.add_etapa nucleo.add_matriz nucleo.add_matrizetapacc
nucleo.add_parceiro nucleo.add_parceiroano nucleo.add_projeto nucleo.add_projetocor
nucleo.add_projetopasso nucleo.add_revistasecao nucleo.add_tarefa nucleo.add_template
nucleo.add_templateversao nucleo.change_componente nucleo.change_corpadrao nucleo.change_corte
nucleo.change_descritor nucleo.change_etapa nucleo.change_matriz nucleo.change_matrizetapacc
nucleo.change_parceiro nucleo.change_parceiroano nucleo.change_projeto nucleo.change_projetocor
nucleo.change_projetopasso nucleo.change_revista nucleo.change_revistafasciculo
nucleo.change_revistasecao nucleo.change_tarefa nucleo.change_template nucleo.validar_revista
nucleo.view_ano nucleo.view_bloqueio nucleo.view_componente nucleo.view_corpadrao
nucleo.view_corte nucleo.view_descritor nucleo.view_etapa nucleo.view_fotorevista
nucleo.view_matriz nucleo.view_matrizetapacc nucleo.view_parceiro nucleo.view_parceiroano
nucleo.view_projeto nucleo.view_projetocor nucleo.view_projetopasso nucleo.view_revista
nucleo.view_revistafasciculo nucleo.view_revistasecao nucleo.view_tarefa nucleo.view_template
nucleo.view_templateversao
""".split()

# Grupos são fixos (só view_group); usuário se desativa, não se apaga.
USUARIOS = """
auth.add_user auth.change_user auth.view_group auth.view_user
""".split()

IMPRESSO = """
nucleo.marcar_impressa nucleo.view_ano nucleo.view_bloqueio nucleo.view_componente
nucleo.view_corpadrao nucleo.view_corte nucleo.view_descritor nucleo.view_etapa
nucleo.view_fotorevista nucleo.view_matriz nucleo.view_matrizetapacc nucleo.view_parceiro
nucleo.view_parceiroano nucleo.view_projeto nucleo.view_projetocor nucleo.view_projetopasso
nucleo.view_revista nucleo.view_revistafasciculo nucleo.view_revistasecao nucleo.view_tarefa
nucleo.view_template nucleo.view_templateversao
""".split()

GRUPOS = {
    "Admin": PEDAGOGICA + USUARIOS,  # admin não marca impressa (pergunta em aberto)
    "Pedagógica": PEDAGOGICA,
    "Mídias Digitais": PEDAGOGICA,
    "Impresso": IMPRESSO,
}

CUSTOMIZADAS = ("abrir_ano", "validar_revista", "marcar_impressa")


def criar_grupos(apps, schema_editor):
    # Em banco novo, add_*/change_*… só nasceriam no post_migrate: cria agora.
    for label in ("auth", "nucleo"):
        config = apps.get_app_config(label)
        config.models_module = True  # o stub da migração vem sem; create_permissions exige
        try:
            create_permissions(config, apps=apps, verbosity=0, using=schema_editor.connection.alias)
        finally:
            config.models_module = None

    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    for nome, perms in GRUPOS.items():
        objetos = []
        for perm in perms:
            app_label, codename = perm.split(".")
            # get() falha alto se a permissão não existir: tabela e modelos fora de sincronia.
            objetos.append(Permission.objects.get(content_type__app_label=app_label, codename=codename))
        grupo, _ = Group.objects.get_or_create(name=nome)  # reaplicar reusa o grupo
        grupo.permissions.set(objetos)


def remover_customizadas(apps, schema_editor):
    # Os grupos ficam: apagá-los levaria junto auth_user_groups (quem é de qual
    # perfil). Reaplicar a 0007 reusa os grupos e regrava as permissões.
    apps.get_model("auth", "Permission").objects.filter(
        content_type__app_label="nucleo", codename__in=CUSTOMIZADAS
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("contenttypes", "0002_remove_content_type_name"),
        ("nucleo", "0006_template_versao_so_insert"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="ano",
            options={"permissions": [("abrir_ano", "Pode abrir ano novo")]},
        ),
        migrations.AlterModelOptions(
            name="revista",
            options={
                "permissions": [
                    ("validar_revista", "Pode clicar em Validado"),
                    ("marcar_impressa", "Pode clicar em Revista Impressa Atualizada"),
                ]
            },
        ),
        migrations.RunPython(criar_grupos, remover_customizadas),
    ]
