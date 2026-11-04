# Ficha: Cortes (T08, parceiros T04)

Endereço: `/ui/projeto/ano/<ano>/cortes/` (rota `cortes`), a aba Cortes do hub Projetos. O endereço antigo `/cortes/<ano>/` (e `/cortes/`) redireciona para cá (302).

## Objetivo

Lançar os cortes dos padrões de cada parceiro no ano, numa grade só: uma linha por parceiro, uma coluna por etapa × componente. Cada célula aceita "350, 400, 500". O corte é o que faz nascer o projeto e as revistas do parceiro. Na mesma grade se cria um parceiro novo e se corrige o nome de um parceiro.

## Quem usa

| Perfil | O que faz |
|---|---|
| Pedagógica, Mídias Digitais, Admin | Lançam e corrigem cortes, criam parceiros e renomeiam parceiros. |
| Impresso | Vê a grade com as células só leitura; não vê "+ Adicionar parceiro" nem o lápis de renomear. Todo POST recebe 403. |
| Sem permissão de ver cortes | Recebe 403. |
| Sem login | Vai ao login do admin. |

## Jornada

- **Antes:** o ano aberto, com etapas e componentes cadastrados ("Configurar <ano>", ficha [`anos.md`](anos.md)).
- **Aqui:** abrir Projetos › Cortes, digitar os cortes de cada parceiro. Cada célula salva sozinha ao sair dela.
- **Depois:** o projeto do parceiro aparece na aba Lista de Projetos, com uma revista por componente que tem corte. Lá se escolhem matriz e templates (ficha [`projeto.md`](projeto.md)).

## Dados mostrados

- Cabeçalho do hub Projetos e as abas Lista · Cortes · Variáveis (`_componentes/projetos_abas.html`).
- Linha de ações: a frase "Cortes dos padrões de cada parceiro, por etapa e componente.", o status do salvamento (só para quem grava) e o botão "Baixar planilha de grupos".
- Grade: cabeçalho em duas linhas, etapa ("5EF até 500") e, embaixo, os componentes (LP, MT). Primeira coluna com o nome do parceiro. Todos os parceiros cadastrados aparecem, em ordem alfabética, mesmo sem corte no ano.
- Ajuda acima da grade (só para quem grava): "De 1 a 4 cortes inteiros e crescentes, separados por vírgula, maiores que 0 e menores que o máximo da escala da etapa. Célula vazia apaga o corte. Cada célula salva sozinha ao sair dela."

## Dados gravados

- **Célula:** os cortes daquele parceiro naquela etapa × componente. O servidor regrava a linha inteira do parceiro com essa célula trocada e passa pela mesma validação da grade inteira (`cascata.validar_linhas`). Célula vazia apaga o corte.
- **Cascata:** o primeiro corte do parceiro no ano cria o projeto ("<parceiro> - NOME DO PROJETO") e a revista do componente. Apagar todos os cortes de um componente arquiva a revista dele. Apagar todos os cortes do parceiro arquiva o projeto.
- **Parceiro novo:** só o nome. Nasce sem cortes; o projeto nasce quando o primeiro corte da linha for salvo.
- **Renomear parceiro:** o nome vale para todos os anos e entra no texto da revista (`nome_parceiro`). Se alguma revista validada mudar, o modal de impacto abre antes de gravar.

## Ações

| Ação | Quem | Resultado |
|---|---|---|
| Sair de uma célula alterada | quem grava cortes | salva só aquela célula; o status mostra "Salvo às HH:MM". "350 400" volta normalizado como "350, 400" |
| Lápis "Renomear <nome>" | quem altera parceiro | troca o nome por um campo com foco. Enter ou sair do campo salva; Esc volta o nome |
| "+ Adicionar parceiro" (logo abaixo da grade) | quem cria parceiro | abre uma linha com o foco no nome. Enter ou "Incluir parceiro" cria; Esc ou "Descartar" tira a linha |
| Baixar planilha de grupos | todos | baixa `cortes-<ano>.xlsx` pelo admin (`/admin/nucleo/corte/exportar/?ano=<ano>`): uma aba por etapa × componente, parceiros agrupados pelos mesmos cortes |
| Abas Lista / Variáveis | todos | outra aba do hub Projetos |

## Estados

- **Vazio:** sem parceiro cadastrado, a grade mostra "Nenhum parceiro cadastrado." e, para quem cria parceiro, "Adicione o primeiro abaixo."
- **Erro na célula (422):** a célula fica marcada, o erro aparece embaixo dela e o status diz "Não salvo: corrija o campo marcado". Nada grava.
- **Conflito (409, duas abas ou duas pessoas):** a grade não tem bloqueio. Cada envio manda o `original` (o valor que a célula tinha na tela). Se o banco já tem outro valor, nada grava: o status diz "Não salvo: outra pessoa mudou este valor" e a célula mostra a mensagem do conflito. O valor digitado fica na célula, e "Tentar de novo" grava por cima, de propósito.
- **Impacto:** se a célula ou o nome mudam o texto de uma revista validada, o modal lista as revistas que perdem o "Validado" ("Salvar o corte tira o “Validado” de N revista(s)" / "Renomear tira…"). Cancelar ou Esc volta o valor gravado e o foco.
- **Sem conexão:** "Não salvo: sem conexão · Tentar de novo". Só nesse caso (ou com envio pendente) o navegador avisa ao sair da página.
- **Só leitura (perfil):** aviso no topo; células `readonly`; sem lápis e sem "+ Adicionar parceiro".
- **Sucesso do parceiro novo:** a página recarrega com "Parceiro <nome> criado. Preencha os cortes da linha e salve."

## Mensagens exatas

- Corte não inteiro: "<ETAPA> <CC>: cortes precisam ser inteiros (ex.: 350, 400, 500)."
- Validação da linha (`cascata.validar_linhas`): "<ETAPA> <CC>: informe de 1 a 4 cortes." · "…: cortes precisam ser crescentes." · "…: cortes precisam estar entre 1 e <escala_max - 1>."
- Célula de outro ano ou apagada: "Célula não encontrada neste ano. Recarregue a página."
- Conflito: "<parceiro>: outra pessoa mudou este corte depois que a página abriu (agora: <valor ou vazio>). Seu valor ficou na célula; Tentar de novo grava por cima."
- Parceiro novo recusado: "Parceiro não criado: <erro do nome>." (nome vazio ou repetido).
- Só leitura: "Só leitura: seu perfil vê os cortes, mas não altera. Para editar, peça a permissão de cortes a um administrador."

## Permissões

- Login obrigatório; anônimo vai ao login do admin.
- Ver: `view_corte` ou `change_corte`. Sem elas, 403.
- Gravar célula: `add_corte` + `change_corte`. Sem elas, células só leitura e POST 403.
- Criar parceiro: `add_parceiro`. Renomear parceiro: `change_parceiro`. Sem elas, o botão não aparece e o POST dá 403.
- Sem bloqueio de edição: o conflito entre duas abas é otimista, pelo `original` de cada célula.

## Interações (Alpine e HTMX)

- A grade é um `<form x-data="campoAuto" data-url="…/celula/">` (rota `cortes_celula`, `POST /cortes/<ano>/celula/`). O campo vai como `c-<parceiro>-<etapa>-<componente>`, com `valor` e `original`. Protocolo do autosave em [`design-system.md`](../design-system.md) §5.
- O nome do parceiro é o componente `nomeInline` dentro do mesmo form; o `data-url` dele troca a rota para `cortes_renomear_parceiro` (`POST /cortes/<ano>/parceiro/<pk>/renomear/`).
- "+ Adicionar parceiro" é o componente `linhaNova` com um form próprio (fora do form da grade), que envia `POST /cortes/<ano>/parceiro/` (rota `cortes_novo_parceiro`) e recarrega a página.
- Sem HTMX nesta tela.

## Aba Cortes do projeto

A página do projeto tem a aba Cortes (`/ui/projeto/<pk>/?aba=cortes`) com a linha deste parceiro, um bloco por etapa e os componentes lado a lado. Grava pela mesma rota `cortes_celula`, com o mesmo conflito otimista. O link "Ver a grade de cortes de <ano>" volta para esta tela.

## Wireframe (1440 px)

```
┌ Revista Eletrônica  [2026 ▾]  Painel [Projetos] Matrizes Templates Impresso          Ana  Admin  Sair ┐
│ Projetos                                                                                           │
│ Um projeto por parceiro no ano. Nasce quando os cortes do parceiro são lançados.                    │
│  Lista   Cortes   Variáveis                                                                         │
│          ━━━━━━                                                                                     │
│ Cortes dos padrões de cada parceiro…        ✓ Salvo às 10:15      [⤓ Baixar planilha de grupos]     │
│ De 1 a 4 cortes inteiros e crescentes… Cada célula salva sozinha ao sair dela.                      │
│ ┌──────────────────┬──────── 5EF até 500 ────────┬──────── 9EF até 500 ────────┐                    │
│ │ Parceiro         │ LP            │ MT          │ LP            │ MT          │                    │
│ ├──────────────────┼───────────────┼─────────────┼───────────────┼─────────────┤                    │
│ │ GO ✎             │ [150, 200, 250]│ [175, 225] │ [200, 250, 300]│ [        ] │                    │
│ │ PE ✎             │ [150, 200]    │ [abc      ]!│ …             │             │                    │
│ │  • PE: 5EF MT: cortes precisam ser inteiros (ex.: 350, 400, 500).                                │
│ └──────────────────┴───────────────┴─────────────┴───────────────┴─────────────┘                    │
│ [+ Adicionar parceiro]                                                                              │
└─────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

Em 390 px: a grade rola na horizontal dentro da caixa, com a coluna Parceiro fixa; a página não rola de lado.

## Critérios de aceite

1. Quem grava abre `/ui/projeto/ano/2026/cortes/` e vê a grade, o status do salvamento e "+ Adicionar parceiro" abaixo da tabela. `/cortes/2026/` redireciona para cá.
2. Digitar "350 400" numa célula e sair dela grava e mostra "Salvo às"; a célula volta como "350, 400". Recarregar não abre diálogo de saída.
3. Valor inválido (não inteiro, decrescente, fora da escala) responde 422 com a mensagem "<ETAPA> <CC>: …" embaixo da célula; nada grava.
4. Duas abas: a segunda a salvar a mesma célula recebe 409 com o valor atual; nada grava por cima até "Tentar de novo".
5. Célula que muda uma revista validada abre o modal de impacto; Cancelar volta o valor; confirmar grava e tira o "Validado".
6. O primeiro corte de um parceiro sem projeto cria o projeto e a revista do componente.
7. Renomear pelo lápis: Enter grava, Esc cancela, nome vazio ou repetido dá 422; com revista validada, o modal abre antes.
8. Impresso vê tudo só leitura, sem lápis nem "+ Adicionar parceiro"; POST em célula, renomear ou parceiro novo dá 403. Sem `view_corte`: 403.
9. "Baixar planilha de grupos" baixa o xlsx do ano.

## Referências técnicas

- Regra: `app/nucleo/cortes.py` (`grade`, `linhas_atuais`, `interpretar`, `formatar`, `planilha`, `pode_ver`, `pode_gravar`, `gravar`), `servicos/cascata.py` (`validar_linhas`, `gravar_cortes`). O admin usa a mesma regra (`admin/cortes.py`).
- View: `app/nucleo/urls/cortes.py` (`cortes`, `antiga`, `celula`, `novo_parceiro`, `renomear_parceiro`). A rota `cortes` mora em `urls/ui_projeto.py`.
- Templates: `templates/ui/cortes.html`, `templates/ui/parciais/cortes_grade.html` (também usado pela aba Cortes do projeto), `_componentes/nome_inline.html`, `_componentes/status_salvo.html`.
- JS: `static/ui/componentes/autosave.js` (`campoAuto`, `saida`), `static/ui/componentes.js` (`nomeInline`, `linhaNova`).
- Testes: `app/nucleo/tests/test_ui_cortes.py`, `test_ui_autosave.py`; `app/e2e/tests/cortes.spec.ts`, `autosave.spec.ts`, `impacto.spec.ts`.
- Decisões: D-049, D-055, D-056, D-061, D-068, D-135, D-168 e as do plano de UX (D-195 em diante).
