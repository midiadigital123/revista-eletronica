---
title: "No referencial do F2, a mescla com a etapa de cima é marcada à mão por coluna, e vazio sem marcar fica vazio"
author: Otavio
date: 2026-11-27
branch: feat/f2-mescla
id: l-6f71916b
scope: repo
status: active
src: agent
touches:
  - app/e2e/fixtures/pagina/f2-alfa.html
  - app/e2e/fixtures/pagina/f2-outras-etapas.html
  - app/e2e/fixtures/revista.zip
  - app/nucleo/dados/infografico-docx.json
  - app/nucleo/infografico.py
  - app/nucleo/models/revista.py
  - app/nucleo/servicos/f2.py
  - app/nucleo/servicos/resolver.py
  - app/nucleo/servicos/seed_infografico.py
  - app/nucleo/static/ui/telas/revista.css
---

## Decided
Em 27/11 o usuário mostrou que deixar código e texto vazios fazia a célula de cima se estender: etapa sem habilidade avaliada (9EF a 3EM) aparecia com a habilidade do 8EF, o que é falso para quem lê o infográfico. A mescla passou a ser explícita: cada etapa (menos a 1EF) tem "Junta com a de cima" na marca e na habilidade, independentes. A marca juntada herda a de cima e aparece como uma letra só, no meio do grupo.

## Tried and ruled out
Grupos por intervalo ("mesclar de X até Y"): mais cliques e validação de sobreposição. Letra repetida em cada etapa da marca juntada: o usuário quer uma letra só, centrada.

## Watch out
As chaves junta_* só entram no resolvido quando ligadas: revista sem mescla mantém o hash do Validado. A migração 0029 liga junta_habilidade onde o vazio estendia, para o desenho não mudar; nessas revistas o hash muda uma vez. No seed, a flag desligada (False) conta como vazio para o preenchimento, senão a carga nunca ligaria a mescla.

In the code: app/nucleo/servicos/resolver.py::_etapas, app/nucleo/servicos/f2.py::_tabela, migração 0029_infografico_junta, seed_infografico._decidir, scripts/docx_infografico.py (vMerge do Word vira junta_*).
