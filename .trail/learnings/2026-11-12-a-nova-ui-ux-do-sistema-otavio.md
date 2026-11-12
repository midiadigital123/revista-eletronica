---
title: "A nova UI/UX do sistema é uma esteira de 5 fases desenhada como régua, não um menu por tipo de objeto"
author: Otavio
date: 2026-11-12
branch: feat/ux-proposta
id: l-9517fc58
scope: repo
status: active
src: agent
touches:
  - kanban.md
  - state.md
---

## Decided
O usuário liberou o visual e escolheu a direção "régua de proficiência" para a proposta de nova UI/UX. A revista é o objeto central e anda numa esteira de 5 fases (Preparar, Montar, Conferir, Validada, Impressa), desenhada como uma régua de 5 trechos numa rampa de cobalto. A navegação segue a esteira: Hoje, Revistas, Parceiros, Entrega (Validar, Impresso, Pacotes) e Biblioteca (Matrizes, Templates). As fases saem de dados que já existem (pendências, Validado, foto do impresso), sem regra de negócio nova. As cores dos Padrões 01–05 só aparecem como dado, nunca como decoração. A demo é HTML estático gerado em Python, em `example/`, com dados fictícios, sem tocar em `app/`.

## Tried and ruled out
- Atlas temático (sorteado pela skill de design): mosaico de parceiros colorido pela fase; o usuário preferiu a régua, que ecoa o produto e é mais barata de implementar.
- Ferramenta limpa padrão (saída da categoria): a mais segura e a menos distintiva.
- Artifact publicado e página única com roteador em JS: o usuário quis o HTML clicável em `example/`.

## Watch out
- `PRODUCT.md` e `DESIGN.md` da raiz descrevem o editor React antigo; a demo não os altera, e o sistema visual proposto está no `LEIA-ME.md` da demo.
- A demo ainda não foi aprovada para virar código; a implementação no Django seria um plano à parte.

In the code: `example/ux-proposta/` (`gerar.py`, `dados.py`, `paginas/`, `app.css`, `app.js`, `LEIA-ME.md`), branch `feat/ux-proposta`, D-267 e K-041; contrato da direção em `.impeccable/surfaces/ux-proposta.md`.
