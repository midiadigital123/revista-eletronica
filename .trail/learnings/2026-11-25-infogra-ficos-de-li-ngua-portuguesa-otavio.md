---
title: "Infográficos de Língua Portuguesa vêm de um modelo único pré-preenchido pelos Word da Pedagógica, e cada revista pode sobrescrever qualquer campo"
author: Otavio
date: 2026-11-25
branch: feat/redesenho-figma
id: l-8bdcd965
scope: repo
status: active
src: agent
touches:
  - docs/telas/telas-b.md
  - kanban.md
  - state.md
  - app/nucleo/models/revista.py
  - app/nucleo/servicos/resolver.py
---

## Decided
Em 25/11 o usuário decidiu (D-297): o conteúdo dos infográficos Alfa e Outras Etapas de LP, enviado pela Pedagógica em dois Word, vira um modelo único por ano × componente × tipo, editado num lugar só e com o modal de impacto. A revista pode sobrescrever qualquer campo, não só o descritor. A Pedagógica diz que só o descritor muda entre parceiros, mas o usuário preferiu "ter e não precisar". Só LP tem modelo; MT continua preenchida revista a revista. Vem antes do redesenho pelo Figma (etapa 11). Ainda não implementado.

## Tried and ruled out
- Copiar o conteúdo do Word em cada revista na carga: cada correção teria de ser feita em 33 revistas.
- Permitir sobrescrever só a habilidade destacada: depende da promessa da Pedagógica de que só ela muda.
- Pedir ao design a imagem do item do 5EF Alfa já montada: atrasa a carga. A carga junta o suporte e o enunciado numa imagem só, porque o item guarda uma imagem (D-232).

## Watch out
- Na sobrescrita, NULL quer dizer "herda do modelo" e "" quer dizer "vazio de propósito". A célula mesclada da tabela de habilidades já usa código e texto vazios, então "" não pode significar "herdar".
- As marcas da tabela de descrição e da de progressão coincidem nos dois Word. Etapas que dividem a mesma linha podem ter marcas diferentes (3EF A, 4EF A, 5EF C), e o modelo já aceita porque a marca é por etapa.
- O E2E não pode editar o modelo de LP, porque ele alimenta revistas reais. Teste o editor do modelo no Django.

In the code: plano em docs/superpowers/plans/2026-11-25-infografico-modelo-lp.md; campos em app/nucleo/models/revista.py (RevistaInfografico, RevistaInfograficoEtapa, RevistaInfograficoItem); junção em app/nucleo/servicos/resolver.py::_infograficos.
