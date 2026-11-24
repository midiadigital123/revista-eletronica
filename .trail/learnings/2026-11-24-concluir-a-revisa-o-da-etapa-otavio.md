---
title: Concluir a revisão da etapa do projeto lê a base uma vez só e confere o hash dos itens que a tela mostrou
author: Otavio
date: 2026-11-24
branch: feat/concluir-revisao
id: l-481440c6
scope: repo
status: active
src: agent
touches:
  - app/nucleo/servicos/etapa_projeto.py
  - app/nucleo/tests/test_etapa_projeto.py
  - docs/regras-de-negocio.md
  - kanban.md
  - state.md
---

## Decided
Quem conclui a revisão em 3 vias devolve o hash da classificação inteira (os itens que viu), não só o hash da base. E a conclusão lê a base e o projeto uma única vez: a classificação, a gravação e a foto nova saem dessa leitura (D-284).

## Tried and ruled out
- Hash só da base (plano de 06/11): uma edição no projeto entre abrir a tela e concluir passava, e "usar o da base" apagava um texto que ninguém viu.
- Ler a base de novo na hora de gravar a foto: a edição normal da matriz não toma a trava da matriz, então uma mudança feita no meio entrava na foto sem ter sido perguntada, e a pendência sumia.
- Teste de concorrência com duas conclusões largando juntas: passava mesmo sem a trava da etapa do projeto, porque a trava da matriz da base já serializa as duas.

## Watch out
- A tela (etapa 8) chama sob o bloqueio de escrita e relê a etapa do banco antes de cada revisão: a instância passada não é atualizada.
- "Usar o da base" muda a revista, então o Validado não volta sozinho; só volta com "manter o meu" em tudo.

In the code: `app/nucleo/servicos/etapa_projeto.py` (`revisao`, `concluir`, `_objetos`, `_foto`), `app/nucleo/tests/test_etapa_projeto.py::ConcluirConcorrenteTest`.
