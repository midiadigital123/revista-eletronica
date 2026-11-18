---
title: "Link simbólico chamado node_modules escapa do ignore e, depois de commitado, o git apaga a pasta real ao trocar de branch"
author: Otavio
date: 2026-11-18
branch: main
cost: { minutes: 57, tokens: 278742 }
id: l-dd67997a
scope: repo
status: active
src: agent
touches:
  - kanban.md
  - state.md
  - docs/telas/design-system.md
  - app/nucleo/templates/cotton/botao.html
  - app/nucleo/templates/ui/_componentes/impacto.html
  - app/nucleo/templates/ui/_componentes/status_salvo.html
  - app/nucleo/templates/ui/_componentes/vazio.html
  - app/nucleo/templates/ui/anos/ano.html
  - app/nucleo/templates/ui/anos/anos.html
  - app/nucleo/templates/ui/base.html
---

## Decided
- A regra de ignore de node_modules fica sem a barra no fim, para cobrir também link simbólico. O Playwright é instalado em cada worktree com `npm ci`; nada de link para a pasta de outra worktree.

## Tried and ruled out
- Reaproveitar o node_modules da main por link simbólico na worktree de trabalho: a regra com barra só cobre pasta, um `git add -A` commitou o link, e ao mesclar na main o git trocou a pasta real por um link que aponta para ele mesmo. O E2E passou a falhar com "Cannot find module '@playwright/test'".

## Watch out
- Enquanto o link estiver rastreado em alguma branch, trocar para ela apaga a pasta node_modules instalada, sem aviso. Depois de mesclar a correção, rode `npm ci` de novo em `app/e2e`.

In the code:
- `app/.gitignore` (regra `node_modules`), `app/e2e/`; commits `7ec3a37` (entrou) e `735564d` (saiu)
