---
title: "Página com bloqueio que volta do bfcache precisa recarregar, e o Playwright não reproduz o bfcache"
author: Otavio
date: 2026-11-05
branch: main
cost: { minutes: 10, tokens: 164121 }
id: l-1fadf603
scope: repo
status: active
src: agent
touches:
  - app/nucleo/static/nucleo/bloqueio.js
  - app/e2e/tests/bfcache.spec.ts
---

## Decided
Ao voltar, o pagehide libera o bloqueio da aba; ao avançar, o navegador restaura a página do bfcache com a sessão antiga, a renovação dá 409 e o formulário vira "Você perdeu o bloqueio". O bloqueio.js agora recarrega a página no pageshow com persisted: o GET novo pega outro bloqueio (o mesmo usuário assume, D-191). D-222.

## Tried and ruled out
- Rodar o voltar/avançar de verdade no Playwright, mesmo tirando o --disable-back-forward-cache dos argumentos padrão: o Chromium sob o Playwright não restaura do bfcache (notRestoredReasons: "masked", a instrumentação do próprio Playwright bloqueia).
- Deixar de liberar no pagehide quando a página entra no bfcache: o bloqueio ficaria preso 30 s ao sair de verdade.

## Watch out
O teste simula o bfcache: libera o bloqueio (o POST do pagehide) e dispara um PageTransitionEvent("pageshow", {persisted: true}). Ele falha com o bloqueio.js antigo.
Ao escolher uma revista no E2E, evite projeto "Em edição": o dono do banco de dev pode estar com ela aberta no navegador.

In the code: app/nucleo/static/nucleo/bloqueio.js (handler pageshow); app/e2e/tests/bfcache.spec.ts.
