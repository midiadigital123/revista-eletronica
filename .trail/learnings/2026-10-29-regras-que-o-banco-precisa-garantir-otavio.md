---
title: "Regras que o banco precisa garantir ficam em SQL, porque o ORM do Django deixa passar"
author: Otavio
date: 2026-10-29
branch: refatoracao-django
cost: { minutes: 23, tokens: 74565 }
id: l-08d35e91
scope: repo
status: active
src: agent
touches:
  - state.md
  - app/nucleo/migrations/0006_template_versao_so_insert.py
  - app/nucleo/models/texto.py
  - app/nucleo/tests/test_constraints.py
  - app/nucleo/tests/test_revista.py
  - app/nucleo/db.py
  - app/nucleo/migrations/0004_projeto_revista_texto_controle.py
  - app/nucleo/migrations/0005_fks_compostas_projeto_revista.py
  - app/nucleo/models/__init__.py
  - app/nucleo/models/cadastro.py
---

## Decided
- A matriz duplicada aponta para a origem com ON DELETE SET NULL no próprio banco. A FK do Django é criada sem constraint, e a constraint real entra por SQL na migração.
- As versões de template são só de inserção, garantidas por um trigger no banco que recusa UPDATE e DELETE. O save() do modelo só dá uma mensagem amigável.

## Tried and ruled out
- `on_delete=DB_SET_NULL` (Django 6.1): o check recusa misturar on_delete de banco com PROTECT na mesma cadeia de referências (fields.E323).
- Recusar update só no save(): passam `QuerySet.update()`, `bulk_update` e um objeto novo com pk existente, que tem `_state.adding=True` e mesmo assim faz UPDATE.

## Watch out
- FK composta é MATCH SIMPLE: uma coluna nula desliga a checagem inteira. Só podem ser nulas `parceiro_ano.matriz_id` e `revista_fasciculo.template_id`, e o teste de catálogo confere `attnotnull`.
- Toda FK composta nova precisa de um caso no teste de recusa, senão o teste falha de propósito.

In the code: app/nucleo/db.py (fk_composta), migrações 0003 (fk_matriz_duplicada_de) e 0006 (template_versao_so_insert, ERRCODE 23001 → IntegrityError), app/nucleo/tests/test_constraints.py, test_revista.py (test_cada_fk_composta_recusa).
