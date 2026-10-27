---
title: "O que mudou para o impresso vem de um botão, não de um histórico"
author: Otavio
date: 2026-10-27
standing: true
id: l-75429450
scope: repo
status: active
src: init-sessions
---

## Decided
- O time de impresso só precisa ver o texto final que mudou para ajustar no InDesign. Rastrear mudanças tabela por tabela é complexo e fácil de errar, e o marco por data de download foi trocado pelo botão "Revista Impressa Atualizada".
- In the code: Calcular o diff comparando o texto final da revista de cada projeto com o instantâneo guardado no último clique de "Revista Impressa Atualizada". Ao clicar, o projeto zera os avisos. Mostrar só o trecho alterado. Não usar a data do download como marco (D-069 foi substituída).

_From past Claude sessions here, Oct 27._
