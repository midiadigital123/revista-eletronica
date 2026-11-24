---
title: "O svg-tour aceita HTML dentro de um SVG gerado pelo servidor, com dois cuidados: minimapa sem estilo pela raiz e seleção de texto liberada"
author: Otavio
date: 2026-11-06
branch: feat/f2-fase0
id: l-7981697c
scope: repo
status: active
src: agent
touches:
  - state.md
  - example/f2-gerado/gerar.py
---

## Decided
O svg-tour aceita um SVG gerado pelo servidor com HTML dentro de foreignObject sem nenhuma alteração no tour: o protótipo da fase 0 provou zoom e pan (o tour troca o viewBox, então o HTML escala junto e fica vetorial a 1200%), minimapa, texto longo com corte em 3 linhas e o resto no modal, passo desligado com o layout refluindo por coluna, e clique, Enter e Escape nos botões de mais. O usuário aprovou em 06/11: a navegação funciona, e o visual é trabalho do design depois. Por isso as fases seguintes geram o F2 em SVG no servidor em vez de HTML por blocos.

## Tried and ruled out
CSS interno do SVG com seletor pela classe da raiz do svg: o minimapa clona o SVG e tira class e style da raiz antes de serializar numa imagem, então todo estilo morria e os blocos saíam pretos na miniatura; os seletores não podem depender da raiz. Deixar a seleção de texto como vem: o stage do tour usa user-select none, e o texto do foreignObject não era selecionável; user-select text só nos divs do HTML resolve, e o arrasto continua movendo a vista sem criar seleção.

## Watch out
Texto que transborda do foreignObject não aumenta a caixa que o tour mede (getBBox): a altura tem de ser fixa e o corte feito por CSS. Um bloco mais alto que a área visível no minScale do tour ancora e pede arrasto, e o que fica abaixo da dobra some do passo: ou baixar o bloco, ou reduzir o minScale. Fontes da página não chegam ao minimapa; só o style interno do SVG. Nada foi testado em Safari e Firefox (o Playwright local só tem Chromium), e foreignObject dentro de imagem é onde o Safari costuma falhar.

In the code:
example/f2-gerado/gerar.py (CSS interno sem seletor na raiz; .f2g-tabela com grid-auto-rows 32px e -webkit-line-clamp 3; user-select text em .f2g-desc e .f2g-tabela), verificar.cjs (NODE_PATH do checkout principal). svg-tour.js: minimapa remove class em :559, user-select none no stage em :33, zoom por viewBox em :1164. Decisão D-228 no state.md.
