---
title: "Para rodar a suíte de navegador inteira sem tocar no banco de dev, use uma stack isolada com a demonstração"
author: Otavio
date: 2026-11-05
branch: main
cost: { minutes: 35, tokens: 138069 }
id: l-dd8f742d
scope: repo
status: active
src: agent
touches:
  - state.md
  - app/e2e/tests/autosave.spec.ts
  - app/e2e/tests/estados.spec.ts
  - app/e2e/tests/helpers.ts
  - app/e2e/tests/impresso.spec.ts
  - app/e2e/tests/item.spec.ts
  - app/e2e/tests/linhas.spec.ts
  - app/e2e/tests/mec.spec.ts
  - app/e2e/tests/painel.spec.ts
  - app/e2e/tests/revista-textos.spec.ts
---

## Decided
Os specs da matriz e da revista partem da DEMONSTRAÇÃO (para copiá-la ou só lê-la), e o banco de dev do usuário normalmente não a tem. A suíte inteira roda numa stack compose própria: banco e volume novos, migrate, criar_demo --ano 2026, Ano 2025, superusuário e2e e usuário imp-e2e (grupo Impresso), app numa porta própria. No fim, a stack é derrubada com o volume.

## Tried and ruled out
- Só passar -p <nome>: o .env fixa COMPOSE_PROJECT_NAME, e o compose sobe em cima do dev. Defina também COMPOSE_PROJECT_NAME=<nome> no ambiente do comando.
- Achar o D01 da matriz própria pela busca do admin: a cópia da Demonstração tem o mesmo texto, e a busca devolve dois. Filtre por matriz (matriz_etapa_cc__matriz__id__exact).

## Watch out
Projeto recém-criado aparece na planilha de Variáveis com o nome provisório "<parceiro> - NOME DO PROJETO"; o rótulo da célula é esse nome + o campo.
O teardown do Playwright limpa o banco de E2E_COMPOSE_PROJECT; sem essa variável, limpa o dev.

In the code: COMPOSE_PROJECT_NAME=<nome> APP_PORT=8040 docker compose -p <nome> up -d --wait db app; E2E_BASE_URL=http://localhost:8040 E2E_COMPOSE_PROJECT=<nome> npx playwright test; helpers matrizPropria/revistaPropria/regional em app/e2e/tests/helpers.ts.
