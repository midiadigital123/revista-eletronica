# D-312: o F2 troca a seção "fechamento" ("Agora é com você") por "fechamento-alfa" e "fechamento-outras"
# (nucleo.texto.SECOES_F2), como a 0031 fez com "tarefas-fechamento". O MT Alfa recebe o texto do Word da
# Pedagógica de 27/11 (com os 2 parágrafos do 3º ano e o link do D-307). Regra congelada: não importa nucleo.texto.
#   1. cada Template F2 cuja versão atual tem "## fechamento" ganha uma TemplateVersao nova (só INSERT, D-207),
#      montada seção por seção a partir da atual (edição feita na tela fica):
#      - MT: "fechamento-alfa" com o texto do Word; "fechamento-outras" com o corpo atual;
#      - outros componentes: as duas com o corpo atual;
#   2. cada cópia (RevistaSecao) "fechamento" do F2 vira as duas novas, com o mesmo texto.
# Sem registro do simple-history (como na 0031). Sem volta: o texto antigo fica na versão anterior.
import re

from django.db import migrations

BLOCO = re.compile(r"^## ([\w-]+)\n(.*?)(?=^## |\Z)", re.S | re.M)
ANTIGA = "fechamento"
NOVAS = ("fechamento-alfa", "fechamento-outras")

FECHAMENTO_MT_ALFA = """Agora é com você

A seguir, apresentamos o template do Infográfico, que poderá ser utilizado para analisar outras habilidades da Matriz de Referência e estabelecer relações com o Referencial Curricular da Rede. O objetivo é aprofundar a compreensão sobre as relações entre **currículo e avaliação externa**, evidenciando como as habilidades previstas no currículo são mobilizadas e avaliadas nos instrumentos apresentados nesta seção.

[**Acesse aqui** o template do Infográfico.](#pendente)

A partir da noção sobre a complexidade pedagógica das tarefas é possível pensar estratégias para a consolidação dessa habilidade. Podemos dizer que os estudantes com menor desempenho são aqueles que conseguem realizar apenas as tarefas muito fáceis, enquanto aqueles com maior desempenho conseguem realizar desde as tarefas muito fáceis até as muito difíceis.

Para auxiliar nesse processo de mitigação das defasagens, apresentamos, a seguir, uma sugestão de prática voltada para os estudantes do 3º ano, com diferentes perfis de aprendizagem. Nessa proposta estão indicados os níveis de complexidade das atividades, de forma que vocês, professores, possam não só utilizá-las em suas salas de aula, mas possam, também, se inspirar para elaborar seus planejamentos.
"""


def por_tipo(texto, mt):
    """Texto do template (com ao menos uma seção) com "fechamento" trocado pelas duas novas; no MT, a Alfa com o
    texto do Word. O que vem antes da 1ª seção (comentário de revisão do seed) fica."""
    saida = texto[: BLOCO.search(texto).start()]
    for m in BLOCO.finditer(texto):
        id_, bloco = m.group(1), m.group(2).strip("\n") + "\n"
        if id_ == ANTIGA:
            saida += f"## {NOVAS[0]}\n{FECHAMENTO_MT_ALFA if mt else bloco}\n## {NOVAS[1]}\n{bloco}\n"
        else:
            saida += f"## {id_}\n{bloco}\n"
    return saida.rstrip("\n") + "\n"


def frente(apps, schema_editor):
    Template = apps.get_model("nucleo", "Template")
    TemplateVersao = apps.get_model("nucleo", "TemplateVersao")
    RevistaSecao = apps.get_model("nucleo", "RevistaSecao")

    for template in Template.objects.filter(fasciculo="F2").select_related("componente"):
        ultima = TemplateVersao.objects.filter(template=template).order_by("-numero").first()
        if ultima is None or f"## {ANTIGA}\n" not in ultima.texto:  # idempotente
            continue
        TemplateVersao.objects.create(
            template=template,
            numero=ultima.numero + 1,
            texto=por_tipo(ultima.texto, template.componente.codigo == "MT"),
        )

    for copia in RevistaSecao.objects.filter(revista_fasciculo__fasciculo="F2", secao=ANTIGA):
        RevistaSecao.objects.create(
            revista_fasciculo_id=copia.revista_fasciculo_id, template_id=copia.template_id, secao=NOVAS[0],
            texto=copia.texto, template_versao_id=copia.template_versao_id,
        )  # fmt: skip
        copia.secao = NOVAS[1]
        copia.save(update_fields=["secao"])


class Migration(migrations.Migration):
    dependencies = [("nucleo", "0033_permissoes_atividades")]

    operations = [migrations.RunPython(frente, migrations.RunPython.noop)]
