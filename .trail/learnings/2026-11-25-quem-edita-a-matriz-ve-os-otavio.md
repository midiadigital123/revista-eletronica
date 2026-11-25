---
title: "Quem edita a matriz vê os projetos com cópia por um aviso fixo no editor, não por um modal a cada gravação"
author: Otavio
date: 2026-11-25
branch: feat/abre-revisao
id: l-c3c7a459
scope: repo
status: active
src: agent
touches:
  - app/nucleo/templates/ui/_componentes/impacto.html
  - app/nucleo/templates/ui/matriz/mec.html
  - app/nucleo/tests/test_ui_matriz.py
  - app/nucleo/ui_autosave.py
  - app/nucleo/urls/ui_matriz.py
  - docs/regras-de-negocio.md
  - state.md
---

## Decided
Em 25/11 o usuário escolheu: o editor de uma etapa da matriz mostra um aviso fixo com os projetos que têm cópia a partir dela ("Mudança aqui abre revisão neles"), e o modal de impacto, quando abre, ganha a linha "Abre revisão em N projeto(s)…". O aviso aparece mesmo sem revista validada.

## Tried and ruled out
- Modal em toda gravação de etapa com cópias: o editor grava campo a campo, então apareceria um modal por campo alterado.
- Só a linha no modal: o modal só abre quando uma revista validada perde o "Validado"; sem revista validada ninguém seria avisado.

## Watch out
O modal de impacto é montado por dois caminhos: o include nos templates do editor (recebe o contexto da página) e o autosave em JSON, que renderiza o modal sozinho. Contexto novo do modal precisa chegar aos dois; o teste cobre os dois.

In the code: `app/nucleo/urls/ui_matriz.py::_abre_revisao` (sobre `servicos/etapa_projeto.derivadas`), `app/nucleo/ui_autosave.py::responder_campo(aviso=…)`, `templates/ui/_componentes/impacto.html`, `templates/ui/matriz/mec.html`; D-294.
