---
title: "Documento para a Infra diz o que o sistema exige, não como configurar o servidor"
author: Otavio
date: 2026-11-05
branch: main
cost: { minutes: 4, tokens: 34338 }
id: l-cbaa3e8f
scope: repo
status: active
src: agent
touches:
  - state.md
  - INFRA.md
  - README.md
  - docs/docker.md
---

## Decided
O guia para a equipe de Infra lista só o que é necessário e as particularidades deste sistema (repassar o Host, uploads de 50 MB, requisições de 120 s, proxy em container). A Infra sabe configurar proxy e HTTPS; exemplo de configuração sobra.

## Tried and ruled out
Seção de proxy com exemplo completo de Nginx (redirect, certificado, cabeçalhos): o usuário pediu para tirar, porque a Infra já sabe fazer.

In the code: INFRA.md, seção 3.
