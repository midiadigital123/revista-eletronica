---
title: "As pendências da revista ficam num módulo próprio, e quem usa importa de lá, não do resolver"
author: Otavio
date: 2026-11-10
branch: feat/f2-f3
cost: { minutes: 36, tokens: 295116 }
id: l-14c3501a
scope: repo
status: active
src: agent
touches:
  - app/nucleo/management/commands/criar_demo.py
  - app/nucleo/tests/test_ui_templates.py
  - app/nucleo/dados/infografico-docx.json
  - app/nucleo/tests/test_preview.py
  - app/nucleo/infografico.py
  - app/nucleo/servicos/arquivos.py
  - app/nucleo/tests/test_infografico.py
  - app/nucleo/cortes.py
  - app/nucleo/revista.py
  - app/nucleo/servicos/cascata.py
---

## Decided
As pendências que travam o "Validado" saíram do resolver para um módulo próprio, separadas em F1 e F2 (D-252). Os chamadores passaram a importar do módulo novo.

## Tried and ruled out
Reexportar `pendencias` e `Pendencia` pelo resolver, para não mexer nos chamadores: o módulo novo importa o resolver (precisa de `resolver(revista)`), e o resolver importando o módulo novo fecha um ciclo que quebra quando o módulo de pendências é importado primeiro.

## Watch out
Código novo que precise das pendências deve importar de `servicos/pendencias.py`. A ordem da lista (F1, F2, capa, variáveis, nome do projeto) é a que a Situação da ficha e os testes esperam.

In the code: `app/nucleo/servicos/pendencias.py` (`Pendencia`, `pendencias`, `pendencias_f1`, `pendencias_f2`, `problema_dos_cortes`); chamadores `servicos/validacao.py`, `urls/painel.py`, `nucleo/revista.py`, `servicos/empacotar.py`; commit `b6347c4`.
