---
title: "A carga de 2026 cria as etapas não canônicas e preenche com 100, 200, 300 o corte que falta, em vez de deixar vazio"
author: Otavio
date: 2026-11-24
branch: feat/carga-nao-canonica
id: l-838869bd
scope: repo
status: active
src: agent
touches:
  - README.md
  - app/nucleo/management/commands/importar_cortes.py
  - app/nucleo/tests/test_importar_cortes.py
  - docs/regras-de-negocio.md
  - kanban.md
  - scripts/povoar-banco-2026.sh
  - state.md
---

## Decided
Em 24/11 o usuário mudou três pontos da carga de 12/11: a etapa que a planilha Somativas pede e o ano não tem é criada pela carga (1EF e 2EF com escala 1000, as demais 500); o corte sem valor na planilha de cortes, canônica ou não, entra como "100, 200, 300" e sai listado no relatório; todo parceiro recebe a matriz Comunitária, inclusive CE, Joinville e ES, até o superusuário trocar. Motivo: prazo apertado, o superusuário povoa o máximo e os usuários só corrigem pela tela. Continua valendo da carga de 12/11: nomes dos parceiros, ALFA e regular no mesmo parceiro, só LP e MT.

## Tried and ruled out
- Criar as 7 etapas novas no comando dos cadastros: os testes usam esse comando e contam com 4 etapas; a carga cria só o que a planilha pede.
- Projeto com etapa marcada e corte vazio: é o corte que diz ao sistema que o parceiro avalia a etapa, e mudar isso mexeria na cascata.

## Watch out
- Na tela, corte arbitrário é igual a corte real: a única lista é o relatório do comando (84 de 232 nas planilhas reais).
- A etapa não canônica nasce com a pendência de matriz sem saída até existir a tela de apontar.
- O comando segue pulando parceiro que já tem corte: banco já carregado precisa ser refeito do zero.

In the code: app/nucleo/management/commands/importar_cortes.py (ESCALA_1000, ARBITRARIO, --matriz), scripts/povoar-banco-2026.sh, D-278 no state.md.
