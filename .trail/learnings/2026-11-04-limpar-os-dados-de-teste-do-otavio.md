---
title: Limpar os dados de teste do banco de dev quebra o Playwright; recrie a demo e um ano vazio antes de rodar
author: Otavio
date: 2026-11-04
branch: feat/telas-b-ux
cost: { minutes: 18, tokens: 29545 }
id: l-9fb3f4a9
scope: repo
status: active
src: agent
touches:
  - state.md
  - app/nucleo/static/ui/telas/templates.css
---

## Decided
Depois de apagar do banco de dev o que foi criado para teste, recrie os dados de que os specs dependem antes de rodar o Playwright completo: a revista de demonstração de 2026 e um segundo ano vazio (2025).

## Tried and ruled out
- Atribuir as 7 falhas ao merge do "projeto primeiro": com a demo e o ano 2025 recriados, a mesma branch passou 51/51.

## Watch out
- Sem login E2E, 32 specs pulam em silêncio. Os usuários de teste já existem; dá para definir uma senha temporária só para a execução, sem gravá-la.
- Não abra 2027 com abrir_ano para ter o segundo ano: ele copia os descritores e o item.spec passa a achar dois "D01".

In the code: `docker compose exec -T app python manage.py criar_demo --ano 2026`; `Ano.objects.get_or_create(ano=2025)`; variáveis `E2E_ADMIN_USUARIO/SENHA` (usuário `e2e`) e `E2E_IMPRESSO_USUARIO/SENHA` (usuário `imp-e2e`); specs `app/e2e/tests/{ano,painel,impresso,item,revista-textos}.spec.ts`.
