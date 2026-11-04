---
title: "Playwright espera o DOMContentLoaded antes do alpinePronto, porque o Alpine vem do CDN com cache vazio"
author: Otavio
date: 2026-11-04
branch: feat/ux-u10d-critica
cost: { minutes: 25 }
id: l-201947d5
scope: repo
status: active
src: agent
touches:
  - "app/e2e/tests/helpers.ts#alpinePronto"
  - app/e2e/tests/estados.spec.ts
  - app/nucleo/templates/ui/base.html
---

## Decided
O helper alpinePronto (app/e2e/tests/helpers.ts) espera page.waitForLoadState('domcontentloaded') e só então o data-estado="" do status do autosave. Todo spec que esperava o data-estado direto passou a usar o helper (autosave, anos, cortes).

## Tried and ruled out
- Culpar o servidor: a planilha de Variáveis responde em ~0,13 s no banco da demo.
- Culpar o spec anterior: o estados.spec isolado e com --repeat-each=5 passa.
- Reproduzido: com page.route atrasando o @alpinejs/csp do jsDelivr em 6 s, o alpinePronto antigo falha com a mesma mensagem (timeout de 5 s, atributo ausente). O entrar() termina quando a URL muda, antes do DOMContentLoaded; os scripts defer do CDN (Alpine e Sortable) seguram esse evento, e cada contexto do Playwright começa com o cache vazio.

## Watch out
Não suba o timeout do expect para esconder isso: com a espera do DOMContentLoaded, um Alpine quebrado (SRI errado, 404) ainda falha em 5 s.
