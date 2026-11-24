---
title: "Superusuário cria matriz, template, parceiro e projeto; os usuários só editam, e o redesenho das telas fica por último"
author: Otavio
date: 2026-11-24
branch: feat/carga-nao-canonica
id: l-d9160ba7
scope: repo
status: active
src: agent
touches:
  - state.md
  - kanban.md
---

## Decided
Em 24/11 o usuário decidiu, por causa do prazo apertado, que criar matriz, criar template de texto, atribuir matriz e criar parceiro ou projeto ficam com o superusuário, pelo admin ou por comando, fora das telas do dia a dia. Os usuários editam matriz, template, cortes do projeto, variáveis, textos, capa e infográficos. A exceção é apontar a etapa não canônica para uma canônica, que a Pedagógica faz pela tela. Ordem do trabalho: carga, etapa do projeto no servidor, telas de apontar e de revisão no layout atual e, por último, o redesenho pelo Figma (menu Projetos, Modelos, Impresso).

## Tried and ruled out
- Fazer o redesenho antes da etapa do projeto: atrasa o apontamento, que é imprescindível.
- Desenhar as telas de apontar e de revisão direto no layout novo: só ficariam disponíveis depois do redesenho. O custo aceito é refazê-las no redesenho.
- Apontar pela planilha, na carga: o usuário quer a Pedagógica decidindo na tela.

## Watch out
- Isso contraria em parte a regra antiga de que toda função do servidor tem controle na tela: não acrescente botão de criar matriz, template ou parceiro em tela nova.
- Os botões de criar que existem hoje só saem no redesenho.
- A carga não escolhe template: toda revista nasce com a pendência de template.

In the code: D-277 no state.md; plano de 11 etapas no kanban.md (K-034, K-048).
