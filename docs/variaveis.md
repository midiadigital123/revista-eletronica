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

`pd01`..`pd05` são o nome de cada padrão na escala do F1 (no lugar de "Padrão 01".."Padrão 05")
e também podem ser usados nos textos, como qualquer variável. Só contam os padrões que a
revista tem (2 a 5, conforme os cortes): numa revista de 4 padrões, `pd05` vazio não pesa,
mas `pd01`..`pd04` vazios geram a pendência abaixo. A cor de cada padrão continua separada.

## Variável vazia

Variável usada no template (ou `pdNN` de um padrão da revista) e sem valor no projeto aparece no preview com o mesmo
destaque vermelho da faixa de "falta template" (D-116) e gera a pendência "variáveis",
que impede marcar a revista como "Validado".

## Para quem mantém o sistema

A lista vive em `app/nucleo/variaveis.py` (`VARIAVEIS`). Variável nova = item novo na
lista + campo novo em `Projeto` + migração (`makemigrations`), com CHECK de tamanho.
