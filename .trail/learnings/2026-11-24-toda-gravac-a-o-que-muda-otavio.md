---
title: "Toda gravação que muda o conteúdo da revista passa pela simulação do Validado e pelo modal de impacto, sem exceção por raciocínio"
author: Otavio
date: 2026-11-24
branch: feat/apontar-etapa
id: l-8d61910c
scope: repo
status: active
src: agent
touches:
  - app/nucleo/contexto.py
  - app/nucleo/static/ui/telas/projeto.css
  - app/nucleo/templates/ui/matriz/excluir.html
  - app/nucleo/templates/ui/matriz/mec.html
  - app/nucleo/templates/ui/projeto/projeto.html
  - app/nucleo/tests/test_ui_matriz.py
  - app/nucleo/tests/test_ui_projeto_abas.py
  - app/nucleo/urls/ui_matriz.py
  - app/nucleo/urls/ui_projeto.py
  - docs/regras-de-negocio.md
---

## Decided
Em 24/11, ao apontar a etapa não canônica do projeto para uma canônica, a primeira versão gravava direto, sem modal de impacto. O usuário corrigiu: o apontamento muda o conteúdo da revista, e o impresso só é informado de mudança pelo "Validado"; qualquer mudança precisa tirar o Validado e avisar antes. Toda tela que grava algo que entra na revista usa a mesma simulação (quem perde o Validado) e o modal de impacto antes de gravar.

## Tried and ruled out
- Dispensar o modal com o argumento "nesse estado a revista nunca está validada" (a validação recusa revista com pendência de etapa sem base): é uma exceção que depende de outra regra continuar igual, e o usuário quer a regra sem exceção.
- Autosave ao escolher a base no select: apontar não deve gravar só por trocar a opção, e a página precisa recarregar para mostrar a etapa apontada.

## Watch out
- Em form nativo (POST com redirect), o modal não tem como abrir na resposta: o POST sem confirmação não grava e redireciona para a aba com o pedido na query; o GET refaz a simulação e mostra o modal ligado ao form da linha; confirmar reenvia com o campo de confirmação.
- A simulação roda o serviço de verdade num savepoint desfeito: recusa do serviço sobe como exceção e precisa ser tratada nos dois pontos.

In the code:
- app/nucleo/urls/ui_projeto.py: _apontar, _perdem_ao_apontar, _etapas_do_projeto
- app/nucleo/servicos/impacto.py: perdem_validado, avisar_perdidos
- app/nucleo/templates/ui/_componentes/impacto.html
- state.md: D-286, D-202
