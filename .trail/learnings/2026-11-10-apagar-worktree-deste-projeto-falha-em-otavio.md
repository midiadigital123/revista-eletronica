---
title: "Apagar worktree deste projeto falha em arquivos do container, e a limpeza termina pelo próprio Docker"
author: Otavio
date: 2026-11-10
branch: chore/kanban-pausa
cost: { minutes: 1, tokens: 1995 }
id: l-5e1a6921
scope: repo
status: active
src: agent
touches:
  - kanban.md
  - state.md
---

## Decided
Worktree que subiu a stack Docker fica com arquivos do root (mídia enviada, screenshots do E2E) que o usuário não consegue apagar. O comando do git que remove a worktree então falha no meio. Ele já apagou o registro da worktree, mas a pasta fica para trás. Termine apagando essas pastas órfãs por um container com o diretório montado (como root). Nunca use sudo, e nunca toque numa pasta que ainda é worktree registrada. A stack Docker de cada worktree (containers e o volume de banco) não sai junto: derrube-a à parte, pelo rótulo do projeto do compose.

## Tried and ruled out
- Remover só pelo git: 44 de 78 falharam com "Permissão negada" por causa dos arquivos do root.
- Loop do shell sobre a lista de projetos no zsh: o zsh não separa a variável em palavras, e o loop rodou uma vez com a lista inteira, sem apagar nada. Rode o script com bash.

## Watch out
- Antes de apagar, confira os arquivos ignorados que não estão no git. As worktrees antigas tinham .env do sistema Express antigo, que só existiam ali; eles foram guardados fora do repositório.
- A pasta revista-eletronica contém o .git do repositório inteiro: nunca é uma worktree a apagar.
- Commit que só existe numa worktree destacada vira lixo ao removê-la. Guarde-o numa branch antes (foi feito com arquivo/s07-agente).

In the code:
- Pastas órfãs: `docker run --rm --user root --entrypoint sh -v "<pasta-pai>:/w" revista-eletronica-app:latest -c "rm -rf /w/<nome>"` e depois `git worktree prune`.
- Stack de uma worktree: os containers saem do filtro `label=com.docker.compose.project=<nome>`; os volumes vêm de `docker inspect` dos Mounts.
