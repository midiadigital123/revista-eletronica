# D-240: o texto genérico do template não fala de item; o que é da revista vai na `analise` do item. O 1º parágrafo
# de tarefas-fechamento (seed 2026, igual em LP e MT) fala da tirinha e da charge do D05 de LP, e o impresso passa a
# ler essa seção: sai do seed e das cópias ainda iguais a ele. Regra congelada: migração não importa nucleo.servicos
# nem nucleo.texto, e não lê o seed; o parágrafo exato vai na constante abaixo.
#   1. cada Template F2 cuja versão atual (a de maior número, como na 0023) tem o parágrafo ganha uma TemplateVersao
#      nova (só INSERT, D-207) com o mesmo texto sem ele. O RevistaFasciculo aponta para o Template, não para a
#      versão: a revista passa a ler a versão nova sozinha, como na 0023;
#   2. a cópia tarefas-fechamento de cada revista que tem o parágrafo exato perde o parágrafo; cópia em que o
#      parágrafo foi editado fica como está (o texto é de quem editou). A cópia que saiu da versão substituída
#      passa a apontar para a nova (template_versao): ela já tem a única mudança, e a pendência de seção
#      desatualizada seria ruído. Cópia de versão mais antiga fica apontando para ela: faltam outras mudanças.
#      Revista arquivada fica de fora, de propósito (ao contrário do item 3 da 0023): o texto dela continua válido,
#      só desatualizado, e o arquivamento congela a revista (D-117); ao voltar, ela é revista com a pendência.
# Linhas criadas ou alteradas aqui não têm registro do simple-history (o modelo histórico das migrações não dispara
# o sinal): é aceito, como na 0022 e na 0023. Sem volta: o texto antigo fica na versão anterior; o das cópias se perde.
from django.db import migrations

PARAGRAFO = (
    "Ao analisar conjuntamente os itens apresentados para os diferentes anos de escolaridade, é possível "
    "observar uma progressão na complexidade das tarefas e nas estratégias de leitura mobilizadas. No 2º "
    "ano do Ensino Fundamental, a interpretação da tirinha exige que o estudante relacione falas e "
    "imagens para inferir uma informação sobre o comportamento de um personagem, a partir de uma situação "
    "simples e de pistas bastante evidentes. No 5º ano, a leitura da charge amplia essa exigência, pois "
    "envolve a compreensão de uma crítica construída por meio de recursos visuais e de conhecimentos "
    "prévios. No 9º ano, a interpretação da tirinha demanda uma compreensão mais global da narrativa, "
    "articulando diálogos e elementos visuais para inferir o comportamento das personagens. Já na 3ª "
    "série do Ensino Médio, espera-se que o estudante mobilize estratégias de leitura mais autônomas e "
    "sofisticadas, acompanhando a progressão narrativa e relacionando diferentes elementos verbais e não "
    "verbais para identificar as intenções do personagem."
)
RETIRAR = PARAGRAFO + "\n\n"  # o parágrafo e a linha em branco que sobra


def frente(apps, schema_editor):
    Template = apps.get_model("nucleo", "Template")
    TemplateVersao = apps.get_model("nucleo", "TemplateVersao")
    RevistaSecao = apps.get_model("nucleo", "RevistaSecao")

    trocadas = {}  # pk da versão substituída -> versão nova
    for template in Template.objects.filter(fasciculo="F2"):
        ultima = TemplateVersao.objects.filter(template=template).order_by("-numero").first()
        if ultima is not None and RETIRAR in ultima.texto:  # idempotente: a versão nova não tem o parágrafo
            trocadas[ultima.pk] = TemplateVersao.objects.create(
                template=template, numero=ultima.numero + 1, texto=ultima.texto.replace(RETIRAR, "")
            )

    copias = RevistaSecao.objects.filter(
        revista_fasciculo__fasciculo="F2",
        revista_fasciculo__revista__arquivada_em__isnull=True,
        secao="tarefas-fechamento",
        texto__contains=RETIRAR,
    )
    for copia in copias:
        copia.texto = copia.texto.replace(RETIRAR, "")
        campos = ["texto"]
        if copia.template_versao_id in trocadas:  # já tem a única mudança da versão nova: não fica desatualizada
            copia.template_versao = trocadas[copia.template_versao_id]
            campos.append("template_versao")
        copia.save(update_fields=campos)


class Migration(migrations.Migration):
    dependencies = [("nucleo", "0024_revista_sem_svg")]

    operations = [migrations.RunPython(frente, migrations.RunPython.noop)]
