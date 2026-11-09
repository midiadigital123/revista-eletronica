# D-238: o F2 passa a ter 8 seções fixas (SECOES_F2). Regra congelada: migração não importa nucleo.servicos
# nem nucleo.texto, e não lê o seed; o texto do seed 2026 (f2-lp.hbs = f2-mt.hbs, sem o comentário de revisão)
# vai nas constantes abaixo.
#   1. cada Template F2 de LP ou MT ganha uma TemplateVersao nova (só INSERT, D-207) com esse texto;
#   2. as cópias dlg-p2 e dlg-p3 das revistas viram texto_progressao e texto_habilidades do infográfico "outras"
#      (ou do "alfa", se a revista só tem esse), só em campo vazio;
#   3. as cópias do F2 cujo id não está nas 8 seções são apagadas.
# Linhas criadas ou apagadas aqui não têm registro do simple-history (o modelo histórico das migrações não
# dispara o sinal): é aceito, como na 0022. Sem volta: o texto antigo fica na versão anterior, e as cópias
# apagadas não voltam.
from django.db import migrations

SECOES_F2 = (
    "abertura", "passo-descritor", "passo-habilidades", "passo-progressao", "passo-tarefas",
    "dlg-descritor", "tarefas-fechamento", "fechamento",
)  # fmt: skip

TEXTO_F2 = """## abertura
Avaliação e Currículo

A Base Nacional Comum Curricular (BNCC) constitui a principal diretriz da Educação Básica brasileira. Com caráter normativo e referencial, ela estabelece as competências gerais e as específicas de cada área do conhecimento, bem como define os conteúdos indispensáveis a serem trabalhados em cada etapa de escolarização.

A partir da BNCC, são criados os referenciais curriculares dos estados e municípios brasileiros. Esses documentos detalham e adaptam as orientações nacionais, incorporando as especificidades culturais e regionais de cada sistema de ensino.

Quando falamos em avaliação externa em larga escala, é comum ter dúvidas sobre o processo de elaboração da Matriz de Referência. Resumidamente, podemos entender a Matriz de Referência como um “recorte” do currículo, reunindo as habilidades essenciais que os estudantes precisam desenvolver e que conseguimos avaliar por meio de testes padronizados.

Diante disso, esta seção tem como objetivo destacar a relação entre currículo e avaliação, apresentando a correlação entre habilidades curriculares e habilidades da Matriz de Referência, a sua progressão ao longo da Educação Básica, trazendo exemplos de tarefas relacionadas a essas habilidades e apresentando alguns indicadores derivados das avaliações externas em larga escala. Para tanto, organizamos essas informações em um infográfico e as detalhamos na sequência. Apresentamos, também, sugestões de práticas para a sala de aula, objetivando o desenvolvimento das habilidades destacadas.

## passo-descritor
Descritor

Descritor da Matriz de Referência em destaque nesta revista. Clique no botão amarelo para ver a relação entre o currículo e a avaliação.

## passo-habilidades
Descrição das habilidades no referencial curricular

Habilidades do referencial curricular do estado relacionadas ao descritor, com a legenda: I — Introduzir, A — Aprofundar, C — Consolidar, R — Retomar.

## passo-progressao
Progressão da habilidade

Como a habilidade avança do 1º ano do EF à 3ª série do EM no referencial curricular. Clique no botão amarelo para ver o detalhamento.

## passo-tarefas
Tarefas por nível de complexidade

Itens exemplares do descritor nas etapas de terminalidade. Clique nos botões amarelos para ver cada item.

Aqui, apresentamos alguns itens exemplares, que representam possibilidades de avaliar a habilidade destacada nas etapas de terminalidade da Educação Básica. Isto é 2º ano do Ensino Fundamental, 5º ano do Ensino Fundamental, 9º ano do Ensino Fundamental e 3ª série do Ensino Médio.

## dlg-descritor
Descritor

O desenvolvimento das habilidades previstas na Matriz de Referência requer um trabalho pedagógico contínuo e progressivo ao longo da Educação Básica. Isso significa que uma habilidade não deve ser compreendida como uma aprendizagem pontual, mas como um conhecimento que se constrói gradualmente, por meio de diferentes oportunidades de exploração, retomada e aprofundamento.

Nesse percurso, é fundamental definir quais aprendizagens são esperadas em cada etapa, considerando tanto os conhecimentos que constituem o ponto de partida quanto aqueles que se pretende consolidar ao final de determinado período. A partir dessa perspectiva, uma mesma habilidade pode ser mobilizada em diferentes momentos da escolarização, com níveis crescentes de complexidade e em situações diversificadas de uso.

Essa progressão possibilita acompanhar o desenvolvimento dos estudantes e favorecer a consolidação das aprendizagens de maneira gradual, ampliando as condições para que os conhecimentos construídos sejam mobilizados com autonomia em diferentes contextos.

## tarefas-fechamento
Fechamento das tarefas

Ao analisar conjuntamente os itens apresentados para os diferentes anos de escolaridade, é possível observar uma progressão na complexidade das tarefas e nas estratégias de leitura mobilizadas. No 2º ano do Ensino Fundamental, a interpretação da tirinha exige que o estudante relacione falas e imagens para inferir uma informação sobre o comportamento de um personagem, a partir de uma situação simples e de pistas bastante evidentes. No 5º ano, a leitura da charge amplia essa exigência, pois envolve a compreensão de uma crítica construída por meio de recursos visuais e de conhecimentos prévios. No 9º ano, a interpretação da tirinha demanda uma compreensão mais global da narrativa, articulando diálogos e elementos visuais para inferir o comportamento das personagens. Já na 3ª série do Ensino Médio, espera-se que o estudante mobilize estratégias de leitura mais autônomas e sofisticadas, acompanhando a progressão narrativa e relacionando diferentes elementos verbais e não verbais para identificar as intenções do personagem.

Essa trajetória evidencia que o desenvolvimento da habilidade não se limita à ampliação da diversidade de textos e suportes, mas envolve o aprofundamento das operações de leitura necessárias à construção dos sentidos. Ao longo da escolarização, os estudantes avançam da identificação de relações mais diretas entre imagens e informações verbais para a interpretação de sentidos implícitos, críticas, intenções e efeitos produzidos pela articulação entre diferentes linguagens. Essa progressão é fundamental para orientar o planejamento pedagógico, pois permite compreender que a formação de leitores proficientes exige experiências de leitura cada vez mais desafiadoras, que favoreçam a mobilização integrada de conhecimentos linguísticos, visuais e contextuais. Desse modo, o trabalho sistemático com textos multissemióticos contribui para a formação de leitores capazes de interpretar, analisar e construir sentidos de maneira crítica e autônoma em diferentes situações comunicativas.

## fechamento
Agora é com você

A seguir, apresentamos o template do Infográfico, que poderá ser utilizado para analisar outras habilidades da Matriz de Referência e estabelecer relações com o referencial curricular do estado. O objetivo é aprofundar a compreensão sobre as relações entre **currículo e avaliação externa**, evidenciando como as habilidades previstas no currículo são mobilizadas e avaliadas nos instrumentos apresentados nesta seção.
"""


def criar(apps, schema_editor):
    Template = apps.get_model("nucleo", "Template")
    TemplateVersao = apps.get_model("nucleo", "TemplateVersao")
    RevistaSecao = apps.get_model("nucleo", "RevistaSecao")
    RevistaInfografico = apps.get_model("nucleo", "RevistaInfografico")

    templates = Template.objects.filter(fasciculo="F2", componente__codigo__in=["LP", "MT"])
    for template in templates:
        ultima = TemplateVersao.objects.filter(template=template).order_by("-numero").first()
        if ultima is None or ultima.texto != TEXTO_F2:  # idempotente
            numero = ultima.numero + 1 if ultima else 1
            TemplateVersao.objects.create(template=template, numero=numero, texto=TEXTO_F2)

    copias = RevistaSecao.objects.filter(revista_fasciculo__fasciculo="F2", template__in=templates)
    destino = {"dlg-p2": "texto_progressao", "dlg-p3": "texto_habilidades"}
    for copia in copias.filter(secao__in=destino).select_related("revista_fasciculo"):
        infograficos = RevistaInfografico.objects.filter(revista_id=copia.revista_fasciculo.revista_id)
        info = infograficos.filter(tipo="outras").first() or infograficos.filter(tipo="alfa").first()
        if info and not getattr(info, destino[copia.secao]):
            setattr(info, destino[copia.secao], copia.texto)
            info.save(update_fields=[destino[copia.secao]])
    copias.exclude(secao__in=SECOES_F2).delete()


class Migration(migrations.Migration):
    dependencies = [("nucleo", "0022_infograficos_existentes")]

    operations = [migrations.RunPython(criar, migrations.RunPython.noop)]
