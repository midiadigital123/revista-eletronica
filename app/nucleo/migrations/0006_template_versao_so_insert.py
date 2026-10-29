# template_versao é só INSERT (D-115, D-125): o banco recusa UPDATE e DELETE
# vindos de qualquer caminho (QuerySet.update, bulk_update, save com pk, SQL).
# ERRCODE 23001 (restrict_violation) chega ao Django como IntegrityError.
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("nucleo", "0005_fks_compostas_projeto_revista")]

    operations = [
        migrations.RunSQL(
            sql=[
                """
                CREATE FUNCTION template_versao_so_insert() RETURNS trigger
                LANGUAGE plpgsql AS $$
                BEGIN
                    RAISE EXCEPTION 'template_versao_so_insert: % recusado; salve uma versão nova', TG_OP
                        USING ERRCODE = 'restrict_violation';
                END
                $$
                """,
                """
                CREATE TRIGGER template_versao_so_insert
                BEFORE UPDATE OR DELETE ON template_versao
                FOR EACH ROW EXECUTE FUNCTION template_versao_so_insert()
                """,
            ],
            reverse_sql=[
                "DROP TRIGGER template_versao_so_insert ON template_versao",
                "DROP FUNCTION template_versao_so_insert()",
            ],
        ),
    ]
