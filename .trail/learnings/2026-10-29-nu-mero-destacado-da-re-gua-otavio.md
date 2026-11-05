---
title: "Número destacado da régua escolhe a cor do texto pelo contraste do WCAG, não pelo APCA"
author: Otavio
date: 2026-10-29
branch: refatoracao-django
cost: { minutes: 23, tokens: 72675 }
id: l-66210edd
scope: repo
status: active
src: agent
touches:
  - app/nucleo/static/revista/f1/script.js
  - state.md
---

## Decided
- A cor do texto sobre a cor do padrão (número destacado da régua) é a que dá a maior razão de contraste do WCAG 2 entre preto e branco. Com as cores atuais, sai sempre preto (sobre o vermelho #f72628: 5,3:1).

## Tried and ruled out
- Branco escolhido por APCA (como estava): sobre o vermelho dá 3,99:1, abaixo do AA (4,5:1) que a revisão de acessibilidade cobra.
- Escurecer o vermelho do padrão 1 mantendo o branco: mudaria a cor do padrão em toda a revista.

## Watch out
- Branco "parece melhor" no vermelho e o APCA concorda, mas o critério exigido é a razão do WCAG 2; não volte para o branco sem trocar a cor do padrão.

In the code: `corTextoSobre` em app/nucleo/static/revista/f1/script.js e os asserts correspondentes em regua.test.mjs. Decisão D-158 no state.md.
