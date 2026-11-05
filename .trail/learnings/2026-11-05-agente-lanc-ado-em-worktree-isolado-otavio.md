---
title: "Agente lançado em worktree isolado nasce no main, não na branch de integração; o brief precisa mandar refazer a branch a partir do commit certo"
author: Otavio
date: 2026-11-05
branch: feat/telas-b-ux
cost: { minutes: 45, tokens: 318765 }
id: l-da214a7e
scope: repo
status: active
src: agent
touches:
  - app/e2e/tests/downloads.spec.ts
  - app/nucleo/admin/revista.py
  - app/nucleo/servicos/arquivos.py
  - app/nucleo/templates/ui/cortes.html
  - app/nucleo/templates/ui/parciais/matriz_painel.html
  - app/nucleo/templates/ui/parciais/matriz_tarefa.html
  - app/nucleo/templates/ui/parciais/revista_arquivos.html
  - app/nucleo/templates/ui/revista/revista.html
  - app/nucleo/tests/test_ui_cortes.py
  - app/nucleo/tests/test_ui_matriz.py
---

## Decided
Todo brief de agente com worktree isolado diz o SHA de partida e manda criar a branch com `git checkout -B <branch> <sha>` antes de qualquer mudança.

## Tried and ruled out
- Confiar que o worktree do agente parte do HEAD de `feat/telas-b-ux`: em 05/11 os 4 agentes (S6–S9 e docs) nasceram em `34f3579` (main, árvore antiga com `assets/escala/`). Só não deu errado porque o brief citava `2dc2825` e os agentes conferiram.

## Watch out
- Sem o SHA no brief, o agente trabalha numa árvore sem as telas B e o merge traz uma bagunça.

In the code: worktrees em `/home/otavio.peres/dev/revista-eletronica/.claude/worktrees/agent-*`; checkout principal em `revista-eletronica` na branch `django`.
