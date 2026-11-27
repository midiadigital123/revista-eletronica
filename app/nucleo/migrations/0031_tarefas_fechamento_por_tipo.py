# D-306: o F2 troca a seção "tarefas-fechamento" por "tarefas-fechamento-alfa" e "tarefas-fechamento-outras"
# (nucleo.texto.SECOES_F2), e o LP recebe os textos novos dos Word da Pedagógica de 27/11 (com o link do D-307).
# Regra congelada, como na 0028: não importa nucleo.texto nem lê o seed.
#   1. cada Template F2 cuja versão atual tem "## tarefas-fechamento" ganha uma TemplateVersao nova (só INSERT,
#      D-207), montada seção por seção a partir da atual (edição feita na tela fica):
#      - LP: as duas seções novas com os textos de cada Word, e o "fechamento" novo;
#      - outros componentes: as duas seções com o corpo atual de "tarefas-fechamento"; o "fechamento" fica;
#   2. cada cópia (RevistaSecao) "tarefas-fechamento" vira as duas novas, com o mesmo texto.
# Sem registro do simple-history (como na 0022, 0023, 0025 e 0028). Sem volta: o texto antigo fica na versão
# anterior.
import re

from django.db import migrations

BLOCO = re.compile(r"^## ([\w-]+)\n(.*?)(?=^## |\Z)", re.S | re.M)
ANTIGA = "tarefas-fechamento"
NOVAS = ("tarefas-fechamento-alfa", "tarefas-fechamento-outras")

TAREFAS_LP_ALFA = """Ao analisar todos os itens apresentados para os diferentes anos de escolaridade, é possível observar uma progressão na forma como a habilidade é mobilizada. No 2º ano do Ensino Fundamental, a habilidade é trabalhada a partir de um convite de aniversário, gênero bastante próximo do universo infantil e cuja finalidade é concreta e facilmente relacionada à situação comunicativa. No 5º ano, o suporte é um cartaz de campanha de vacinação canina, ampliando-se a diversidade dos contextos sociais e exigindo que o estudante relacione as informações do texto à divulgação de uma ação destinada a determinado público.

No 9º ano, o item apresenta um rótulo de produto, levando o estudante a identificar uma finalidade em um gênero que circula em uma situação de consumo e que pode estar associado a diferentes ações comunicativas. Nesse caso, além de reconhecer o caráter informativo do texto, é necessário distingui-lo de uma finalidade próxima, como vender um produto. Já na 3ª série do Ensino Médio, a tarefa é apresentada por meio de um texto de curiosidade e de um conjunto de alternativas que mobilizam finalidades discursivas mais amplas, como informar, opinar, narrar, orientar e persuadir, demandando do estudante uma compreensão mais refinada da função predominante do texto.

Essa progressão evidencia que a habilidade permanece a mesma, mas se modifica o nível de complexidade das tarefas por meio das quais ela é avaliada. Ao longo da escolarização, ampliam-se os gêneros e os contextos de circulação mobilizados, tornam-se mais diversificadas as finalidades colocadas em contraste e aumenta a necessidade de que o estudante articule diferentes elementos para construir sua resposta. Assim, o desenvolvimento da habilidade não significa apenas reconhecer, de maneira cada vez mais automática, “para que serve” um texto, mas avançar na capacidade de compreender como, por que, para quem e em que contexto os textos são produzidos e circulam.

A manutenção da habilidade ao longo da escolarização é acompanhada pela complexificação dos textos, dos contextos de circulação e das relações que o estudante precisa estabelecer para identificar sua finalidade. Essa perspectiva é fundamental para compreender a progressão das aprendizagens: espera-se que, à medida que avança na escolarização, o estudante mobilize conhecimentos e estratégias cada vez mais sofisticados para compreender os textos que circulam socialmente e os propósitos que orientam sua produção.
"""

TAREFAS_LP_OUTRAS = """Ao analisar conjuntamente os itens apresentados para os diferentes anos de escolaridade, é possível observar uma progressão na complexidade das tarefas e nas estratégias de leitura mobilizadas. No 2º ano do Ensino Fundamental, a interpretação da tirinha exige que o estudante relacione falas e imagens para inferir uma informação sobre o comportamento de um personagem, a partir de uma situação simples e de pistas bastante evidentes. No 5º ano, a leitura da charge amplia essa exigência, pois envolve a compreensão de uma crítica construída por meio de recursos visuais e de conhecimentos prévios. No 9º ano, a interpretação da tirinha demanda uma compreensão mais global da narrativa, articulando diálogos e elementos visuais para inferir o comportamento das personagens. Já na 3ª série do Ensino Médio, espera-se que o estudante mobilize estratégias de leitura mais autônomas e sofisticadas, acompanhando a progressão narrativa e relacionando diferentes elementos verbais e não verbais para identificar as intenções do personagem.

Essa trajetória evidencia que o desenvolvimento da habilidade não se limita à ampliação da diversidade de textos e suportes, mas envolve o aprofundamento das operações de leitura necessárias à construção dos sentidos. Ao longo da escolarização, os estudantes avançam da identificação de relações mais diretas entre imagens e informações verbais para a interpretação de sentidos implícitos, críticas, intenções e efeitos produzidos pela articulação entre diferentes linguagens. Essa progressão é fundamental para orientar o planejamento pedagógico, pois permite compreender que a formação de leitores proficientes exige experiências de leitura cada vez mais desafiadoras, que favoreçam a mobilização integrada de conhecimentos linguísticos, visuais e contextuais. Desse modo, o trabalho sistemático com textos multissemióticos contribui para a formação de leitores capazes de interpretar, analisar e construir sentidos de maneira crítica e autônoma em diferentes situações comunicativas.
"""

FECHAMENTO_LP = """Agora é com você

A seguir, apresentamos o template do Infográfico, que poderá ser utilizado para analisar outras habilidades da Matriz de Referência e estabelecer relações com o Referencial Curricular da Rede. O objetivo é aprofundar a compreensão sobre as relações entre **currículo e avaliação externa**, evidenciando como as habilidades previstas no currículo são mobilizadas e avaliadas nos instrumentos apresentados nesta seção.

[**Acesse aqui** o template do Infográfico.](#pendente)

A compreensão dos diferentes níveis de complexidade pedagógica das tarefas permite pensar em estratégias que favoreçam o desenvolvimento e a consolidação da habilidade ao longo do processo de aprendizagem. Nesse sentido, estudantes que apresentam menor desempenho tendem a demonstrar domínio de tarefas de menor complexidade, enquanto aqueles que apresentam níveis mais elevados de desempenho conseguem mobilizar seus conhecimentos e estratégias diante de tarefas que envolvem diferentes graus de complexidade, incluindo as mais desafiadoras.

Considerando essa perspectiva e com o objetivo de contribuir para a superação de possíveis defasagens de aprendizagem, apresentamos, a seguir, atividades que podem ser desenvolvidas com grupos de estudantes que se encontram em diferentes padrões de desempenho. A proposta contempla atividades organizadas segundo seus diferentes níveis de complexidade, permitindo ao professor adequá-las às necessidades de aprendizagem de seus estudantes.
"""


def por_tipo(texto, lp):
    """Texto do template (com ao menos uma seção) com a antiga trocada pelas duas novas e, no LP, os textos novos.
    O que vem antes da 1ª seção (comentário de revisão do seed) fica."""
    saida = texto[: BLOCO.search(texto).start()]
    for m in BLOCO.finditer(texto):
        id_, bloco = m.group(1), m.group(2).strip("\n") + "\n"
        if id_ == ANTIGA:
            titulo, _, corpo = bloco.partition("\n")
            for nova, corpo_lp in zip(NOVAS, (TAREFAS_LP_ALFA, TAREFAS_LP_OUTRAS)):
                saida += f"## {nova}\n{titulo}\n\n{corpo_lp if lp else corpo.strip() + chr(10)}\n"
        elif id_ == "fechamento" and lp:
            saida += f"## fechamento\n{FECHAMENTO_LP}\n"
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
            texto=por_tipo(ultima.texto, template.componente.codigo == "LP"),
        )

    for copia in RevistaSecao.objects.filter(revista_fasciculo__fasciculo="F2", secao=ANTIGA):
        RevistaSecao.objects.create(
            revista_fasciculo_id=copia.revista_fasciculo_id, template_id=copia.template_id, secao=NOVAS[0],
            texto=copia.texto, template_versao_id=copia.template_versao_id,
        )  # fmt: skip
        copia.secao = NOVAS[1]
        copia.save(update_fields=["secao"])


class Migration(migrations.Migration):
    dependencies = [("nucleo", "0030_infografico_item_habilidade")]

    operations = [migrations.RunPython(frente, migrations.RunPython.noop)]
