---
title: Texto de um passo desligado do infográfico não pode contar variável nem mudar o hash da revista
author: Otavio
date: 2026-11-10
branch: feat/f2-f2
id: l-7c9c957c
scope: repo
status: active
src: agent
touches:
  - app/nucleo/servicos/resolver.py
  - app/nucleo/models/revista.py
  - app/nucleo/servicos/empacotar.py
---

## Decided
- Os textos dos cliques de progressão e de habilidades só são renderizados quando o passo está ligado; desligado, o texto sai vazio e nenhuma variável dele entra na lista das usadas. O texto do descritor sempre conta, porque o descritor nunca desliga.
- O resolvido do F2 traz dados crus (habilidade, código, texto, descritor, rótulos), e só os textos dos cliques e a análise do item saem renderizados; o gerador do SVG faz o escape.
- Até a tarefa 6, o zip lê o hash do SVG antigo com fallback para o da revista: na revista ativa a conferência já era sempre verdadeira, então a ponte não perde nada.

## Tried and ruled out
- Renderizar os três textos sempre: uma variável vazia num texto que nunca aparece virava pendência "Variáveis sem valor" e bloqueava o "Validado"; editar um texto invisível também mudava o hash.

## Watch out
- Ao incluir os infográficos no resolvido, o hash de toda revista muda uma vez e o "Validado" cai (D-237): esperado, não é regressão.
- Teste de migração que compara o resolvido antes e depois precisa ignorar a chave dos infográficos.

In the code:
- app/nucleo/servicos/resolver.py: montagem de f2.infograficos e pendência "infografico"
- app/nucleo/models/revista.py: PASSOS = ("descritor", *PASSOS_DESLIGAVEIS)
- app/nucleo/servicos/empacotar.py: .get("svg_sha256", revista.svg_sha256) até a tarefa 6
- teste: test_texto_de_passo_desligado_nao_conta_variavel em test_resolver
