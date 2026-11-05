---
title: "No F2 animado, peça escondida à espera do passo só pode usar opacidade, senão o tour enquadra o lugar errado"
author: Otavio
date: 2026-11-05
branch: main
cost: { minutes: 7, tokens: 55092 }
id: l-8c812f98
scope: repo
status: active
src: agent
touches:
  - app/nucleo/static/revista/f2/svg-tour.js
---

## Decided
Na animação por passo do F2, as peças de um bloco ainda não visitado ficam escondidas só por opacidade. O deslocamento e a escala do movimento entram no primeiro quadro da animação, quando o tour já enquadrou o passo.

## Tried and ruled out
Esconder com a pose inicial do movimento (translate e scale até 0): os passos 2 e 3 passaram a enquadrar o título e o descritor, a 219%, em vez do bloco.

## Watch out
O svg-tour mede o alvo com getBBox no momento do go(). Um filho com transform CSS scale(0) conta como um ponto perto da origem do SVG e estica a caixa até o canto superior esquerdo. A opacidade não altera a caixa.

In the code:
- example/f2-animado-tour/animacao.js: `hide` do `fx()` faz só `op(g, 0)` e limpa o transform; `play()` aplica a pose inicial.
- Medição do tour: `_bbox` em app/nucleo/static/revista/f2/svg-tour.js (getBBox × getScreenCTM).
- Conferência usada: enquadramento (`t.current`) dos 4 passos igual ao da página com prefers-reduced-motion.
