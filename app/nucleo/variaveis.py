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


TAMANHO_MAX = 200  # o ER fixa length <= 200 para as variáveis

VARIAVEIS = (
    Variavel("parceiro", "Parceiro", "Nome do parceiro (GO, JOINVILLE).", automatica=True),
    Variavel("nome_projeto", "Nome do projeto", "Nome do projeto no ano.", automatica=True),
    Variavel("ano", "Ano", "Ano da edição (2026).", automatica=True),
    Variavel("gentilico_masc_sing", "Gentílico masc. sing.", "Ex.: goiano."),
    Variavel("gentilico_fem_sing", "Gentílico fem. sing.", "Ex.: goiana."),
    Variavel("gentilico_masc_plur", "Gentílico masc. plural", "Ex.: goianos."),
    Variavel("gentilico_fem_plur", "Gentílico fem. plural", "Ex.: goianas."),
)
