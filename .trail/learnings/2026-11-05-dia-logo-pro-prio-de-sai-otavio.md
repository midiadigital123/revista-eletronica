---
title: "Diálogo próprio de saída precisa segurar o campo, porque abrir o modal tira o foco e o autosave grava antes da escolha"
author: Otavio
date: 2026-11-05
branch: main
cost: { minutes: 42, tokens: 123471 }
id: l-dc96bb21
scope: repo
status: active
src: agent
touches:
  - app/nucleo/static/ui/componentes/autosave.js
  - app/nucleo/templates/ui/_componentes/status_salvo.html
  - app/e2e/tests/autosave.spec.ts
---

## Decided
O diálogo "Alterações não salvas" (D-223) intercepta mousedown e click em links, gatilhos HTMX e botões de outro form quando há campo sujo. O mousedown com preventDefault impede que o campo perca o foco; o showModal, porém, move o foco para o diálogo e dispara o change do campo, e o autosave gravava antes de o usuário escolher. Solução: o campo fica "segurado" (o campoAuto ignora o change dele) enquanto o diálogo está aberto; em "Continuar editando", um blur único volta a salvar, porque o change daquele valor já foi gasto.

## Tried and ruled out
- Diálogo no base.html: aparece em páginas somente leitura (o texto "Salvar" quebra os testes de leitura) e só faz sentido onde há autosave. Ficou no status_salvo.html.
- Trocar o diálogo nativo no Voltar/fechar/recarregar: o navegador não deixa; o usuário aceitou manter o nativo nesses casos.

## Watch out
O <header> do diálogo dentro do cabeçalho da página quebrava um teste que recortava o HTML até o primeiro </header>.
Testes E2E de autosave rodam no banco de dev: escolha linha não aberta por quem usa o banco (a 1ª da planilha costuma estar) e apague os parceiros "E2E …" que os specs de Cortes, Impacto e Revista criam a cada execução.

In the code: app/nucleo/static/ui/componentes/autosave.js (sairSemSalvar, segurado, saidaLiberada); app/nucleo/templates/ui/_componentes/status_salvo.html; app/e2e/tests/autosave.spec.ts ("sair por link…").
