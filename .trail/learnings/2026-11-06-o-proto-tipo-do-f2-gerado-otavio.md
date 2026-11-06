---
title: "O protótipo do F2 gerado a partir de dados é um exemplo estático fora do sistema, não uma tela do Django"
author: Otavio
date: 2026-11-06
branch: feat/f2-fase0
id: l-d1a54951
scope: repo
status: active
src: agent
touches:
  - state.md
---

## Decided
O protótipo que decide se o F2 pode ser um SVG gerado a partir de dados (fase 0 da D-227) vive como exemplo estático fora do sistema, aberto por file://, porque o que ele precisa provar é só comportamento de navegador (HTML dentro de foreignObject no zoom do svg-tour, minimapa que serializa o SVG numa imagem, texto longo em caixa fixa, passo desligado refluindo o layout). Sem banco e sem Django ele sai em 1 dia e é descartável; o gerador é um script Python só com stdlib, que faz o papel do futuro template do servidor. O svg-tour continua intocado e é reaproveitado da demo da animação por caminho relativo, para não existir uma terceira cópia.

## Tried and ruled out
View Django de preview gerando o SVG a partir da revista de demonstração: já nasceria no lugar final, mas exige a stack docker, dados fixos dentro do código do sistema e custa 1,5 a 2 dias; o usuário preferiu o estático em 06/11 porque a decisão de tecnologia não depende de nada do servidor.

## Watch out
O id f2-titulo já é do h2 da página da revista, então o SVG gerado usa f2-cabecalho. O Playwright só existe no checkout principal (node_modules não vem na worktree): rodar o script com NODE_PATH apontando para lá, sem npm install. Só há Chromium instalado; Safari e Firefox precisam de olho humano, e o foreignObject dentro de imagem é justamente onde o Safari costuma falhar.

In the code:
example/f2-gerado/: dados.json, gerar.py (python3 gerar.py --check; --desligar habilidades -o index-sem-habilidades.html), verificar.cjs (NODE_PATH=/home/otavio.peres/dev/revista-express/app/e2e/node_modules node verificar.cjs), LEIA-ME.md. Tour reaproveitado de example/f2-animado-tour/f2/. Plano aprovado: ~/.claude/plans/planeje-antes-de-fazer-eager-snowflake.md. Branch feat/f2-fase0 a partir de integ/f2-interface.
