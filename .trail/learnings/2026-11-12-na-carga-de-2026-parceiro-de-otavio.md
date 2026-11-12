---
title: "Na carga de 2026, parceiro de estado leva a sigla da UF, e linhas ALFA e regular do mesmo estado são um parceiro só"
author: Otavio
date: 2026-11-12
branch: feat/carga-2026
id: l-a314fbe7
scope: repo
status: active
src: agent
touches:
  - kanban.md
  - state.md
---

## Decided
O usuário escolheu (12/11) nomear o parceiro pela sigla da UF para estado (GO, SC) e pelo nome já usado na planilha de cortes para cidade (Florianópolis, JOINVILLE, PORTO ALEGRE, SALVADOR). Cidades novas de 2026: Anchieta, Angra dos Reis, Belo Horizonte, Niterói e "Rio (município)", separado de RJ (estado).
Na planilha Somativas, a linha "ALFA" e a linha regular do mesmo estado são o mesmo parceiro, com uma só revista por componente. A diferença é só o F2: Alfa se há corte no 2EF, Outras Etapas se há corte em outra etapa.
Parceiro que só tem etapas fora de 2EF, 5EF, 9EF e 3EM nasce sem cortes. O Subprograma (SAEGO, PAEBES…) não preenche variáveis do projeto.

## Tried and ruled out
Nome completo do estado (Goiás, Santa Catarina): foge da planilha de cortes e dos 29 parceiros de 2025, que a Pedagógica já conhece.
Um parceiro por linha ALFA e por linha regular: duplicaria revista e projeto, e o sistema aceita um projeto ativo por parceiro e ano.
Preencher nome_programa e sigla_programa pelo Subprograma: fora do pedido, e ALFA e regular dividem o projeto, então não há um programa só.

## Watch out
A planilha "Cortes dos Padrões por Etapa e Parceiro.xlsx" recebida em 2026 é idêntica à de 2025 (mesmo sha256). Os valores precisam da validação da Pedagógica.
A aba "9EF - LP" dessa planilha tem uma coluna E sobrando: ler por índice de coluna, não por desempacotamento de 4 valores.
A gravação de cortes substitui todos os cortes do parceiro no ano, então o importador pula quem já tem corte.

In the code: `app/nucleo/management/commands/importar_cortes.py` (dict NOMES; `ler_somativas`, `ler_cortes`), `nucleo.servicos.cascata.gravar_cortes`, D-261 no `state.md`.
