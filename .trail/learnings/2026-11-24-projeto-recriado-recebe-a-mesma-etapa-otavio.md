---
title: "Projeto recriado recebe a mesma etapa do projeto que estava no arquivado, em vez de uma cópia"
author: Otavio
date: 2026-11-24
branch: feat/cascata-herda-etapa
id: l-83b20fd9
scope: repo
status: active
src: agent
touches:
  - app/nucleo/servicos/cascata.py
  - app/nucleo/tests/test_etapa_projeto.py
  - state.md
---

## Decided
Quando um parceiro perde todos os cortes e depois os recebe de volta, nasce um projeto novo. A etapa não canônica que o projeto antigo tinha (a cópia editada pela Pedagógica) muda de dono: a mesma linha passa para o projeto novo, com descritores, tarefas, arquivos dos itens, base e foto. Assim nada do que foi digitado se perde, e a revisão em 3 vias volta sozinha se a base mudou enquanto o projeto esteve arquivado. A etapa é levada mesmo que o corte dela não volte: fica guardada, sem uso.

## Tried and ruled out
- Copiar a etapa para o projeto novo: ficariam duas versões do mesmo texto e o arquivo do item duplicado.
- Trocar o dono com update em massa: não grava histórico (autor e motivo).
- Levar só as etapas cujo corte voltou: o texto das outras ficaria preso no projeto arquivado.
- Travar a troca de dono no trigger: o trigger só recusa trocar a base; não foi preciso mexer nele nem criar migration.

## Watch out
É a única exceção à regra "projeto arquivado fica congelado". Depois da transferência o projeto arquivado fica sem etapas próprias, então não espere encontrá-las nele. O relatório do trail check nesta branch aponta conflitos que são da branch inteira contra a main (etapas 2 a 5), não desta mudança.

In the code:
- `app/nucleo/servicos/cascata.py`, `gravar_cortes`, logo depois de criar o projeto novo: laço sobre `MatrizEtapaCC` de projeto arquivado do mesmo `parceiro_ano`, com `_salvar(mec, usuario, update_fields=["projeto"])` e `_change_reason = "projeto recriado pela cascata"`.
- Testes: `app/nucleo/tests/test_etapa_projeto.py`, classe `CascataTest`.
- Decisões D-281 e D-285 no `state.md`.
