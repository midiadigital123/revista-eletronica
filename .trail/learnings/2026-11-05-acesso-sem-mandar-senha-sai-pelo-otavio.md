---
title: Acesso sem mandar senha sai pelo botão Link de acesso; o Novo usuário continua pedindo senha
author: Otavio
date: 2026-11-05
branch: main
cost: { minutes: 32, tokens: 178460 }
id: l-8d61a02f
scope: repo
status: active
src: agent
touches:
  - state.md
  - app/nucleo/static/ui/favicon.png
  - app/nucleo/templates/ui/base.html
  - app/nucleo/templates/ui/entrar.html
  - app/nucleo/urls/ui_usuarios.py
  - app/nucleo/usuarios.py
  - app/nucleo/urls/conta.py
---

## Decided
- Para dar acesso a alguém sem mandar senha, a tela Usuários tem "Link de acesso" em cada linha: o link do Django para a pessoa criar a própria senha (vale 3 dias, uma vez só), com mensagem pronta. Mesma regra de "Redefinir senha": o perfil Admin não gera link de outro Admin nem do Impresso.
- O usuário escolheu manter o "Novo usuário" pedindo senha. O link sai só pelo botão da linha.
- O endereço absoluto do link vem do cabeçalho Origin do POST, que o CSRF já validou e que traz o https do navegador.

## Tried and ruled out
- "Novo usuário" nascer sem senha e cair direto no link: recusado pelo usuário, que prefere manter o fluxo atual.
- Montar o link só com build_absolute_uri: em produção o proxy faz o HTTPS e o app recebe http, então o link sairia http://.
- Link por GET: ficaria no histórico do navegador e nos logs.

## Watch out
- A página aberta pelo link usava os templates do admin ("Administração do Django"); agora usa templates próprios. View nova de conta precisa passar template_name, senão volta o admin.
- O usuário `e2e` do banco de dev estava desativado em 05/11: o E2E falha no login com "Usuário ou senha incorretos". Reative só para a execução e desative de novo.

In the code: `app/nucleo/urls/ui_usuarios.py::link` (rota `ui_usuarios_link`), `app/nucleo/usuarios.py::caminho_definir_senha` (também usada por `criar_usuarios`), `app/nucleo/urls/conta.py` com `ui/senha_definir.html` e `ui/senha_pronto.html`, teste `test_link_usa_a_origem_https_atras_do_proxy`. Decisão D-216.
