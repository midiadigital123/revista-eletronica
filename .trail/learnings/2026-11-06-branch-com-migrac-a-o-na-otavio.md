---
title: "Branch com migração não se desenvolve no diretório do dev ao vivo: vai para um worktree irmão com stack própria"
author: Otavio
date: 2026-11-06
branch: main
cost: { minutes: 1, tokens: 1470 }
id: l-54f46d2b
scope: repo
status: active
src: agent
touches:
  - docker-compose.yml
---

## Decided
Uma branch que muda o banco é desenvolvida num worktree irmão, com `.env` próprio e stack própria do compose, porque o diretório principal roda o dev que a equipe acessa pela rede e o compose monta o código por volume: qualquer alteração de modelo salva ali entra no app ao vivo antes de o banco ser migrado, e o app quebra para quem está usando.

## Tried and ruled out
- Criar a branch no próprio diretório do dev com `git switch -c`: descartado porque o código montado por volume muda o app ao vivo no mesmo instante do primeiro arquivo salvo.

## Watch out
O `.env` copiado precisa trocar o nome do projeto do compose, porque senão a stack do worktree sobe em cima do dev (o nome fixo no `.env` vence o diretório), e precisa tirar o bind em 0.0.0.0, porque senão abre outra porta com DEBUG na rede.

In the code: `docker-compose.yml` monta `./app:/app`; worktree em `/home/otavio.peres/dev/revista-express-etapa` com `COMPOSE_PROJECT_NAME=etapa-projeto` no `.env`; testes com `docker compose run --rm app python manage.py test` nesse diretório.
