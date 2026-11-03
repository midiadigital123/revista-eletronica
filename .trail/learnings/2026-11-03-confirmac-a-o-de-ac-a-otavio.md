---
title: "Confirmação de ação que afeta vários lugares é um modal, não um checkbox, e linha nova só aparece ao clicar em adicionar"
author: Otavio
date: 2026-11-03
branch: feat/telas-b-lacunas
cost: { minutes: 1, tokens: 23063 }
id: l-84eedfda
scope: repo
status: active
src: agent
touches:
  - app/nucleo/templates/ui/cortes.html
---

## Decided
O usuário revisou as telas B (docx de comentários, 3/11) e corrigiu dois padrões que estavam espalhados:
- Ação que mexe em mais de um lugar (tira o "Validado", afeta N revistas) pede confirmação num modal que lista o impacto. Checkbox "Confirmo: afeta N revista(s)" ao lado do botão não serve.
- Tabelas editáveis não terminam com uma linha vazia para "preencher e adicionar": parece erro. A linha nova só aparece depois de clicar em "Adicionar <coisa>". Ordem não é digitada pelo usuário; o sistema infere (e reordena por arrastar/setas).

## Tried and ruled out
- Checkbox de confirmação junto do botão (cortes/renomear, matriz/intervalo mínimo, descritor): rejeitado como UX ruim.
- Linha em branco no fim da grade (etapas, componentes) e campo "Ordem" obrigatório.

## Watch out
Ao fundir páginas, nenhuma função do back pode sumir da tela (ver a learning de 30/10 sobre botão para toda função).

In the code: app/nucleo/templates/ui/cortes.html (renomear com checkbox), páginas de ano (etapas/componentes), editor de matriz (intervalo mínimo e "Salvar descritor" com checkbox).
