---
title: "Exclusão pelo Collector, FKs DEFERRED e a chave do trigger"
author: Otavio
date: 2026-11-04
branch: feat/excl-base
id: l-e205d071
scope: repo
status: active
src: agent
---

## Decided
- `servicos/exclusao.py` pergunta ao `Collector` do Django o que impede (`ProtectedError.protected_objects`), separado para o objeto e para cada parte de `PARTES`, porque o PROTECT não desconta o que já está sendo coletado (o ParceiroAno do parceiro apareceria como uso).
- Dentro de `excluir`, depois do `delete()`, roda `SET CONSTRAINTS ALL IMMEDIATE` e, no fim, `SET CONSTRAINTS ALL DEFERRED`. As FKs que o Django cria no Postgres são DEFERRABLE INITIALLY DEFERRED: sem isso, uma linha nova gravada por outra transação só estouraria no commit, fora do `try`, e a página daria 500 em vez de mostrar o impedimento.
- A chave `revista.apagar_versoes` do trigger é ligada com `SET LOCAL` e desligada de novo antes de sair do bloco (`_versoes_apagaveis`). `SET LOCAL` dura até o fim da transação mais externa, não do savepoint: chamado dentro de outro `atomic`, o DELETE de versões ficaria liberado pelo resto da transação.
- O `apagar_ano` apaga por `Collector` (com `_history_user` em cada instância coletada), na ordem de `ORDEM_ANO`, e não chama `Etapa.delete()`: renumerar um ano que está saindo é trabalho à toa.

## Tried and ruled out
- Um `Collector` só para o ano inteiro: o PROTECT entre as tabelas do próprio ano barra a coleta. A ordem explícita das folhas para a raiz é o que funciona.
- Testar a corrida com duas conexões: o `mock.patch.object` no `remote_field.on_delete` (DO_NOTHING) faz o Django não ver o corte e o banco recusar, o mesmo caminho da corrida real.

## Watch out
- Na rota `ui_excluir`, o `<pk>` do ano é o próprio ano (2027), não o id.
- O `abrir_ano` só abre o maior ano + 1, então um spec não consegue criar 2019: o `excluir.spec.ts` abre o próximo ano (2027) e o apaga no mesmo teste.
