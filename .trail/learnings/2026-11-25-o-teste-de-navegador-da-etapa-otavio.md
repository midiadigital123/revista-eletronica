---
title: "O teste de navegador da etapa do projeto não cobre o Apontar, porque exigiria uma etapa não canônica fixa no banco de teste"
author: Otavio
date: 2026-11-25
branch: feat/abre-revisao
id: l-53865b20
scope: repo
status: active
src: agent
touches:
  - app/e2e/tests/helpers.ts
  - app/nucleo/management/commands/limpar_e2e.py
  - app/nucleo/management/commands/criar_demo.py
  - docs/e2e.md
  - app/nucleo/tests/test_ui_projeto_abas.py
---

## Decided
Em 25/11, ao planejar o E2E da etapa do projeto, o usuário decidiu que o "Apontar" (etapa não canônica apontada para uma canônica) fica só nos testes Django. O E2E cobre cópia local, edição isolada, aviso no editor da matriz, revisão, impresso e desfazer. O Apontar usa a mesma rota e o mesmo serviço da cópia local.

## Tried and ruled out
- Criar a etapa 4EF no preparo da stack do E2E: o comando de limpeza não apaga etapa, e a etapa nova vira coluna na grade de cortes de todos os outros specs.
- O próprio spec criar e apagar a 4EF pela página do ano: se o teste falhar no meio, a etapa fica no banco e afeta os outros specs.

## Watch out
- O banco do E2E só tem 2EF, 5EF, 9EF e 3EM, e a matriz Demonstração só tem 5EF e 9EF de LP.
- O spec da etapa do projeto deve copiar de uma matriz "E2E" própria, nunca da Demonstração: uma cópia derivada dela faria o aviso de projetos com cópia aparecer nos specs que abrem a Demonstração.

In the code: `app/e2e/tests/helpers.ts` (`matrizPropria`, `revistaPropria`), `app/nucleo/management/commands/limpar_e2e.py`, `app/nucleo/management/commands/criar_demo.py`, `docs/e2e.md`; testes Django do Apontar em `app/nucleo/tests/test_ui_projeto_abas.py` (`ApontarEtapaTest`).
