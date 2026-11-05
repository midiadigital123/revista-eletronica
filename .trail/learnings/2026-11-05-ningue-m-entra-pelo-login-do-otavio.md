---
title: "Ninguém entra pelo login do admin: o login e o sair são das telas novas, e o endereço de login do admin só redireciona"
author: Otavio
date: 2026-11-05
branch: feat/telas-b-ux
cost: { minutes: 25, tokens: 71437 }
id: l-85337ade
scope: repo
status: active
src: agent
touches:
  - state.md
  - app/e2e/tests/item.spec.ts
  - app/nucleo/static/ui/ui.css
  - app/nucleo/templates/ui/base.html
  - app/nucleo/templates/ui/entrar.html
  - app/nucleo/tests/test_impresso.py
  - app/nucleo/tests/test_painel.py
  - app/nucleo/tests/test_preview.py
  - app/nucleo/tests/test_ui_base.py
  - app/nucleo/tests/test_ui_cortes.py
---

## Decided
O usuário não quer ver "Administração do Django" ao entrar, sair ou trocar de perfil. O login e o logout são páginas próprias no visual das telas B; o endereço de login do admin virou um redirecionamento para elas, levando o `next`. Depois de entrar sem `next`, a pessoa cai no Painel do ano mais recente.

## Tried and ruled out
- Só restilizar o template de login do admin: o endereço continuaria sob /admin/ e o `next=/admin/` seguiria deixando a pessoa no índice do admin.
- Um login customizado no AdminSite: mais código para o mesmo efeito do redirecionamento.

## Watch out
- View nova não passa `login_url`: o padrão vem do settings. Passar `login_url="admin:login"` de novo traz a tela do admin de volta.
- Os specs do Playwright entram por /admin/login/ (passam pelo redirecionamento) e dependem de `#id_username`, `#id_password` e `input[type=submit]` na página de login. Trocar o botão para `<button>` quebra ~15 specs.
- O admin codifica o `next` (`?next=%2Fadmin%2F`); o redirecionamento repassa a query como veio.

In the code: `app/sistema/settings.py` (LOGIN_URL = "entrar", LOGIN_REDIRECT_URL = "inicio", LOGOUT_REDIRECT_URL = "entrar"); `app/sistema/urls.py` (RedirectView em admin/login/); `app/nucleo/urls/conta.py` (rotas `entrar` e `sair`); `app/nucleo/templates/ui/entrar.html`; teste `test_ui_base.EntrarTest`; decisão D-212.
