---
title: "Passos paralelos que só dependem da base não precisam de commit local, e os PDFs grandes de exemplo ficam fora do app"
author: Otavio
date: 2026-10-29
branch: refatoracao-django
cost: { minutes: 8, tokens: 191152 }
id: l-a4bd7b17
scope: repo
status: active
src: agent
touches:
  - state.md
---

## Decided
- Na Fase B da refatoração Django, cada passo roda num worktree próprio criado a partir do topo de refatoracao-django e termina sem commit. O commit local por passo da Fase A só existia porque S02 e S03 precisavam enxergar o passo anterior.
- Os PDFs SAEGO de exemplo (10–11 MB cada) não são copiados para dentro do app. O teste do importador lê de uma pasta montada no container e é pulado quando o arquivo falta.

## Tried and ruled out
- Copiar os 3 PDFs para as fixtures de teste: 31 MB no git.

## Watch out
- O PDF Alfa (2EF/5EF) não está no repositório, só na máquina do usuário.
- Na Fase B só o passo de perfis (S14) pode criar migração. Os outros passam o usuário como parâmetro em vez de mudar o modelo (ex.: a foto exige criada_por).

In the code: decisão D-134 no state.md; branches feat/s04..s14; PDFs em examples/ (LP, MT) e ~/Documentos (Alfa); montar com `docker compose run --rm -v "$PWD/examples:/pdfs:ro" app ...`.
