---
title: "Agentes paralelos dividem o mesmo scratchpad, então cada um precisa da sua subpasta para credenciais e scripts de teste"
author: Otavio
date: 2026-11-03
branch: feat/telas-b-ux
cost: { minutes: 11, tokens: 124813 }
id: l-3641ba7f
scope: repo
status: active
src: agent
touches:
  - app/e2e/tests/revista-textos.spec.ts
  - app/nucleo/servicos/arquivos.py
  - app/nucleo/static/ui/componentes/autosave.js
  - app/nucleo/static/ui/telas/revista.css
  - app/nucleo/templates/ui/_componentes/impacto.html
  - app/nucleo/templates/ui/parciais/revista_arquivos.html
  - app/nucleo/templates/ui/parciais/revista_secao.html
  - app/nucleo/templates/ui/parciais/revista_situacao.html
  - app/nucleo/templates/ui/parciais/revista_textos.html
---

## Decided
Ao disparar agentes em paralelo (ondas da reforma de UX), cada prompt deve mandar o agente guardar senhas, arquivos .env do E2E e scripts auxiliares numa subpasta própria do scratchpad (ex.: `<scratchpad>/u4/`), nunca na raiz dele.

## Tried and ruled out
Dizer só "guarde no scratchpad": na onda 3, os dois agentes receberam o mesmo diretório de scratchpad da sessão. O agente do U5 sobrescreveu o `e2e.env` e o `pw.sh` do agente do U4 (porta 8022 no lugar de 8021), e a rodada base de Playwright do U4 rodou alguns segundos contra o app do outro agente.

## Watch out
Um resultado de Playwright "verde" ou "vermelho" pode ser da stack do outro agente se a URL veio de um arquivo compartilhado. Confira o `E2E_BASE_URL` contra a porta do próprio agente.

In the code:
- Portas da onda 3: U4/U9 `ux-u4` 8021, U5/U8b `ux-u5` 8022; integração `ux-integ` 8030.
