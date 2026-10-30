# Variáveis dos templates

Para quem escreve os textos dos templates (Pedagógica).

## Como usar

Escreva o nome da variável entre chaves duplas: `{{nome}}`. Na revista, ela vira o valor
cadastrado no projeto. Exemplo com preposição:

```
Os estudantes {{do_da_de_nome_parceiro}} {{nome_parceiro}}
```

Com `do_da_de_nome_parceiro` = "de" e o parceiro JOINVILLE no cadastro, sai
"Os estudantes de JOINVILLE".

A planilha da equipe usa `<<nome>>`; no sistema a sintaxe é sempre `{{nome}}`.
Nome fora da lista é recusado ao salvar o template.

## Lista

| Nome | Descrição | Automática? |
| --- | --- | --- |
| `nome_parceiro` | Nome do parceiro no cadastro (GO, JOINVILLE). | sim |
| `nome_projeto` | Nome do projeto no ano. | sim |
| `ano` | Ano da edição (2026). | sim |
| `issn` | ISSN da coleção (capa, folha de rosto e ficha catalográfica). | não |
| `adjetivo_patrio_singular_masculino` | Adjetivo pátrio masc. sing. Ex.: mineiro. | não |
| `adjetivo_patrio_singular_feminino` | Adjetivo pátrio fem. sing. Ex.: mineira. | não |
| `adjetivo_patrio_plural_masculino` | Adjetivo pátrio masc. plural. Ex.: mineiros. | não |
| `adjetivo_patrio_plural_feminino` | Adjetivo pátrio fem. plural. Ex.: mineiras. | não |
| `do_da_de_nome_parceiro` | Preposição "de" antes do nome do parceiro (do, da, de). | não |
| `no_na_em_nome_parceiro` | Preposição "em" antes do nome do parceiro (no, na, em). | não |
| `nome_programa` | Nome por extenso do programa. | não |
| `do_da_nome_programa` | Preposição "de" antes do nome por extenso do programa. | não |
| `no_na_nome_programa` | Preposição "em" antes do nome por extenso do programa. | não |
| `nome_regional` | Nome por extenso da regional. | não |
| `nome_secretaria` | Nome por extenso da secretaria. | não |
| `pd01` | Nome do 1º padrão de desempenho do programa. | não |
| `pd02` | Nome do 2º padrão de desempenho do programa. | não |
| `pd03` | Nome do 3º padrão de desempenho do programa. | não |
| `pd04` | Nome do 4º padrão de desempenho do programa. | não |
| `pd05` | Nome do 5º padrão de desempenho do programa (SPAECE ALFA). | não |
| `plataforma` | Endereço da plataforma do programa. | não |
| `quais_redes` | Nomes das redes de ensino avaliadas. | não |
| `sigla_programa` | Sigla do programa: PAEBES, SAEGO etc. | não |
| `do_da_sigla_programa` | Preposição "de" antes da sigla do programa. | não |
| `no_na_sigla_programa` | Preposição "em" antes da sigla do programa. | não |
| `sigla_regional` | Sigla da regional: DRE, CREDE etc. | não |
| `sigla_secretaria` | Sigla da secretaria: SEDU, SEMED etc. | não |

Automáticas saem do cadastro. As outras são preenchidas por projeto, no form do projeto
ou na aba Variáveis ("Copiar valores do ano anterior" preenche as vazias).

## Padrões de desempenho (`pd01`..`pd05`)

`pd01`..`pd05` são o nome de cada padrão na escala do F1 e também podem ser usados nos
textos (F1 e F2), como qualquer variável.

Regra: **nome do ano, sobrescrito pelo `pdNN` do projeto.** Cada ano tem um nome por padrão,
guardado junto da cor do padrão. O projeto só preenche `pdNN` quando quer outro nome; com
`pdNN` vazio, vale o nome do ano, tanto na escala quanto em `{{pdNN}}` nos textos. É o mesmo
modelo da cor (cor do ano + cor do projeto).

- **Nome do ano:** admin > Núcleo > "Padrões do ano (cor e nome)" (`CorPadrao`, filtre pelo ano), campo "Nome". Começa como
  "Padrão 01".."Padrão 05" e é copiado ao abrir o ano seguinte. Mudar esse nome muda todas
  as revistas do ano que não sobrescrevem (e elas precisam ser validadas de novo).
- **Nome do projeto:** form do projeto ou aba Variáveis. O campo vazio mostra o nome do ano
  ("padrão do ano: …").

Só contam os padrões que a revista tem (2 a 5, conforme os cortes): numa revista de 4
padrões, `pd05` não pesa. Um padrão que a revista tem gera a pendência abaixo só se o
projeto e o ano estiverem vazios.

## Variável vazia

Variável usada no template (ou `pdNN` de um padrão da revista) e sem valor no projeto
(para `pdNN`: nem no projeto nem no ano) aparece no preview com o mesmo
destaque vermelho da faixa de "falta template" (D-116) e gera a pendência "variáveis",
que impede marcar a revista como "Validado".

## Para quem mantém o sistema

A lista vive em `app/nucleo/variaveis.py` (`VARIAVEIS`). Variável nova = item novo na
lista + campo novo em `Projeto` + migração (`makemigrations`), com CHECK de tamanho.
