---
title: "No F2, animar peças dentro do passo ativo do tour exige vencer o opacity !important do svg-tour"
author: Otavio
date: 2026-11-05
branch: main
cost: { minutes: 34, tokens: 447686 }
id: l-745a043b
scope: repo
status: active
src: agent
touches:
  - example/f2-animado-tour/abertura.css
  - example/f2-animado-tour/abertura.js
  - example/f2-animado-tour/animacao.js
  - example/f2-animado-tour/animacao.css
  - app/nucleo/static/revista/f2/svg-tour.js
---

## Decided
A animação por passo do F2 grava a opacidade de cada peça também numa variável CSS (`--ab-o`) e uma regra mais específica, também !important, aplica essa variável dentro do passo ativo. O svg-tour.js fica sem alteração.

## Tried and ruled out
Animar só com `style.opacity` inline: dentro do passo ativo nada some; só translate/scale aparecem. O sintoma visto pelo usuário: "as cores animam, o texto tem uma ligeira animação mas já está à mostra antes".

## Watch out
O svg-tour injeta `.svg-tour--dim .svg-tour-active, .svg-tour--dim .svg-tour-active * { opacity: 1 !important }` (dimOthers). Qualquer efeito de opacidade em filhos do alvo do passo é anulado por essa regra. Para medir, a opacidade inline aparece 0 e a calculada (getComputedStyle) aparece 1.

In the code:
- example/f2-animado-tour/animacao.js: helper `op(el, v)` grava `opacity` e `--ab-o`; '' limpa os dois.
- example/f2-animado-tour/animacao.css: `#revista.svg-tour--dim .svg-tour-active [style*="--ab-o"] { opacity: var(--ab-o) !important; }`
- Regra de origem: app/nucleo/static/revista/f2/svg-tour.js, CSS injetado (linha ~106).
