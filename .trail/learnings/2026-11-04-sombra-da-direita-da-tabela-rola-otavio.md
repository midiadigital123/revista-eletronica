---
title: "Sombra da direita da tabela rolável é um ::after sticky com top e right, num invólucro flex"
author: Otavio
date: 2026-11-04
branch: feat/ux-u10a-tabela-rolavel
id: l-3f3ff84b
scope: repo
status: active
src: agent
touches:
  - app/nucleo/static/ui/ui.css
---

## Decided
A sombra da borda direita da .tabela-rolavel (ui.css) é o ::after do próprio invólucro: o invólucro é display:flex, o ::after vem depois da tabela com width 0.5rem e margin-left -0.5rem (não cria rolagem) e position:sticky com top:0 e right:0. A da esquerda é box-shadow na .fixa, não ::after.

## Tried and ruled out
- ::after sticky só com right:0: a faixa tem a altura da caixa e sobe junto quando a tabela rola na vertical; no fim da rolagem ela some. Precisa do top:0 também.
- ::after absolute (left:100%) na .fixa: quando a .fixa vira static (lista de Projetos abaixo de 53rem, projeto.css), o ::after passa a medir pela caixa e cria rolagem lateral nela.
- Sombra inset ou background-attachment no invólucro: fica por baixo das células com fundo (thead, linha de grupo do painel).

## Watch out
O painel tinha um script próprio (data-rolou-x/-y) no painel.html; o componente tabelaRolavel o substitui e não liga sombra vertical (Flat Rule do DESIGN.md: a borda do thead basta).
