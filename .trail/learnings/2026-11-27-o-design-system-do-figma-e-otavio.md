---
title: "O design system do Figma é extraído para HTML estático em docs, e a extração tem de ser refeita quando o arquivo troca de biblioteca"
author: Otavio
date: 2026-11-27
branch: feat/design-system-v2
id: l-9d870116
scope: repo
status: active
replaces: l-7e429e41
src: agent
touches:
  - docs/design-system-figma/componentes.css
  - docs/design-system-figma/componentes.html
  - docs/design-system-figma/doc.css
  - docs/design-system-figma/index.html
  - docs/design-system-figma/telas.html
  - docs/design-system-figma/tokens.css
  - docs/design-system-figma/tokens.html
  - kanban.md
  - state.md
---

## Decided
Em 27/11 o Figma "Sistemas CAEd" foi religado à biblioteca nova "UI Fundação CAEd" e a primeira extração (D-304) ficou velha no mesmo dia: os nomes dos tokens, a fonte e medidas de modal, tooltip e menu mudaram. A extração foi refeita no mesmo formato (D-306): HTML estático versionado em docs/, sem build e sem CDN, cada valor saído do get_variable_defs ou do get_design_context, cada componente com node-id e o par nas telas B. A fonte agora é Montserrat (livre), e os tokens têm nomes por papel (texto, superfície, borda, ícone, situação, tamanho).

## Tried and ruled out
- Artifact privado no claude.ai: o usuário preferiu versionar junto do código, como insumo da K-048.
- Só renomear os tokens: medidas de modal (raio 20→8), tooltip (sem sombra), menu (NavBar) e upload também mudaram.
- Apagar as variáveis antigas: componentes da biblioteca ainda usam Global.Color.*, dimension/* e dois estilos em Proxima Nova; ficam num bloco "Legado" do tokens.css apontando para a nova.
- Confiar na página "Revisão da biblioteca": ela lista 11 candidatos a componente, mas 10 foram publicados no mesmo dia. Conferir com search_design_system e com as instâncias das telas antes de chamar algo de "proposta".

## Watch out
- Para saber se o Figma mudou: get_metadata sem nodeId lista as páginas (uma página "Backup" indica troca de biblioteca), e get_variable_defs nas 4 seções mostra os nomes atuais. get_variable_defs falha no nó da página (canvas).
- spacing/4xl e spacing/5xl valem os dois 32 no Figma: pergunta aberta ao design.
- Contraste abaixo do WCAG continua: #808080 texto terciário, #ccc borda do campo, #fdea00 sublinhado ativo.
- A extração não é o CSS do sistema: só o tokens.css pode ser copiado; componentes.css (prefixo ds-) é referência de medidas.

In the code:
- docs/design-system-figma/{index,tokens,componentes,telas}.html, tokens.css, componentes.css, doc.css; propostas em telas.html#propostas
- Figma fileKey aMiF7hiCBPNc1X9yYFuZO6; Telas – v1 266:5193 (seções 266:5194/5196/5198/5200), Componentes 11:33, Revisão da biblioteca 264:4255
