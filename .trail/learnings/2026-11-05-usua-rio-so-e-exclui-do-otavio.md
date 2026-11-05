---
title: Usuário só é excluído se nunca registrou nada no sistema; quem trabalhou é desativado
author: Otavio
date: 2026-11-05
branch: main
cost: { minutes: 10, tokens: 96280 }
id: l-bfae581d
scope: repo
status: active
src: agent
touches:
  - state.md
  - README.md
  - app/e2e/tests/usuarios.spec.ts
  - app/nucleo/management/commands/criar_usuarios.py
  - app/nucleo/static/ui/telas/usuarios.css
  - app/nucleo/static/ui/ui.css
  - app/nucleo/templates/ui/senha_definir.html
  - app/nucleo/templates/ui/senha_pronto.html
  - app/nucleo/templates/ui/usuarios/link.html
  - app/nucleo/templates/ui/usuarios/lista.html
---

## Decided
- O perfil Admin exclui usuários pela tela Usuários, mas só quem não tem rastro: nenhuma edição no histórico, versão de template, validação de revista, foto de revista nem ação no admin. Com rastro, a página lista o que impede e manda desativar. Escolha do usuário em 05/11 ("só sem rastro").
- Quem pode excluir é quem pode desativar: ninguém se exclui, e o Admin só mexe em Pedagógica e Mídias Digitais.
- A permissão usada é a de alterar usuário. O Admin não ganha a permissão de excluir usuário do Django.

## Tried and ruled out
- Excluir sempre, deixando o autor vazio: perde a auditoria de forma irreversível e exigiria trocar 3 chaves estrangeiras de PROTECT para SET_NULL. O usuário recusou.
- Dar ao Admin a permissão de excluir usuário do Django: o excluir do admin não conhece a regra de rastro e apagaria o autor do histórico sem aviso, porque o autor no histórico é SET_NULL.
- Esconder o ícone de excluir de quem tem rastro: seriam ~20 contagens por linha na lista.

## Watch out
- O autor do histórico (history_user do django-simple-history) é uma chave escondida (related_name="+"): não aparece em _meta.related_objects nem no Collector. Quem contar o "uso" de um usuário precisa buscar esse campo em cada tabela de histórico.
- O teste de navegador de Usuários agora exclui o usuário que cria; antes deixava um desativado por execução.

In the code: `app/nucleo/usuarios.py::rastros` e `::excluir` (select_for_update + nova conferência), view `excluir` em `app/nucleo/urls/ui_usuarios.py` (rota `ui_usuarios_excluir`, template comum `ui/excluir.html`), testes `test_com_rastro_so_desativa` e `test_excluir_corrida_com_rastro_novo`. Decisão D-218 (modifica D-205 só para usuário).
