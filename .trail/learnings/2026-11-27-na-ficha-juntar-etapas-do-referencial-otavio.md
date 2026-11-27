---
title: "Na ficha, juntar etapas do referencial é um elo sobre a linha entre elas, e a célula juntada vira uma célula só"
author: Otavio
date: 2026-11-27
branch: feat/f2-mescla
id: l-c4908b78
scope: repo
status: active
src: agent
touches:
  - app/e2e/fixtures/pagina/f2-alfa.html
  - app/e2e/fixtures/pagina/f2-outras-etapas.html
  - app/e2e/fixtures/revista.zip
  - app/e2e/tests/infografico.spec.ts
  - app/nucleo/dados/infografico-docx.json
  - app/nucleo/infografico.py
  - app/nucleo/models/revista.py
  - app/nucleo/servicos/f2.py
  - app/nucleo/servicos/resolver.py
  - app/nucleo/servicos/seed_infografico.py
---

## Decided
Em 27/11 o usuário recusou duas UIs da mescla antes de aceitar a terceira. A mescla é uma relação entre duas etapas vizinhas, então o controle é um elo redondo sobre a linha que as separa, um por coluna (marca e habilidade). Juntado, a célula de cima cobre o grupo, como o rowspan do infográfico. Para propor a UI, o usuário escolheu a skill ui-ux-pro-max (a mais instalada no skills.sh) entre três opções.

## Tried and ruled out
Caixas "Junta com a de cima" com rótulo em cada célula: 22 rótulos repetidos e linhas desalinhadas. Botão-ícone em cada célula com "igual à de cima": repetido, não dizia com quem juntava e não parecia uma célula só. Skills interaction-design e ui-design (uxpilot): menos usadas, uma só de interação e outra só de aparência.

## Watch out
A grade é CSS grid, não tabela. O servidor entrega as spans e um componente Alpine as refaz a cada clique: as duas regras precisam ficar iguais. Comentário Django de várias linhas precisa de {% comment %}: o {# #} só vale numa linha e aparece na tela. A coluna de habilidade precisa de largura mínima, senão encolhe a zero no celular.

In the code: nucleo/infografico.py::grade_referencial, static/ui/componentes/referencial.js (carregado na base antes do Alpine), revista_infograficos.html, revista.css (.inf-ref, .inf-elo).
