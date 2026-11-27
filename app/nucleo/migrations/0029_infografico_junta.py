# D-301: a mescla do referencial do F2 fica explícita (junta_marca, junta_habilidade). Antes, código e texto
# vazios estendiam a célula de cima (servicos/f2.py::_tabela até a D-300). Para o desenho atual não mudar, a
# linha que hoje se estende ganha junta_habilidade=True; a etapa não gravada que se estende é criada. A
# Pedagógica desliga onde a mescla era falsa. Regra congelada (não importa nucleo). Sem registro do
# simple-history (como na 0028). Sem volta: o RunPython reverso não faz nada (os campos saem junto).
from django.db import migrations, models

ETAPAS = ["1EF", "2EF", "3EF", "4EF", "5EF", "6EF", "7EF", "8EF", "9EF", "1EM", "2EM", "3EM"]


def juntas(linhas):
    """Etapas que hoje se estendem: `linhas` é {etapa: (codigo, texto)} só das gravadas."""
    saida, acima_tem = [], False
    for etapa in ETAPAS:
        codigo, texto = linhas.get(etapa, ("", ""))
        if codigo or texto:
            acima_tem = True
        elif acima_tem:
            saida.append(etapa)
    return saida


def frente(apps, schema_editor):
    Infografico = apps.get_model("nucleo", "RevistaInfografico")
    Etapa = apps.get_model("nucleo", "RevistaInfograficoEtapa")
    for inf in Infografico.objects.all():
        gravadas = {e.etapa: e for e in Etapa.objects.filter(infografico=inf)}
        for etapa in juntas({k: (e.codigo, e.texto) for k, e in gravadas.items()}):
            e = gravadas.get(etapa) or Etapa(infografico=inf, ano_id=inf.ano_id, etapa=etapa)
            e.junta_habilidade = True
            e.save()


class Migration(migrations.Migration):
    dependencies = [("nucleo", "0028_f1_sem_fechamento")]

    operations = [
        migrations.AddField(
            model_name="historicalrevistainfograficoetapa",
            name="junta_habilidade",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="historicalrevistainfograficoetapa",
            name="junta_marca",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="revistainfograficoetapa",
            name="junta_habilidade",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="revistainfograficoetapa",
            name="junta_marca",
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(frente, migrations.RunPython.noop),
    ]
