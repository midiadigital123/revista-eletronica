---
title: "As tarefas do projeto ficam num quadro kanban em markdown, e o Plano do state só aponta para ele"
author: Otavio
date: 2026-11-10
branch: chore/kanban
cost: { minutes: 8, tokens: 159392 }
id: l-b7fa2bab
scope: repo
status: active
src: agent
touches:
  - kanban.md
  - state.md
---

## Decided
A lista de tarefas do projeto é um quadro kanban de 4 colunas (Backlog, Doing, Review, Done) num arquivo markdown versionado na raiz, com uma página HTML gerada a partir dele para ver as colunas. A seção "Plano" do state.md só aponta para o quadro, porque duas listas de tarefas acabariam divergindo. O "Plano" antigo estava parado em S17 e não tinha as fases do F2. Doing tem no máximo 1 card; Review é o que espera o usuário olhar, aprovar ou mergear; Done é o que ele aprovou ou mergeou. Card nunca é apagado: o descartado vai para Done com o motivo.

## Tried and ruled out
- Artifact no claude.ai com banco compartilhado: fica fora do repositório e depende do claude.ai.
- Manter o "Plano" do state.md junto com o quadro: as duas listas divergiriam.
- Arrastar cards na página HTML: exigiria um servidor gravando o markdown.

## Watch out
- Cada worktree tem a sua cópia do quadro, e as cópias podem divergir, como acontece com o state.md. Mova os cards na branch que vai ser mergeada.
- A página HTML é gerada e fica fora do git; não a edite à mão.
- Os IDs K-NNN são sequenciais e nunca são reaproveitados.

In the code:
- kanban.md (raiz), kanban.html no .gitignore, state.md seção "Plano", decisão D-252.
- Skill global do usuário: ~/.claude/skills/kanban/ (SKILL.md + kanban.py). Hooks SessionStart e PostToolUse Write|Edit em ~/.claude/settings.json rodam `python3 ~/.claude/skills/kanban/kanban.py hook`.
- Para regenerar à mão: `python3 ~/.claude/skills/kanban/kanban.py kanban.md`.
