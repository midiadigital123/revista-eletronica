---
title: "No F2 gerado, o tour leva texto puro e os modais levam HTML já escapado: são duas convenções diferentes"
author: Otavio
date: 2026-11-10
branch: feat/f2-f2
id: l-2d4caa28
scope: repo
status: active
src: agent
touches:
  - app/nucleo/servicos/f2.py
  - app/nucleo/templates/revista/index.html
  - state.md
---

## Decided
- O texto do tour (título e texto de cada passo e da abertura) sai em texto puro, porque o svg-tour o põe por textContent: HTML ali apareceria como tags literais.
- Os modais (título e corpo) saem como HTML seguro, porque a página os imprime com |safe. Os títulos das seções já chegam escapados do resolvido; o título do modal do item é montado com format_html a partir dos dados crus.
- Os conectores do descritor até os blocos são os pontos fixos do desenho: o trecho inicial, na altura do 1º ponto, anda com o bloco quando ele sobe por reflow. Só a progressão se move (quando as habilidades estão desligadas).

## Tried and ruled out
- Regra do protótipo "progressão sem linha com menos de 2 marcas": o desenho em uso não tem linha na progressão, as 12 colunas são fixas.

## Watch out
- Somar "" (str) com um SafeString dá str comum: o corpo do item sem imagem perdia a marca de seguro. Envolva a soma inteira em mark_safe.
- O gerador recebe o nome do componente à parte: o dict do infográfico não o traz.

In the code:
- app/nucleo/servicos/f2.py: gerar(infografico, secoes, base_imagens, componente), texto_puro, ROTULO_TOUR (movidos de html.py para evitar import circular), CONECTORES, _conector
- app/nucleo/templates/revista/index.html: {{ m.titulo|safe }} e {{ m.corpo|safe }}
- Decisão D-242 no state.md
