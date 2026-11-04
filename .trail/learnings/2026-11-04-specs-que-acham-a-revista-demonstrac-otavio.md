---
title: Specs que acham a revista DEMONSTRAÇÃO na lista do admin quebram quando o banco passa de 100 revistas
author: Otavio
date: 2026-11-04
branch: feat/ux-u10d-critica
cost: { minutes: 10 }
id: l-a47aa572
scope: repo
status: active
src: agent
touches:
  - "app/e2e/tests/helpers.ts#revistaDemo"
  - app/e2e/tests/item.spec.ts
  - app/e2e/tests/revista-textos.spec.ts
---

## Decided
item.spec e revista-textos.spec acham a revista LP da demonstração pelo helper revistaDemo (app/e2e/tests/helpers.ts), que lê a Lista de Projetos B (revistaDaLista com o parceiro DEMONSTRAÇÃO), e abrem /admin/nucleo/revista/<pk>/change/ direto.

## Tried and ruled out
Procurar 'DEMONSTRAÇÃO' em #result_list de /admin/nucleo/revista/: o admin pagina em 100 e lista as mais novas primeiro; cada execução completa do Playwright cria projetos E2E (cortes, variáveis, autosave…) e, com 106 revistas, a demo caiu na 2ª página e os 3 testes estouraram 30 s só no projeto desktop-1440 (o 2º a rodar).

## Watch out
O banco de dev acumula esses projetos a cada rodada; falha que só aparece no 2º projeto do Playwright ou depois de várias rodadas costuma ser volume de dados, não a mudança.
Depois de ~10 rodadas completas no mesmo banco, o anos.spec já tinha criado ~20 componentes "Componente E2E Z…" em 2026: a grade de Cortes passou a ~95 parceiros × 100 células (1,8 MB de HTML) e o autosave.spec e o impacto.spec estouraram os 5 s com o status parado em "Salvando…". Com o banco recriado (criar_demo + 2025), 120/120.
