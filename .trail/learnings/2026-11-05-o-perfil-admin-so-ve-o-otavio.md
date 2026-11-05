---
title: "O perfil Admin só vê o usuário do Impresso: trocar a senha dele seria entrar como Impresso e marcar revista como impressa"
author: Otavio
date: 2026-11-05
branch: feat/telas-b-ux
cost: { minutes: 26, tokens: 62365 }
id: l-9baf0b12
scope: repo
status: active
src: agent
touches:
  - state.md
  - app/nucleo/tests/test_admin_cadastro.py
  - app/nucleo/tests/test_ui_usuarios.py
  - app/nucleo/usuarios.py
  - docs/regras-de-negocio.md
  - CLAUDE.md
  - README.md
  - docs/telas/fichas/cortes.md
  - docs/telas/fichas/matriz.md
  - docs/telas/fichas/revista.md
---

## Decided
O perfil Admin (não superusuário) não altera nada de quem tem grupo que ele não pode atribuir (outro Admin ou Impresso): nem dados, nem senha, nem grupo, nem ativo. Só o superusuário mexe nesses usuários. A regra vale para o admin do Django e para a tela de Usuários, porque as duas usam o mesmo módulo de regras.

## Tried and ruled out
- Bloquear só a troca de senha: dados e "Desativar" continuariam abertos a um perfil que nem pode dar o grupo Impresso a ninguém.
- Deixar como estava (o Admin redefinia a senha do Impresso): o Admin entraria como Impresso e ganharia `marcar_impressa`, anulando ADMIN_MARCA_IMPRESSA = False.

## Watch out
- Pedido de "deixar o Admin desativar quem é do Impresso" reabre a discussão: a recusa é de propósito.
- Qualquer tela nova que mexa em usuário precisa passar por `pode_editar`, não checar o grupo Admin à mão.

In the code: `app/nucleo/usuarios.py` (`pode_editar`, `grupos_permitidos`, `GRUPOS_DO_ADMIN`); testes `test_ui_usuarios.UsuariosUiTest.test_nao_altera_quem_tem_grupo_fora_dos_permitidos` e `test_admin_cadastro` (PerfisTest); decisão D-211.
