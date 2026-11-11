# D-230: as revistas que já existem ganham os infográficos do F2 (alfa <=> corte no 2EF; outras <=> corte em
# outra etapa). Regra congelada: migração não importa nucleo.servicos. Linhas criadas aqui não têm registro do
# simple-history (o modelo histórico das migrações não dispara o sinal): é aceito.
from django.db import migrations


def criar(apps, schema_editor):
    Revista = apps.get_model("nucleo", "Revista")
    Corte = apps.get_model("nucleo", "Corte")
    RevistaInfografico = apps.get_model("nucleo", "RevistaInfografico")
    for revista in Revista.objects.filter(arquivada_em__isnull=True).select_related("projeto"):
        codigos = {
            c.strip().upper()
            for c in Corte.objects.filter(
                parceiro_ano_id=revista.projeto.parceiro_ano_id, componente_id=revista.componente_id
            ).values_list("etapa__codigo", flat=True)
        }
        tipos = []
        if "2EF" in codigos:
            tipos.append("alfa")
        if codigos - {"2EF"}:
            tipos.append("outras")
        for tipo in tipos:
            RevistaInfografico.objects.get_or_create(
                revista=revista, tipo=tipo,
                defaults={"componente_id": revista.componente_id, "ano_id": revista.ano_id},
            )


class Migration(migrations.Migration):
    dependencies = [("nucleo", "0021_permissoes_infograficos")]

    operations = [migrations.RunPython(criar, migrations.RunPython.noop)]
