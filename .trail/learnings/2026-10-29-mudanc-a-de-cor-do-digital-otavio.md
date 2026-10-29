---
title: "Mudança de cor do digital aparece para o impresso, e corte não pode encostar nos limites da escala"
author: Otavio
date: 2026-10-29
branch: refatoracao-django
cost: { minutes: 20, tokens: 205738 }
id: l-a54a9016
scope: repo
status: active
src: agent
touches:
  - app/nucleo/servicos/cascata.py
  - state.md
  - plans/revista-express-django.md
---

## Decided
- As cores dos padrões do F1 fazem parte do que o impresso vê em "o que mudou", junto com escalas e textos. O usuário escolheu isso mesmo sabendo que o impresso usa uma rampa verde própria (#b8ffd8 → #00662e), diferente das cores do digital.
- O corte precisa ficar estritamente dentro da escala: valor igual a 0 ou igual à escala máxima é recusado na gravação dos cortes. Isso ajusta a D-055, que aceitava os limites.

## Tried and ruled out
- Tirar as cores do conteúdo do impresso (era a recomendação): o usuário preferiu que nenhum ajuste passe sem ser visto.
- O JS da revista aceitar padrão vazio: a régua mostraria um padrão sem faixa; recusar na entrada mostra o erro na tela de cortes.

## Watch out
- Um corte nos limites cria um padrão vazio, e o JS do F1 recusa a etapa inteira (a escala some do preview sem erro visível ao usuário).

In the code: `conteudo_impresso` em app/nucleo/servicos/resolver.py inclui as cores; validação em `validar_linhas` de app/nucleo/servicos/cascata.py (teste `test_aceita_limites` muda). Decisão D-153 no state.md.
