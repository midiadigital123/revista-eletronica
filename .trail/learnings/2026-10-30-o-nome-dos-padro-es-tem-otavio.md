---
title: "O nome dos padrões tem um valor do ano, guardado junto da cor, e o projeto só preenche pd01 a pd05 para trocá-lo"
author: Otavio
date: 2026-10-30
branch: refatoracao-django
cost: { minutes: 4, tokens: 17747 }
id: l-9618ae3b
scope: repo
status: active
replaces: l-7411a4e0
src: agent
touches:
  - state.md
  - docs/variaveis.md
---

## Decided
- Cada padrão de desempenho (1 a 5) tem um nome por ano, guardado junto da cor do padrão. Em 2026, o padrão é "Padrão 01" a "Padrão 05".
- O projeto sobrescreve esse nome preenchendo pd01..pd05. Quando o pdNN está vazio, vale o nome do ano. A regra é a mesma da cor: valor do ano, com sobrescrita do projeto.
- O valor efetivo vale para o rótulo do padrão na escala do F1 e para {{pdNN}} nos textos. Pendência só quando o projeto e o ano estão vazios.
- O nome é impresso, então trocar o nome do ano muda o hash das revistas que não o sobrescrevem.
- nome_parceiro é automático e vem do cadastro do parceiro; não existe coluna manual para ele. A planilha usa <<x>>, mas o sistema continua com {{x}}.

## Tried and ruled out
- Exigir o pdNN em todo projeto, com vazio gerando pendência: foi a primeira versão, e o usuário corrigiu, porque o nome é definido uma vez e o projeto só sobrescreve.
- Ação em lote que grava o pdNN em vários projetos: o valor ficaria duplicado em cada projeto.
- Nome padrão por parceiro/programa: o usuário escolheu por ano.
- Coluna manual nome_parceiro: o valor ficaria duplicado com o cadastro.

## Watch out
- Na planilha recebida, os exemplos de singular e plural do adjetivo pátrio estão trocados, e "no_na_ em_nome_parceiro" tem um espaço no nome.
- Branches paralelas que regeram o revista.zip do e2e sempre conflitam nele, porque é binário. Pegue um lado e regere com REGERAR_FIXTURES=1.

In the code: CorPadrao.nome (models/cadastro.py), servicos/resolver.py (rotulo_do_padrao e a montagem das variáveis), abrir_ano copia o nome, carregar_cadastros cria "Padrão 0N", docs/variaveis.md. Implementação em feat/nome-padrao (D-175).
