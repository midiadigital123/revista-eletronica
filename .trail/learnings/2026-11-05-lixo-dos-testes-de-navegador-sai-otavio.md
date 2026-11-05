---
title: "Lixo dos testes de navegador sai no fim da execução por um comando, não dentro de cada spec"
author: Otavio
date: 2026-11-05
branch: main
cost: { minutes: 4, tokens: 51978 }
id: l-52dcd562
scope: repo
status: active
src: agent
touches:
  - state.md
  - app/e2e/tests/autosave.spec.ts
  - app/nucleo/static/ui/componentes/autosave.js
  - app/nucleo/templates/ui/_componentes/status_salvo.html
  - app/nucleo/tests/test_ui_matriz.py
  - docs/telas/design-system.md
  - app/e2e/tests/bfcache.spec.ts
  - app/nucleo/static/nucleo/bloqueio.js
  - app/nucleo/lotes.py
  - app/nucleo/templates/ui/parciais/validar_cartao.html
---

## Decided
Os specs do Playwright criam parceiros "E2E …" (com projeto e revista da cascata) e templates "E2E …" no banco de dev. No fim de toda execução, o globalTeardown roda o comando limpar_e2e. Ele apaga só o que tem nome "E2E …" e cujo registro de criação no histórico é do usuário de teste. Parceiro sai na ordem do apagar_ano; template sai pela regra da lixeira da tela, e fica (com aviso) se uma revista ainda o usa.

## Tried and ruled out
- Limpar em afterAll de cada spec: não roda quando o spec falha no meio. Foi assim que sobrou um template "E2E textos".
- Excluir o parceiro pela tela: o parceiro-ano protege o parceiro que tem projeto.
- Apagar por nome sem olhar o autor: levaria um "E2E …" criado por uma pessoa.
- Apagar as versões 2 a 8 do template "Padrão (F1)" LP 2026 (texto "Atualizado E2E…" de rodadas antigas): a v8 é a base das cópias da introdução de SAESE LP e SAEGO LP, e versão só sai junto com o template (D-207). Ficou como pergunta ao usuário.

## Watch out
O teardown chama docker compose exec a partir da raiz do repositório. Numa stack de worktree (-p <nome>), defina E2E_COMPOSE_PROJECT, senão ele limpa o banco errado ou só avisa.
Antes de apagar uma versão de template, confira as cópias de seção (RevistaSecao.template_versao) que apontam para ela.

In the code: app/nucleo/management/commands/limpar_e2e.py (--simular, --usuario); app/e2e/limpar.ts; app/e2e/playwright.config.ts (globalTeardown); app/nucleo/tests/test_limpar_e2e.py.
