---
title: "O item do infográfico do F2 não é uma tarefa da matriz: tem descritor, etapa, imagem e análise próprios"
author: Otavio
date: 2026-11-06
branch: feat/f2-f1
id: l-3f6b88ab
scope: repo
status: active
src: agent
touches:
  - state.md
  - app/nucleo/models/revista.py
---

## Decided
Cada um dos 4 itens do bloco "Tarefas por nível de complexidade" do F2 é conteúdo próprio do infográfico: o código do descritor na matriz de referência (ex. D05), a etapa (ex. 2º ano do Ensino Fundamental), uma imagem única montada pelo design (item + suporte) com texto alternativo, e 2 parágrafos de análise. Não há ligação com as tarefas da matriz (as faixas da régua do F1). O usuário corrigiu isso em 06/11: "Nenhum item do infográfico usa a matriz de tarefas".

## Tried and ruled out
Item como chave estrangeira para Tarefa, mostrando a imagem de Tarefa.arquivo (estava no plano das fases 1 a 5): premissa errada. Ainda puxava um problema falso, porque a reimportação da matriz e a exclusão de tarefa quebrariam com o PROTECT; chegou a virar decisão (D-234) e foi substituída (D-235).

## Watch out
O rótulo do item no docx é "(4,1) D05 – 2º ano do Ensino Fundamental"; o código P00208914 é só o nome do arquivo da imagem e não foi guardado. Se o plano do F2 citar Tarefa no item, ele está desatualizado.

In the code: app/nucleo/models/revista.py (RevistaInfograficoItem: etapa, descritor, imagem + imagem_sha256, texto_alternativo, analise); migração 0020_infograficos.py corrigida no lugar, antes de qualquer merge; state.md D-235.
