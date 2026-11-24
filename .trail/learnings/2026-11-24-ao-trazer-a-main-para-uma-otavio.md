---
title: "Ao trazer a main para uma branch antiga, mudança feita numa função que a main moveu de arquivo some sem aviso e precisa ser copiada à mão"
author: Otavio
date: 2026-11-24
branch: feat/etapa-do-projeto
id: l-2c1bf161
scope: repo
status: active
src: agent
touches:
  - kanban.md
  - state.md
  - app/nucleo/servicos/pendencias.py
  - app/nucleo/tests/test_etapa_projeto.py
  - app/nucleo/migrations/0026_etapa_do_projeto.py
---

## Decided
Em 24/11 a branch da etapa do projeto (parada desde 10/11, 165 commits atrás) recebeu a main. A main tinha movido a função das pendências para um módulo próprio. O git mostrou o conflito só como "bloco removido de um lado, alterado do outro": ficando com o lado da main, as duas mudanças da branch (a etapa do projeto conta como etapa da matriz; pendências de base e de etapa em dobro) sumiriam. Elas foram copiadas à mão para o módulo novo, e o teste da branch passou a importar a função de lá.

Antes do merge de verdade, o merge foi simulado sem tocar em nada, para listar os conflitos e planejar a resolução.

## Tried and ruled out
- Renumerar os dois learnings da branch que citam as decisões com número antigo: learning existente não se edita. Eles continuam citando D-229 a D-231, que hoje são D-279 a D-281.

## Watch out
- Teste da branch antiga pode usar campo que a main removeu: o preparo da revista "pronta" usava o SVG do F2, apagado pela migração 0024. O preparo certo hoje é o helper dos infográficos.
- As decisões da branch foram renumeradas ao receber a main (D-279 a D-281). Se a main ganhar decisão nova antes do merge final, a colisão volta e renumera-se de novo.
- Na renumeração, trocar só as linhas que a branch acrescentou: os mesmos arquivos citam D-230 legítimas da main (infográficos).

In the code:
- simulação: `git merge-tree --write-tree --name-only main feat/etapa-do-projeto`
- `app/nucleo/servicos/pendencias.py` (`pendencias_f1`: `Q(matriz_id=…) | Q(projeto=…)`; lacunas `base` e `etapa_em_dobro`)
- `app/nucleo/tests/test_etapa_projeto.py` (`_pronta` usa `preencher_infograficos`)
- `app/nucleo/migrations/0026_etapa_do_projeto.py` (era 0020; depende da 0025)
- mapa: D-226/D-229 → D-279; D-227/D-230 → D-280; D-228/D-231 → D-281
