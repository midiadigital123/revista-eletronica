---
title: "Teste de navegador do autosave precisa esperar o 'Salvo às' visível, porque o texto escondido também conta como presente"
author: Otavio
date: 2026-11-03
branch: feat/telas-b-ux
cost: { minutes: 10, tokens: 155453 }
id: l-d70a7993
scope: repo
status: active
src: agent
touches:
  - state.md
  - app/e2e/tests/impacto.spec.ts
  - app/e2e/tests/impresso.spec.ts
  - app/e2e/tests/painel.spec.ts
  - app/e2e/tests/projeto.spec.ts
  - app/nucleo/lotes.py
  - app/nucleo/servicos/matriz.py
  - app/nucleo/static/ui/telas/projeto.css
  - app/nucleo/templates/ui/cortes.html
  - app/nucleo/templates/ui/parciais/cortes_grade.html
---

## Decided
Nos specs Playwright das telas B, a confirmação de que o autosave gravou é esperar `getByText(/Salvo às \d/)` visível, depois de `alpinePronto(page)`. Só então o teste navega ou confere o banco.

## Tried and ruled out
`toContainText("Salvo às")` no bloco de status: o status do autosave tem o texto no HTML escondido por `x-show`, então a asserção passa antes do POST gravar. O teste segue, navega, e o POST chega depois da navegação ou nem chega. Isso derrubou `impresso`, `painel` e `revista-textos` de forma consistente depois do U7b (hub Projetos), embora passassem antes.

## Watch out
O motivo de a corrida ter ficado consistente justamente com o U7b não foi achado. Se um spec de autosave voltar a falhar de forma intermitente, comece conferindo se ele espera o texto visível, e não apenas presente.

In the code:
- Helper `alpinePronto` em `app/e2e/tests/helpers.ts`.
- Specs corrigidos no U7: `impacto.spec.ts`, `impresso.spec.ts`, `painel.spec.ts`.
