---
title: No admin só se exclui a sobrescrita do projeto; tarefa e descritor da matriz não se apagam pela tela
author: Otavio
date: 2026-10-29
branch: refatoracao-django
cost: { minutes: 30, tokens: 253353 }
id: l-89647354
scope: repo
status: active
src: agent
touches:
  - app/nucleo/permissoes.py
  - app/nucleo/tests/test_permissoes.py
  - plans/revista-express-django.md
  - state.md
---

## Decided
Pedagógica, Mídias Digitais e Admin podem excluir apenas as sobrescritas de intervalo mínimo (passo) e de cor de um projeto. Excluir a sobrescrita é o jeito de "voltar ao valor da matriz/paleta do ano". Nenhum outro modelo tem permissão de exclusão para os perfis; o Impresso não exclui nada.

## Tried and ruled out
- Liberar exclusão de tarefa e descritor para a Pedagógica: uma exclusão errada na matriz Comunitária muda ~25 revistas de uma vez. Correção de tarefa/descritor errado continua por reimportação da matriz ou por superusuário.
- Manter tudo sem exclusão (regra anterior): quem sobrescrevia o passo ou a cor ficava preso à sobrescrita, porque passo vazio significa "sem linhas vazias", não "usar o da matriz".

## Watch out
Mudar essa tabela exige migração de dados nos grupos (listas congeladas, como a das permissões iniciais) e o teste que compara banco × tabela de permissões falha se esquecer.

In the code: app/nucleo/permissoes.py (tabela papel × ação), migração 0008 nos grupos, app/nucleo/tests/test_permissoes.py.
