---
title: "Etapa não canônica nasce só apontando para uma canônica de qualquer matriz, como clone editável com vínculo; etapa em branco foi descartada"
author: Otavio
date: 2026-11-24
branch: main
cost: { minutes: 3, tokens: 22004 }
id: l-3d366d80
scope: repo
status: active
src: agent
touches:
  - app/nucleo/servicos/resolver.py
  - app/nucleo/models/cadastro.py
---

## Decided
Em 24/11 a equipe pedagógica explicou que alguns projetos avaliam etapas não canônicas, que são todas exceto 2EF, 5EF, 9EF e 3EM (por exemplo 4EF, 6EF, 8EF). Toda etapa não canônica de um projeto passa a ser criada obrigatoriamente apontando para uma etapa canônica já existente em alguma matriz. Apontar é clonar com vínculo: a Pedagógica edita a cópia (acrescenta e tira itens), e mudança na base abre a pendência de revisão em 3 vias, que bloqueia o Validado. A canônica pode ser de qualquer matriz e de qualquer ano, mas só uma das 4 canônicas. A etapa não canônica nunca serve de base de outra.

## Tried and ruled out
- Criar a etapa não canônica em branco: o desenho da branch feat/etapa-do-projeto (D-229 a D-231) oferecia "Em branco" ou "A partir de". Em branco deixa de existir, porque toda não canônica deve ter uma canônica de origem.
- Só usar a canônica, sem cópia nem edição local (a 4EF mostraria a 5EF): descartado porque a Pedagógica precisa acrescentar e tirar itens da cópia.
- Limitar a escolha à matriz do parceiro: descartado, a base pode vir de outra matriz.

## Watch out
- O conceito "canônica" não existe no código: Etapa tem só codigo, escala_max e ordem. Proposta: constante com os 4 códigos, sem campo no banco. Se a lista mudar, edita-se a constante.
- Hoje a pendência corte_sem_matriz só informa e não há tela para apontar. A UI é imprescindível e vem logo depois de terminar a tarefa 5 (matriz_id nulo).
- A UI de apontar sem a tela de revisão em 3 vias deixa uma base que mude com pendência sem saída na tela.
- A branch está 160 commits atrás da main e a migration 0020_etapa_do_projeto colide com a 0020_infograficos da main: renumerar para 0026.
- Uma não canônica como 4EF conta como "Outras Etapas" no F2, pois só o 2EF gera "Alfa".

In the code:
- app/nucleo/servicos/etapa_projeto.py::criar (tarefa 2, já aceita criar em branco; precisa exigir base)
- docs/superpowers/specs/2026-11-06-etapa-do-projeto-design.md, seção 4.1
- app/nucleo/servicos/resolver.py: pendência corte_sem_matriz
- app/nucleo/models/cadastro.py: Etapa
