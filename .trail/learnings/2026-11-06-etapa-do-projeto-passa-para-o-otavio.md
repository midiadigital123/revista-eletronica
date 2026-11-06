---
title: "Etapa do projeto passa para o projeto recriado, e matriz que ganha a mesma etapa abre pendência de escolha"
author: Otavio
date: 2026-11-06
branch: main
cost: { minutes: 12, tokens: 62885 }
id: l-a5013407
scope: repo
status: active
src: agent
touches:
  - docs/superpowers/specs/2026-11-06-etapa-do-projeto-design.md
  - state.md
---

## Decided
Quando a cascata arquiva o projeto e cria outro para o mesmo parceiro no ano, o projeto novo herda as etapas do projeto (com a foto da base e o vínculo). Se a matriz do parceiro passar a ter a mesma etapa, abre-se uma pendência que bloqueia o Validado, com dois botões: "manter a do projeto" ou "usar a da matriz". Até a escolha, vale a do projeto.

## Tried and ruled out
- Projeto novo começar sem a etapa: o texto digitado ficaria preso no arquivado.
- Botão "trazer do arquivado": depende de alguém lembrar de clicar.
- A etapa do projeto continuar valendo só com um aviso: o parceiro fica numa versão paralela sem decisão.
- A da matriz passar a valer sozinha: a revista muda sem ninguém ver.

## Watch out
Só existe 1 projeto ativo por parceiro no ano (unique parcial), então "dono = projeto" quase equivale a parceiro_ano. A regra "só para etapa que a matriz não tem" não cabe em CHECK, porque a matriz fica no parceiro_ano: vale na criação, e o caso posterior vira a pendência.

In the code: D-228 no state.md; docs/superpowers/specs/2026-11-06-etapa-do-projeto-design.md, seção 10; servicos/cascata.py::gravar_cortes (arquiva e cria o projeto).
