---
title: Escolha de matriz do parceiro se perde ao abrir o ano se ficar só no projeto
author: Otavio
date: 2026-10-27
branch: dev
cost: { minutes: 12, tokens: 157657 }
id: l-957de440
scope: repo
status: active
src: agent
touches:
  - state.md
  - docs/Modelo_ER_Revista.pdf
  - docs/modelo-er.md
  - docs/Modelagem_Banco_Conceitos_Essenciais.pdf
---

## Decided
- Nada decidido ainda: ficou como pergunta em aberto para a sessão de modelagem. O rascunho do ER guarda matriz e texto-modelo no Projeto, e projetos não são clonados ao abrir o ano (renascem pela cascata dos cortes). Resultado: em 2027 o CE, o ES e o JOINVILLE nasceriam sem a matriz própria. A escolha precisa morar em algo que entra no clone (por parceiro × ano), não só no projeto.

## Watch out
- `on_delete` do Django (CASCADE, PROTECT, SET_NULL) roda em Python antes do DELETE; a FK criada no PostgreSQL é NO ACTION (`confdeltype = 'a'`). DELETE cru no psql não cascateia; quem barra é a FK. Django 6.1 tem `DB_CASCADE`, `DB_SET_NULL`, `DB_SET_DEFAULT` para gravar a ação no banco; não existe `DB_PROTECT`.
- Coerência de ano entre FKs (Projeto 2027 com matriz 2026) não cabe em CHECK; testado com FK composta `(matriz_id, ano_id) REFERENCES matriz(id, ano_id)` + `UNIQUE(id, ano_id)` na matriz, criada por SQL (no projeto: `RunSQL` em migration).
- Fonte DejaVuSans-Oblique não está instalada nesta máquina; o gerador de PDF da skill de material didático quebra. Os TTFs vêm no `mpl-data/fonts/ttf` do matplotlib.

In the code:
- docs/Modelagem_Banco_Conceitos_Essenciais.pdf (v2, desafio da página de questões); docs/modelo-er.md (Projeto.matriz_id, Projeto.texto_modelo_id); state.md, Perguntas em aberto.
