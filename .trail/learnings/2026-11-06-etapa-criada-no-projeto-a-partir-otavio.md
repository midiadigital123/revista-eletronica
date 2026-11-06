---
title: "Etapa criada no projeto a partir de outra etapa recebe as mudanças da base por revisão em 3 vias, nunca sozinha"
author: Otavio
date: 2026-11-06
branch: main
cost: { minutes: 27, tokens: 84286 }
id: l-d9e95479
scope: repo
status: active
src: agent
touches:
  - state.md
---

## Decided
Parceiros que avaliam etapas incomuns (4EF, 6EF, 8EF) ganham uma etapa só do projeto, criada em branco ou como clone de qualquer etapa de qualquer matriz. O clone guarda o vínculo com a base. Quando a base muda, o projeto ganha uma pendência obrigatória que bloqueia o Validado, com comparação em 3 vias: a base de quando clonou, a base atual e o local. O que o projeto não tocou vem pré-marcado "aplicar", mas só grava quando alguém clica em "Concluir revisão". O projeto pode recusar item a item. Não há fusão dentro de um texto: escolhe-se o campo inteiro (D-115).
O dono é o projeto (escolha do usuário em 06/11, contra a recomendação de usar o parceiro_ano). Clone de clone é proibido na 1ª versão: a base é sempre etapa de matriz. A etapa própria só existe para uma etapa que a matriz do parceiro não tem.

## Tried and ruled out
- Somar a base nova com o local e descartar duplicatas (ideia do usuário): não propaga remoção nem correção de texto, e o texto velho fica ao lado do novo.
- Remontar a base antiga pelo django-simple-history: a reimportação apaga e recria descritores e tarefas com ids novos.
- Camada de sobrescrita (copy-on-write) e versões imutáveis da matriz: reescrevem o editor e a reimportação, e propagam sem revisão.
- Aplicar a mudança sozinha ao gravar a base: escreve no conteúdo de outro projeto sem ninguém ver.
- Dono parceiro_ano: recomendado por 2 dos 3 agentes (as regionais compartilhariam a etapa), mas o usuário escolheu o projeto.

## Watch out
Isso substitui em parte a D-051 ("projeto não tem conteúdo próprio"). A foto da base precisa usar o código (Dxx, faixa da tarefa), não o id. Reimportação com mudança só de espaços gera pendência enorme se o texto não for normalizado.

In the code: decisões D-229 e D-230 no state.md. Pontos de encaixe: `servicos/matriz.py::_afetadas`, `_conteudo` e `diferencas`; `servicos/impacto.py::perdem_validado`; `servicos/resolver.py` (`_f1_escalas`, lacunas, `pendencias`); `models/matriz.py::MatrizEtapaCC`.
