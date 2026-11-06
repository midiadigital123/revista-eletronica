---
title: Todo trabalho vai para uma worktree própria e só chega à main pela branch intermediária que o usuário mergeia
author: Otavio
date: 2026-11-06
branch: docs/f2-mapeamento
id: l-a1df7cf7
scope: repo
status: active
src: agent
touches:
  - state.md
---

## Decided
Nada é modificado direto na worktree da main, porque o usuário quer revisar e decidir sozinho o que entra nela. Cada trabalho roda numa worktree irmã com branch própria, criada a partir de uma branch intermediária integ/<tema> (saída da main). O merge na intermediária acontece só depois de tudo testado na worktree, porque a intermediária é o único ponto onde o conjunto é testado integrado; o merge da intermediária na main é sempre do usuário. O state.md também é editado na worktree, nunca na main, senão o checkout principal fica com mudança solta.

## Tried and ruled out
Commitar direto na main: contraria o pedido do usuário de 06/11. Branch de trabalho direto para a main sem intermediária: perde o ponto único onde o conjunto é testado integrado, e foi assim que o integ/ui-b evitou conflito entre agentes paralelos.

## Watch out
Ao disparar um subagente que escreve arquivo, mandar o caminho da worktree, não o do checkout principal; senão o artefato nasce fora da branch (aconteceu nesta sessão: o brief saiu antes da regra, e o agente precisou ser redirecionado). A stack docker da worktree precisa de -p <nome> próprio, porque o .env fixa COMPOSE_PROJECT_NAME e sobe em cima do dev.

In the code:
Padrão: git branch integ/<tema> main; git worktree add ../revista-express-<tema> -b <branch> integ/<tema>. Exemplo desta sessão: integ/f2-interface e /home/otavio.peres/dev/revista-express-f2 (docs/f2-mapeamento). Decisão D-226 no state.md.
