---
title: O banco do dev é o do nome fixado na .env da raiz; worktree sem .env sobe outro banco vazio
author: Otavio
date: 2026-11-12
branch: feat/carga-2026
id: l-762817bf
scope: repo
status: active
src: agent
touches:
  - kanban.md
  - state.md
  - docker-compose.yml
---

## Decided
Em 12/11 o usuário mandou apagar os bancos de teste das worktrees (stack da carga e uma stack vazia) e as imagens Docker antigas do projeto, e manter só o banco do dev da porta 8000.

## Tried and ruled out
Apagar o volume do dev: é o banco com os dados que o usuário criou à mão, e ele não marcou.
`docker volume prune` nos volumes anônimos: nenhum é atribuível a este projeto, e o mesmo Docker guarda volumes de outros projetos do usuário.

## Watch out
A `.env` da raiz fixa o nome do projeto do compose, então o dev é o volume desse nome. Worktree sem `.env` usa o nome da pasta: um `docker compose up` sem `COMPOSE_PROJECT_NAME` sobe um banco novo e vazio, e o app disputa a porta 8000 com o dev. Ao conferir telas de uma worktree, use `COMPOSE_PROJECT_NAME=<nome> APP_PORT=8001` e avise a porta.

In the code: `.env` (COMPOSE_PROJECT_NAME), `docker-compose.yml` (APP_PORT), D-262 no `state.md`.
