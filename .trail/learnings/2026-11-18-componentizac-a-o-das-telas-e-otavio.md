---
title: "Componentização das telas é por componente de template com django-cotton, não por DaisyUI; a demo é a página do projeto"
author: Otavio
date: 2026-11-18
branch: main
cost: { minutes: 23, tokens: 268261 }
id: l-c1380cb2
scope: repo
status: active
src: agent
touches:
  - state.md
  - kanban.md
  - app/requirements.txt
  - app/sistema/settings.py
  - app/nucleo/templates/ui/projeto/projeto.html
  - app/nucleo/templates/ui/projeto/lista.html
  - app/nucleo/templates/ui/usuarios/lista.html
---

## Decided
O usuário sente que as telas do dia a dia "parecem soltas". A medição confirmou: os componentes existem só como classes CSS, repetidas à mão em cada tela (botão 117 vezes, campo 39, card 28, cabeçalho de página 24). Em 18/11 ele escolheu ver uma demo de componentes de template com django-cotton, na página de detalhe do projeto, antes de decidir se adota no sistema todo. A demo mantém o mesmo CSS, as mesmas views e nenhum teste editado; os 52 testes de projeto passam com o template reescrito. No mesmo dia ele abandonou a proposta de nova UI/UX (a esteira de 5 fases): a branch dela fica no GitHub como arquivo, sem merge.

## Tried and ruled out
- DaisyUI: também é só classe CSS, então não resolve o "solto"; exige Tailwind 4 e um passo de build que o projeto não tem; e sete nomes de classe colidem com os atuais (btn, badge, card, input, select, textarea, link).
- Só `{% include %}`: não aceita conteúdo dentro da peça, então card, campo e modal ficam desajeitados.
- Rota paralela ou cópia da página para a demo: converter a página real numa branch deixa os testes existentes provarem que nada mudou.
- Demo na lista de projetos (recomendada pelo agente) ou na lista de usuários: o usuário preferiu o detalhe do projeto, a página maior.

## Watch out
- Prop sem valor padrão no `<c-vars>` pode herdar uma variável de mesmo nome do contexto da página: dê padrão vazio a todas.
- Atributo condicional não vai solto na tag do componente; passe como prop (`oculto="{% if … %}1{% endif %}"`) e decida dentro do componente.
- `{{ attrs }}` vazio deixa um espaço antes do `>` e quebra testes que comparam o HTML exato; teste com `{% if attrs.attrs_dict %}` (o `attrs` puro é sempre verdadeiro quando há props).
- Os testes conferem a ordem dos atributos (`id`, `aria-labelledby`, `hidden`): o componente precisa emitir nessa ordem.
- Valor de atributo do cotton não pode conter aspas duplas: use aspas simples nas tags Django dentro dele.
- O banco da worktree de trabalho nasce vazio; o usuário que o comando de demonstração cria não tem perfil e recebe 403 na página do projeto.

In the code: worktree `../revista-express-trabalho`, branch `feat/cotton-demo` (de `integ/cotton`), porta 8001; `app/nucleo/templates/cotton/` (`pagina_cab`, `card`, `campo`, `badge`, `botao`, `abas`, `aba`); `app/nucleo/templates/ui/projeto/projeto.html`; `django-cotton>=2.9,<3` em `app/requirements.txt`; `django_cotton` em `INSTALLED_APPS`; decisões D-269 e D-270 no `state.md`, card K-042.
