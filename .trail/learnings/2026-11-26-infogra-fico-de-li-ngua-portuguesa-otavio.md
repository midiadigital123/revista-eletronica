---
title: "Infográfico de Língua Portuguesa nasce preenchido pelo seed: a suíte Django desliga isso, e o teste de navegador grava valor diferente do seed"
author: Otavio
date: 2026-11-26
branch: feat/infografico-lp
id: l-83a3eebc
scope: repo
status: active
src: agent
touches:
  - CLAUDE.md
  - README.md
  - app/e2e/tests/infografico.spec.ts
  - app/e2e/tests/revista-textos.spec.ts
  - app/nucleo/servicos/cascata.py
  - app/nucleo/tests/__init__.py
  - app/sistema/settings.py
  - docs/e2e.md
  - docs/regras-de-negocio.md
  - docs/superpowers/plans/2026-11-26-infografico-lp-copia.md
---

## Decided
Desde a D-298 (26/11), a cascata dos cortes preenche pelo seed dos Word todo infográfico de LP que ela cria, e o comando de carga preenche os que já existem. A chave INFOGRAFICOS_DO_SEED (settings, ligada por padrão) controla isso. A suíte Django a desliga no import do pacote de testes, e só os testes do seed a religam. Sem isso, toda fixture com LP de 2026 nasceria preenchida: mudam pendências e hashes esperados, e as imagens vão para o media/ real.

## Tried and ruled out
- Deixar a chave ligada nos testes: 22 arquivos de teste passam pela cascata com ano 2026, e só 9 usam mídia temporária.
- Passar a chave como argumento de gravar_cortes: teria de passar por todos os chamadores (tela, comandos, testes), por um efeito que só os testes querem desligar.

## Watch out
- No E2E a chave fica ligada. O passo Infográficos de uma revista de LP já nasce pronto (a contagem "N de 6" sobe um), e um campo preenchido com o mesmo valor do seed não dispara o autosave. O teste que espera a resposta da gravação fica parado até estourar o tempo. Grave sempre um valor que o seed não tem (por exemplo, a etapa 1EF no item).
- Cada revista de LP criada no E2E deixa as 8 imagens do seed no media/, porque o limpar_e2e apaga registros, não arquivos.

In the code: app/sistema/settings.py (INFOGRAFICOS_DO_SEED), app/nucleo/tests/__init__.py, app/nucleo/servicos/cascata.py::_seeds_validos, app/e2e/tests/infografico.spec.ts.
