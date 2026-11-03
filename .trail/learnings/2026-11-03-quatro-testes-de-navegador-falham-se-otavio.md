---
title: "Quatro testes de navegador falham se o banco não tiver a revista de demonstração, sem relação com a mudança"
author: Otavio
date: 2026-11-03
branch: feat/telas-b-lacunas
cost: { minutes: 18, tokens: 53953 }
id: l-a6c6a4fe
scope: repo
status: active
src: agent
touches:
  - state.md
  - app/e2e/tests/fumaca.spec.ts
  - app/nucleo/static/ui/componentes.js
  - app/nucleo/templates/ui/base.html
  - app/nucleo/tests/test_ui_base.py
  - docs/telas/design-system.md
  - app/e2e/tests/cortes.spec.ts
  - app/nucleo/templates/ui/cortes.html
  - plans/revista-express-telas-b-ux.md
---

## Decided
Antes de culpar uma mudança por falha no Playwright completo, confira se o banco tem a revista DEMONSTRAÇÃO. Os specs painel, impresso, item e revista-textos procuram por ela no admin e estouram o tempo de 30 s quando ela não existe.

## Tried and ruled out
- Atribuir as 4 falhas ao carregamento do Alpine/Sortable na base (U1): os outros 28 specs, que abrem todas as telas B, passaram; as 4 falhas são exatamente os specs que dependem da demo.

## Watch out
- O spec antigo de Cortes cria parceiros "E2E A/B <sufixo>" no banco a cada execução; o banco de dev acumula esses parceiros.
- Sem E2E_ADMIN_* e E2E_IMPRESSO_* os specs pulam em silêncio: "0 falhas" com muitos pulados não prova nada.

In the code: app/e2e/tests/{painel,impresso,item,revista-textos}.spec.ts; dados com `docker compose run --rm app python manage.py criar_demo --ano 2026`.
