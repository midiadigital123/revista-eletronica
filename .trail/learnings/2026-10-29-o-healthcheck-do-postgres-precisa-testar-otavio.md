---
title: "O healthcheck do Postgres precisa testar por TCP, senão o app conecta durante o initdb"
author: Otavio
date: 2026-10-29
branch: refatoracao-django
cost: { minutes: 5, tokens: 31342 }
id: l-af81f53a
scope: repo
status: active
src: agent
touches:
  - docker-compose.yml
---

## Decided
O healthcheck do Postgres no compose usa `pg_isready -h 127.0.0.1`, e o app só sobe quando o banco está saudável. A porta do app fica presa a localhost e é configurável, porque vários worktrees sobem o compose ao mesmo tempo.

## Tried and ruled out
- `pg_isready` sem `-h`: ele testa o socket Unix. Num volume novo, a imagem oficial roda um servidor temporário só no socket durante o initdb. O check passa nessa fase, o app roda o migrate e a conexão cai quando o servidor reinicia. A falha é intermitente e acontece em todo worktree novo.
- Porta fixa `8000:8000` em todas as interfaces: o segundo worktree falha com "port already allocated", e o runserver com DEBUG fica exposto na rede local.

## Watch out
- `docker compose run --rm app ...` não publica porta, então os testes rodam em paralelo entre worktrees. Só `up` e Playwright disputam a porta.
- A senha do Postgres só vale na criação do volume. Se mudar o `.env`, é preciso rodar `docker compose down -v`.

In the code: docker-compose.yml (serviços db e app), APP_PORT, E2E_BASE_URL em app/e2e/playwright.config.ts.
