---
title: Toda função do back precisa de botão na tela nova; link para o admin não conta
author: Otavio
date: 2026-10-30
branch: refatoracao-django
cost: { minutes: 8, tokens: 62767 }
id: l-9d315257
scope: repo
status: active
src: agent
touches:
  - state.md
  - docker-compose.yml
  - app/nucleo/tests/test_ui_cortes.py
  - app/nucleo/urls/cortes.py
  - app/nucleo/templates/ui/cortes.html
---

## Decided
O usuário exige que as telas novas (fora do admin) ofereçam tudo o que o back permite ao perfil, e que nada errado apareça para quem não pode usar. Rota no banco ou ação no admin não basta: se o perfil pode fazer, a tela precisa ter o controle. Se não pode, o controle não aparece.
Caso que motivou: a grade de cortes editava e apagava células, mas não criava linhas. Cada linha é um parceiro, e cada parceiro vira um projeto. Criar parceiro só existia no admin. Foi corrigido com um formulário "Nova linha" na própria grade.

## Tried and ruled out
- Dizer que o CRUD "já existia" porque as permissões e a grade cobriam as células: o usuário rejeitou, porque faltava criar a linha.
- Mandar para o admin ("Cadastre os parceiros no admin"): a tela nova deve dispensar o admin no trabalho do dia a dia.

## Watch out
Ao conferir uma tela, liste também as entidades das linhas e colunas (quem cria, quem apaga), não só os campos editáveis. Cada controle deve checar `perms.` no template, e a view deve repetir a checagem.

In the code: `app/nucleo/urls/cortes.py` (`novo_parceiro`, rota `cortes_novo_parceiro`, exige `nucleo.add_parceiro`); `app/nucleo/templates/ui/cortes.html`; teste `test_adicionar_parceiro_cria_linha` em `app/nucleo/tests/test_ui_cortes.py`. Para achar lacunas: `grep -rn "admin:" app/nucleo/templates/ui`.
