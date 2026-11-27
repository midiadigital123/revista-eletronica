---
title: "O infográfico de Matemática usa o mesmo SVG do de Português, com as tarefas por nível decididas pelo componente"
author: Otavio
date: 2026-11-27
branch: feat/f2-mt
id: l-7b70bbe5
scope: repo
status: active
src: agent
touches:
  - app/e2e/tests/helpers.ts
  - app/e2e/tests/infografico.spec.ts
  - app/nucleo/infografico.py
  - app/nucleo/models/revista.py
  - app/nucleo/servicos/f2.py
  - app/nucleo/servicos/pendencias.py
  - app/nucleo/servicos/resolver.py
  - app/nucleo/templates/revista/f2.svg
  - app/nucleo/templates/ui/parciais/revista_infograficos.html
  - app/nucleo/tests/test_f2.py
---

## Decided
Em 27/11 chegou a informação de que, em MT (todo parceiro, Alfa e Outras Etapas), o bloco "Tarefas por nível de complexidade" não usa [Descritor · Etapa · Item]: são 4 linhas com barrinhas 1 a 4, o texto da habilidade e a coluna Itens igual à de LP. Ficou um SVG só, com um ramo nas linhas do bloco, porque o resto do infográfico é igual e dois arquivos obrigariam a corrigir tudo duas vezes. O usuário escolheu: texto longo faz a linha crescer (como a tabela de habilidades), o modal do item se chama "Nível N", e o texto da habilidade nos 4 itens é pendência para validar.

## Tried and ruled out
- SVG separado para MT: duplica ~200 linhas.
- Campo "modelo das tarefas" no infográfico: nenhum caso pede LP por nível; a regra é o componente.
- Guardar o texto no campo descritor: limite de 20 caracteres e outro sentido.
- Limite de caracteres ou reticências: o usuário quer o texto inteiro na tela inicial.

## Watch out
- `por_nivel` e `habilidade` só entram no resolvido de MT: o hash (Validado) de LP não muda. Foto arquivada antiga não tem a chave; quem lê usa `.get("por_nivel")`.
- O ramo LP do f2.svg sai byte a byte igual; a regra CSS `.f2-niv` só é escrita quando `por_nivel`, senão o SVG de toda revista de LP mudaria.
- O seed dos Word (carregar_infograficos) segue só LP; não existe seed de MT.

In the code: `TAREFAS_POR_NIVEL` em app/nucleo/models/revista.py; `f2._tarefas` (geometria e crescimento); bloco `f2-tarefas` em templates/revista/f2.svg; campo `RevistaInfograficoItem.habilidade` (migração 0030); D-305 no state.md.
