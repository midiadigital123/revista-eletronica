---
title: "No Alpine em build CSP, toda propriedade do componente precisa estar declarada no objeto, senão ela vai parar no componente de fora"
author: Otavio
date: 2026-11-03
branch: feat/telas-b-ux
cost: { minutes: 107, tokens: 243841 }
id: l-6186f186
scope: repo
status: active
src: agent
touches:
  - app/nucleo/static/ui/ui.css
  - app/nucleo/templates/ui/templates/lista.html
  - app/nucleo/tests/test_ui_templates.py
  - app/nucleo/tests/test_ui_matriz.py
  - app/nucleo/urls/ui_matriz.py
  - app/nucleo/templates/ui/anos/ano.html
  - app/nucleo/tests/test_ui_anos.py
  - app/nucleo/urls/ui_anos.py
  - app/nucleo/templates/ui/parciais/revista_secoes.html
  - app/nucleo/templates/ui/revista/revista.html
---

## Decided
Componentes Alpine das telas B (registrados com `Alpine.data`, build CSP) declaram no objeto retornado todas as propriedades que o `init()` ou os métodos atribuem, mesmo que comecem `null`.

## Tried and ruled out
Atribuir `this.algo = …` só dentro do `init()`: no build CSP, a propriedade não declarada resolve para o escopo do componente pai. Na aba de cores do projeto, as 5 amostras de cor ficavam dentro de um `campoAuto` e todas passaram a mexer no mesmo controle.

## Watch out
O sintoma parece bug de evento (clicar numa amostra mexe na outra). Antes de depurar listeners, confira se a propriedade está declarada no objeto do `Alpine.data`.

In the code:
- `app/nucleo/static/ui/componentes.js` e `app/nucleo/static/ui/componentes/autosave.js`
