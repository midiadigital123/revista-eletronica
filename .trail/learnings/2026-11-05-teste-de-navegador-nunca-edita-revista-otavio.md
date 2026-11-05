---
title: Teste de navegador nunca edita revista que ele mesmo não criou
author: Otavio
date: 2026-11-05
branch: main
cost: { minutes: 1, tokens: 5870 }
id: l-a00fd662
scope: repo
status: active
src: agent
touches:
  - CLAUDE.md
  - app/e2e/tests/helpers.ts
---

## Decided
Regra do usuário, sem exceção: um teste E2E nunca edita uma revista que o próprio teste não criou, nem o que alimenta a revista (projeto, variáveis, cortes, textos, arquivos, template escolhido). O spec cria o próprio parceiro "E2E …", a cascata gera o projeto e a revista dele, e o teste edita só esse. A limpeza do fim da execução apaga tudo.

## Tried and ruled out
- Gravar num dado real e "voltar o valor original no fim": quando o teste falha no meio, o dado real fica alterado. Aconteceu em 05/11: a regional do SAESE ficou "E2E".
- Usar a revista DEMONSTRAÇÃO ou a 1ª/última linha da planilha: não foi o teste que criou.

## Watch out
Specs antigos ainda gravam em dados que não criaram (autosave na planilha de Variáveis, estados, os que usam a DEMONSTRAÇÃO). Spec novo ou alterado segue a regra.

In the code: CLAUDE.md (Conventions); helper novoParceiro em app/e2e/tests/helpers.ts; manage.py limpar_e2e (D-224).
