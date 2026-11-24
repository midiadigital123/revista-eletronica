---
title: "Duas rodadas de teste do Django na mesma stack travam: as duas disputam o mesmo banco de teste"
author: Otavio
date: 2026-11-24
branch: feat/matriz-nulo
id: l-bc2806ce
scope: repo
status: active
src: agent
touches:
  - kanban.md
  - state.md
---

## Decided
Roda-se uma rodada de testes por vez em cada stack do compose, e sempre com `--noinput`.

## Tried and ruled out
Disparar um teste rápido de módulo enquanto a suíte inteira roda em segundo plano na mesma stack: a segunda rodada encontra o banco de teste já criado e fica parada na pergunta "apagar o banco?", sem terminar; com `--noinput` ela apagaria o banco da primeira.

## Watch out
A rodada travada não dá erro: só não termina. O sinal é a linha "database test_revista already exists" no log do contêiner. Uma suíte que começou antes de uma correção também não a valida: os módulos já estavam carregados.

In the code: `docker compose run --rm app python manage.py test --noinput`; banco `test_revista`; para rodar em paralelo, outra stack (outro `COMPOSE_PROJECT_NAME`).
