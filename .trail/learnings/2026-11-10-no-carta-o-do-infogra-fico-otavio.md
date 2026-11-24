---
title: "No cartão do infográfico, salvar um campo não redesenha o cartão, e o passo desligado se esconde por CSS"
author: Otavio
date: 2026-11-10
branch: feat/f2-f3
cost: { minutes: 1, tokens: 2047 }
id: l-5cf04cb1
scope: repo
status: active
src: agent
touches:
  - app/nucleo/urls/ui_revista.py
  - app/nucleo/templates/ui/parciais/revista_infograficos.html
  - app/nucleo/static/ui/telas/revista.css
---

## Decided
Salvar um campo de texto, checkbox ou select do infográfico devolve só a coluna Situação para trocar, because redesenhar o cartão apagaria o campo seguinte. O cartão inteiro só é redesenhado no upload da imagem, because a miniatura muda. O bloco de um passo desligado some por CSS (`:has()` no checkbox marcado), because o Alpine em uso não aceita objeto inline no `x-data`.

## Tried and ruled out
Trocar o cartão inteiro a cada gravação: o autosave grava ao sair do campo, quando o foco já está no campo seguinte; otherwise o redesenho substitui esse campo e apaga o que a pessoa começou a digitar.
Esconder o bloco com `x-show` e um objeto no `x-data`: fails with o build CSP do Alpine (3.14.9), que recusa objeto inline no `x-data`.

## Watch out
A grade do referencial (12 etapas) é das Habilidades e da Progressão ao mesmo tempo, because a Progressão usa a marca e as Habilidades usam código e texto: some só quando os dois passos estão desligados. Ao acrescentar campo novo no cartão, não inclua `infograficos` no `trocar` da resposta, because isso volta a apagar o campo seguinte; só inclua se o campo mudar algo fora dele (como a miniatura).

In the code: `app/nucleo/urls/ui_revista.py` (`_infografico`, `trocar` com `situacao`, + `infograficos` só na imagem), `app/nucleo/templates/ui/parciais/revista_infograficos.html`, `app/nucleo/static/ui/telas/revista.css` (regras `:has`), commit `96c37d8`.
