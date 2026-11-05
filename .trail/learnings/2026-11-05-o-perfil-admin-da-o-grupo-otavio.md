---
title: O perfil Admin dá o grupo Impresso e também marca a revista como impressa
author: Otavio
date: 2026-11-05
branch: main
cost: { minutes: 21, tokens: 60446 }
id: l-80cc11bf
scope: repo
status: active
replaces: l-9baf0b12
src: agent
touches:
  - state.md
  - CLAUDE.md
  - INFRA.md
  - README.md
  - app/nucleo/management/commands/tornar_superusuario.py
  - app/nucleo/permissoes.py
  - app/nucleo/tests/test_tornar_superusuario.py
  - docs/regras-de-negocio.md
  - app/e2e/tests/usuarios.spec.ts
  - app/nucleo/static/ui/telas/usuarios.css
---

## Decided
- Em 05/11 o usuário decidiu que o Admin atribui o grupo Impresso e gerencia esses usuários (grupo, senha, link de acesso, desativar, excluir sem rastro). Junto, o Admin passou a marcar "Revista Impressa Atualizada".
- O grupo Admin e a alteração de outro Admin continuam só com o superusuário.

## Tried and ruled out
- Liberar o Impresso e manter o Admin sem marcar impressa: quem gerencia um Impresso entra como ele (senha, link, ou cria com senha conhecida e move de grupo), então a proibição seria só de fachada.
- Liberar só a atribuição do grupo, sem gerenciar o Impresso depois: contornável do mesmo jeito.
- Manter como estava e delegar com o comando de superusuário: o usuário preferiu liberar.

## Watch out
- Voltar a proibir o Admin de marcar impressa exige tirar o Impresso dos grupos que ele atribui; senão a regra volta a ser contornável.
- Mudar a flag exige migração de dados nova nos grupos (o teste dos grupos no banco falha sem ela).

In the code: `ADMIN_MARCA_IMPRESSA = True` em `app/nucleo/permissoes.py`, `GRUPOS_DO_ADMIN` em `app/nucleo/usuarios.py`, migração `app/nucleo/migrations/0019_admin_marca_impressa.py`. Decisão D-220.
