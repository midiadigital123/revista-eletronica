---
title: "Pela tela se excluem a sobrescrita do projeto, o arquivo do item, a tarefa e o descritor da matriz, sempre com confirmação forte"
author: Otavio
date: 2026-10-30
branch: refatoracao-django
cost: { minutes: 39, tokens: 151658 }
id: l-1d975bc9
scope: repo
status: active
replaces: l-89647354
src: agent
touches:
  - state.md
  - app/nucleo/migrations/0012_cor_padrao_verbose_name.py
  - app/nucleo/models/cadastro.py
  - docs/variaveis.md
  - app/nucleo/admin/cadastro.py
  - app/nucleo/admin/projeto.py
  - app/nucleo/admin/variaveis.py
  - app/nucleo/management/commands/carregar_cadastros.py
  - app/nucleo/migrations/0011_cor_padrao_nome.py
  - app/nucleo/servicos/resolver.py
---

## Decided
- Pedagógica, Mídias Digitais e Admin podem excluir pela tela:
  - as sobrescritas do projeto (passo e cor), que é o jeito de voltar ao valor da matriz ou do ano;
  - o arquivo do item;
  - a tarefa e o descritor da matriz.
- O Impresso não exclui nada.
- Excluir uma tarefa ou um descritor exige confirmação forte: a tela lista as revistas afetadas e as que perdem o "Validado", e a pessoa digita o código para confirmar.
- O arquivo do item só sai do disco quando nenhuma tarefa de nenhum ano aponta mais para ele, porque o abrir ano copia o caminho.

## Tried and ruled out
- Proibir a exclusão de tarefa e descritor (regra de 29/10): corrigir uma tarefa errada exigia reimportar a matriz. Hoje já existem o aviso de impacto, o "Validado" por hash e o histórico.
- Liberar a exclusão só para o Admin: a Pedagógica ficaria parada no meio da temporada.
- Lixeira restaurável por 30 dias: custo de modelo e tela sem pedido.
- Nunca apagar o arquivo do disco: o usuário preferiu limpar quando não há mais referência.

## Watch out
- Mudar a tabela de permissões exige migração de dados nos grupos (as listas da migração são congeladas). O teste que compara o banco com a tabela falha se a migração for esquecida.
- Excluir na matriz Comunitária afeta umas 25 revistas de uma vez.

In the code: app/nucleo/permissoes.py, migração de dados dos grupos, app/nucleo/admin/matriz.py, app/nucleo/servicos/arquivos.py, test_permissoes.py (D-181).
