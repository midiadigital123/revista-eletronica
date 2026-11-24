---
title: Etapa canônica que falta na matriz do parceiro não ganha botão de criar etapa do projeto; a correção é trocar de matriz
author: Otavio
date: 2026-11-24
branch: main
cost: { minutes: 8, tokens: 215468 }
id: l-5b3b0e6a
scope: repo
status: active
src: agent
touches:
  - app/nucleo/servicos/resolver.py
---

## Decided
O botão "Criar etapa do projeto" aparece só para etapa não canônica (fora de 2EF, 5EF, 9EF e 3EM). Se o parceiro tem corte numa etapa canônica que a matriz dele não tem, a pendência corte_sem_matriz continua só informando, sem botão: a correção é trocar de matriz.

## Tried and ruled out
Botão para qualquer etapa sem matriz, como no desenho antigo da branch: deixaria criar uma versão paralela de etapa da Comunitária apontando para outra matriz, o que o desenho já tratava como antiobjetivo.

## Watch out
O botão e a regra de criar dependem da constante com as 4 canônicas. Mudar a lista exige revisar a pendência e o diálogo de criar.

In the code:
- app/nucleo/servicos/resolver.py: pendencias, corte_sem_matriz
- app/nucleo/servicos/etapa_projeto.py: criar (na branch feat/etapa-do-projeto)
