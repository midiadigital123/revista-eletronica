---
title: "Mudança que vai sozinha para a main sai de uma branch criada da main, nunca da integração do F2"
author: Otavio
date: 2026-11-10
branch: chore/kanban
cost: { minutes: 1, tokens: 1849 }
id: l-4c4be576
scope: repo
status: active
src: agent
touches:
  - state.md
  - kanban.md
---

## Decided
Uma mudança pequena que deve entrar na main antes do F2 (docs, kanban, correção) sai de uma branch criada a partir da main, e não da branch de integração do F2. Um PR saído da integração levaria junto todos os commits do F2, que só entram na main com as fases 1 a 4. Quando vários PRs mexem no state.md, mergeie um de cada vez. O último é refeito a partir da main já atualizada, reaplicando as edições do state.md, em vez de resolver conflito em cima de conflito.

## Tried and ruled out
- Commitar o kanban na branch criada da integração do F2 e abrir o PR para a main: o PR levaria 44 commits do F2 junto.
- Rebasear as edições do state.md sobre a main: o arquivo diverge muito entre as branches (decisões e sessões no fim), e o conflito sai maior que reaplicar as poucas edições.

## Watch out
- Depois desses merges, a integração do F2 fica atrás da main. Ao mergear a main nela, o state.md conflita nas decisões e nas sessões. Resolva mantendo os dois lados, como no PR #9.
- O trail check marca falsos positivos no state.md (palavras soltas do texto histórico). Justifique na descrição do PR.

In the code:
- PRs #8 (integ/abrir-ano), #9 (integ/docs-atualizacao) e #10 (chore/kanban), mergeados em 10/11, nessa ordem.
- Para refazer a branch: trocar para uma branch nova a partir de origin/main e reaplicar só as edições do state.md; o kanban.md não rastreado atravessa a troca.
