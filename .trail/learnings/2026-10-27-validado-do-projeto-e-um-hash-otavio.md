---
title: "Validado do projeto é um hash da revista montada, não uma marca derrubada por cada tabela"
author: Otavio
date: 2026-10-27
branch: dev
cost: { minutes: 1, tokens: 0 }
id: l-9e7c3413
scope: repo
status: active
src: agent
touches:
  - docs/modelo-er.md
  - state.md
---

## Decided
- "Validado" (pedagógica) e "o que mudou" (impresso) saem da revista já resolvida, não do histórico das tabelas. O texto final muda por muitos caminhos (matriz compartilhada por ~25 projetos, texto-modelo herdado, marcador {NOME DO PROJETO}, corte que joga a tarefa para outro padrão); comparar a revista montada pega todos sem código de invalidação em cada tabela.
- Validado = hash da revista resolvida guardado no clique; se o hash atual difere, o projeto deixou de estar validado. O diff do impresso compara com a última foto (JSON) tirada no clique "Revista Impressa Atualizada", nunca com a última validação, para nenhum ajuste escapar.

## Tried and ruled out
- Flag `validado` derrubada por sinais em cada modelo: frágil, qualquer caminho esquecido deixa revista mudada como validada.
- Marco pela data/hora do download das planilhas: o impresso não baixa de novo, quer só ver o texto que mudou.

## Watch out
- Gerar PDF de diagrama Mermaid com `google-chrome --headless --print-to-pdf` imprime antes do Mermaid terminar (páginas em branco). Esperar um sinal da página (Playwright `wait_for_function`) antes de `page.pdf`.
- `direction LR` em `erDiagram` só funciona a partir do mermaid 11.6.0; no 11.4.1 vira duas tabelas chamadas "direction" e "LR".

In the code:
- Projeto.hash_validado e FotoRevista.conteudo (jsonb) em docs/modelo-er.md; decisões D-074, D-077, D-078, D-084 no state.md.
