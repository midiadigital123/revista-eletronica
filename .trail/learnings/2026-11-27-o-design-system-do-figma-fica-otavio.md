---
title: "O design system do Figma fica documentado em HTML estático versionado no repositório, separado do CSS do sistema"
author: Otavio
date: 2026-11-27
branch: feat/design-system-figma
id: l-7e429e41
scope: repo
status: active
src: agent
touches:
  - kanban.md
  - state.md
  - docs/telas/design-system.md
---

## Decided
Em 27/11 o usuário pediu o design system do Figma "Sistemas CAEd" (página Telas – v1 e página Componentes, biblioteca "UI Fundação CAEd") extraído antes de mexer nas telas (etapa 11, K-048). Ficou em páginas HTML estáticas versionadas em docs/, sem build e sem CDN, e inclui a página Componentes porque as telas só mostram os estados usados. Cada valor sai de variável do Figma ou do get_design_context, e cada componente aponta o node-id e o equivalente de hoje nas telas B. Decisão D-304.

## Tried and ruled out
- Artifact privado no claude.ai: o usuário preferiu versionar junto do código, como insumo da K-048.
- Extrair só a página Telas – v1: faltariam as variantes que estão na página Componentes.
- Guardar capturas PNG das telas: pesam e envelhecem; o link do Figma por node-id basta.

## Watch out
- A extração não é o CSS do sistema: o componentes.css (prefixo ds-) é referência de medidas. O que pode ser copiado como está é o tokens.css.
- Três pares de cor do Figma ficam abaixo do WCAG: cinza terciário #808080 (3,78:1), borda do campo #ccc (1,54:1) e sublinhado amarelo do item ativo #fdea00 (1,19:1). A K-048 precisa resolver isso antes de adotar os tokens.
- O Figma não desenha hover, foco, erro, desligado nem modo escuro; as regras atuais de docs/telas/design-system.md continuam valendo.
- Os ícones das páginas são aproximações Lucide; os SVG reais do componente "Icons" ainda precisam ser exportados. Proxima Nova é paga e não está no repositório.

In the code:
- docs/design-system-figma/{index,tokens,componentes,telas}.html, tokens.css, componentes.css, doc.css
- Figma fileKey aMiF7hiCBPNc1X9yYFuZO6, páginas 266:5193 e 11:33
- get_variable_defs falha no nó da página (canvas); funciona nas seções 266:5194, 266:5196, 266:5198, 266:5200
