---
title: "A revista mostra os descritores na ordem do editor, por uma lista própria que entra no hash do Validado"
author: Otavio
date: 2026-11-24
branch: fix/descritor-codigo-livre
id: l-b50f4b30
scope: repo
status: active
src: agent
touches:
  - CLAUDE.md
  - app/e2e/fixtures/pagina/f1.html
  - app/e2e/fixtures/revista.zip
  - app/nucleo/matriz.py
  - app/nucleo/servicos/html.py
  - app/nucleo/servicos/resolver.py
  - app/nucleo/static/revista/f1/regua.test.mjs
  - app/nucleo/static/revista/f1/script.js
  - app/nucleo/tests/fixtures/resolver-4cortes.json
  - app/nucleo/tests/fixtures/resolver-passo-nulo.json
---

## Decided
O usuário decidiu em 24/11 que a ordem dos descritores na revista segue a ordem arrastada no editor, não a alfabética do código. A etapa do F1 ganhou a lista "ordem" com os códigos, e a página a usa. Reordenar descritores passa a tirar o Validado, com o modal de impacto.

## Tried and ruled out
- Só tirar a ordenação alfabética da página e confiar na ordem das chaves do JSON: o hash do Validado ordena as chaves, então a ordem ficaria fora dele e reordenar não avisaria o impresso.
- Tirar a ordenação de chaves do hash: o hash passaria a mudar por ordem de inserção de qualquer dicionário, sem mudança de conteúdo.

## Watch out
- O hash de toda revista mudou uma vez com esta mudança: revista validada antes dela precisa ser validada de novo.
- Mudança no formato do JSON do F1 quebra 4 testes de gabarito (JSON do resolver, página do F1 e zip); eles se regeram com REGERAR_FIXTURES=1.
- Reordenar tarefas continua sem efeito na revista: a tarefa entra na escala pela faixa.
- Revista arquivada antes desta mudança não tem a lista; a página cai na ordem alfabética.

In the code:
- app/nucleo/servicos/resolver.py: _f1_escalas ("ordem")
- app/nucleo/static/revista/f1/script.js: descriptorKeys
- docker compose run --rm -e REGERAR_FIXTURES=1 app python manage.py test nucleo.tests.test_resolver nucleo.tests.test_preview nucleo.tests.test_empacotar --noinput
- state.md: D-291
