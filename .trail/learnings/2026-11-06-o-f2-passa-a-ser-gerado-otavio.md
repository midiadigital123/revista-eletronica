---
title: "O F2 passa a ser gerado pelo sistema a partir de passos fixos que o projeto pode desligar, em SVG gerado com o svg-tour intocado"
author: Otavio
date: 2026-11-06
branch: docs/f2-mapeamento
id: l-2d6876ae
scope: repo
status: active
src: agent
touches:
  - docs/superpowers/specs/2026-11-06-f2-na-interface-mapeamento.md
  - state.md
---

## Decided
O F2 deixa de ser um SVG desenhado no Illustrator e passa a ser montado pelo sistema sobre um template único de passos canônicos: abertura e descritor são fixos; habilidades, progressão e tarefas podem ser desligados por projeto, e passo desligado não aparece no tour, no desenho nem no impresso. O usuário aprovou em 06/11 porque o texto vira texto real (acessível, entra no hash e no 'o que mudou') e acaba o trabalho de nomear camadas à mão e o risco de ordem de camadas na animação. O render recomendado é SVG gerado pelo servidor com o svg-tour intocado, porque preserva zoom, minimapa, modais e o evento de troca de passo que a animação usa; um protótipo de 1 dia confirma antes de construir o resto (8 a 12 dias úteis).

## Tried and ruled out
HTML por blocos com tour próprio: perde minimapa, zoom e modais prontos do svg-tour; fica como plano B se o protótipo mostrar foreignObject ruim no zoom ou no minimapa. Manter o SVG do design e só preencher textos: não resolve passo desligado (posições fixas, sem reflow) nem tira o Illustrator do caminho. Desligar passo por revista: o usuário ainda não decidiu; a proposta é por projeto (LP e MT juntos).

## Watch out
O referencial curricular por descritor (1EF a 3EM, I/A/C/R) não existe no banco nem nas fontes de 2025: sem planilha da Pedagógica vira ~500 linhas digitadas. O minimapa do svg-tour serializa o SVG numa imagem, e foreignObject sai sem estilo: CSS dentro do SVG ou minimapa desligado. Trocar o render muda o JSON resolvido e derruba o Validado de todas as revistas do ano de uma vez. Os textos dos passos 2 e 3 do seed atual estão trocados em relação ao desenho.

In the code:
Mapeamento: docs/superpowers/specs/2026-11-06-f2-na-interface-mapeamento.md. Decisão D-227 no state.md. Futuro: servicos/f2.py, templates/revista/f2.svg, modelos DescritorProgressao e RevistaF2Descritor, coluna Projeto.f2_passos_desligados; sai arquivos.py (sanitizador de SVG), svg_f2/svg_sha256/svg_ids e media/f2. Minimapa: svg-tour.js:578-580.
