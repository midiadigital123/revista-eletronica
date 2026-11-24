---
title: "Cada clique numerado do infográfico do F2 é um botão + que abre o seu texto, e o template SVG precisa desligar a localização"
author: Otavio
date: 2026-11-10
branch: feat/f2-f2
id: l-584de2e2
scope: repo
status: active
src: agent
touches:
  - app/nucleo/templates/revista/f2.svg
  - state.md
---

## Decided
- Os cliques ❶ a ❹ do docx são botões + no infográfico: ❶ no cartão do descritor (laranja, porque amarelo some no cartão amarelo), ❷ sob a progressão, ❸ sob a descrição das habilidades, ❹ sob "Tarefas por nível de complexidade" (abre só o parágrafo de abertura do bloco), e um + por item (imagem montada + análise). Não há botão sob "Itens". Confirmado pelo usuário em 09/11.
- A letra I/A/C/R de cada etapa é preenchida pela Pedagógica e sai uma por linha, mesmo nas linhas de texto mesclado.

## Tried and ruled out
- Abertura do bloco ❹ no painel do tour: o usuário quer o botão, como nos outros passos.
- Juntar a letra nas linhas mescladas, como o desenho antigo fazia só em alguns grupos: inconsistente, e a marca é por etapa.

## Watch out
- Com LANGUAGE_CODE pt-br, o Django escreve float com vírgula (405,7) e quebra as coordenadas do SVG: o template roda dentro de localize off.
- O hover do svg-tour pinta o botão de laranja; o botão ❶, já laranja, não muda de cor no hover (o CSS do tour não pode ser alterado).

In the code: app/nucleo/templates/revista/f2.svg ({% localize off %}, classe f2-laranja, ids f2-btn-action-{descritor|habilidades|progressao|tarefas|tarefa-N}); seção dlg-tarefas em texto.SECOES_F2; state.md D-241.
