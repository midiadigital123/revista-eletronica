---
title: "Todo projeto parte da matriz Comunitária e edita localmente a etapa que precisar, por uma cópia criada no botão; a cópia sempre vale sobre a matriz"
author: Otavio
date: 2026-11-24
branch: feat/apontar-etapa
id: l-b1976ec9
scope: repo
status: active
replaces: l-90fc2221
src: agent
touches:
  - state.md
  - app/nucleo/servicos/etapa_projeto.py
  - app/nucleo/servicos/pendencias.py
  - app/nucleo/urls/ui_projeto.py
---

## Decided
Em 24/11 a Pedagógica pediu que qualquer projeto possa editar localmente todos os elementos da matriz (descritores, tarefas, passo), sem alterar a matriz nem os outros projetos. O usuário decidiu:
- A cópia de uma etapa × componente nasce pelo botão "Editar só neste projeto", na aba Matriz do projeto, para toda etapa com corte (canônica ou não). Sem clicar, o projeto continua lendo a matriz e não entra em revisão.
- Quando o projeto tem cópia, a cópia sempre vale. A pendência de escolha "a matriz agora tem a etapa: escolha qual usar" e os botões de escolha saem. Voltar à matriz é desfazer a cópia (confirmação forte).
- Só haverá uma matriz, a Comunitária. ES, CE e Joinville não terão matriz própria: todo projeto parte da Comunitária e faz as modificações locais.
- Se a matriz do parceiro for trocada, as cópias ficam, ligadas à base de onde vieram.
- Continuam: a cópia é clone com vínculo e revisão em 3 vias; clone de clone é proibido; o projeto recriado pela cascata herda as cópias; a abertura de ano não leva as cópias; etapa não canônica nasce apontada para uma canônica.

## Tried and ruled out
- Projeto só aponta para a matriz, sem conteúdo próprio (regra antiga): cai, porque a Pedagógica precisa de edição local em qualquer projeto.
- Clonar todas as etapas ao atribuir a matriz: cada mudança na Comunitária abriria revisão e bloquearia o Validado de até 66 revistas.
- Criar a cópia sozinha na primeira gravação do editor: o mesmo editor gravaria em dois lugares conforme a porta de entrada.
- Manter a pendência de escolha só para a etapa não canônica: dois comportamentos para a mesma coisa.
- Recusar ou apagar as cópias na troca de matriz: perde edição local, e com uma só matriz o caso quase não ocorre.
- Matrizes próprias para ES, CE e Joinville (duplicar a Comunitária): não são mais necessárias.

## Watch out
- Em 24/11 isto ainda não estava implementado: a criação da etapa do projeto recusava etapa canônica e etapa que a matriz do parceiro já tem, e a pendência de escolha ainda existia.
- Editar a Comunitária passa a abrir revisão nos projetos com cópia: o modal de impacto de quem edita a base precisa listar esses projetos.

In the code:
- docs/edicao-local-por-projeto.md (requisito e critérios de aceite)
- state.md: D-288 (substitui em parte D-051, D-276 itens 3 e 4, D-280 item 5, D-281 item 2)
- app/nucleo/servicos/etapa_projeto.py: criar, vigente, escolher
- app/nucleo/servicos/pendencias.py: etapa_em_dobro
- app/nucleo/urls/ui_projeto.py: _etapas_do_projeto
