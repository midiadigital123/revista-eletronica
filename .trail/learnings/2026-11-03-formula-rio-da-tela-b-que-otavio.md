---
title: "Formulário da tela B que deixa o ano de fora precisa checar o código repetido à mão, inclusive entre linhas do mesmo envio"
author: Otavio
date: 2026-11-03
branch: feat/telas-b-lacunas
cost: { minutes: 19, tokens: 158667 }
id: l-f54ee959
scope: repo
status: active
src: agent
touches:
  - state.md
  - app/e2e/tests/anos.spec.ts
  - app/nucleo/templates/ui/anos/ano.html
  - app/nucleo/templates/ui/anos/anos.html
  - app/nucleo/tests/test_ui_anos.py
  - app/nucleo/urls/ui_anos.py
---

## Decided
Nas tabelas por ano da tela B (etapas, componentes), o ano não é campo do formulário. Por isso o Django pula a checagem de unicidade (ano, código), e o banco recusaria com erro 500. A checagem é feita à mão em dois níveis: contra o banco (por linha) e entre as linhas do mesmo envio (no formset). O save fica em transação, e uma recusa do banco por corrida vira mensagem.

## Tried and ruled out
Só a checagem por linha contra o banco: duas linhas novas com o mesmo código passam (nenhuma existe ainda) e o save dá 500. A revisão reproduziu isso com POST forjado.
Limite de tamanho só no widget (maxlength): o servidor aceita e a mensagem que aparece é a do CHECK do banco ("Restrição ... foi violada").

## Watch out
Não rode a suíte Django em paralelo com outro agente que também roda testes: os dois usam o mesmo banco de teste e um apaga o do outro ("database test_revista does not exist").

In the code:
- app/nucleo/urls/ui_anos.py: _DoAno.clean_codigo, _SemRepetir.clean, transaction.atomic + IntegrityError na view `ano`
- campos TextField do modelo declarados como forms.CharField(max_length=20/200)
