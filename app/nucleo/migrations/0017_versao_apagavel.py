# D-206, D-207: a versão de template continua só INSERT (D-125), com uma exceção: o DELETE passa quando a
# transação ligou `SET LOCAL revista.apagar_versoes = 'on'`. Só `servicos.exclusao` liga a chave (template
# sem uso e ano inteiro). UPDATE segue recusado sempre. O reverse volta a função da 0006.
from django.db import migrations

ANTIGA = """
CREATE OR REPLACE FUNCTION template_versao_so_insert() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'template_versao_so_insert: % recusado; salve uma versão nova', TG_OP
        USING ERRCODE = 'restrict_violation';
END
$$
"""

NOVA = """
CREATE OR REPLACE FUNCTION template_versao_so_insert() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP = 'DELETE' AND current_setting('revista.apagar_versoes', true) = 'on' THEN
        RETURN OLD;
    END IF;
    RAISE EXCEPTION 'template_versao_so_insert: % recusado; salve uma versão nova', TG_OP
        USING ERRCODE = 'restrict_violation';
END
$$
"""


class Migration(migrations.Migration):
    dependencies = [("nucleo", "0016_excluir_sem_uso")]

    operations = [migrations.RunSQL(sql=NOVA, reverse_sql=ANTIGA)]
