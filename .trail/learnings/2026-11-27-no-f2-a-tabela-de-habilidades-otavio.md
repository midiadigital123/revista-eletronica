---
title: "No F2, a tabela de habilidades cresce pelo texto estimado no servidor, e texto curto tem que gerar o SVG idêntico ao de antes"
author: Otavio
date: 2026-11-27
branch: feat/f2-linhas-crescem
id: l-9938eea4
scope: repo
status: active
src: agent
touches:
  - app/nucleo/servicos/f2.py
  - app/nucleo/templates/revista/f2.svg
---

## Decided
Em 27/11 o usuário escolheu que as linhas da tabela "Descrição das habilidades" cresçam com o texto, em vez de mostrar o texto inteiro só no modal. O servidor estima as linhas por caracteres; a altura do desenho é o mínimo, e a tabela, a legenda, a Progressão e o viewBox descem o quanto a tabela cresceu.

## Tried and ruled out
- Texto completo só no modal: a tela inicial continuaria com reticências.
- Medir o texto no navegador e reposicionar por JS: o SVG é gerado no servidor e o svg-tour mede o desenho; seriam mais peças móveis para o mesmo resultado.

## Watch out
- Um 0.0 (float) no deslocamento escreve "589.0" no translate e muda o SVG de toda revista cujo texto já cabia, o que quebra os gabaritos. Quando a tabela não cresce, o deslocamento tem que ser o inteiro 0.
- Existem dois gabaritos que o F2 alimenta: o zip (test_empacotar) e as páginas (test_preview). Mudou o f2.svg? Regere e confira os dois. O das páginas tinha ficado velho desde a D-299.
- A prévia pede login. Para medir a página sem digitar senha: gerar o HTML com o Client do Django (force_login num superusuário), pôr <base href="http://localhost:8002/"> e servir a cópia por um http.server local. Aberta como file://, a cópia vira imagem estática no navegador do app.

In the code:
- app/nucleo/servicos/f2.py: _tabela (CARACTERES_LINHA = 88, LINHA_CEL = 12, RESPIRO_CEL = 6), _layout(ligados, cresceu) devolve também altura_svg
- app/nucleo/templates/revista/f2.svg: viewBox, fim_tabela, legenda_y
- Regerar os gabaritos: REGERAR_FIXTURES=1 em test_empacotar.ZipTest e test_preview.PaginaTest (test_gabarito_do_playwright)
