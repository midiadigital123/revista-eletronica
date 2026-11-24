---
title: "O F2 não recebe mais SVG do design, por isso o sanitizador saiu; o prefixo f2- e o defusedxml ficam"
author: Otavio
date: 2026-11-11
branch: feat/f2-f4-t4a
id: l-1ce96774
scope: repo
status: active
replaces: l-705761ad
src: agent
touches:
  - app/nucleo/servicos/arquivos.py
  - app/nucleo/servicos/f2.py
  - app/nucleo/templates/revista/f2.svg
  - app/nucleo/static/revista/f2/revista.css
  - app/requirements.txt
---

## Decided
- O SVG do F2 não é mais enviado nem sanitizado, porque o servidor gera o SVG a partir dos infográficos da revista (D-239). Por isso o sanitizador (lista fixa de tags, atributos e CSS, recusa de DOCTYPE, at-rule e url externa), a conferência de ids, o gabarito e as colunas svg_f2/svg_sha256/svg_ids saíram na fase 4 do F2 (migração 0024, D-256).
- O arquivos.py ficou só com capa, imagem do item do infográfico e arquivo do item da matriz, porque são os únicos uploads que sobraram; todos conferem só a assinatura dos bytes.

## Tried and ruled out
- Manter o upload do SVG ao lado do SVG gerado: descartado porque dois caminhos do F2 dobram testes, telas e o render da foto arquivada, e o desenho enviado não acompanha os textos editados na interface.
- Tirar o defusedxml do requirements junto com o sanitizador: descartado porque o openpyxl o usa ao ler a planilha da matriz enviada (importacao/xlsx.py); sem ele, um xlsx malicioso volta a ser lido pelo parser XML padrão.

## Watch out
- O prefixo f2- continua nos ids e classes do f2.svg gerado (D-145), porque o revista.css depende dele ([id^="f2-btn-action-"], .f2-st20) e o svg-tour acha os botões por esses ids; renomear quebra o foco e o hover do tour sem erro visível.
- As medidas do desenho original ficaram em example/f2-gerado/desenho-original.svg, porque o f2.py cita os números dele; não é fixture de teste nem passa por sanitizador, então não volte a servi-lo inline.

In the code: app/nucleo/servicos/f2.py (gera o SVG), app/nucleo/templates/revista/f2.svg (ids f2-), app/nucleo/static/revista/f2/revista.css (seletores f2-), app/nucleo/servicos/arquivos.py (receber_capa, receber_imagem_item, receber_item), app/requirements.txt (defusedxml); decisões D-145, D-239 e D-256 no state.md.
