"""Lista fixa de variáveis dos templates (D-100).

Automáticas saem do próprio projeto e não são gravadas. Cada variável não
automática é uma coluna text de `Projeto`, com o mesmo nome e CHECK de
tamanho `TAMANHO_MAX` (variável nova = campo novo + makemigrations).
"""

from typing import NamedTuple


class Variavel(NamedTuple):
    nome: str
    rotulo: str
    descricao: str
    automatica: bool = False
    grupo: str = ""  # fieldset no form do projeto


TAMANHO_MAX = 200  # o ER fixa length <= 200 para as variáveis

VARIAVEIS = (
    Variavel("nome_parceiro", "Nome do parceiro", "Nome do parceiro no cadastro (GO, JOINVILLE).", automatica=True),
    Variavel("nome_projeto", "Nome do projeto", "Nome do projeto no ano.", automatica=True),
    Variavel("ano", "Ano", "Ano da edição (2026).", automatica=True),
    # Lista oficial da equipe (planilha com <<x>>; aqui a sintaxe continua {{x}}, D-123).
    Variavel("issn", "ISSN", "ISSN da coleção (capa, folha de rosto e ficha catalográfica).", grupo="Coleção"),
    Variavel("adjetivo_patrio_singular_masculino", "Adjetivo pátrio masc. sing.", "Ex.: mineiro.", grupo="Adjetivo pátrio"),
    Variavel("adjetivo_patrio_singular_feminino", "Adjetivo pátrio fem. sing.", "Ex.: mineira.", grupo="Adjetivo pátrio"),
    Variavel("adjetivo_patrio_plural_masculino", "Adjetivo pátrio masc. plural", "Ex.: mineiros.", grupo="Adjetivo pátrio"),
    Variavel("adjetivo_patrio_plural_feminino", "Adjetivo pátrio fem. plural", "Ex.: mineiras.", grupo="Adjetivo pátrio"),
    Variavel("do_da_de_nome_parceiro", "do/da/de + parceiro", 'Preposição "de" antes do nome do parceiro (do, da, de).', grupo="Parceiro"),
    Variavel("no_na_em_nome_parceiro", "no/na/em + parceiro", 'Preposição "em" antes do nome do parceiro (no, na, em).', grupo="Parceiro"),
    Variavel("nome_programa", "Nome do programa", "Nome por extenso do programa.", grupo="Programa"),
    Variavel("do_da_nome_programa", "do/da + programa", 'Preposição "de" antes do nome por extenso do programa.', grupo="Programa"),
    Variavel("no_na_nome_programa", "no/na + programa", 'Preposição "em" antes do nome por extenso do programa.', grupo="Programa"),
    Variavel("nome_regional", "Nome da regional", "Nome por extenso da regional.", grupo="Regional e secretaria"),
    Variavel("nome_secretaria", "Nome da secretaria", "Nome por extenso da secretaria.", grupo="Regional e secretaria"),
    Variavel("pd01", "Padrão 1", "Nome do 1º padrão de desempenho do programa.", grupo="Padrões de desempenho"),
    Variavel("pd02", "Padrão 2", "Nome do 2º padrão de desempenho do programa.", grupo="Padrões de desempenho"),
    Variavel("pd03", "Padrão 3", "Nome do 3º padrão de desempenho do programa.", grupo="Padrões de desempenho"),
    Variavel("pd04", "Padrão 4", "Nome do 4º padrão de desempenho do programa.", grupo="Padrões de desempenho"),
    Variavel("pd05", "Padrão 5", "Nome do 5º padrão de desempenho do programa (SPAECE ALFA).", grupo="Padrões de desempenho"),
    Variavel("plataforma", "Plataforma", "Endereço da plataforma do programa.", grupo="Programa"),
    Variavel("quais_redes", "Redes avaliadas", "Nomes das redes de ensino avaliadas.", grupo="Parceiro"),
    Variavel("sigla_programa", "Sigla do programa", "Sigla do programa: PAEBES, SAEGO etc.", grupo="Programa"),
    Variavel("do_da_sigla_programa", "do/da + sigla", 'Preposição "de" antes da sigla do programa.', grupo="Programa"),
    Variavel("no_na_sigla_programa", "no/na + sigla", 'Preposição "em" antes da sigla do programa.', grupo="Programa"),
    Variavel("sigla_regional", "Sigla da regional", "Sigla da regional: DRE, CREDE etc.", grupo="Regional e secretaria"),
    Variavel("sigla_secretaria", "Sigla da secretaria", "Sigla da secretaria: SEDU, SEMED etc.", grupo="Regional e secretaria"),
)
