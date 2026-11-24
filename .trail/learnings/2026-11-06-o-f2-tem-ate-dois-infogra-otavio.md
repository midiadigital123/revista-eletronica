---
title: "O F2 tem até dois infográficos por revista, Alfa e Outras Etapas, que a cascata dos cortes decide, e o passo é desligado por infográfico"
author: Otavio
date: 2026-11-06
branch: feat/f2-fase0
id: l-ab85944c
scope: repo
status: active
replaces: l-2d6876ae
src: agent
touches:
  - app/nucleo/servicos/cascata.py
  - state.md
  - docs/superpowers/specs/2026-11-06-f2-campos-do-docx.md
---

## Decided
O F2 de uma revista (projeto × componente) tem até dois infográficos, e não um: 'Avaliação e Currículo – Alfa' e 'Avaliação e Currículo – Outras Etapas'. Nenhum dos dois é escolhido à mão: a cascata dos cortes decide. O Alfa existe quando o parceiro tem cortes para o 2EF naquele componente, porque o Alfa é o 2EF; o Outras Etapas existe quando há cortes para qualquer outra etapa, todas aglutinadas num só. Até quatro por projeto (2 LP + 2 MT), e a interface mostra só os que existem. Os passos canônicos (abertura, descritor, habilidades, progressão, tarefas) continuam fixos no código, gerados em SVG pelo servidor com o svg-tour intocado, mas quem desliga um passo é o infográfico (revista × tipo), não o projeto nem a revista inteira, porque LP e MT, e Alfa e Outras Etapas, podem ter composições diferentes.

## Tried and ruled out
Desligar passos por projeto (versão de 06/11 de manhã): obrigaria LP e MT à mesma composição; o usuário decidiu por revista à tarde, e com os dois infográficos a unidade certa é o infográfico. Um infográfico por revista: não cobre o Alfa, que é um infográfico próprio do 2EF. Escolha manual de quais infográficos a revista tem: a regra é determinística pelos cortes e a escolha abriria incoerência com as etapas avaliadas.

## Watch out
Todo campo do F2 que o levantamento do docx marcou como 'da revista' (habilidade destacada, tabela por etapa, itens, textos dos cliques) passa a ser por infográfico. Navegação do F2 na página e no zip, planilha do impresso e Validado precisam contar com 0, 1 ou 2 infográficos por revista. O docx recebido chama-se AF_EM mas traz um item do 2EF: confirmar com a Pedagógica se é o Outras Etapas e se o Alfa tem a mesma estrutura.

In the code:
Cascata: app/nucleo/servicos/cascata.py (gravar_cortes cria e arquiva revistas por componente; a existência dos infográficos entra ali). Futuro: tabela revista_f2_infografico com tipo CHECK alfa/outras e os passos desligados. Decisões D-229 e D-230 no state.md; levantamento em docs/superpowers/specs/2026-11-06-f2-campos-do-docx.md §6.
