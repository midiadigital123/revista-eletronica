---
title: Item que cruza um corte acende a cor do padrão mais alto
author: Otavio
date: 2026-10-27
standing: true
id: l-ff1c6d33
scope: repo
status: active
src: init-sessions
touches:
  - revista/script.js
  - revista/regua.test.mjs
  - "revista/script.js#montarFaixasRegua"
---

## Decided
- Quando a habilidade tem âncora menor em um padrão e maior em outro, a cor correta é a do padrão da âncora maior. O topo da linha é limite aberto, senão toda linha abaixo de uma que começa no corte ficaria no padrão acima.
- In the code: Lógica em `montarFaixasRegua` (revista/script.js), testada em `node revista/regua.test.mjs`. Exemplo: 390→446 com corte em 400 vira P03. Já 350→400 continua P02. Na linha mais alta, o topo é o máximo da escala. Registrado como D-044.

_From past Claude sessions here, Oct 23._
