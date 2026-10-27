---
title: "Projeto não herda de outro projeto: ele apenas aponta para uma matriz"
author: Otavio
date: 2026-10-27
standing: true
id: l-90fc2221
scope: repo
status: active
src: init-sessions
touches:
  - state.md
  - docs/modelo-er.md
---

## Decided
- A ideia inicial era herança viva entre projetos, com sobrescrita local. Na conversa de modelagem ficou claro que nenhum projeto edita conteúdo da matriz e que as exceções são matrizes separadas, então o conflito pai e filho deixou de existir.
- In the code: No novo modelo Django o Projeto tem uma chave para a matriz (são 4 matrizes independentes) e não tem campo de projeto-base nem cadeia de herança. Ajustes de conteúdo só nas matrizes. O projeto guarda nome, textos da revista e intervalo mínimo. Ver D-051 (substitui D-045) em state.md e docs/modelo-er.md.

_From past Claude sessions here, Oct 27._
