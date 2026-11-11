---
title: "O F2 gerado só vai para produção com as fases 1 a 3 juntas, e o template F2 troca para seções fixas já na fase 2"
author: Otavio
date: 2026-11-09
branch: feat/f2-f2
id: l-8e6e6e0e
scope: repo
status: active
src: agent
touches:
  - app/nucleo/tests/fixtures/f2-lp.svg
  - docs/superpowers/plans/2026-11-09-f2-fase-2.md
  - state.md
---

## Decided
- As fases 1 a 3 do F2 gerado entram na main juntas (substitui a ideia de mandar a fase 1 com a 2). A fase 2 cria pendências por infográfico que só a tela da fase 3 resolve, e com pendência o "Validado" e o zip são recusados: com só a fase 2 em produção ninguém validaria nem baixaria revista.
- O template F2 deixa os ids antigos (passo1..4, dlg-p2, dlg-p3, dlg-p4-iN) e passa a ter 8 seções fixas e obrigatórias, como o F1, já na fase 2 (escolha do usuário em 09/11). Uma migração grava versão nova de cada template F2 e leva as cópias dlg-p2/dlg-p3 da revista para os textos do infográfico.
- O desenho do infográfico é o do SVG em uso (confirmado com a equipe em 09/11). Alfa e Outras Etapas usam o mesmo desenho; mudam só os textos e os itens do último passo.

## Tried and ruled out
- Fase 2 sem pendências novas (elas entrariam na fase 3): revista com infográfico vazio poderia ser validada.
- Manter a troca dos ids na fase 3 com um mapa provisório passo1→descritor … passo4→tarefas: código e testes jogados fora, e os títulos antigos estavam trocados.
- Esperar referência nova do design para o visual: não virá.

## Watch out
- Entre a fase 2 e a 3, os specs E2E que validam revista ficam vermelhos (revistaPropria espera "5 de 6").
- A planilha e o "o que mudou" do impresso só ganham os infográficos na fase 4; decidir antes da fase 3 se puxa essa parte ou se o deploy leva 1 a 4.

In the code: texto.SECOES_F2 = abertura, passo-descritor, passo-habilidades, passo-progressao, passo-tarefas, dlg-descritor, tarefas-fechamento, fechamento; migração 0023_template_f2_secoes; recusas em servicos/validacao.py:43 e servicos/empacotar.py:101; desenho em app/nucleo/tests/fixtures/f2-lp.svg; plano em docs/superpowers/plans/2026-11-09-f2-fase-2.md; state.md D-237 a D-239.
