---
title: "A obrigação de a etapa do projeto ter base fica na função que cria, não no banco, e a etapa não canônica sem conteúdo tem pendência própria"
author: Otavio
date: 2026-11-24
branch: feat/so-apontar-canonica
id: l-89ec3baa
scope: repo
status: active
src: agent
touches:
  - app/nucleo/models/cadastro.py
  - app/nucleo/servicos/etapa_projeto.py
  - app/nucleo/servicos/pendencias.py
  - app/nucleo/urls/painel.py
  - app/nucleo/urls/ui_revista.py
---

## Decided
Em 24/11, ao aplicar a regra "etapa não canônica nasce só apontando para uma canônica", a checagem ficou na função que cria a etapa do projeto: sem base, etapa canônica ou base não canônica são recusadas ali. A etapa não canônica com corte e sem conteúdo deixou de aparecer como "a matriz não tem a etapa" e ganhou pendência própria, cujo link leva à aba Matriz do projeto. O motivo: o link antigo levava ao editor da matriz, onde a não canônica nunca será corrigida.

## Tried and ruled out
- Regra no banco, recusando INSERT de etapa de projeto sem base (estava no plano de 24/11): a base apagada vira nulo, então etapa de projeto sem base é estado legítimo (cópia solta), e o projeto recriado pela cascata precisa herdar essa etapa por INSERT. O banco recusaria a herança.
- Lista das canônicas no módulo do serviço da etapa do projeto: import circular, porque as pendências importam a lista, a validação importa as pendências, o serviço da matriz importa a validação e o serviço da etapa do projeto importa o serviço da matriz.

## Watch out
- Até existir a tela de apontar, a pendência nova leva a uma aba que ainda não tem o botão.
- Mudar a lista das canônicas muda de uma vez o que pode ser criado, o que pode ser base e qual pendência aparece.

In the code:
- `app/nucleo/models/cadastro.py`: `ETAPAS_CANONICAS = ("2EF", "5EF", "9EF", "3EM")`
- `app/nucleo/servicos/etapa_projeto.py::criar` (base sem default)
- `app/nucleo/servicos/pendencias.py::pendencias_f1`: códigos `corte_sem_matriz` (canônica) e `etapa_sem_base` (não canônica)
- links: `app/nucleo/urls/painel.py::link`, `app/nucleo/urls/ui_revista.py::_situacao`
