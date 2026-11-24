---
title: A suíte de navegador continua em série mesmo depois que cada teste passou a gravar só no que cria
author: Otavio
date: 2026-11-09
branch: docs/atualizacao-2026-11-09
id: l-26ed2d0a
scope: repo
status: active
src: agent
touches:
  - CLAUDE.md
  - app/.env.example
  - app/e2e/playwright.config.ts
  - app/e2e/tests/helpers.ts
  - app/nucleo/models/controle.py
  - app/nucleo/usuarios.py
  - docs/e2e.md
  - docs/regras-de-negocio.md
  - state.md
  - app/e2e/tests/anos.spec.ts
---

## Decided
A suíte E2E segue com um worker só. O motivo antigo (vários specs gravavam na mesma revista de demonstração) caiu quando cada spec passou a criar o próprio dado, mas sobram dois: todos os specs entram com o mesmo usuário, e a mesma pessoa em outra aba toma o bloqueio; e o teste de anos abre e apaga o ano 2027, que vira o "ano mais recente" para quem entra pela raiz ou pelas rotas de início no mesmo momento.

## Tried and ruled out
Dois workers: o ano 2027 aberto por um spec vaza para os outros, e a suíte fica instável sem ganho medido.

## Watch out
O helper de login dos specs confere o sucesso olhando se a página saiu do login do admin. Desde que o login passou para as telas B, o login falho fica no login novo, então essa conferência sempre passa: senha errada não falha no login, falha depois, num passo sem relação. Pendente de correção (pergunta aberta no state.md).

In the code: `app/e2e/playwright.config.ts` (`workers: 1`), `app/e2e/tests/anos.spec.ts` (`abrirMaiorAno`), `app/e2e/tests/helpers.ts::entrar` (`not.toHaveURL(/\/admin\/login\//)`), `app/nucleo/contexto.py::ano_da_sessao`, decisões D-191, D-212, D-225, D-234.
