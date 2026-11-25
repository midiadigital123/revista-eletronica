---
title: "Tirar uma seção de um template exige apagar as cópias dela nas revistas, senão o texto continua aparecendo"
author: Otavio
date: 2026-11-25
branch: feat/f1-sem-fechamento
id: l-e6017437
scope: repo
status: active
src: agent
touches:
  - app/e2e/fixtures/pagina/f1.html
  - app/e2e/fixtures/revista.zip
  - app/e2e/tests/impacto.spec.ts
  - app/e2e/tests/impresso.spec.ts
  - app/e2e/tests/painel.spec.ts
  - app/e2e/tests/revista-textos.spec.ts
  - app/nucleo/servicos/html.py
  - app/nucleo/templates/revista/f1.html
  - app/nucleo/tests/test_admin_templates.py
  - app/nucleo/tests/test_resolver.py
---

## Decided
Em 25/11 o F1 deixou de ter a seção "fechamento" (D-296). Além de tirar a seção da lista do fascículo, da página e do seed, uma migração de dados cria uma versão nova de cada template F1 sem o bloco e apaga as cópias da seção que as revistas tinham, inclusive de revista arquivada (a foto dela não muda).

## Tried and ruled out
Editar os templates pela tela e deixar as cópias: o resolver mantém cópia de seção que saiu do template (cópia órfã, com o título da versão de onde saiu). O texto seguiria no hash do "Validado", no "o que mudou" do impresso e na tela de textos da revista.
Trocar o texto F1 de exemplo dos testes para uma seção só: os testes de cópia, desatualizada e removida precisam de duas seções; o exemplo grava sem passar pela validação, então ficou com fechamento, com comentário.

## Watch out
Uma tupla de um item precisa da vírgula: ("introducao") é texto, e a validação passa a conferir letra por letra, recusando todo template.
Formatador do editor (Prettier) em arquivo .hbs junta as linhas e quebra o formato "## id / título / linha em branco / corpo".
Regerar os gabaritos com REGERAR_FIXTURES=1: a página do F1 e o revista.zip do Playwright mudam.

In the code: app/nucleo/migrations/0028_f1_sem_fechamento.py, app/nucleo/servicos/resolver.py (laço das cópias órfãs), app/nucleo/texto.py SECOES_F1.
