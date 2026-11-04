# D-208: parceiro desativado (nulo = ativo), com histórico. Data, não boolean: diz desde quando.
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("nucleo", "0017_versao_apagavel")]

    operations = [
        migrations.AddField(
            model_name="historicalparceiro",
            name="desativado_em",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="parceiro",
            name="desativado_em",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
