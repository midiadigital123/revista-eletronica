# FKs compostas de ano (D-090, D-124): o ORM não as declara.
from django.db import migrations

from nucleo.db import fk_composta


class Migration(migrations.Migration):
    dependencies = [("nucleo", "0001_initial")]

    operations = [
        fk_composta("matriz_etapa_cc", "matriz"),
        fk_composta("matriz_etapa_cc", "etapa"),
        fk_composta("matriz_etapa_cc", "componente"),
    ]
