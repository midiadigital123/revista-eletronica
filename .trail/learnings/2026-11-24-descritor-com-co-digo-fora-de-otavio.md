---
title: Descritor com código fora de D + 2 dígitos sumia da revista porque a página separava descritor das outras chaves pelo formato do código
author: Otavio
date: 2026-11-24
branch: fix/descritor-codigo-livre
id: l-a8f31a13
scope: repo
status: active
src: agent
touches:
  - app/nucleo/static/revista/f1/script.js
  - app/nucleo/matriz.py
  - app/nucleo/servicos/resolver.py
  - app/nucleo/static/revista/f1/regua.test.mjs
  - state.md
---

## Decided
A revista mostra todo descritor, com qualquer código (D011, D1, H05). Só os três nomes que a própria etapa usa no JSON do F1 ficam de fora da lista de descritores, e o formulário recusa esses três nomes como código.

## Tried and ruled out
- Obrigar o formato "D" + 2 dígitos no formulário: a Pedagógica acrescenta itens na cópia do projeto e pode numerar de outro jeito.
- Alargar a expressão para "D" + qualquer número: esconderia um código como H05 do mesmo jeito.
- Pôr os descritores numa lista própria do JSON: muda o formato do F1 e o hash de todas as revistas.

## Watch out
- O sintoma é silencioso: o descritor existe no banco e no JSON da revista, mas não aparece nos botões nem na lista. Antes de procurar no servidor, olhe o filtro da página.
- A ordem dos descritores na revista é alfabética pelo código, não a ordem arrastada no editor (D011 vem antes de D02). Pergunta aberta ao usuário em 24/11.
- No JSON da etapa, o descritor é uma chave ao lado das chaves da etapa: chave nova da etapa no servidor precisa entrar também na lista da página e na lista de códigos reservados.

In the code:
- app/nucleo/static/revista/f1/script.js: CHAVES_DA_ETAPA, descriptorKeys (antes: /^D\d{2}$/)
- app/nucleo/matriz.py: CHAVES_DA_ETAPA, DescritorForm.clean_codigo
- app/nucleo/servicos/resolver.py: _f1_escalas (scaleRange, cortes, padroes)
- node app/nucleo/static/revista/f1/regua.test.mjs
- state.md: D-290
