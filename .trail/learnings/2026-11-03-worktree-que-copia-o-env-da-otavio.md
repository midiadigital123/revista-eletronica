---
title: "Worktree que copia o .env da raiz sobe o compose em cima do ambiente de dev, porque o nome do projeto está fixo no .env"
author: Otavio
date: 2026-11-03
branch: feat/telas-b-ux
cost: { minutes: 25, tokens: 67236 }
id: l-f7419e3e
scope: repo
status: active
src: agent
touches:
  - app/e2e/tests/helpers.ts
  - app/e2e/tests/impresso.spec.ts
  - app/e2e/tests/painel.spec.ts
  - app/nucleo/static/ui/telas/painel.css
  - app/nucleo/templates/ui/painel/painel.html
  - app/nucleo/templates/ui/parciais/painel_corpo.html
  - app/nucleo/tests/test_ui_painel.py
  - app/nucleo/urls/ui_painel.py
  - plans/revista-express-telas-b-ux.md
---

## Decided
Ao preparar um worktree com compose próprio, copie o .env da raiz e apague a linha COMPOSE_PROJECT_NAME (ou exporte um nome próprio em todo comando). Só assim o worktree ganha banco, volume e containers próprios.

## Tried and ruled out
- Confiar que o nome do projeto vem da pasta do worktree: o COMPOSE_PROJECT_NAME do .env tem precedência. Na onda 2 da reforma de UX, dois agentes recriaram o app do dev do usuário com o código do worktree e rodaram migrate e criar_demo no banco de dev (criar_demo troca a senha do demo-preview a cada execução).

## Watch out
- Depois de um incidente desses, recrie o app do dev a partir da raiz (`docker compose up -d app`) e confira `docker ps` com o label com.docker.compose.project.working_dir.

In the code: .env (COMPOSE_PROJECT_NAME=revista-eletronica), docker-compose.yml (APP_PORT), plans/revista-express-telas-b-ux.md ("Modo de execução").
