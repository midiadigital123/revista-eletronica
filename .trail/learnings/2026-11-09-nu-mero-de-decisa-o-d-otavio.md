---
title: Número de decisão D-xxx só vale quando a branch entra na main; branches paralelas colidem
author: Otavio
date: 2026-11-09
branch: docs/atualizacao-2026-11-09
id: l-842d0ee1
scope: repo
status: active
src: agent
touches:
  - state.md
---

## Decided
Cada branch paralela pega o próximo número livre da main para suas decisões, então duas frentes abertas ao mesmo tempo usam o mesmo número para coisas diferentes. Quem renumera é a branch que entrar na main depois, no momento do merge, e registra a renumeração numa decisão nova (o state.md é append-only).

## Tried and ruled out
Renumerar só uma vez, ao mesclar a main na branch: em 06/11 a branch da etapa do projeto renumerou D-226..D-228 para D-229..D-231, e a main avançou de novo para D-229..D-232 com outras decisões. A colisão voltou.

## Watch out
Em 09/11 havia três colisões abertas: D-233 é "Docs alinhados" na branch de documentação e "Uma página por fascículo" na fase 1 do F2; D-229 a D-231 da etapa do projeto são outras decisões na main. Antes de citar "D-2xx" em commit ou doc de uma branch paralela, confira o número na main.

In the code:
- `state.md` de `integ/docs-atualizacao` (PR #6), `feat/f2-f1` e `feat/etapa-do-projeto`
- conferir: `git show "<branch>:state.md" | grep -E '^### D-2'` (no zsh, aspas em volta de `<branch>:state.md`)
