---
title: "Tela de revisão das mudanças da base: duas colunas com diff, ordem num cartão só e imagem antiga apenas com aviso"
author: Otavio
date: 2026-11-24
branch: fix/descritor-codigo-livre
id: l-6dead934
scope: repo
status: active
src: agent
touches:
  - state.md
  - app/nucleo/servicos/etapa_projeto.py
  - app/nucleo/urls/ui_matriz.py
  - app/nucleo/urls/impresso.py
---

## Decided
Em 24/11, ao planejar a etapa 8 (tela em que o projeto revisa o que mudou na base da sua cópia), o usuário escolheu:
- Cada trecho aparece em 2 colunas, "No projeto" e "Na base agora", com diff por palavra (riscado saiu, sublinhado entrou). O valor de quando o projeto copiou fica num recolhível.
- Mudança de ordem vira um cartão por grupo (descritores; tarefas de cada descritor) e a escolha vale para o grupo todo, porque arrastar um descritor na base renumera vários.
- Quando base e projeto trocaram a imagem da mesma tarefa e o arquivo antigo já foi apagado, a tela só avisa "A imagem de antes não existe mais.". A escolha é entre as duas imagens que existem.
Decisões do plano (do Claude, ainda sem o "ok" do usuário): botão "Concluir revisão" sempre ativo, com o navegador levando o foco à decisão que falta; campos do formulário por índice do cartão mais o hash do que foi visto, descartando as escolhas se a lista mudou.

## Tried and ruled out
- 3 colunas de texto inteiro, sem diff: em texto longo a pessoa procura a diferença no olho.
- Um item por descritor reordenado: uma reordenação gera vários itens iguais e permite misturar as duas ordens.
- Guardar o arquivo antigo enquanto alguma cópia o cita: 3 pontos de código e limpeza no concluir e no desfazer, para uma imagem que não entra na escolha.
- Rota da tela dentro do caminho do editor da matriz: 4 specs E2E usam esse caminho como seletor.

## Watch out
- O texto que a classificação devolve vem da foto, que junta espaços e quebras de linha. A caixa de "Escrever outro texto" precisa do texto bruto do objeto do projeto, senão salvar apaga as quebras.
- A rota de revisão precisa dar 404 antes de tomar o bloqueio quando a etapa é da matriz ou não tem base: com o alvo comum do editor, um GET travaria a Comunitária.
- Dois defeitos no concluir achados só por leitura, a confirmar com teste vermelho: descritor de código "passo" cai no ramo do passo da etapa; código com "/" quebra a separação da chave da tarefa.

In the code: D-292 no `state.md`; plano em `~/.claude/plans/planeje-a-etapa-8-cryptic-karp.md`; `app/nucleo/servicos/etapa_projeto.py` (`revisao`, `concluir`, l.254 `item.chave == "passo"`, `_objeto` com `partition("/")`, `_norm`); `app/nucleo/urls/ui_matriz.py::_alvo_mec`; diff por palavra em `app/nucleo/urls/impresso.py::_partes`; rota prevista `/ui/revisao/<pk>/`.
