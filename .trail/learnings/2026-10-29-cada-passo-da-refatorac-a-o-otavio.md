---
title: "Cada passo da refatoração Django faz commit local na própria branch, e as branches se encadeiam"
author: Otavio
date: 2026-10-29
branch: refatoracao-django
cost: { minutes: 3, tokens: 129901 }
id: l-eea319ff
scope: repo
status: active
src: agent
touches:
  - state.md
---

## Decided
Na Fase A, cada passo faz um commit local na sua própria branch feat/sNN, sem push e sem PR. As branches se encadeiam: a do S01 sai de refatoracao-django; S02 e S03b saem da do S01; S03 sai da do S02. O merge em refatoracao-django só acontece quando o usuário pedir.

## Tried and ruled out
- Fazer tudo sem commit: os subagentes rodam em worktree, e um worktree nasce do último commit. Assim, o S02, o S03 e o S03b não veriam o S01 e as branches por passo ficariam vazias.
- Parar depois de cada passo para o usuário commitar: isso trava o paralelismo entre (S02 → S03) e S03b.

## Watch out
- O state.md, o plano e o ER revisado continuam sem commit no checkout principal. Por isso, os worktrees não os enxergam: os subagentes leem esses arquivos pelo caminho absoluto do checkout principal.
- Os serviços db e app do compose não têm container_name, então cada worktree vira um projeto compose separado. Mesmo assim, a porta 8000 é única no host: só um app pode subir por vez.

In the code: decisão D-127 no state.md; branches feat/s01-esqueleto, feat/s02-*, feat/s03-*, feat/s03b-*.
