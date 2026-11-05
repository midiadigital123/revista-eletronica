---
title: "No ano novo, matriz e template de texto nascem sem escolha, de propósito"
author: Otavio
date: 2026-10-29
branch: dev
cost: { minutes: 1, tokens: 892 }
id: l-5a316984
scope: repo
status: active
replaces: l-957de440
src: agent
touches:
  - state.md
  - docs/modelo-er.md
---

## Decided
Ao abrir um ano, o parceiro não herda a matriz nem os templates de texto do ano anterior. Tudo nasce sem escolha e o "Validado" fica bloqueado até alguém escolher. O usuário quer que nada seja atribuído automaticamente; a escolha em lote na página "Templates" reduz o trabalho.

## Tried and ruled out
Clonar a escolha junto com o ano (era a D-088): seria atribuição automática, que o usuário recusou.

## Watch out
Valores das variáveis também renascem vazios; o atalho é o botão manual "Copiar valores do ano anterior", por projeto.

In the code: state.md D-106 (substitui o clone da escolha da D-088), D-107; docs/modelo-er.md ainda mostra o clone antigo.
