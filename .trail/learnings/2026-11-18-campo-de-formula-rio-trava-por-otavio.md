---
title: "Campo de formulário trava por permissão com prop positiva, porque o componente não entende negação e variável ausente deixa o campo livre"
author: Otavio
date: 2026-11-18
branch: integ/cotton-3
id: l-fe4fc971
scope: repo
status: active
src: agent
touches:
  - docs/telas/design-system.md
  - kanban.md
  - state.md
  - app/nucleo/templates/cotton/input.html
  - app/nucleo/widgets.py
  - app/nucleo/tests/test_componentes_cotton.py
---

## Decided
Os controles das telas (campo de texto, lista e texto longo) viraram componentes com o estado em props: erro (`:erros`, `erro_id`) e trava (`:editavel`, `trava`). A prop de trava é positiva ("editável") e recebe a variável de permissão direto. Condição composta de erro vai como texto: `erros="{% if a or b %}1{% endif %}"`.

## Tried and ruled out
- Prop negativa (`:travado="not pode_gravar"`): o django-cotton não avalia `not` em prop dinâmica; o valor fica sempre verdadeiro.
- Chamar a função da classe dos widgets de `classe`: colide com a variável local `classe` (o modelo) na view de exclusão.

## Watch out
- Variável ausente do contexto em `:editavel="x"` deixa o campo editável, enquanto o `{% if not x %} readonly` antigo travava. A view tem de mandar a permissão sempre. Em `:erros`, variável ausente não acende o erro (certo).
- Três controles ficam crus de propósito: autofocus só no primeiro campo de um laço, e dois onde `aria-invalid` e `aria-describedby` dependem de condições diferentes.

In the code: `app/nucleo/templates/cotton/input.html`, `select.html`, `textarea.html`; `app/nucleo/widgets.py::classe_css`; catraca e exceções em `app/nucleo/tests/test_componentes_cotton.py`; D-274.
